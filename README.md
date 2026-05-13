# Sancho Assistant AI 🤖

### Prototipo de Automatización Inteligente On-Premise para Odoo ERP

**Sancho Assistant AI** es un proyecto desarrollado originalmente durante un Hackathon/Datathon, diseñado para democratizar el acceso a la Inteligencia Artificial en PYMEs, priorizando la seguridad de los datos y el cumplimiento del RGPD.

## 🌟 El Problema
Muchas empresas no adoptan IAs generativas por el riesgo de enviar datos sensibles (facturación, datos de clientes) a nubes públicas. Esto genera una brecha tecnológica por miedo a vulnerar la privacidad.

## 🚀 La Solución
Un plugin nativo para **Odoo** que interactúa con un servidor de inferencia de IA **On-Premise** (local).
- **Privacidad Total:** Los datos nunca abandonan la infraestructura de la empresa.
- **Lenguaje Natural:** El usuario solicita acciones (ej: "Crea un presupuesto para el cliente X con 5 sillas") y la IA procesa la orden.
- **Automatización:** Extracción de entidades (productos, cantidades) y ejecución de acciones directamente sobre la base de datos de Odoo.

## 🛠️ Stack Tecnológico
- **ERP:** Odoo (Python)
- **Lógica de IA:** Modelos de Lenguaje Locales (LLMs)
- **Base de Datos:** PostgreSQL
- **Comunicación:** JSON API / REST

## 📂 Estructura del Repositorio
- `sancho_assistant_ai/`: Carpeta del módulo lista para instalar en Odoo.
  - `models/`: Lógica de negocio en Python.
  - `views/`: Interfaz de usuario en XML.
  - `security/`: Reglas de acceso y permisos.
  - `static/`: Recursos visuales del módulo.

## 📝 Estado del Proyecto
Este repositorio contiene el **MVP (Producto Mínimo Viable)** funcional presentado en el Hackathon, centrado en la generación inteligente de presupuestos.
