# Tipos de convenio disponibles en el Gestor de templates

## Cambio visible

Al crear una plantilla lógica de Informe Técnico, el campo **Tipo de
convenio** sólo ofrece estas condiciones:

- Personería jurídica.
- Personería jurídica eclesiástica.
- Asociación de hecho.

La tercera opción toma el valor existente **Organización Base** del catálogo
`TipoConvenio`. Es una etiqueta funcional del Gestor: no renombra el catálogo
ni modifica el tipo de convenio guardado en las admisiones existentes.

## Regla

El formulario consulta los registros `TipoConvenio` vigentes por nombre y
rechaza cualquier valor distinto, incluso si se intenta enviar manualmente en
la solicitud. Así quedan fuera los valores no utilizables para esta selección,
por ejemplo `Sin uso`.
