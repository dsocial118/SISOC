# Issue 1901: seguimiento de certificaciones mensuales

## Objetivo

Corregir la advertencia de certificación pendiente y presentar el historial de
PDF mensuales en una sección propia del legajo del comedor.

## Cambios

- Web y PWA consideran pendiente exclusivamente el mes calendario anterior y
  ocultan la advertencia cuando existe una conformidad para ese comedor y
  período, incluido el cambio de año.
- El legajo muestra los seis PDF más recientes en la card
  `Certificaciones Mensuales de Prestaciones`, ubicada antes de Colaboradores.
- La card informa período, usuario generador, fecha de certificación y acceso
  al PDF.
- Se incorporó una vista paginada para consultar el historial completo.

## Compatibilidad

La regla y la card usan `PrestacionAlimentariaConformidad`, fuente que ya
almacena la certificación generada por la PWA para todos los programas. No se
agregan modelos ni migraciones.
