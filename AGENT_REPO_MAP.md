# AGENT_REPO_MAP.md

Mapa practico del repositorio `SISOC` para futuros agentes de IA y desarrolladores.

## Como leer este documento

- `Hecho observado`: confirmado leyendo codigo, config, workflows o docs del repo.
- `Inferencia`: deduccion razonable por nombres, estructura o convenciones, pero no validada en profundidad.
- `No confirmado`: no encontre evidencia suficiente en esta exploracion acotada.

## Resumen ejecutivo

### Hechos observados

- Es un monolito Django grande, modularizado por apps de dominio, con backend renderizado por templates y APIs DRF convivientes.
- El stack principal es Python 3.11 + Django 4.2 + MySQL 8 + Docker Compose.
- La operacion local y CI estan pensadas en modo Docker-first.
- El repo mezcla backoffice web tradicional, APIs internas/server-to-server, flujos asincronos simples sin Celery, y una capa PWA/API para ciertos casos de uso.
- La logica de negocio suele vivir en `services/` cuando la app la tiene, pero coexisten apps mas legacy con mas logica en `views.py`, `models.py` o `tasks.py`.
- Hay un esfuerzo explicito de control arquitectonico incremental con `import-linter` (`.importlinter`) para evitar que el monolito siga acoplandose.

### Inferencias utiles

- No parece ser un repositorio "nuevo" ni estrictamente homogenizado: conviven zonas modernas, refactors en curso y zonas legacy con patrones distintos.
- Antes de tocar cualquier feature conviene asumir side effects ocultos: signals, syncs con externos, commands bootstrap y permisos por grupos.

## Stack y herramientas detectadas

### Backend

| Item | Estado | Evidencia |
| --- | --- | --- |
| Python 3.11 | Hecho observado | `pyproject.toml`, workflows CI |
| Django 4.2.27 | Hecho observado | `requirements/base.txt` |
| Django REST Framework | Hecho observado | `requirements/base.txt`, `config/settings.py` |
| drf-spectacular | Hecho observado | `requirements/base.txt`, `config/urls.py` |
| Gunicorn | Hecho observado | `requirements/base.txt`, `docker/django/entrypoint.py` |
| MySQL 8.4 | Hecho observado | `docker-compose.yml` |
| PyMySQL + mysqlclient | Hecho observado | `requirements/base.txt` |
| pytest / pytest-django / pytest-xdist / pytest-cov | Hecho observado | `requirements/test.txt`, `pytest.ini` |
| black / pylint / djlint | Hecho observado | `pyproject.toml`, `requirements/dev.txt`, `requirements/lint.txt` |
| import-linter | Hecho observado | `.importlinter`, `requirements/arch.txt` |
| Sentry | Hecho observado | `.env.example`, `requirements/base.txt` |
| OCR / PDF / DOCX / Excel tooling | Hecho observado | `requirements/base.txt`, app `ocr/`, templates/docx/pdf |

### Frontend

| Item | Estado | Evidencia |
| --- | --- | --- |
| Templates Django server-side | Hecho observado | `templates/`, `*/templates/` |
| JS/CSS estaticos propios | Hecho observado | `static/custom/js`, `static/custom/css` |
| Bootstrap/AdminLTE/Select2 | Hecho observado | `static/dist/`, `requirements`, templates |
| PWA backend + endpoints | Hecho observado | `pwa/`, `config/urls.py`, docs PWA |
| Toolchain Node formal en raiz | No confirmado como toolchain real; mas bien ausente | hay `package-lock.json` en raiz, pero no `package.json` |

### Operacion y CI

| Item | Estado | Evidencia |
| --- | --- | --- |
| Docker Compose para local | Hecho observado | `docker-compose.yml` |
| Compose separado para deploy | Hecho observado | `docker-compose.deploy.yml`, `docker-compose.produccion.yml` |
| GitHub Actions para lint/tests/arquitectura/release sanity | Hecho observado | `.github/workflows/` |
| Helpers de Codex/worktrees | Hecho observado | `scripts/ai/`, `.codex/environments/environment.toml` |

## Que tipo de proyecto es

### Hechos observados

