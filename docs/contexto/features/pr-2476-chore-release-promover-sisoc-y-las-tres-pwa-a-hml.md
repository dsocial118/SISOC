# Contexto de feature PR #2476 - chore(release): promover SISOC y las tres PWA a HML

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2476
- Base: `homologacion`
- Rama origen: `development`
- Autor: `juanikitro`

## Contexto funcional

- Publicación coordinada de las PWA de SISOC y disponibilidad de la API de DataCalle en HML.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Hay cambios en capa API/DRF y conviene revisar contratos de request/response.
- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.
- El alcance incluye automatización o tooling de CI/CD.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: feature
- Área principal declarada: despliegue PWA
- Impacto usuario declarado: Acceso a las nuevas aplicaciones desde el dominio de SISOC HML.
- Riesgos / rollback: Reinicio normal del backend y migraciones de la rama; rollback PWA por imágenes previas y restauración del snippet Nginx guardado. Pruebas autenticadas y de sincronización offline pendientes.

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: admisiones/templates/admisiones/includes/boton_tecnicos.html, admisiones/templates/admisiones/informe_tecnico_detalle.html, admisiones/templates/admisiones/informe_tecnico_form.html, ciudadanos/templates/ciudadanos/ciudadano_form.html, datacalle/templates/datacalle/encuesta_detail.html, datacalle/templates/datacalle/relevamiento_confirm_delete.html, datacalle/templates/datacalle/relevamiento_detail.html, datacalle/templates/datacalle/relevamiento_form.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2476.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.github/workflows/deploy.yml`
- `.gitignore`
- `AGENT_REPO_MAP.md`
- `CHANGELOG.md`
- `admisiones/forms/admisiones_forms.py`
- `admisiones/services/admisiones_service/impl.py`
- `admisiones/services/docx_service/impl.py`
- `admisiones/services/informes_service/impl.py`
- `admisiones/templates/admisiones/includes/boton_tecnicos.html`
- `admisiones/templates/admisiones/informe_tecnico_detalle.html`
- `admisiones/templates/admisiones/informe_tecnico_form.html`
- `admisiones/templatetags/admisiones_tags.py`
- `admisiones/tests/test_variables_documentales_renovacion.py`
- `admisiones/views/web_views.py`
- `ciudadanos/templates/ciudadanos/ciudadano_form.html`
- `comedores/api_serializers.py`
- `comedores/api_views_territorial.py`
- `comedores/migrations/0059_comedorpwacreateoperation.py`
- `comedores/models.py`
- `config/settings.py`
- ... y 96 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-2452-feat-datacalle-modulo-de-relevamientos-de-situacion-de-calle-y-api-para-la-app.md`
- `docs/contexto/features/pr-2453-fix-datacalle-500-en-el-detalle-de-relevamiento-por-out-of-sort-memory-de-mysql.md`
- `docs/contexto/features/pr-2467-eliminada-linea-de-texto.md`
- `docs/contexto/features/pr-2468-fix-admisiones-reubicar-descarga-gde-validada.md`
- `docs/contexto/features/pr-2470-fix-admisiones-corregir-selects-y-acreditaciones.md`
- `docs/contexto/features/pr-2471-feat-deploy-coordinar-pwa-privadas-y-preparar-rutas-de-nginx.md`
- `docs/contexto/features/pr-2474-feat-deploy-preparar-activacion-web-de-datacalle-y-gestionar.md`
- `docs/contexto/features/pr-2475-fix-sync-recuperar-datacalle-de-main-en-development.md`
- `docs/operacion/deploy_automatizado.md`
- `docs/operacion/deploy_pwas.md`
- `docs/operacion/nginx/README.md`
- `docs/operacion/nginx/sisoc-produccion.conf`
- `docs/operacion/nginx/sisoc-pwas-preview.conf.example`
- `docs/operacion/nginx/sisoc-pwas.conf`
- `docs/plans/2026-09-08-issue-2443-gde-design.md`
- `docs/registro/cambios/2026-09-01-datacalle-rol-relevador-calle.md`
- `docs/registro/cambios/2026-09-03-datacalle-modulo-relevamientos.md`
- `docs/registro/cambios/2026-09-06-datacalle-casos-y-api.md`
- `docs/registro/cambios/2026-09-07-issue-2403-informes-alimentar.md`
- `docs/registro/cambios/2026-09-08-activacion-pwa-web.md`
- `docs/registro/cambios/2026-09-08-coordinacion-pwa-privadas.md`
- `docs/registro/cambios/2026-09-08-informe-tecnico-gde.md`
- `docs/registro/cambios/2026-09-08-pwa-altas-comedores-idempotentes.md`
- `docs/registro/cambios/2026-09-08-sincronizacion-datacalle-main.md`
- `docs/registro/prs/PR-2452.md`
- `docs/registro/prs/PR-2453.md`
- `docs/registro/prs/PR-2467.md`
- `docs/registro/prs/PR-2468.md`
- `docs/registro/prs/PR-2470.md`
- `docs/registro/prs/PR-2471.md`
- `docs/registro/prs/PR-2474.md`
- `docs/registro/prs/PR-2475.md`
- `docs/registro/releases/pending/2026-09-09-pr-2452.md`
- `docs/registro/releases/pending/2026-09-09-pr-2453.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
