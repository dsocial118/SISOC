# Contexto de feature PR #2260 - cdi nomina restriccion

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2260
- Base: `development`
- Rama origen: `cdi_nomina_res`
- Autor: `MariaNavarro90`

## Contexto funcional

- Nominalización de destinatarios en Centros de Infancia. Una persona sólo puede tener una inscripción vigente (Activo o Pendiente) en un único CDI; los registros en Baja no bloquean, preservando la derivación entre centros.

## Arquitectura tocada

- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: Feature
- Área principal declarada: Centro de Infancia (CDI) — nómina de destinatarios
- Impacto usuario declarado: El alta y la reactivación de una ficha se bloquean cuando la persona ya está registrada en otro CDI, con un mensaje neutro y sin perder los datos cargados en el formulario. El resto de los flujos (duplicado en el mismo centro, derivación entre centros) se mantiene sin cambios.
- Riesgos / rollback: Sin migraciones ni cambios de schema; el rollback es revertir el commit. Riesgo operativo: si en producción hay personas con vigencia en más de un CDI, la regla no las modifica (sólo bloquea altas nuevas), pero su derivación empieza a fallar con el mensaje neutro. Conviene contar esos casos antes de desplegar:

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: static/custom/js/nomina_detail.js

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2260.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `centrodeinfancia/admin.py`
- `centrodeinfancia/forms.py`
- `centrodeinfancia/models.py`
- `centrodeinfancia/services.py`
- `centrodeinfancia/tests/test_nomina_integridad.py`
- `centrodeinfancia/tests/test_nomina_vigencia_unica.py`
- `centrodeinfancia/views.py`
- `core/soft_delete/cascade.py`
- `core/trash_views.py`
- `docs/registro/cambios/2026-08-07-cdi-nomina-vigente-en-un-solo-centro.md`
- `static/custom/js/nomina_detail.js`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-08-07-cdi-nomina-vigente-en-un-solo-centro.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
