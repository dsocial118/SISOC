# Issue 2153: mover expedientes de pago a Comedores

## Objetivo

Ubicar el acceso a expedientes de pago dentro de `Legajos → Comedores` y
eliminar el submenú redundante de importación.

## Cambios

- El enlace directo `Expedientes de Pago` queda como cuarto ítem de Comedores,
  después de Ver Comedores, Admisión - Comedores y Acompañamiento.
- Se elimina la entrada independiente `Importar Expediente de Pago` y su opción
  `Ver Importar Expediente de Pago`.
- El acceso conserva el permiso
  `importarexpediente.view_archivosimportados` y la URL existente
  `importarexpedientes/listar`.
- Los usuarios que solo tienen permiso de importación continúan viendo el
  enlace dentro de Comedores, sin obtener acceso al listado de comedores.

## Validación

- `scripts/ai/codex_run.ps1 test core/tests/test_sidebar_menu.py -q`
