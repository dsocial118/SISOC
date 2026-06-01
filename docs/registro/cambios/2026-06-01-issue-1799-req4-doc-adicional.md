# 2026-06-01 — Issue #1799 (Req 4): Documentacion Adicional en el legajo de Organizacion

Rama: `claude/issue-1799-req4-doc-adicional-org` (apilada sobre Fase 0)
Plan: [docs/plans/2026-06-01-issue-1799-documentacion-organizacion-admisiones.md](../../plans/2026-06-01-issue-1799-documentacion-organizacion-admisiones.md)

## Resumen

Habilita cargar "Documentacion Adicional" (documentos personalizados, sin
catalogo) en el legajo de la Organizacion, como ya existe en Admisiones. Opcional,
requiere nombre + archivo, se pueden agregar N.

## Cambios

- Modelo `ArchivoOrganizacion` (organizaciones/models.py):
  - `documentacion` pasa de FK obligatoria `PROTECT` a `null=True, blank=True, on_delete=SET_NULL`.
  - Nuevo `nombre_personalizado` (CharField nullable).
  - Propiedades `es_personalizado` y `nombre_documento`; `__str__` ya no asume catalogo.
- Migracion [0014_archivoorganizacion_nombre_personalizado_and_more.py](../../../organizaciones/migrations/0014_archivoorganizacion_nombre_personalizado_and_more.py): AlterField + AddField (no destructiva).
- Vista `agregar_documento_personalizado_organizacion` (organizaciones/views.py) + ruta `organizacion_documento_personalizado_agregar` (organizaciones/urls.py). Valida permisos de envio (tecnico/superuser), nombre y archivo.
- `_build_documentacion_organizacion_rows` ahora incluye los personalizados; helper `_render_documentacion_organizacion_personalizado_row` para el alta AJAX.
- Template: partial `documentacion_organizacion_row.html` soporta personalizados (nombre libre, badge "Adicional", sin historial/re-subida); seccion "Documentacion Adicional" en `organizacion_detail.html`.
- JS `organizacionesDocumentos.js`: alta del personalizado (validacion de nombre, file picker, XHR con progreso, append de la fila).

## Alcance / decisiones

- El ciclo de estado (Documento adjunto → A Validar → Aceptado/Rectificar) y la
  edicion de vencimiento aplican a los personalizados sin codigo nuevo (los
  endpoints son por `archivo_id`).
- **Materializacion org → admision de personalizados: diferida al Req 1**, donde se
  arma el flujo de sincronizacion integral. Hacer `documentacion` nullable NO rompe
  el `congelar_documentacion_organizacional` actual (itera el catalogo e ignora los
  `documentacion_id=None`).
- No se agrega endpoint de borrado (no existe para documentacion de organizacion).

## Validacion

Entorno local Windows (venv Django 4.2.27, sqlite; Docker apagado):

- `pytest organizaciones/` → 27 passed (incluye `test_documento_personalizado.py`).
- `manage.py makemigrations --check --dry-run organizaciones admisiones` → sin cambios.
- `manage.py migrate organizaciones` (sqlite) → aplica 0014 OK.
- `black` y `djlint --check` sobre los archivos tocados → limpio.
