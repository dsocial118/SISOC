# Contexto de feature PR #1613 - Release: development -> main (2026-04-23)

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/1613
- Base: `main`
- Rama origen: `development`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Hay cambios en capa API/DRF y conviene revisar contratos de request/response.
- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.
- El alcance incluye automatización o tooling de CI/CD.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: VAT/templates/vat/centros/centro_create_form.html, VAT/templates/vat/centros/centro_detail.html, VAT/templates/vat/centros/partials/centro_cursos_panel.html, VAT/templates/vat/curso/curso_form.html, VAT/templates/vat/institucion/ubicacion_form.html, VAT/templates/vat/oferta_institucional/comision_detail.html, "acompanamientos/templates/acompa\303\261amiento_detail.html", admisiones/templates/admisiones/admisiones_tecnicos_form.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-1613.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.codex/environments/environment.toml`
- `.github/workflows/lint.yml`
- `.gitignore`
- `AGENTS.md`
- `CHANGELOG.md`
- `CODEX.md`
- `README.md`
- `VAT/cache_utils.py`
- `VAT/forms.py`
- `VAT/migrations/0044_centro_listado_indexes.py`
- `VAT/models.py`
- `VAT/serializers.py`
- `VAT/services/centro_filter_config/impl.py`
- `VAT/services/nomina_export.py`
- `VAT/templates/vat/centros/centro_create_form.html`
- `VAT/templates/vat/centros/centro_detail.html`
- `VAT/templates/vat/centros/partials/centro_cursos_panel.html`
- `VAT/templates/vat/curso/curso_form.html`
- `VAT/templates/vat/institucion/ubicacion_form.html`
- `VAT/templates/vat/oferta_institucional/comision_detail.html`
- ... y 247 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/agentes/guia.md`
- `docs/contexto/aplicaciones.md`
- `docs/contexto/features/pr-1564-update-main-2026-04-16.md`
- `docs/contexto/memoria/README.md`
- `docs/contexto/memoria/TEMPLATE.md`
- `docs/contexto/memoria/sisoc-base.md`
- `docs/operacion/codex_desktop.md`
- `docs/operacion/comandos_administracion.md`
- `docs/operacion/infraestructura.md`
- `docs/operacion/instalacion.md`
- `docs/plans/2026-04-16-performance-benchmark-system-design.md`
- `docs/plans/2026-04-17-export-relaciones-territoriales-plan.md`
- `docs/registro/cambios/2026-03-31-acompanamiento-modelo-por-admision.md`
- `docs/registro/cambios/2026-04-10-cdi-nomina-filtro-ubicacion.md`
- `docs/registro/cambios/2026-04-13-fix-vat-edicion-cursos-comisiones-centro.md`
- `docs/registro/cambios/2026-04-14-fix-celiaquia-nacionalidad-por-json-pais.md`
- `docs/registro/cambios/2026-04-14-optimizacion-listado-ciudadanos-paginacion-sin-count.md`
- `docs/registro/cambios/2026-04-14-optimizacion-listados-pesados-sin-count.md`
- `docs/registro/cambios/2026-04-15-celiaquia-registros-erroneos-subsanacion-nacionalidad-y-campos-invalidos.md`
- `docs/registro/cambios/2026-04-16-actualizar-docs-operacion-ci-spec-as-source.md`
- `docs/registro/cambios/2026-04-16-analisis-predeploy-main.md`
- `docs/registro/cambios/2026-04-16-celiaquia-limpieza-logs-validaciones-usuario.md`
- `docs/registro/cambios/2026-04-16-dependency-sdk-drift-alignment.md`
- `docs/registro/cambios/2026-04-16-fix-celiaquia-renaper-ciudad-localidad.md`
- `docs/registro/cambios/2026-04-16-fix-cffi-cryptography-resolver.md`
- `docs/registro/cambios/2026-04-16-fix-comedores-nomina-duplicados.md`
- `docs/registro/cambios/2026-04-16-fix-jobs-pr-1530.md`
- `docs/registro/cambios/2026-04-16-memoria-contexto-agentes.md`
- `docs/registro/cambios/2026-04-16-performance-benchmark-system.md`
- `docs/registro/cambios/2026-04-16-pr-1546-fix-jobs-lint.md`
- `docs/registro/cambios/2026-04-16-pr-1546-resolucion-conflictos.md`
- `docs/registro/cambios/2026-04-16-pr1446-ajustes-jobs-listados.md`
- `docs/registro/cambios/2026-04-16-resolucion-merge-pr-1537-identidad-ciudadano.md`
- `docs/registro/cambios/2026-04-16-vat-centro-cursos-click-filtrado-comisiones.md`
- `docs/registro/cambios/2026-04-16-vat-centro-switch-activo.md`
- `docs/registro/cambios/2026-04-16-vat-centros-filtro-codigo-cue.md`
- `docs/registro/cambios/2026-04-16-vat-comisiones-default-25.md`
- `docs/registro/cambios/2026-04-17-celiaquia-nomina-sintys-sexo.md`
- `docs/registro/cambios/2026-04-17-celiaquia-renaper-clasificacion-errores-y-logs.md`
- `docs/registro/cambios/2026-04-17-export-relaciones-territoriales-fixture.md`
- `docs/registro/cambios/2026-04-17-fix-ci-prs-abiertos.md`
- `docs/registro/cambios/2026-04-17-fix-comedor-crear-validacion-estado-general.md`
- `docs/registro/cambios/2026-04-17-main-a-development-conflicto-vat-serializers.md`
- `docs/registro/cambios/2026-04-17-select2-ux-migration-lotes-2-3.md`
- `docs/registro/cambios/2026-04-17-select2-ux-migration.md`
- `docs/registro/cambios/2026-04-20-admisiones-ajax-actualizar-estado-n-plus-one.md`
- `docs/registro/cambios/2026-04-20-celiaquia-rechazo-con-motivo.md`
- `docs/registro/cambios/2026-04-20-fix-celiaquia-buscador-localidades-refresh.md`
- `docs/registro/cambios/2026-04-20-fix-celiaquia-documentos-obligatorios-envio.md`
- `docs/registro/cambios/2026-04-20-fix-celiaquia-nomina-sintys-y-lint-integracion.md`
- `docs/registro/cambios/2026-04-20-fix-ciudadanos-merge-migration.md`
- `docs/registro/cambios/2026-04-20-fix-comedores-nomina-paginacion-estable.md`
- `docs/registro/cambios/2026-04-20-fix-conflicto-migraciones-ciudadanos.md`
- `docs/registro/cambios/2026-04-20-pr-1585-fix-hallazgos-acompanamiento.md`
- `docs/registro/cambios/2026-04-20-pr1565-ci-registros-responsable-y-migracion.md`
- `docs/registro/cambios/2026-04-20-select2-global-theme.md`
- `docs/registro/cambios/2026-04-20-vat-comision-export-nomina-preinscriptos.md`
- `docs/registro/cambios/2026-04-21-admisiones-finalizar-carga-documentacion.md`
- `docs/registro/cambios/2026-04-21-admisiones-modificacion-documental-tecnicos.md`
- `docs/registro/cambios/2026-04-21-iam-infraestructura.md`
- `docs/registro/cambios/2026-04-21-relevamientos-asignar-territorial-pendiente.md`
- `docs/registro/cambios/2026-04-22-fix-nomina-baja-reorden-y-asistentes-activos.md`
- `docs/registro/cambios/2026-04-22-soft-delete-estado-operativo.md`
- `docs/registro/decisiones/2026-04-10-identidad-ciudadano.md`
- `docs/registro/decisiones/2026-04-16-memoria-contexto-agentes.md`
- `docs/registro/prs/PR-1564.md`
- `docs/registro/releases/pending/2026-04-22-pr-1564.md`
- `docs/seguridad/iam_infraestructura.md`
- `docs/superpowers/plans/2026-04-17-celiaquia-sintys-sexo-export.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
