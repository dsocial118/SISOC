# 2026-08-13 - Certificaciones de prestaciones sin fuente

## Contexto

La PWA permitía registrar la conformidad cuando faltaba informe técnico o convenio,
pero omitía la generación del PDF. El Legajo mostraba esos registros como
"No disponible".

## Cambios aplicados

- Se incorpora una fuente fallback explícita con prestaciones en cero.
- El PDF generado con fallback incorpora la leyenda "Datos de prestaciones no disponibles.".
- Se conserva el rollback: ante fallas de generación o storage no se guarda la conformidad.

## Impacto esperado

Las conformidades nuevas, tanto Sí como No, siempre tendrán PDF descargable en PWA y
Legajo. Los registros históricos sin archivo no se modifican.

## Validación

- Tests de API y de la transformación de la plantilla DOCX.

## Riesgos y rollback

El PDF fallback declara explícitamente la falta de datos y no atribuye prestaciones
inexistentes. Revertir el cambio restaura el comportamiento anterior para nuevas altas.