- Sistema interno/backoffice multi-modulo orientado a gestion social/territorial.
- Mueve varias areas funcionales bajo un mismo monolito: comedores, relevamientos, ciudadanos, centro de familia, celiaquia, admisiones, usuarios, rendiciones, VAT, ticketera, OCR y otros modulos satelite.
- Expone UI HTML tradicional, APIs DRF y algunos endpoints server-to-server.

### Flujos principales inferibles

1. Usuarios internos autenticados operan el backoffice Django.
2. Los modulos de dominio persisten en MySQL y renderizan templates o exponen APIs.
3. Algunas acciones sincronizan datos con sistemas externos como GESTIONAR o RENAPER.
4. La PWA consume endpoints dedicados bajo `/api/pwa/`.
5. El arranque Docker ejecuta migraciones, fixtures y bootstrap de grupos/usuarios de prueba segun entorno.

## Como se corre localmente

### Flujo principal recomendado

1. Copiar `.env.example` a `.env`.
2. Ajustar variables minimas de DB, puertos y claves externas si hace falta.
3. Levantar con `docker compose up`.
4. Acceder a `http://localhost:8001` por default.

### Hechos observados

- `docker-compose.yml` levanta `mysql`, `django` y `ocr_worker`.
- El contenedor `django` monta el repo completo en `/sisoc/`.
- `docker/django/entrypoint.py` espera MySQL, puede correr `makemigrations`, siempre corre `migrate`, `load_fixtures`, `create_test_users`, `create_groups`, y luego levanta `runserver` o `gunicorn` segun `ENVIRONMENT`.

### Helpers operativos del repo

- `scripts/ai/codex_task.ps1 <slug>`: crea branch `codex/<slug>`, worktree en `../worktrees/<slug>` y bootstrap.
- `scripts/ai/codex_run.ps1 up`: bootstrap + levantar entorno.
- `scripts/ai/codex_run.ps1 validate`: corre `black`, `djlint`, smoke tests y `makemigrations --check`.
- `scripts/operacion/deploy_refresh.sh`: refresh operativo de deploy.

## Estructura general del proyecto

### Raiz

```text
SISOC/
|-- config/                  # settings, urls, middleware, views globales
|-- docs/                    # fuente de verdad operativa y arquitectonica
|-- docker/                  # Dockerfile Django y dump local MySQL
|-- scripts/                 # helpers IA, CI y operacion
|-- templates/               # templates globales y componentes compartidos
|-- static/                  # JS/CSS/img y vendor assets
|-- tests/                   # suite transversal del proyecto
|-- <apps Django>/           # modulos funcionales
|-- .github/workflows/       # CI, lint, arquitectura, release
|-- docker-compose*.yml      # local y deploy
|-- .env.example             # catalogo de variables
|-- pytest.ini               # config de tests
|-- .importlinter            # contratos de imports
```

### Carpetas raiz importantes

| Ruta | Para que sirve | Cuando mirarla primero |
| --- | --- | --- |
| `config/` | configuracion global de Django, URLs y middleware | cambios cross-cutting, auth, API docs, seguridad, entorno |
| `docs/` | documentacion operativa y de arquitectura | siempre antes de expandir contexto |
| `scripts/ai/` | flujo recomendado para worktrees/validacion desde Codex | tareas de agentes, bootstrap, validaciones |
| `scripts/ci/` | automatizaciones de PR docs y lint | si falla CI o hay autoformato |
| `docker/` | runtime contenedorizado real | bugs de arranque/deploy |
| `templates/components/` | primitives HTML reutilizables | cambios de UI server-side compartidos |
| `static/custom/js/` | comportamiento cliente legacy por pantalla | bugs front puntuales en templates |
| `tests/` | tests transversales del proyecto | caracterizacion y regresiones |
| `postman/` | coleccion y entorno API | contratos API/manual testing |
| `tmp/` | basura/artefactos temporales | evitar tocar salvo necesidad muy puntual |

## Puntos de entrada del sistema

### Backend web/API

- `manage.py`
- `config/settings.py`
- `config/urls.py`
- `docker/django/entrypoint.py`

### Rutas HTTP centrales

- Auth/UI base: `config/urls.py`
- APIs:
  - `api/users/`
  - `api/comedores/`
  - `api/centrodefamilia/`
  - `api/vat/`
  - `api/comunicados/`
  - `api/renaper/`
  - `api/pwa/`
  - `api/ticketera/`
