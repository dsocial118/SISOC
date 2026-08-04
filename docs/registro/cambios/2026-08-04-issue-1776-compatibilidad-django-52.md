# Compatibilidad previa para Django 5.2

## Contexto

Primera etapa de la issue #1776. Mantiene Django 4.2.27 para aislar el cambio de
framework de la actualizacion del ecosistema y de los ajustes de compatibilidad.

## Cambios

- El logout web usa POST con CSRF en todos sus controles, en lugar de GET.
- Los HTML constantes dejan de llamar `format_html()` sin argumentos y usan
  `mark_safe()` de forma explicita.
- Se alinean las librerias Django con versiones compatibles con 4.2 y 5.2.
- Se actualizan `diff-match-patch` y `tablib` al contrato requerido por
  `django-import-export` 4.3.
- El admin conserva la exportacion completa por formato mediante `ExportForm`,
  evitando introducir la seleccion parcial de columnas de la version 4.x.
- Se retiran `django-select2`, `django-multiselectfield` y `django-appconf`, sin
  consumidores detectados en codigo ni migraciones.
- El smoke generico de URLs trata logout como POST y declara su dependencia de
  base de datos de forma explicita.

## Riesgos y controles

- `django-import-export` 4.x contiene cambios incompatibles; se conservaron los
  formatos CSV/XLSX explicitos y la exportacion completa, cubiertos por los tests
  de preview, confirmacion, importacion y exportacion.
- Los cambios de paquetes pueden incorporar migraciones de terceros; el chequeo
  de migraciones propias no detecto cambios, pero CI debe repetirlo sobre MySQL.
- La generacion OpenAPI concluye con codigo 0, aunque mantiene deuda preexistente:
  128 warnings y 155 errores de inferencia que no se corrigen en esta issue.

## Validacion

- Resolver de dependencias sobre Python 3.12 y Django 4.2: exitoso.
- Resolver temporal sobre Django 5.2.16: exitoso; el pin final de este PR sigue
  siendo Django 4.2.27.
- Chequeo estatico de los cinco controles de logout: POST + CSRF, sin enlaces GET.
- Barrido AST de `format_html()` sin argumentos: sin hallazgos.
- `pip check`, `manage.py check` y `makemigrations --check --dry-run`: exitosos.
- Suite focalizada de auth, API, ticketera, import/export y auditoria: 138 passed,
  1 skipped.
- Suite completa en Docker/SQLite: 3839 passed, 8 skipped. Las tres warnings de
  logout GET detectadas en esa corrida quedaron corregidas; el smoke focalizado
  posterior pasa 3/3 con warnings tratados como errores.
- Generacion/validacion OpenAPI y `collectstatic --dry-run`: comandos exitosos,
  con la deuda de inferencia OpenAPI detallada arriba.
