{
    "name": "Sancho Assistant AI",
    "version": "1.0",
    "summary": "Chatbot con IA local",
    "description": "Chat bot para tareas rutinarias de cualquier empresa: nóminas, facturas, presupuestos... Actualmente solo realizar presupuestos ya que es un prototipo",
    "author": "IA-Men",
    "depends": ["sale_management", "web"],
    "data": [
        "security/ir.model.access.csv",
        "views/sancho_assistant_ai_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "sancho_assistant_ai/static/src/js/ai_widget.js",
        ],
    },
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}