# Fix de warnings de migraciones PWA/MySQL

## Contexto

Al iniciar Django en entornos MySQL aparecía el warning:

- `pwa.PushSubscriptionPWA.endpoint: (mysql.W003) MySQL may not allow unique CharFields to have a max_length > 255`

Además, en checkouts atrasados respecto de `origin/development` podía aparecer:

- `Your models in app(s): 'users' have changes that are not yet reflected in a migration`

Ese segundo warning no requería un cambio nuevo en `users`: la causa era no tener incorporada la migración `users/0027_bulk_credentials_jobs.py`, ya presente en la base actualizada de `development`.

## Cambio realizado

- `pwa.PushSubscriptionPWA` deja de depender de un `unique=True` sobre `endpoint`.
- Se agrega `endpoint_hash` (`sha256`, longitud fija 64) como nueva clave única indexable en MySQL.
- El alta/baja de suscripciones push se resuelve por `endpoint_hash`, manteniendo `endpoint` completo para interoperar con Web Push y para auditoría/admin.
- Se agrega migración para backfill de hashes existentes.
- Se agrega test de regresión para endpoints largos.

## Impacto esperado

- Desaparece el warning `mysql.W003` para suscripciones push PWA.
- Se preserva el comportamiento de `upsert`/baja lógica por endpoint, incluso con endpoints largos.
- Para eliminar el warning de `users` en un checkout viejo, alcanza con sincronizar `development` actualizado y correr migraciones.
