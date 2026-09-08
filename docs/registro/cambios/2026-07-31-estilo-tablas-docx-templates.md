# Estilo de tablas en DOCX de templates dinámicos

Fecha: 2026-07-31

## Cambio visible

Las tablas insertadas en una versión publicada del Gestor de templates se
generan en el DOCX con bordes finos, margen interno en cada celda y alineación
vertical centrada. Si la primera fila fue definida con encabezados HTML
`<th>`, recibe además un fondo celeste suave.

El autor del template sólo debe usar la estructura semántica `table`, `th` y
`td`; no necesita agregar CSS de bordes al contenido.

## Alcance

El formato se aplica únicamente al DOCX generado desde una versión publicada
del Gestor de templates. Los documentos históricos que usan el fallback HTML
mantienen su comportamiento actual.
