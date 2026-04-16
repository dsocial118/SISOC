# Mobile: rendición offline-first

Fecha: 2026-03-30

## Qué cambió

- La creación y gestión de rendiciones en mobile pasó a un esquema offline-first.
- Ahora la rendición se guarda primero en almacenamiento local del dispositivo y luego se sincroniza con el servidor cuando hay conexión.
- El mismo criterio aplica para:
  - alta de rendición
  - adjuntos de documentación
  - presentación de la rendición
  - borrado de archivos
  - borrado de la rendición

## Implementación

- Se agregaron tablas locales para rendiciones y archivos de rendición en `Dexie`.
- Se extendió la `outbox` del sync engine con acciones específicas de rendición.
- La sincronización verifica el estado remoto luego de crear, adjuntar o presentar, y actualiza el estado local para reflejar si quedó verificada en servidor.
- Las pantallas de listado, detalle y selector inicial de rendición ahora leen primero desde local y sincronizan en segundo plano.

## Comportamiento visible

- Si se corta internet, la rendición sigue quedando guardada localmente.
- Cuando vuelve la conexión, la app intenta sincronizar automáticamente.
- El estado de sincronización operativo se sigue viendo desde la nube del header.

## Validación

- `npm run build` en `mobile/`
