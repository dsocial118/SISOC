# Admisiones: bloqueos de eliminación y finalización de informe técnico

## Fecha
2026-04-23

## Objetivo
Evitar inconsistencias en admisiones bloqueando eliminaciones de documentos en etapas cerradas y evitando finalizar informes técnicos con documentación obligatoria incompleta o sin validar.

## Alcance
Se aplicaron cambios backend y frontend sobre eliminación de documentos, copy del modal de confirmación y validaciones de finalización de informe técnico; se agregaron tests unitarios de regresión asociados.

## Archivos tocados
- admisiones/services/informes_service/impl.py
- admisiones/views/web_views.py
- admisiones/templates/admisiones/admisiones_tecnicos_form.html
- admisiones/templates/admisiones/includes/documento_row.html
- static/custom/js/admisionestecnico.js
- admisiones/tests/test_documento_row_template.py
- tests/test_admisiones_web_views_unit.py
- tests/test_informes_service_unit.py

## Cambios realizados
- Se bloqueó en backend la eliminación de documentos cuando `estado_admision` está en `informe_tecnico_finalizado` o estados posteriores.
- Se ocultó en UI el botón `Eliminar` en esos mismos estados.
- Se simplificó el modal de eliminación para mostrar solo confirmación y nombre del archivo.
- Se bloqueó `guardar_informe(..., action="submit")` cuando faltan obligatorios cargados.
- Se bloqueó `guardar_informe(..., action="submit")` cuando hay obligatorios cargados pero no validados.
- Se agregaron tests unitarios para los bloqueos de eliminación y de finalización.

## Supuestos
- La finalización del informe técnico debe requerir documentación obligatoria completa y validada.
- Los estados posteriores a `informe_tecnico_finalizado` mantienen bloqueo de eliminación.

## Validaciones ejecutadas
- `python -m pytest -q tests/test_admisiones_web_views_unit.py tests/test_informes_service_unit.py admisiones/tests/test_documento_row_template.py -k "eliminar_archivo_admision_bloqueado_si_informe_finalizado or guardar_informe_submit_bloquea_si_faltan_obligatorios or guardar_informe_submit_bloquea_si_obligatorios_no_validados or boton_eliminar"` -> no ejecutable (`No module named pytest`).

## Pendientes / riesgos
- Ejecutar tests en entorno con `pytest` disponible (local o contenedor del proyecto).
- Commit/push en la rama actual si se habilita escritura de índice git en este entorno.
