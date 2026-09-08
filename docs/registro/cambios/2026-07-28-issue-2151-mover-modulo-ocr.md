# Issue 2151: mover módulo OCR en el sidebar

## Objetivo

Hacer visible el acceso al módulo OCR para usuarios que poseen el permiso
`ocr.use_ocr`, sin depender de que tengan acceso a Administración del sistema.

## Cambios

- OCR deja de estar dentro de Administración del sistema y pasa a ser una
  sección principal del sidebar.
- La sección queda entre Configuración de Comedores y Comunicados.
- Se conservan la URL `/ocr/` y el permiso `ocr.use_ocr`; no se amplía el
  acceso a usuarios sin ese permiso.

## Validación

- `scripts/ai/codex_run.ps1 test core/tests/test_sidebar_menu.py ocr/tests/test_views.py -q`
