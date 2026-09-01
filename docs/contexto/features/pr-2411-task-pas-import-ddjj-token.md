# Contexto de feature PR #2411 - Task/pas import ddjj token

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2411
- Base: `development`
- Rama origen: `task/PAS-Import-DDJJ-Token`
- Autor: `Esteban-Royo`

## Contexto funcional

- Gestión del padrón PAS, actualización periódica de datos mediante Declaración Jurada y distribución segura de enlaces de acceso.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: Nueva funcionalidad, persistencia, migración de base de datos, seguridad de archivos y configuración operativa.
- Área principal declarada: PAS — Importación, Declaraciones Juradas y tokens.
- Impacto usuario declarado: Los operadores pueden importar titulares y distribuir enlaces DDJJ; los titulares pueden presentar su declaración mediante un enlace de un solo uso; los usuarios autorizados pueden descargar los PDF generados.
- Riesgos / rollback: La migración agrega campos y tablas PAS y genera tokens para titulares existentes. Para rollback, revertir el despliegue y aplicar la migración inversa antes de que existan DDJJ productivas; una vez recibidas declaraciones reales, preservar y respaldar los PDF y datos antes de cualquier reversión. Verificar especialmente DOMINIO, permisos y bloqueo NGINX por contener datos personales.

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: pas/templates/pas/ddjj_confirmacion.html, pas/templates/pas/ddjj_formulario.html, pas/templates/pas/titulares_import.html, static/custom/css/pas_ddjj.css, static/custom/js/pas_ddjj.js

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2411.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.gitignore`
- `.importlinter`
- `AGENT_REPO_MAP.md`
- `config/settings.py`
- `config/urls.py`
- `docs/operacion/deploy_entornos_docker_nginx_mysql.md`
- `docs/operacion/nginx/sisoc-produccion.conf`
- `docs/operacion/qa_trixie_deploy.md`
- `docs/registro/cambios/2026-08-06-pas-declaracion-jurada.md`
- `docs/registro/cambios/2026-09-01-nucleo-pas.md`
- `pas/__init__.py`
- `pas/admin.py`
- `pas/api.py`
- `pas/apps.py`
- `pas/forms.py`
- `pas/migrations/0001_initial.py`
- `pas/migrations/0002_pas_import_ddjj_tokens.py`
- `pas/migrations/__init__.py`
- `pas/models.py`
- `pas/services/__init__.py`
- ... y 13 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/operacion/deploy_entornos_docker_nginx_mysql.md`
- `docs/operacion/nginx/sisoc-produccion.conf`
- `docs/operacion/qa_trixie_deploy.md`
- `docs/registro/cambios/2026-08-06-pas-declaracion-jurada.md`
- `docs/registro/cambios/2026-09-01-nucleo-pas.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
