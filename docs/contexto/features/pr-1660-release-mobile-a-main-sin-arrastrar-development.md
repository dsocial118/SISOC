# Contexto de feature PR #1660 - Release mobile a main sin arrastrar development

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/1660
- Base: `main`
- Rama origen: `codex/release-mobile-main-only-20260503`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Hay cambios en capa API/DRF y conviene revisar contratos de request/response.
- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: comedores/templates/comedor/comedor_convenio_pnud_form.html, comedores/templates/comedor/comedor_detail.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-1660.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `comedores/api_serializers.py`
- `comedores/api_views.py`
- `comedores/forms/convenio_pnud_form.py`
- `comedores/migrations/0037_imagencomedor_origen.py`
- `comedores/migrations/0038_comedordatosconveniopnud.py`
- `comedores/models.py`
- `comedores/services/capacitaciones_certificados_service.py`
- `comedores/services/comedor_service/impl.py`
- `comedores/templates/comedor/comedor_convenio_pnud_form.html`
- `comedores/templates/comedor/comedor_detail.html`
- `comedores/urls.py`
- `comedores/views/__init__.py`
- `comedores/views/comedor.py`
- `config/settings.py`
- `config/urls.py`
- `docs/registro/cambios/2026-05-01-capacitaciones-y-cursos-mobile-web.md`
- `docs/registro/cambios/2026-05-01-pwa-mobile-beneficiarios-actividades-y-nomina-por-programa.md`
- `docs/registro/cambios/2026-05-01-pwa-mobile-versionado-fecha-settings.md`
- `pwa/api_serializers.py`
- `pwa/api_views.py`
- ... y 5 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-05-01-capacitaciones-y-cursos-mobile-web.md`
- `docs/registro/cambios/2026-05-01-pwa-mobile-beneficiarios-actividades-y-nomina-por-programa.md`
- `docs/registro/cambios/2026-05-01-pwa-mobile-versionado-fecha-settings.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
