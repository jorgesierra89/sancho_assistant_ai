from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import json
import re


class SaleOrder(models.Model):
    _inherit = "sale.order"

    ai_instruction = fields.Text(
        string="Instrucción IA",
        placeholder="Ej: Cliente quiere 2 portátiles y 5 sillas con 10% de descuento..."
    )
    ai_conversation = fields.Text(
        string="Chat IA",
        readonly=True
    )

    def action_generate_chat(self):
        """Acción principal invocada por el botón de la vista"""
        if not self.ai_instruction:
            raise UserError("¡Escribe primero qué necesita el cliente!")

        # 1. Normalización y detección de PDF
        instruction_text = self.ai_instruction.lower()
        generate_pdf_flag = False
        keywords_pdf = ["genera", "generar", "imprimir", "descargar"]

        if "pdf" in instruction_text and any(verb in instruction_text for verb in keywords_pdf):
            generate_pdf_flag = True
            instruction_text = instruction_text.replace("pdf", "")
            for verb in keywords_pdf:
                instruction_text = instruction_text.replace(verb, "")
            instruction_text = instruction_text.strip()

        # 2. Llamada a la IA
        raw_response, items = self._ask_mistral(instruction_text)

        # 3. Actualizar chat
        self._append_to_chat(f"👤 Tú: {self.ai_instruction}")
        self.ai_instruction = ""

        # 4. Procesar líneas
        return self._create_lines_chat(items, generate_pdf=generate_pdf_flag)

    def _ask_mistral(self, text):
        """Llamada a la API local de Ollama"""
        url = "http://localhost:11434/api/generate"

        prompt = f"""
        Tu tarea es interpretar pedidos de venta y devolver un JSON.

        EJEMPLO 1:
        Usuario: "Quiero un ratón"
        Tú: [{{"qty": 1, "product": "ratón", "discount": 0}}]

        EJEMPLO 2 (Descuentos):
        Usuario: "2 pantallas con 10% y 5 teclados con el 20% de dto"
        Tú: [{{"qty": 2, "product": "pantalla", "discount": 10}}, {{"qty": 5, "product": "teclado", "discount": 20}}]

        Instrucciones:
        1. Extrae cantidad, nombre del producto y DESCUENTO (si existe, sino 0).
        2. Convierte nombres a SINGULAR (ej: "mesas" -> "mesa").
        3. Devuelve solo una lista JSON.

        Usuario: "{text}"
        Sólo JSON:
        """

        try:
            payload = {
                "model": "mistral",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.0, "num_ctx": 4096},
            }
            response = requests.post(url, json=payload, timeout=30)
            data = response.json()
            raw_response = data.get("response", "")

            match = re.search(r"\[.*\]", raw_response, re.DOTALL)
            json_str = match.group(0) if match else "[]"
            parsed = []
            try:
                parsed = json.loads(json_str)
                if isinstance(parsed, dict):
                    parsed = [parsed]
            except:
                pass

            return raw_response, parsed

        except Exception as e:
            raise UserError(f"Error conexión IA: {e}")

    def _append_to_chat(self, message):
        if self.ai_conversation:
            self.ai_conversation += "\n" + message
        else:
            self.ai_conversation = message

    def _create_lines_chat(self, items, generate_pdf=False):
        Lines = self.env["sale.order.line"]
        Products = self.env["product.product"]

        for index, item in enumerate(items):
            qty = item.get("qty") or item.get("cantidad") or 1
            discount = item.get("discount") or item.get("descuento") or 0.0
            search_term = item.get("producto") or item.get("product") or "Desconocido"
            search_term = str(search_term).strip()

            match = re.match(r"(\d+)\s+(.*)", search_term)
            if match:
                qty = int(match.group(1))
                search_term = match.group(2).strip()

            domain = [("name", "ilike", search_term), ("sale_ok", "=", True)]
            products = Products.search(domain)

            if not products and len(search_term) > 3:
                singular_term = False
                if search_term.lower().endswith("s"):
                    singular_term = search_term[:-1]
                if search_term.lower().endswith("es"):
                    singular_term = search_term[:-2]

                if singular_term:
                    products = Products.search([
                        ("name", "ilike", singular_term),
                        ("sale_ok", "=", True)
                    ])

            if len(products) > 1:
                remaining_items = items[index + 1:]

                wizard = self.env["ai.product.selection.wizard"].create({
                    "order_id": self.id,
                    "product_ids": [(6, 0, products.ids)],
                    "qty": qty,
                    "discount": discount,
                    "remaining_items_json": json.dumps(remaining_items),
                    "should_generate_pdf": generate_pdf,
                })

                self._append_to_chat(
                    f"🤖 Sancho: Encontré {len(products)} opciones para '{search_term}'. Por favor elige."
                )

                return {
                    "name": f"Elige: {search_term}",
                    "type": "ir.actions.act_window",
                    "res_model": "ai.product.selection.wizard",
                    "view_mode": "form",
                    "res_id": wizard.id,
                    "target": "new",
                }

            if not products:
                Lines.create({
                    "order_id": self.id,
                    "display_type": "line_note",
                    "name": f"⚠️ No encontré: '{search_term}'",
                })
                self._append_to_chat(f"🤖 Sancho: No encontrado: '{search_term}'")
                continue

            product = products[0]
            Lines.create({
                "order_id": self.id,
                "product_id": product.id,
                "name": product.name,
                "product_uom_qty": qty,
                "price_unit": product.list_price,
                "discount": float(discount),
            })

            msg_desc = f" con {discount}% dto" if discount else ""
            self._append_to_chat(f"🤖 Sancho: Añadido {product.name} (x{qty}){msg_desc}")

        if generate_pdf:
            self.env.cr.commit()
            self._append_to_chat("🤖 Sancho: Pedido completado. Generando PDF...")
            return self.action_generate_pdf()

        return None

    def action_generate_pdf(self):
        action = self.env.ref("sale.action_report_saleorder").report_action(self)
        action["close_on_report_download"] = True
        return action


