# Cambio: preservar snapshot historico al editar FormularioCDI

Fecha: 2026-03-13

## Problema
- La vista de edicion de `FormularioCDI` reutilizaba `initial` construido desde el `CentroDeInfancia`.
- Cuando el centro cambiaba despues de crear el formulario, los campos snapshot (`cdi_name`, `cdi_street` y equivalentes) se mostraban con datos actuales del centro en lugar de los valores historicos persistidos en el formulario.

## Ajuste aplicado
- `FormularioCDIEditBaseView.build_form()` solo carga `initial` desde el centro al crear un formulario nuevo.
- En edicion, el form se instancia unicamente con la `instance` para respetar el snapshot historico guardado en `FormularioCDI`.

## Validacion
- `docker compose exec django pytest -n auto centrodeinfancia/tests/test_formulario_cdi_views.py -k test_formulario_cdi_editar_preserva_snapshot_historico_del_centro`
- `docker compose exec django pytest -n auto centrodeinfancia/tests/test_formulario_cdi_views.py`
