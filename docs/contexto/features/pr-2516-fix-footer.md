# Contexto de feature PR #2516 - Fix footer

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2516
- Base: `development`
- Rama origen: `Corrección-Footer-#2428`
- Autor: `nehuen871`

## Contexto funcional

- Dashboard — tableros embebidos (Looker Studio).

## Arquitectura tocada

- Se modifican templates, con posible impacto visual o de composición UI.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: Fix
- Área principal declarada: dashboard
- Impacto usuario declarado: Las páginas de tableros dejan de trabarse al scrollear hasta el final y la barra de acciones vuelve a ser clickeable. El footer no se muestra en esas pantallas; en el resto del sitio queda igual.
- Riesgos / rollback: Riesgo bajo y acotado:* no se tocan layouts compartidos, modelos, vistas ni URLs. La hoja de estilos se carga solo en la plantilla del tablero. Punto a vigilar:* la regla que oculta el footer depende de igualar la especificidad de main.css y del orden de carga. Si main.css cambia sus selectores del footer, hay que actualizar tableroEmbed.css. Hay un test que cubre exactamente eso. Nota:* el alto del embed es fijo (75vh, mínimo 420px). Es lo que permite que el layout sea correcto sin conocer el alto real del tablero, que el iframe no informa por ser de otro origen. Rollback:* revertir el commit. Sin migraciones ni datos afectados.

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: dashboard/templates/dashboard_tablero.html, static/custom/css/tableroEmbed.css

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2516.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `dashboard/templates/dashboard_tablero.html`
- `static/custom/css/tableroEmbed.css`
- `tests/test_dashboard_tablero_footer_db.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
