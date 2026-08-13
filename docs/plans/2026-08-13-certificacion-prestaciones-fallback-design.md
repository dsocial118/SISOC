# Certificaciones de prestaciones sin fuente

## Diseño aprobado

Cuando una conformidad no tenga informe técnico ni convenio disponible, SISOC genera
el PDF con prestaciones en cero y la leyenda **"Datos de prestaciones no disponibles."**

## Flujo

1. La API resuelve informe o convenio como hasta ahora.
2. Si no existe, usa una fuente fallback explícita, sin persistir datos inventados.
3. El generador inserta la leyenda antes de la tabla y guarda el PDF.
4. Si la generación o el guardado fallan, se elimina la conformidad y se responde 503.

## Validación

- Prueba API para la fuente ausente, URL de descarga y persistencia del PDF.
- Prueba unitaria que inspecciona el DOCX intermedio y verifica la leyenda.
