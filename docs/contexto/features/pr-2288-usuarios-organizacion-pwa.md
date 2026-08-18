# Contexto de feature PR #2288 - Usuarios Organizacion PWA

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2288
- Base: `development`
- Rama origen: `UserOrga`
- Autor: `MariaNavarro90`

## Contexto funcional

- Alcance de espacios en SISOC - Mobile para usuarios asociados a organizaciones. Mantiene sincronizados los comedores visibles cuando cambia la relación Comedor–Organización.

## Arquitectura tocada

- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: Mejora funcional (automatización de una tarea manual) con modelo nuevo y migración de datos.
- Área principal declarada: users / comedores — accesos PWA (AccesoComedorPWA, AccesoOrganizacionPWA).
- Impacto usuario declarado: Los administradores dejan de actualizar usuario por usuario cada vez que se da de alta un comedor. Los usuarios de organización dejan de quedar sin acceso a comedores nuevos. No cambia la regla de visibilidad por estado ni el alcance de los usuarios asociados por espacio.
- Contrato confirmado por issue #2094: una organización representa la totalidad de sus comedores actuales y futuros; no se preservan exclusiones manuales dentro de una organización seleccionada.
- Riesgos / rollback: la propagación, soft-delete y restore corren dentro de la transacción del comedor; un error revierte ambos dominios y GESTIONAR se notifica sólo después del commit. `queryset.update()` y `bulk_create()` no disparan signals, por lo que requieren el comando de catch-up. El dry-run es de sólo lectura y `--apply` transacciona por organización. Revertir migraciones no elimina automáticamente accesos ya materializados: un rollback funcional exige snapshot y reconciliación explícita.

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2288.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `comedores/management/commands/sincronizar_accesos_pwa_organizaciones.py`
- `comedores/signals.py`
- `docs/registro/cambios/2026-08-12-accesos-pwa-organizacion-automaticos.md`
- `tests/test_pwa_accesos_organizacion.py`
- `users/forms.py`
- `users/api.py`
- `users/migrations/0046_acceso_organizacion_pwa.py`
- `users/migrations/0047_backfill_acceso_organizacion_pwa.py`
- `users/models.py`
- `users/services_pwa.py`
- `comedores/models.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-08-12-accesos-pwa-organizacion-automaticos.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
