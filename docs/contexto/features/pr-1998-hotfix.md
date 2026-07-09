# Contexto de feature PR #1998 - hotfix

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/1998
- Base: `main`
- Rama origen: `hoyfix`
- Autor: `dsocial118`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: centrodefamilia/templates/beneficiarios/beneficiarios_detail.html, centrodefamilia/templates/beneficiarios/beneficiarios_list.html, centrodefamilia/templates/beneficiarios/responsable_detail.html, centrodefamilia/templates/beneficiarios/responsable_list.html, centrodefamilia/templates/centros/actividadcentro_asistencia.html, centrodefamilia/templates/centros/actividadcentro_detail.html, centrodefamilia/templates/centros/actividadcentro_list.html, centrodefamilia/templates/centros/centro_detail.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-1998.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `centrodefamilia/access.py`
- `centrodefamilia/migrations/0016_asistenciaactividad.py`
- `centrodefamilia/models.py`
- `centrodefamilia/services/asistencia/__init__.py`
- `centrodefamilia/services/asistencia/impl.py`
- `centrodefamilia/services/beneficiarios_filter_config/impl.py`
- `centrodefamilia/services/beneficiarios_service/impl.py`
- `centrodefamilia/services/responsables_filter_config/impl.py`
- `centrodefamilia/templates/beneficiarios/beneficiarios_detail.html`
- `centrodefamilia/templates/beneficiarios/beneficiarios_list.html`
- `centrodefamilia/templates/beneficiarios/responsable_detail.html`
- `centrodefamilia/templates/beneficiarios/responsable_list.html`
- `centrodefamilia/templates/centros/actividadcentro_asistencia.html`
- `centrodefamilia/templates/centros/actividadcentro_detail.html`
- `centrodefamilia/templates/centros/actividadcentro_list.html`
- `centrodefamilia/templates/centros/centro_detail.html`
- `centrodefamilia/templates/centros/centro_list.html`
- `centrodefamilia/templates/centros/participanteactividad_list.html`
- `centrodefamilia/tests/test_asistencia_actividad.py`
- `centrodefamilia/tests/test_filtro_fecha_beneficiarios.py`
- ... y 7 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-07-03-cdf-asistencia-actividades.md`
- `docs/registro/cambios/2026-07-03-cdf-rediseno-visual.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
