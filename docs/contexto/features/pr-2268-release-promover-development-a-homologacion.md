# Contexto de feature PR #2268 - release: promover development a homologacion

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2268
- Base: `homologacion`
- Rama origen: `codex/promote-development-homologacion-20260810`
- Autor: `juanikitro`

## Contexto funcional

- Promueve los cambios validados de development a homologacion, preservando los commits propios de la rama destino.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Hay cambios en capa API/DRF y conviene revisar contratos de request/response.
- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.
- El alcance incluye automatización o tooling de CI/CD.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: release
- Área principal declarada: release
- Impacto usuario declarado: Habilita la validación integrada en homologación.
- Riesgos / rollback: Revertir el merge commit de promoción si se detecta una regresión.

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: ciudadanos/templates/ciudadanos/ciudadano_detail.html, static/custom/css/comedorFormModerno.css, static/custom/css/poncho_formularios.css, static/custom/js/comedorFormModerno.js, static/custom/js/nomina_detail.js, templates/includes/sidebar/opciones.html, users/templates/user/_mi_cuenta_campos.html, users/templates/user/_mi_cuenta_submit_js.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2268.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.env.example`
- `.github/workflows/architecture.yml`
- `.github/workflows/pr-docs.yml`
- `.importlinter`
- `.importlinter_celiaquia_config`
- `AGENT_REPO_MAP.md`
- `VAT/services/consulta_renaper/__init__.py`
- `VAT/services/consulta_renaper/impl.py`
- `celiaquia/api.py`
- `celiaquia/apps.py`
- `celiaquia/ciudadano_detail.py`
- `celiaquia/global_urls.py`
- `celiaquia/services/ciudadano_resumen_service/__init__.py`
- `celiaquia/services/ciudadano_resumen_service/impl.py`
- `celiaquia/tests/test_public_api.py`
- `celiaquia/views/validacion_renaper.py`
- `centrodefamilia/apps.py`
- `centrodefamilia/services/beneficiarios_service/impl.py`
- `centrodefamilia/services/consulta_renaper/__init__.py`
- `centrodefamilia/services/consulta_renaper/impl.py`
- ... y 88 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/arquitectura.md`
- `docs/contexto/features/pr-2222-feat-comedores-agregar-etiqueta-caritas.md`
- `docs/contexto/features/pr-2227-chore-deps-migrar-django-4-2-a-5-2-lts.md`
- `docs/contexto/features/pr-2228-fix-iam-restringe-accesos-de-ciudadanos-y-acompanamiento.md`
- `docs/contexto/features/pr-2230-comedores-cambios-en-filtros-ordenamiento-columnas.md`
- `docs/contexto/features/pr-2231-style-templates-corrige-formato-para-promocion-a-homologacion.md`
- `docs/contexto/features/pr-2235-issues-1961-2005-2076-2079-y-2188.md`
- `docs/contexto/features/pr-2237-ui-buscadores.md`
- `docs/contexto/features/pr-2253-refactor-architecture-completar-ratchet-de-fase-0.md`
- `docs/contexto/features/pr-2255-fixes-post-revision-issues-1961-2076-2079-y-2188.md`
- `docs/contexto/features/pr-2260-cdi-nomina-restriccion.md`
- `docs/contexto/features/pr-2261-mi-cuenta.md`
- `docs/contexto/features/pr-2264-fix-ci-bloquear-prs-sin-artefactos-spec-as-source.md`
- `docs/contexto/features/pr-2268-release-promover-development-a-homologacion.md`
- `docs/contexto/panorama.md`
- `docs/flujos/consulta_renaper.md`
- `docs/flujos/derivar_nomina_centros.md`
- `docs/ia/MODULAR_BOUNDARIES.md`
- `docs/implementaciones/centrodeinfancia_nomina_renaper.md`
- `docs/implementaciones/usuarios_perfil_iam.md`
- `docs/operacion/integraciones.md`
- `docs/registro/cambios/2026-08-06-mi-cuenta-confirmacion-datos.md`
- `docs/registro/cambios/2026-08-07-cdi-nomina-vigente-en-un-solo-centro.md`
- `docs/registro/cambios/2026-08-10-ci-artefactos-pr-no-trackeados.md`
- `docs/registro/cambios/2026-08-10-select2-formulario-comedores.md`
- `docs/registro/decisiones/2026-08-07-contrato-publico-celiaquia.md`
- `docs/registro/decisiones/2026-08-10-integracion-renaper-compartida.md`
- `docs/registro/prs/PR-2222.md`
- `docs/registro/prs/PR-2227.md`
- `docs/registro/prs/PR-2228.md`
- `docs/registro/prs/PR-2230.md`
- `docs/registro/prs/PR-2231.md`
- `docs/registro/prs/PR-2235.md`
- `docs/registro/prs/PR-2237.md`
- `docs/registro/prs/PR-2253.md`
- `docs/registro/prs/PR-2255.md`
- `docs/registro/prs/PR-2260.md`
- `docs/registro/prs/PR-2261.md`
- `docs/registro/prs/PR-2264.md`
- `docs/registro/prs/PR-2268.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
