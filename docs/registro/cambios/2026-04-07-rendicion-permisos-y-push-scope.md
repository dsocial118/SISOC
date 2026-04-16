# Rendicion: cierre de hallazgos de permisos web y push scope

## Contexto

La revision del PR detecto dos riesgos bloqueantes:

- el detalle web de rendiciones permitia revisar documentos via `POST` aun con
  permisos de solo lectura;
- las notificaciones web push replicadas por proyecto construian el deep link
  siempre con el comedor origen de la rendicion, aunque el receptor accediera
  por otro espacio del mismo scope.

## Cambio realizado

- Se exigio permiso explicito de cambio sobre `RendicionCuentaMensual` para
  ejecutar la revision web de documentos.
- El detalle web ahora expone `puede_revisar_documentos` y oculta los
  controles de revision a usuarios de solo lectura.
- El `POST` AJAX del detalle responde `403` cuando el usuario intenta revisar
  sin permiso.
- El servicio de push ahora resuelve un `space_id` y una `url` validos por
  usuario/suscripcion, tomando un comedor accesible dentro del mismo scope del
  proyecto y priorizando el comedor origen cuando tambien esta disponible.
- Se ajustaron pruebas unitarias/API para cubrir ambos fixes.

## Validacion

- `pytest tests/test_rendicioncuentasmensual_views_unit.py tests/test_pwa_push_api.py -q`

## Supuesto

- La revision web por documento debe quedar restringida a usuarios con permiso
  Django de cambio sobre la rendicion, en lugar de reutilizar el permiso mobile
  especifico de la PWA.
