# Rendicion: no mantener notificaciones activas al finalizar

## Contexto

Una rendicion ya finalizada podia seguir apareciendo en la bandeja de
notificaciones mobile con un mensaje del tipo `documento validado`. Eso pasaba
porque al validar el ultimo documento se archivaban las notificaciones previas,
pero luego se publicaba una nueva para el mismo evento final.

## Cambio realizado

- Al crear notificaciones mobile por revision de documento, si la rendicion ya
  quedo en estado `finalizada`, primero se archivan las notificaciones activas
  de esa rendicion y no se publica una nueva.

## Validacion

- `docker compose exec django pytest tests/test_rendicioncuentasmensual_services_unit.py tests/test_pwa_mensajes_api.py -q`
