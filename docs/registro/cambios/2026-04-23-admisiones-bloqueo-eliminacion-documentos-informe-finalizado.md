# Admisiones: bloqueo de eliminacion de documentos tras informe tecnico finalizado

## Fecha
2026-04-23

## Objetivo
Evitar que el tecnico elimine documentos de admision una vez que el informe tecnico esta finalizado o en etapas posteriores.

## Alcance
Se agrego una validacion en el endpoint de eliminacion de documentos de admisiones y un test unitario de regresion.

## Archivos tocados
- admisiones/views/web_views.py
- tests/test_admisiones_web_views_unit.py

## Cambios realizados
- Se bloqueo `eliminar_archivo_admision` cuando `admision.estado_admision` esta en `informe_tecnico_finalizado` o etapas posteriores del flujo tecnico/legal.
- Se devolvio respuesta `400` con mensaje explicito cuando aplica el bloqueo.
- Se agrego `test_eliminar_archivo_admision_bloqueado_si_informe_finalizado` para validar que el endpoint bloquea y no intenta buscar/eliminar archivo.

## Supuestos
- El requisito funcional aplica desde `informe_tecnico_finalizado` y estados posteriores del mismo flujo.

## Validaciones ejecutadas
- `pytest -q tests/test_admisiones_web_views_unit.py -k "eliminar_archivo_admision_bloqueado_si_informe_finalizado or eliminar_archivo_admision_estado_no_permitido_and_success"` -> no disponible (`pytest` no instalado en el entorno local).
- `python -m pytest -q tests/test_admisiones_web_views_unit.py -k "eliminar_archivo_admision_bloqueado_si_informe_finalizado or eliminar_archivo_admision_estado_no_permitido_and_success"` -> no disponible (`No module named pytest`).
- `docker compose exec django pytest -q tests/test_admisiones_web_views_unit.py -k "eliminar_archivo_admision_bloqueado_si_informe_finalizado or eliminar_archivo_admision_estado_no_permitido_and_success"` -> fallo de entorno (`.docker/config.json` sin acceso y variables de compose sin definir).

## Pendientes / riesgos
- Confirmar funcionalmente con negocio si el bloqueo debe alcanzar tambien perfiles superusuario.
