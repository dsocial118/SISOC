# 2026-03-19 - Fix sync de comedores a GESTIONAR (Add/Update)

## Qué se corrigió
- Se agregó soporte de `action` en `build_comedor_payload` para poder enviar `Add` o `Update` según el flujo.
- En `pre_save` de comedores ahora la sincronización usa `Action=Update`.
- En la tarea asíncrona de alta/sync de comedores se incorporó fallback: si AppSheet responde `400` con `Action=Add`, se reintenta una vez con `Action=Update`.
- Se preservó la ruta de recuperación para comedores faltantes en GESTIONAR: si `Action=Update` responde `400`, ahora se reintenta una vez con `Action=Add`.

## Motivo
- Se observaron errores `400 Bad Request` al sincronizar comedores con AppSheet en el endpoint de `Comedores/Action`.
- Un caso probable es reenvío de alta (`Add`) para registros existentes durante ediciones o reintentos.

## Cobertura de tests
- Se agregaron tests unitarios para:
  - `build_comedor_payload` con `action` custom.
  - fallback `Add -> Update` en `AsyncSendComedorToGestionar.run` cuando la primera llamada devuelve `400`.
  - fallback `Update -> Add` en `AsyncSendComedorToGestionar.run` cuando el registro no existe remoto y la primera llamada devuelve `400`.
