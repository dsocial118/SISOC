# Security Baseline - BACKOFFICE (Django/DRF)

## Alcance
- Backend: Django 4.2.27 + DRF 3.15.2 (ver `requirements.txt`)
- Autenticacion API: API Keys via `djangorestframework-api-key==3.0.0`
- Autenticacion web: sesiones Django (`SessionAuthentication`)
- DB: MySQL 8.0 (Docker Compose)
- Infra: Docker/Docker Compose, Gunicorn
- CI/CD: GitHub Actions (`.github/workflows/*.yml`)
- Frontend: No hay Next.js/React en este repo (solo `package.json` sin deps). Si existe un frontend separado, queda fuera de este baseline.

## Controles minimos (checklist)
- [ ] Secretos fuera del repo (no `.env` con valores reales en Git) - Evita filtraciones y obliga a gestionar secretos correctamente.
- [ ] `DEBUG=False` y `ENVIRONMENT=prd` en produccion - Desactiva debug y activa hardening.
- [ ] `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS` definidos explicitamente - Bloquea host/header spoofing.
- [ ] TLS forzado en prod (`SECURE_SSL_REDIRECT=True`) con proxy correcto - Protege datos en transito.
- [ ] HSTS habilitado con valor objetivo definido - Previene downgrade a HTTP.
- [ ] Headers de seguridad activos (CSP, X-Frame-Options, nosniff, referrer) - Mitiga XSS, clickjacking y sniffing.
- [ ] Documentacion API restringida en prod (Swagger/Redoc) - Reduce recon de endpoints.
- [ ] Autenticacion DRF explicitada (sin BasicAuth por defecto) - Evita auth implícita no deseada.
- [ ] Autorizacion por roles/grupos revisada para endpoints sensibles - Minimiza accesos indebidos.
- [ ] Validacion de uploads (tipo, extension, tamano) y ruta de media no publica - Reduce abuso y exposición de archivos.
- [ ] Logs con trazabilidad minima (usuario, IP, accion) sin secretos/PII - Permite auditoría sin exponer datos.
- [ ] Auditoria de cambios habilitada (auditlog/audittrail) - Asegura trazabilidad de modificaciones.
- [ ] Dependencias actualizadas y auditadas periodicamente - Reduce riesgo por CVEs conocidas.
- [ ] Backups y restore testeado (DB + media) - Asegura recuperacion ante incidentes.
- [ ] Contenedores sin root en prod y con puertos minimos expuestos - Limita impacto de RCE y superficie.
- [ ] CI con permisos minimos y checks obligatorios - Evita ejecuciones no autorizadas.

## Configuracion por entorno
### Dev
- `DJANGO_DEBUG=True` - Facilita debugging local.
- `ENVIRONMENT=dev` - Activa defaults no productivos.
- `ALLOWED_HOSTS=localhost,127.0.0.1` - Limita hosts locales.
- `SECURE_SSL_REDIRECT=False` - No fuerza HTTPS en local.
- `SESSION_COOKIE_SECURE=False` - Permite cookies en HTTP local.
- `CSRF_COOKIE_SECURE=False` - Permite CSRF en HTTP local.
- Swagger habilitado - Mejora DX en desarrollo.
- Carga de fixtures y usuarios de prueba permitida - Acelera setup local.

### Staging/QA
- `DJANGO_DEBUG=False` - No exponer debug en QA.
- `ENVIRONMENT=qa` - Activa hardening sin ser prod.
- `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS` con dominios reales - Evita hosts accidentales.
- `SECURE_SSL_REDIRECT=True` - Fuerza HTTPS en QA.
- `SESSION_COOKIE_SECURE=True` - Cookies solo por HTTPS.
- `CSRF_COOKIE_SECURE=True` - CSRF solo por HTTPS.
- Swagger restringido a staff - Evita exposición pública.
- Carga de fixtures controlada por flags - Evita datos inesperados.

### Prod
- `DJANGO_DEBUG=False` - Evita exposición de información sensible.
- `ENVIRONMENT=prd` - Activa hardening de producción.
- `DJANGO_SECRET_KEY` desde gestor de secretos - Evita secretos en repositorio.
- `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS` cerrados - Solo dominios autorizados.
- `SECURE_SSL_REDIRECT=True` y `SECURE_PROXY_SSL_HEADER` correcto - Fuerza HTTPS detrás de proxy.
- `SECURE_HSTS_SECONDS>=31536000` - HSTS fuerte en prod.
- `SESSION_COOKIE_SECURE=True` - Cookies solo por HTTPS.
- `CSRF_COOKIE_SECURE=True` - CSRF solo por HTTPS.
- Swagger/Redoc solo staff o deshabilitado - Reduce recon.
- Migraciones y fixtures no automaticos al arranque - Evita cambios no controlados.
- Contenedor sin root - Limita impacto de exploit.

## Estandares de secretos
- Nunca commitear `.env` con valores reales - Evita exposición de credenciales.
- Usar `.env.example` solo como plantilla - Documenta sin filtrar datos.
- En prod, usar secrets del runtime (Vault/SSM/GHA secrets) y no archivos en el repo - Reduce riesgo operativo.
- Rotar inmediatamente secretos filtrados en Git - Minimiza impacto de leaks.

## Logging y auditoria minima
- Log estructurado (JSON) para eventos clave: login, cambios de estado, uploads - Facilita correlación y análisis.
- Incluir: timestamp, user_id, ip, action, objeto, resultado - Permite trazabilidad.
- No loggear passwords, tokens, API keys ni datos sensibles - Evita filtración en logs.
- Retencion minima: 90 dias - Balance entre auditoría y costo.

## Dependencias: actualizacion y escaneo
- Mantener `requirements.txt` con versiones fijas - Evita actualizaciones sorpresa.
- Revisar dependencias mensualmente o ante CVE criticas - Reduce ventana de exposición.
- Ejecutar auditoria de dependencias (ver comandos) - Detecta CVEs conocidas.

## Backups/DR minimos
- Backups diarios de MySQL y media - Asegura recuperación de datos.
- Retencion minima: 7-30 dias - Permite rollback ante incidentes.
- Restore probado al menos 1 vez por trimestre - Valida que los backups funcionan.

## Como verificar (comandos/pasos)
- Lint/format: `black --check . --config pyproject.toml` - Verifica estilo consistente.
- Templates: `djlint . --check --configuration=.djlintrc` - Valida templates HTML.
- Lint: `pylint **/*.py --rcfile=.pylintrc` - Detecta issues estáticos.
- Tests: `docker compose exec django pytest -n auto` - Ejecuta suite completa.
- Smoke: `docker compose exec django pytest -m smoke` - Verifica críticos rápidos.
- Django deploy checks: `python manage.py check --deploy` - Valida hardening.
- Dependencias (pip): `python -m pip list --outdated` y `python -m pip check` - Detecta drift y conflictos.
- Dependencias (npm): `npm audit --production` - Detecta CVEs frontend.
- Secret scan: `gitleaks detect --source .` - Busca secretos expuestos.
- Container scan: `trivy image <imagen>` - Escanea vulnerabilidades en imágenes.
