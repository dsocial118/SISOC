# Contexto de feature PR #2477 - chore(release): publicar despliegue coordinado de las tres PWA

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2477
- Base: `main`
- Rama origen: `development`
- Autor: `juanikitro`

## Contexto funcional

- Publicación coordinada de las tres PWA privadas de SISOC en producción.

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
- Impacto usuario declarado: Nuevas aplicaciones web disponibles en el dominio de SISOC y conservación de URLs anteriores.
- Riesgos / rollback: Reinicio normal del backend y migraciones de development; baseline del main anterior, estado e imágenes PWA previas y copia del snippet Nginx. Validación autenticada y de sincronización offline pendiente.

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: admisiones/templates/admisiones/docx/renovacion_docx_informe_tecnico_base.docx, admisiones/templates/admisiones/docx/renovacion_docx_informe_tecnico_juridico.docx, admisiones/templates/admisiones/includes/boton_tecnicos.html, admisiones/templates/admisiones/informe_tecnico_detalle.html, admisiones/templates/admisiones/informe_tecnico_form.html, admisiones/templates/admisiones/pdf/renovacion_pdf_informe_tecnico_base.html, admisiones/templates/admisiones/pdf/renovacion_pdf_informe_tecnico_juridico.html, celiaquia/templates/celiaquia/expediente_detail.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2477.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.env.example`
- `.github/workflows/deploy.yml`
- `.gitignore`
- `.importlinter`
- `AGENT_REPO_MAP.md`
- `admisiones/forms/admisiones_forms.py`
- `admisiones/migrations/0080_alter_informetecnico_criterio_seleccionado.py`
- `admisiones/models/admisiones.py`
- `admisiones/services/admisiones_service/impl.py`
- `admisiones/services/docx_service/impl.py`
- `admisiones/services/informe_tecnico_variables_service.py`
- `admisiones/services/informes_service/impl.py`
- `admisiones/templates/admisiones/docx/renovacion_docx_informe_tecnico_base.docx`
- `admisiones/templates/admisiones/docx/renovacion_docx_informe_tecnico_juridico.docx`
- `admisiones/templates/admisiones/includes/boton_tecnicos.html`
- `admisiones/templates/admisiones/informe_tecnico_detalle.html`
- `admisiones/templates/admisiones/informe_tecnico_form.html`
- `admisiones/templates/admisiones/pdf/renovacion_pdf_informe_tecnico_base.html`
- `admisiones/templates/admisiones/pdf/renovacion_pdf_informe_tecnico_juridico.html`
- `admisiones/templatetags/admisiones_tags.py`
- ... y 258 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/analisis/ANALISIS_MODELO_DOCUMENTAL_ADMISIONES.md`
- `docs/analisis/gestionar_formularios_relevamiento.md`
- `docs/analisis/relevamiento_requerimientos_nuevos_2026-09-03.md`
- `docs/analisis/requerimiento_legajo_comedor_informe_tecnico.md`
- `docs/analisis/requerimiento_reporte_incidencias_expedientes_pago_admisiones.md`
- `docs/analisis_modulo_prestacion_mensual.md`
- `docs/analisis_modulo_programa_pas.md`
- `docs/contexto/dominio.md`
- `docs/contexto/features/pr-2392-feat-encuestas-nuevo-modulo-de-encuestas-periodicas-a-usuarios.md`
- `docs/contexto/features/pr-2393-celiaquia-tk1947.md`
- `docs/contexto/features/pr-2404-fix-centrodeinfancia-precargar-provincia-del-cdi.md`
- `docs/contexto/features/pr-2407-chore-sync-integrar-main-en-development.md`
- `docs/contexto/features/pr-2409-nucleo-pas.md`
- `docs/contexto/features/pr-2410-docs-spec-consolidar-contratos-de-relevamientos-y-cdi.md`
- `docs/contexto/features/pr-2411-task-pas-import-ddjj-token.md`
- `docs/contexto/features/pr-2412-pas-informes.md`
- `docs/contexto/features/pr-2416-fix-ci-corregir-formato-djlint-para-promocion-hml.md`
- `docs/contexto/features/pr-2418-chore-sync-integrar-main-en-homologacion.md`
- `docs/contexto/features/pr-2425-chore-sync-integrar-main-en-homologacion.md`
- `docs/contexto/features/pr-2427-feature-modulo-encuestas.md`
- `docs/contexto/features/pr-2429-celiaquia-tk2318.md`
- `docs/contexto/features/pr-2433-fix-ci-destrabar-jobs-de-qa-y-exportaciones.md`
- `docs/contexto/features/pr-2436-feat-pwa-agregar-coordinador-de-equipo-tecnico-de-solo-lectura.md`
- `docs/contexto/features/pr-2439-fix-migrations-corregir-dependencia-de-coordinador-pwa.md`
- `docs/contexto/features/pr-2441-style-comedores-corregir-formato-black.md`
- `docs/contexto/features/pr-2442-docs-incorporar-documentacion-de-analisis-funcional-y-registro-pendiente-en-local.md`
- `docs/contexto/features/pr-2447-chore-sync-integrar-main-en-development.md`
- `docs/contexto/features/pr-2450-chore-sync-integrar-main-en-development.md`
- `docs/contexto/features/pr-2454-fix-users-preservar-permisos-al-suspender-acceso-mobile.md`
- `docs/contexto/features/pr-2461-feat-admisiones-implementar-mejoras-de-informes-alimentar.md`
- `docs/contexto/features/pr-2464-fix-comedores-unificar-migraciones-0057.md`
- `docs/contexto/features/pr-2467-eliminada-linea-de-texto.md`
- `docs/contexto/features/pr-2468-fix-admisiones-reubicar-descarga-gde-validada.md`
- `docs/contexto/features/pr-2470-fix-admisiones-corregir-selects-y-acreditaciones.md`
- `docs/contexto/features/pr-2471-feat-deploy-coordinar-pwa-privadas-y-preparar-rutas-de-nginx.md`
- `docs/contexto/features/pr-2474-feat-deploy-preparar-activacion-web-de-datacalle-y-gestionar.md`
- `docs/contexto/features/pr-2475-fix-sync-recuperar-datacalle-de-main-en-development.md`
- `docs/flujos/relevamiento_sync.md`
- `docs/implementaciones/centrodeinfancia_nomina_ninos_simepi.md`
- `docs/operacion/daily_standup.md`
- `docs/operacion/deploy_automatizado.md`
- `docs/operacion/deploy_entornos_docker_nginx_mysql.md`
- `docs/operacion/deploy_pwas.md`
- `docs/operacion/integraciones.md`
- `docs/operacion/nginx/sisoc-produccion.conf`
- `docs/operacion/nginx/sisoc-pwas-preview.conf.example`
- `docs/operacion/nginx/sisoc-pwas.conf`
- `docs/operacion/qa_trixie_deploy.md`
- `docs/plans/2026-08-20-celiaquia-comentarios-tecnicos-subsanacion.md`
- `docs/plans/2026-08-31-pr-2392-review-fixes-design.md`
- `docs/plans/2026-09-04-hml-migration-graph-fix-design.md`
- `docs/plans/2026-09-04-issue-2403-informes-alimentar-design.md`
- `docs/plans/2026-09-08-issue-2443-gde-design.md`
- `docs/presentacion/SISOC_RESUMEN_PUBLICO_GENERAL.md`
- `docs/registro/analisis/2026-07-16-rendiciones-tres-etapas.md`
- `docs/registro/analisis/2026-07-22-codigo-proyecto-organizacion-comedor.md`
- `docs/registro/analisis/2026-08-03-nomina-sin-dni-historia-social.md`
- `docs/registro/analisis/2026-08-28-modulo-encuestas.md`
- `docs/registro/cambios/2026-07-22-tarea-codigo-proyecto-organizacion.md`
- `docs/registro/cambios/2026-08-06-pas-declaracion-jurada.md`
- `docs/registro/cambios/2026-08-28-issue-1947-total-legajos-expediente.md`
- `docs/registro/cambios/2026-08-31-pr-2392-privacidad-y-validacion-encuestas.md`
- `docs/registro/cambios/2026-09-01-informes-pas.md`
- `docs/registro/cambios/2026-09-01-nucleo-pas.md`
- `docs/registro/cambios/2026-09-01-spec-as-source-relevamientos-cdi.md`
- `docs/registro/cambios/2026-09-03-celiaquia-comentarios-tecnicos-subsanacion.md`
- `docs/registro/cambios/2026-09-03-usuario-coordinador-pwa.md`
- `docs/registro/cambios/2026-09-07-2316-acceso-mobile-y-selecciones.md`
- `docs/registro/cambios/2026-09-07-issue-2403-informes-alimentar.md`
- `docs/registro/cambios/2026-09-08-activacion-pwa-web.md`
- `docs/registro/cambios/2026-09-08-coordinacion-pwa-privadas.md`
- `docs/registro/cambios/2026-09-08-informe-tecnico-gde.md`
- `docs/registro/cambios/2026-09-08-merge-migraciones-comedores.md`
- `docs/registro/cambios/2026-09-08-pwa-altas-comedores-idempotentes.md`
- `docs/registro/cambios/2026-09-08-sincronizacion-datacalle-main.md`
- `docs/registro/prs/PR-2392.md`
- `docs/registro/prs/PR-2393.md`
- `docs/registro/prs/PR-2404.md`
- `docs/registro/prs/PR-2407.md`
- `docs/registro/prs/PR-2409.md`
- `docs/registro/prs/PR-2410.md`
- `docs/registro/prs/PR-2411.md`
- `docs/registro/prs/PR-2412.md`
- `docs/registro/prs/PR-2416.md`
- `docs/registro/prs/PR-2418.md`
- `docs/registro/prs/PR-2425.md`
- `docs/registro/prs/PR-2427.md`
- `docs/registro/prs/PR-2429.md`
- `docs/registro/prs/PR-2433.md`
- `docs/registro/prs/PR-2436.md`
- `docs/registro/prs/PR-2439.md`
- `docs/registro/prs/PR-2441.md`
- `docs/registro/prs/PR-2442.md`
- `docs/registro/prs/PR-2447.md`
- `docs/registro/prs/PR-2450.md`
- `docs/registro/prs/PR-2454.md`
- `docs/registro/prs/PR-2461.md`
- `docs/registro/prs/PR-2464.md`
- `docs/registro/prs/PR-2467.md`
- `docs/registro/prs/PR-2468.md`
- `docs/registro/prs/PR-2470.md`
- `docs/registro/prs/PR-2471.md`
- `docs/registro/prs/PR-2474.md`
- `docs/registro/prs/PR-2475.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
