/** @odoo-module **/

import { registry } from "@web/core/registry";
import { TextField } from "@web/views/fields/text/text_field";
import { useEffect, useRef } from "@odoo/owl"; // Importamos herramientas clave de Owl

export class AiTriggerField extends TextField {
    // Usamos la apariencia estándar
    static template = "web.TextField";

    setup() {
        super.setup();
        
        // 1. "Enganchamos" el elemento textarea del HTML estándar
        // Odoo llama internamente "textarea" a la referencia del campo de texto
        this.textareaRef = useRef("textarea");

        // 2. Usamos useEffect: Esto se ejecuta cuando el componente aparece en pantalla
        useEffect(() => {
            const textareaEl = this.textareaRef.el;
            if (!textareaEl) return;

            // Definimos qué hacer al pulsar una tecla
            const onKeydownHandler = (ev) => {
                // Si es ENTER y NO es Shift (para permitir saltos de línea con Shift+Enter)
                if (ev.key === "Enter" && !ev.shiftKey) {
                    console.log("🚀 Widget IA: ENTER detectado. Ejecutando acción...");
                    
                    ev.preventDefault();  // Evita el salto de línea
                    ev.stopPropagation(); // Evita que Odoo haga otras cosas

                    // Buscamos el botón en la vista de formulario actual
                    // Usamos ?. por seguridad
                    const btn = textareaEl.closest('.o_form_view')?.querySelector('.btn-ai-generate');
                    
                    if (btn) {
                        console.log("🖱️ Botón encontrado. Click enviado.");
                        btn.click();
                    } else {
                        console.warn("⚠️ Widget IA: No encuentro el botón '.btn-ai-generate'. ¿Está en el XML?");
                    }
                }
            };

            // CONECTAMOS EL CABLE: Añadimos el evento manualmente
            textareaEl.addEventListener("keydown", onKeydownHandler);

            // DESCONECTAMOS EL CABLE: Limpieza cuando se cierra la vista (importante para evitar errores)
            return () => {
                textareaEl.removeEventListener("keydown", onKeydownHandler);
            };
        });
    }
}

// Registro del componente
export const aiInstructionTrigger = {
    component: AiTriggerField,
    displayName: "AI Trigger",
    supportedTypes: ["text"],
};

registry.category("fields").add("ai_instruction_trigger", aiInstructionTrigger);