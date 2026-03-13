# Cambio: correcciones de review para Formulario CDI

Fecha: 2026-03-13

## Qué se corrige
- La edición de `FormularioCDI` deja de inyectar valores actuales de `CentroDeInfancia` sobre snapshots históricos ya guardados.
- El detalle de `CentroDeInfancia` deja de exponer la card y el resumen de formularios cuando el usuario no tiene `centrodeinfancia.view_formulariocdi`.
- Se corrige el estado vacío de la tabla de formularios para evitar markup inválido en el `tbody`.

## Validación prevista
- Test de regresión para preservar snapshots históricos en la pantalla de edición.
- Test de permisos para verificar que el detalle del CDI no expone formularios sin el permiso específico.
- `pytest` focalizado en `centrodeinfancia/tests/test_formulario_cdi_views.py`.