# ---------------------------------------------------------
# WIZARD
# ---------------------------------------------------------

class AiProductSelectionWizard(models.TransientModel):
    _name = "ai.product.selection.wizard"
    _description = "Elegir producto Sancho"

    order_id = fields.Many2one("sale.order", string="Presupuesto")
    product_ids = fields.Many2many("product.product", string="Opciones encontradas")
    selected_product_id = fields.Many2one(
        "product.product",
        string="Elige el correcto",
        domain="[('id', 'in', product_ids)]"
    )
    qty = fields.Float(string="Cantidad")
    discount = fields.Float(string="Descuento (%)")

    remaining_items_json = fields.Text()
    should_generate_pdf = fields.Boolean(string="Generar PDF al finalizar")

    def action_confirm_selection(self):
        if not self.selected_product_id:
            raise UserError("Debes seleccionar un producto.")

        self.env["sale.order.line"].create({
            "order_id": self.order_id.id,
            "product_id": self.selected_product_id.id,
            "product_uom_qty": self.qty,
            "price_unit": self.selected_product_id.list_price,
            "discount": self.discount,
        })

        msg_desc = f" (-{self.discount}%)" if self.discount else ""
        self.order_id._append_to_chat(
            f"✅ Tú elegiste: {self.selected_product_id.name}{msg_desc}"
        )

        items_pendientes = []
        if self.remaining_items_json:
            try:
                items_pendientes = json.loads(self.remaining_items_json)
            except:
                items_pendientes = []

        if items_pendientes:
            next_action = self.order_id._create_lines_chat(
                items_pendientes,
                generate_pdf=self.should_generate_pdf
            )
            if next_action:
                return next_action

            return {"type": "ir.actions.act_window_close"}

        if self.should_generate_pdf:
            self.order_id._append_to_chat(
                "🤖 Sancho: Selección completada. Generando PDF..."
            )
            return self.order_id.action_generate_pdf()

        return {"type": "ir.actions.act_window_close"}

    def action_cancel_selection(self):
        self.order_id._append_to_chat("❌ Selección cancelada.")
        return {"type": "ir.actions.act_window_close"}