- Docs OpenAPI:
  - `/api/schema/`
  - `/api/docs/`
  - `/api/redoc/`

### Jobs / workers / asincronia

### Hechos observados

- No hay Celery ni broker declarado.
- La asincronia es "simple":
  - hilos / `ThreadPoolExecutor` en syncs (`comedores/tasks.py`, `relevamientos/tasks.py`);
  - workers dedicados por `DJANGO_SERVICE_ROLE` en `docker/django/entrypoint.py`.

### Roles de contenedor detectados

- `web`
- `bulk_credentials_worker`
- `ciudadanos_import_worker`
- `mailing_worker`
- `user_import_worker`
- `ocr_worker`

## Configuracion y variables de entorno relevantes

### Archivos

- `.env.example`: base local canonicamente documentada.
- `.env.qa`, `.env.homologacion`, `.env.prod`: plantillas saneadas versionadas; no tratarlas como origen de secretos.
- `docker-compose.yml`: local.
- `docker-compose.deploy.yml`, `docker-compose.produccion.yml`: deploy.

### Variables clave

| Grupo | Variables importantes |
| --- | --- |
| Entorno Django | `DJANGO_DEBUG`, `ENVIRONMENT`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS` |
| DB | `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_USER`, `DATABASE_PASSWORD`, `DATABASE_NAME`, `WAIT_FOR_DB`, `DB_CONN_MAX_AGE` |
| Docker/puertos | `DOCKER_MYSQL_PORT_FORWARD`, `DOCKER_DJANGO_PORT_FORWARD`, `DOCKER_DEBUGGER_PORT_FORWARD`, `RUN_UID`, `RUN_GID` |
| Runtime | `RUN_MAKEMIGRATIONS_ON_START`, `GUNICORN_WORKERS`, `GUNICORN_THREADS` |
| Seguridad/CSP | `ENABLE_CSP`, `CSP_REPORT_ONLY`, `CSP_ALLOW_UNSAFE_INLINE_SCRIPTS`, `CSP_ALLOW_UNSAFE_EVAL` |
| Async | `DISABLE_ASYNC_THREADS` |
| Testing | `USE_SQLITE_FOR_TESTS`, `PYTEST_RUNNING` |
| Integracion GESTIONAR | `GESTIONAR_API_KEY`, endpoints `GESTIONAR_API_*`, workers `GESTIONAR_*`, `DOMINIO` |
| Ticketera | `TICKETERA_ENABLED` |
| RENAPER | `RENAPER_API_USERNAME`, `RENAPER_API_PASSWORD`, retries/backoff |
| Google Maps | `GOOGLE_MAPS_API_KEY` |
| Sentry | `SENTRY_ENABLED`, `SENTRY_DSN`, `SENTRY_RELEASE` |
| Email/password reset | `EMAIL_*`, `DEFAULT_FROM_EMAIL`, `PASSWORD_RESET_TIMEOUT`, `INITIAL_PASSWORD_MAX_AGE_HOURS` |
| Web push PWA | `PWA_WEB_PUSH_PUBLIC_KEY`, `PWA_WEB_PUSH_PRIVATE_KEY`, `PWA_WEB_PUSH_SUBJECT` |

### Precauciones

- No tocar `.env*` salvo pedido explicito.
- No asumir que `ENVIRONMENT=dev` representa PRD-like behavior: hay toggles importantes para QA/PRD.
- `RUN_MAKEMIGRATIONS_ON_START=true` en dev puede enmascarar drift de migraciones si nadie mira el diff.

## Mapa de carpetas y capas por responsabilidad

### Configuracion global

| Ruta | Responsabilidad |
| --- | --- |
| `config/settings.py` | settings, apps instaladas, middleware, DB, cache, DRF, Sentry, logging, CSP, modo debug/prod |
| `config/urls.py` | router global del monolito |
| `config/middlewares/` | middleware propio como XSS/threadlocals |
| `config/views.py` | views globales, errores y schema VAT |

### Capa compartida

| Ruta | Responsabilidad |
| --- | --- |
| `core/` | utilidades transversales, fixtures, soft delete, API auxiliar, paginacion, benchmark/debug tooling |
| `users/` | auth, login/reset, perfiles, grupos, import masivo de usuarios, permisos PWA |
| `audittrail/` | auditoria propia del sistema |
| `healthcheck/` | endpoint de salud |

### Presentacion/UI compartida

| Ruta | Responsabilidad |
| --- | --- |
| `templates/includes/` | layout base, navbar, sidebar, scripts globales |
| `templates/components/` | componentes HTML reutilizables |
| `static/custom/js/` | JS por pantalla/flujo; bastante legacy y acoplado a templates |
| `static/custom/css/` | estilos propios |

### Operacion

| Ruta | Responsabilidad |
| --- | --- |
| `docker/` | runtime contenedorizado |
| `scripts/operacion/` | refresh/deploy operativo |
| `scripts/ci/` | utilidades de CI |
| `scripts/ai/` | bootstrap/worktrees/doctor/validate/context memory |

### Tests y calidad

| Ruta | Responsabilidad |
| --- | --- |
| `tests/` | suite transversal, smoke, contratos API, seguridad, PWA, componentes |
| `*/tests/` | tests cercanos al modulo |
| `.github/workflows/` | contratos CI reales |
| `.importlinter` | boundaries arquitectonicos parciales |

## Mapa de dominios / apps

La siguiente tabla mezcla hechos observados con inferencias explicitas cuando no lei el modulo a fondo.

| App | Rol practico | Piezas a mirar primero | Estado de confirmacion |
| --- | --- | --- | --- |
| `users/` | autenticacion, perfiles, grupos, login/reset, import y credenciales masivas | `models.py`, `views.py`, `api_views.py`, `management/commands/`, `services_*` | Alto |
| `core/` | utilidades transversales, helpers, soft delete, filtros/paginacion, comandos compartidos | `views.py`, `services/`, `management/commands/`, `utils.py` | Alto |
| `dashboard/` | tableros internos | `urls.py`, `views.py`, templates | Medio |
| `comedores/` | dominio fuerte: comedores, nomina, estados, sync GESTIONAR | `models.py`, `tasks.py`, `signals.py`, `api_views.py`, `services/`, `urls.py` | Alto |
| `relevamientos/` | relevamientos y sync externo asociado | `models.py`, `tasks.py`, `views.py`, commands | Alto |
| `ciudadanos/` | gestion de ciudadanos/beneficiarios | `models.py`, `views.py`, `api_views.py`, forms | Medio |
| `centrodefamilia/` | beneficiarios/centros/familia + consulta RENAPER + API | `models.py`, `views.py`, `api_views.py`, `services/consulta_renaper` | Alto |
| `celiaquia/` | modulo especializado con bastante logica en services y vistas | `models.py`, `views/`, `services/`, `permissions.py`, tests | Alto |
| `admisiones/` | flujo de admision, legales/tecnicos, generacion DOCX/PDF | `views/web_views.py`, `services/`, `forms/`, templates `docx/` y `pdf/` | Alto |
| `VAT/` | modulo amplio propio con views, API, services y reportes | `models.py`, `views/`, `api_views.py`, `services/`, `serializers.py` | Alto |
| `pwa/` | endpoints backend para experiencia PWA | `api_urls.py`, `api_views.py`, `services/`, `models.py` | Medio |
| `ticketera/` | API server-to-server con kill-switch | `api_urls.py`, `api_views.py`, `api_serializers.py` | Medio |
| `comunicados/` | mensajes/comunicados y API asociada | `models.py`, `views.py`, `api_views.py`, forms | Medio |
| `organizaciones/` | entidades/organizaciones vinculadas | `models.py`, `views.py`, forms | Medio |
| `centrodeinfancia/` | dominio de centros de infancia | `models.py`, `views.py`, urls | Medio |
| `acompanamientos/` | seguimiento/acompanamientos | `views.py`, service, templates | Medio |
| `expedientespagos/` | expedientes de pagos | `models.py`, `views.py`, urls | Bajo |
| `rendicioncuentasfinal/` | rendicion final | `models.py`, `views.py`, urls | Bajo |
| `rendicioncuentasmensual/` | rendicion mensual | `models.py`, `views.py`, urls | Bajo |
| `duplas/` | equipos tecnicos/duplas | `models.py`, `views.py` | Bajo-Medio |
| `dispositivos/` | dominio de dispositivos | `models.py`, `views.py`, tests | Bajo |
| `importarexpediente/` | flujo de importacion de expedientes | `views.py`, `models.py`, urls, tests | Medio |
| `ocr/` | OCR y procesamiento asociado | `models.py`, `views.py`, urls, tests | Medio |
| `ver_para_ser_libre/` | modulo de negocio independiente dentro del monolito | `models.py`, `views.py`, `services/workflow.py` | Medio |
| `audittrail/` | auditoria interna | `models.py`, `views.py`, `services/query_service` | Alto |
| `historial/` | historial de dominio | `models.py`, `services/` | Bajo |
| `intervenciones/` | intervenciones sobre casos | tests + archivos del modulo | Bajo; exploracion parcial |
| `sentry/` | soporte/integracion local de sentry | codigo del modulo si toca observabilidad | Bajo |

## Patrones arquitectonicos y de codigo

### Hechos observados

- Monolito Django por apps funcionales.
- Coexisten:
  - views Django server-rendered;
  - DRF para APIs;
  - templates globales y por app;
  - JS por pantalla en `static/custom/js`;
  - servicios por modulo cuando hubo refactor/hardening.
- El repo intenta llevar la logica de negocio a `services/`, pero no es uniforme.
- Se usan management commands como extension operativa importante.
- Se usan signals para side effects de negocio.
- La arquitectura actual tiene boundaries monitoreados por `import-linter`, pero con baseline de excepciones existentes.

### Convenciones visibles

- Python: `snake_case`.
- Black line-length 88.
- Templates formateados con `djlint`.
- Commits sugeridos con Conventional Commits.
- En varias apps modernas los servicios usan estructura `services/<subservicio>/impl.py`.
- En otras apps legacy todavia existe `views.py` unico o `models.py` monolitico.

### Implicancia practica

- Antes de meter logica en una view, revisar si esa app ya tiene `services/`.
- Antes de crear otro helper global, revisar `core/`.
- Antes de agregar un import cross-app, revisar `.importlinter`: quizas estas rompiendo un boundary aunque el codigo "funcione".

## Donde buscar segun el tipo de cambio

### Si necesitas cambiar autenticacion / login / reset / grupos

- `users/views.py`
- `users/forms.py`
- `users/models.py`
- `users/api_views.py`
- `users/bootstrap/groups_seed.py`
- `users/management/commands/create_groups.py`
- templates en `users/templates/`

### Si necesitas cambiar permisos o IAM

- `users/bootstrap/groups_seed.py`
- `users/services_group_permissions.py`
- `users/api_permissions.py`
- permisos especificos por app, por ejemplo `celiaquia/permissions.py`
- docs: `docs/implementaciones/usuarios_perfil_iam.md`

### Si necesitas cambiar navegacion global, layout o sidebar

- `templates/includes/`
- `templates/includes/sidebar/`
- `templates/components/`
- `static/custom/js/sidebar.js`

### Si necesitas cambiar endpoints API

- router global: `config/urls.py`
- por app: `api_urls.py`, `api_views.py`, `api_serializers.py`, `serializers.py`
- si es PWA: `pwa/api_urls.py`, `pwa/api_views.py`
- si es Ticketera: `ticketera/api_*`

### Si necesitas cambiar una pantalla HTML tradicional

1. Buscar la `view`/`urls.py` de la app.
2. Abrir el template principal en `templates/` o `app/templates/`.
3. Buscar el JS asociado en `static/custom/js/`.
4. Revisar parciales en `templates/components/` o `app/templates/.../partials/`.

### Si necesitas cambiar negocio de Comedores

- `comedores/models.py`
- `comedores/tasks.py`
- `comedores/signals.py`
- `comedores/services/`
- `comedores/api_views.py`
- tests del root `tests/test_comedor*`, `tests/test_comedores*`
- docs de flujo: `docs/flujos/comedor_sync.md`

### Si necesitas cambiar Relevamientos

- `relevamientos/models.py`
- `relevamientos/tasks.py`
- `relevamientos/views.py`
- `tests/test_relevamientos*`
- docs: `docs/flujos/relevamiento_sync.md`

### Si necesitas cambiar Celiaquia

- `celiaquia/views/`
- `celiaquia/services/`
- `celiaquia/models.py`
- `celiaquia/permissions.py`
- `celiaquia/tests/`
- doc especifica de DB en `docs/contexto/documentacion_base_datos_celiaquia.md`

### Si necesitas cambiar Admisiones / documentos

- `admisiones/views/web_views.py`
- `admisiones/services/`
- `admisiones/forms/`
- templates `admisiones/templates/admisiones/docx/`
- templates `admisiones/templates/admisiones/pdf/`
- `admisiones/tests/`

### Si necesitas cambiar PWA

- `pwa/models.py`
- `pwa/api_urls.py`
- `pwa/api_views.py`
- `pwa/services/`
- tests `tests/test_pwa_*`
- docs: `docs/implementaciones/pwa_backend.md`, `docs/seguridad/security_baseline_pwa.md`

### Si necesitas cambiar OCR / procesamiento documental

- `ocr/`
- `docker/django/entrypoint.py` para rol `ocr_worker`
- dependencias PDF/OCR en `requirements/base.txt`

### Si necesitas cambiar syncs externos

- GESTIONAR: `comedores/tasks.py`, `relevamientos/tasks.py`, management commands relacionados, `.env.example`
- RENAPER: `centrodefamilia/services/consulta_renaper.py`, `VAT/services/consulta_renaper/impl.py`, docs `docs/flujos/consulta_renaper.md`
- Ticketera: `ticketera/`, `docs/integraciones/ticketera_api.md`

### Si necesitas cambiar CI o reglas de calidad

- `.github/workflows/tests.yml`
- `.github/workflows/lint.yml`
- `.github/workflows/architecture.yml`
- `.github/workflows/release-sanity.yml`
- `.importlinter`
- `scripts/ci/pr_lint_tools.py`

## Testing, linting, build y deploy

### Lint y formato detectados

- `black --check . --config pyproject.toml`
- `pylint **/*.py --rcfile=.pylintrc`
- `djlint . --configuration=.djlintrc --check`
- CI tiene autofix para PRs internos con Black, DJLint y normalizacion de encoding.

### Tests detectados

- `pytest -m smoke`
- `pytest -n auto --cov=. --cov-fail-under=75`
- `pytest -m mysql_compat -q`
- `python manage.py makemigrations --check --dry-run`
- `lint-imports`
- `python manage.py check --deploy`
- `python manage.py spectacular --validate`

### Validacion minima sugerida por tipo de cambio

| Tipo de cambio | Validacion minima razonable |
| --- | --- |
| view/template local | test cercano del modulo + `djlint` del template |
| servicio Python | test cercano + `pylint` del archivo tocado |
| auth/permisos | tests de auth/permisos cercanos + smoke si afecta login |
| API DRF | test API del modulo + schema si cambia contrato |
| migraciones/modelos | `makemigrations --check --dry-run` + tests del flujo |
| config global | smoke + `manage.py check` |
| import boundaries | `lint-imports` si metiste imports nuevos entre apps |
| release/main | agregar `check --deploy`, `spectacular --validate`, `collectstatic` |

### Build/deploy

- Local: `docker compose up`
- Deploy versionado: `docker compose -f docker-compose.deploy.yml ...`
- Produccion: override `docker-compose.produccion.yml`
- Sanity de release a `main` valida `check --deploy`, OpenAPI y `collectstatic`

## Comandos utiles detectados

### Seguros para inspeccion

- `Get-ChildItem`, `git ls-files`, `rg`
- `docker compose config --services`
- `python manage.py show_urls` si existiera dependencia instalada y entorno levantado
- `scripts/ai/codex_doctor.ps1`
- `scripts/ai/codex_run.ps1 smoke`
- `scripts/ai/codex_run.ps1 validate`

### Seguros pero potencialmente costosos

- `docker compose up -d --build`
- `docker compose exec django pytest -n auto`
- `pylint **/*.py --rcfile=.pylintrc`
- `lint-imports`

### Pedir permiso o tener especial cuidado antes de correr

- `docker compose down -v`
- comandos que destruyan volumenes/MySQL
- imports masivos desde Excel/CSV o commands operativos sobre datos
- commands que sincronicen con GESTIONAR o RENAPER reales
- cualquier deploy refresh sobre servidores
- scripts que dependan de `.env` reales del host

## Riesgos, zonas sensibles y advertencias para agentes

### Zonas sensibles

- `config/settings.py`: cambia todo el runtime, seguridad, cache, auth, logging, docs API.
- `config/urls.py`: cualquier ajuste impacta routing global.
- `docker/django/entrypoint.py`: side effects de arranque, migraciones, workers.
- `users/bootstrap/groups_seed.py` y comandos de grupos: permisos globales.
- `comedores/tasks.py` y `relevamientos/tasks.py`: syncs externos, threads y side effects.
- `signals.py` de varias apps: pueden disparar efectos colaterales no obvios.
- `templates/includes/` y `templates/components/`: impacto transversal de UI.
- `static/custom/js/`: mucho JS parece estar acoplado a IDs/clases exactas del HTML.
- `migrations/`: tocarlas manualmente sin necesidad suele ser mala idea.
- `.env*`: no versionar secretos ni usar valores reales.

### Legacy / deuda tecnica visible

- JS y templates dispersos por pantalla, sin pipeline frontend moderno.
- coexistencia de apps muy refactorizadas y apps con archivos monoliticos.
- `package-lock.json` en raiz sin `package.json`: parece drift/artefacto sobrante, no contrato operativo confirmado.
- `tmp/ci-pr-*`: artefactos temporales; no usarlos como fuente de verdad.

### Precauciones practicas antes de editar

1. Revisar si la app ya tiene `services/` y tests cercanos.
2. Buscar signals, tasks y commands relacionados.
3. Si el cambio toca permisos, revisar `groups_seed.py`, permisos de view/API y docs IAM.
4. Si el cambio toca imports entre apps, pensar en `.importlinter`.
5. Si el cambio toca templates, localizar el JS asociado en `static/custom/js`.
6. Si el cambio toca integraciones, confirmar si existen tests con mocks o docs de flujo antes de asumir contrato.

## Que archivos NO conviene tocar salvo necesidad clara

- `.env`, `.env.qa`, `.env.homologacion`, `.env.prod`
- `docker/mysql/local-dump.sql`
- `migrations/` existentes solo para "ordenar"
- `static/dist/`, `static/debug_toolbar/`, `static/silk/` salvo motivo concreto
- `tmp/`
- workflows CI completos si el problema es solo de codigo del modulo
- `config/settings.py` para fixes locales de negocio si puede resolverse dentro del modulo

## Guias y contexto que conviene leer antes de una feature concreta

### Base minima siempre

1. `AGENTS.md`
2. `docs/indice.md`
3. este `AGENT_REPO_MAP.md`
4. archivo objetivo
5. tests cercanos

### Segun el tipo de tarea

| Tipo | Leer primero |
| --- | --- |
| bugfix view/template | `docs/ia/TESTING.md`, template, view, JS asociado |
| API/serializer | `docs/ia/TESTING.md`, `api_views.py`, serializer, tests API |
| permisos/auth | `docs/ia/SECURITY_AI.md`, `users/`, docs IAM |
| boundaries/refactor | `docs/ia/ARCHITECTURE.md`, `.importlinter` |
| logging/errores/fallbacks | `docs/ia/ERRORS_LOGGING.md` |
| estilo/template | `docs/ia/STYLE_GUIDE.md` |
| PWA | `docs/implementaciones/pwa_backend.md`, `docs/seguridad/security_baseline_pwa.md` |
| deploy/infra | `docs/operacion/infraestructura.md`, `docs/operacion/instalacion.md` |

## Notas utiles sobre calidad y arquitectura

### Import-linter

- Hay una iniciativa explicita de "monolito modular fase 0".
- El baseline actual permite imports legacy, pero CI debe fallar ante nuevas dependencias prohibidas.
- Si un import nuevo entre apps te parece inocente, igual puede ser una regresion arquitectonica.

### Tests

- `pytest.ini` usa `--reuse-db`.
- Existen markers:
  - `smoke`
  - `mysql_compat`
- CI ejecuta algunos jobs contra SQLite y otros contra MySQL real.

### DRF

- `REST_FRAMEWORK` usa `IsAuthenticated` por defecto.
- Hay schema OpenAPI con drf-spectacular y variante propia para VAT.

## Mapa rapido: "si necesitas cambiar X, mira primero Y"

| Necesidad | Mirar primero |
| --- | --- |
| login / reset / perfil | `users/views.py`, `users/forms.py`, templates `users/templates/` |
| grupos / permisos | `users/bootstrap/groups_seed.py`, `users/api_permissions.py`, docs IAM |
| navbar / sidebar / layout | `templates/includes/`, `templates/includes/sidebar/`, `static/custom/js/sidebar.js` |
| filtro/listado generico | `core/`, `templates/components/data_table.html`, JS de la pantalla |
| comedores | `comedores/models.py`, `tasks.py`, `signals.py`, tests `test_comedor*` |
| relevamientos | `relevamientos/models.py`, `tasks.py`, `views.py` |
| RENAPER | `centrodefamilia/services/consulta_renaper.py`, `VAT/services/consulta_renaper/impl.py` |
| GESTIONAR | `comedores/tasks.py`, `relevamientos/tasks.py`, commands relacionados |
| docx/pdf | `admisiones/services/`, templates `docx/` y `pdf/` |
| PWA | `pwa/api_views.py`, `pwa/services/`, tests `test_pwa_*` |
| OCR | `ocr/`, `docker/django/entrypoint.py` |
| auditoria | `audittrail/`, docs `audittrail_*` |
| release/deploy | `docs/operacion/*.md`, workflows, compose deploy |
| CI rota por estilo | `.github/workflows/lint.yml`, `scripts/ci/pr_lint_tools.py` |
| CI rota por imports | `.importlinter`, `requirements/arch.txt` |

## Zonas no analizadas a fondo en esta pasada

- logica interna completa de `dashboard`, `dispositivos`, `duplas`, `expedientespagos`, `historial`, `intervenciones`, `organizaciones`, `rendicioncuentasfinal`, `rendicioncuentasmensual`, `ver_para_ser_libre`
- detalle fino de `ocr/`
- contratos completos de cada API mas alla del routing y docs encontradas
- flujos exactos de algunos workers (`mailing`, `ciudadanos_import_worker`) fuera del entrypoint

Marcar esas zonas como `A inferir` hasta relevarlas cuando una tarea real las toque.

## Recomendaciones para mantener este archivo actualizado

1. Actualizarlo cuando se agregue o elimine una app relevante.
2. Reflejar nuevos entrypoints, workers o compose files.
3. Si se consolida o mueve logica de una app a `services/`, anotar el nuevo hotspot.
4. Si cambia CI, actualizar la matriz de validacion minima.
5. Si se agregan integraciones externas, sumar archivo fuente, variables y riesgos.
6. Si un area legacy se moderniza, reemplazar inferencias por hechos observados.
7. No duplicar specs detalladas de negocio aqui: enlazar a `docs/` cuando exista una fuente de verdad mas especifica.

## Archivos inspeccionados para construir este mapa

- `AGENTS.md`
- `README.md`
- `docs/indice.md`
- `docs/contexto/arquitectura.md`
- `docs/contexto/aplicaciones.md`
- `docs/contexto/panorama.md`
- `docs/contexto/dominio.md`
- `docs/agentes/guia.md`
- `docs/operacion/instalacion.md`
- `docs/operacion/comandos_administracion.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `config/urls.py`
- `config/settings.py` (lectura parcial dirigida)
- `docker-compose.yml`
- `docker/django/entrypoint.py`
- `.env.example`
- `.importlinter`
- `pytest.ini`
- `pyproject.toml`
- `requirements/base.txt`
- `requirements/dev.txt`
- `requirements/test.txt`
- `requirements/lint.txt`
- `requirements/arch.txt`
- `.github/workflows/tests.yml`
- `.github/workflows/lint.yml`
- `.github/workflows/architecture.yml`
- `.github/workflows/release-sanity.yml`
- `scripts/ai/codex_run.ps1`
- `scripts/ai/codex_task.ps1`
- `.codex/environments/environment.toml`
- inventario de archivos con `git ls-files`
- inventario estructural de apps y scripts via shell
