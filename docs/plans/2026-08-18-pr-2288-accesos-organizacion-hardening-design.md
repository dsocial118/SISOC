# Hardening de accesos PWA por organización (PR #2288)

Fecha: 2026-08-18

## Objetivo y clasificación

Corregir las regresiones detectadas en la revisión del PR #2288 sin cambiar la
regla de visibilidad de la PWA. El cambio se clasifica como parte del bounded
context existente `users`–`comedores`–`organizaciones`: comparte tablas y exige
consistencia transaccional dentro del monolito.

## Contrato funcional

- Una membresía activa a una organización representa la totalidad de sus
  comedores activos, actuales y futuros.
- La membresía sobrevive aunque la organización no tenga comedores por un
  período y no depende de `User.is_active`.
- Un acceso materializado por organización sólo autoriza si la membresía sigue
  activa y el comedor continúa en esa organización.
- Soft-delete revoca la proyección y restore la reconstruye.
- Los accesos explícitos por espacio y los operadores mantienen su semántica.

## Diseño

- `AccesoOrganizacionPWA` sigue siendo la fuente de verdad y
  `AccesoComedorPWA` una proyección materializada.
- El formulario expande cada organización con todos sus comedores mediante el
  queryset registrado en `users.form_catalogs`; `users` no importa modelos de
  Comedores u Organizaciones.
- `users.api` expone a Comedores una fachada basada en IDs primitivos. Signals y
  comando no importan internals de `users.services_pwa` ni sus modelos.
- El guardado, soft-delete y restore de `Comedor` incluyen los side effects
  síncronos en la misma transacción. Los envíos a GESTIONAR se difieren con
  `transaction.on_commit`.
- Las altas por organización bloquean las membresías activas con
  `SELECT FOR UPDATE`; la resolución de permisos además exige una membresía
  activa para que un dato residual nunca autorice.
- El comando usa una previsualización de sólo lectura y aplica una transacción
  independiente por organización. El backfill itera y escribe en lotes.

## Errores, operación y rollback

Un error al materializar accesos aborta el cambio de Comedor. Los cambios por
`queryset.update()` o `bulk_create()` no disparan signals y deben repararse con
`sincronizar_accesos_pwa_organizaciones`. Antes de aplicar en un ambiente se
ejecuta el dry-run y se conservan sus totales.

Revertir código o migraciones no elimina automáticamente accesos por comedor ya
materializados. Si hiciera falta rollback funcional, primero se debe capturar el
estado, revertir la aplicación y reconciliar explícitamente los accesos según el
alcance anterior.

## Validación prevista para el PR

- Regresiones de formulario, totalidad, cuenta inactiva, membresía residual,
  soft-delete/restore, fachada pública, atomicidad y dry-run sin escrituras.
- Prueba `mysql_compat` que verifica el lock transaccional real.
- Verificaciones estáticas (`git diff --check`, compilación de Python y
  `lint-imports`) y ejecución de los tests focalizados en CI.

La instrucción del usuario del 2026-08-18 de corregir todos los hallazgos y
publicarlos en la rama del PR aprobó este alcance.
