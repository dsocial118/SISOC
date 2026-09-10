# Contexto de feature PR #2492 - feat(celiaquia): bloquear el envio si un menor quedo sin adulto

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2492
- Base: `development`
- Rama origen: `CeliaquiaTK_2430`
- Autor: `MariaNavarro90`

## Contexto funcional

- Celiaquía — carga y envío de expedientes por parte de la provincia.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Se modifican templates, con posible impacto visual o de composición UI.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: Corrección de bug (validación de integridad de datos).
- Área principal declarada: celiaquia (services, views, template y JS del detalle de expediente).
- Impacto usuario declarado: La provincia recibe una alerta explícita al eliminar el legajo de un responsable y no puede enviar el expediente hasta resolverlo. Impacto medido en producción: cero expedientes afectados hoy — hay un solo expediente en EN_ESPERA (68 en CRUCE_FINALIZADO, 26 en ASIGNADO), con 4 legajos, todos con fecha de nacimiento y ninguno menor de 18. Los 679 vínculos vivos de ciudadanos_grupofamiliar tienen cuidador_principal = 1, que es el criterio que usa el código.
- Riesgos / rollback: Riesgo bajo. Sin migraciones ni cambios de modelo, y la validación solo corre en el paso EN_ESPERA → envío, por lo que no afecta expedientes ya enviados. Rollback = revertir los commits, sin ningún paso de datos.

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: celiaquia/templates/celiaquia/expediente_detail.html, static/custom/js/expediente_detail.js

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2492.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `celiaquia/services/expediente_service/impl.py`
- `celiaquia/services/validacion_edad_service/impl.py`
- `celiaquia/templates/celiaquia/expediente_detail.html`
- `celiaquia/tests/test_menor_sin_responsable.py`
- `celiaquia/views/confirm_envio.py`
- `celiaquia/views/expediente.py`
- `celiaquia/views/legajo.py`
- `docs/contexto/features/pr-2492-feat-celiaquia-bloquear-el-envio-si-un-menor-quedo-sin-adulto.md`
- `docs/registro/cambios/2026-09-09-2430-menor-sin-adulto-responsable.md`
- `docs/registro/prs/PR-2492.md`
- `static/custom/js/expediente_detail.js`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
