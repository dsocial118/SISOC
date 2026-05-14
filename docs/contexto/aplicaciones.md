# Apps y rutas

## Aplicaciones instaladas
- Apps Django/3ros: admin, auth, sessions, messages, staticfiles, admindocs, crispy_forms/bootstrap5, django_extensions, import_export, multiselectfield, auditlog, DRF/rest_framework_api_key, drf_spectacular, corsheaders. Evidencia: config/settings.py:42-63.
- Apps propias: users, core, dashboard, comedores, organizaciones, centrodeinfancia, ciudadanos, duplas, admisiones, intervenciones, historial, acompanamientos, expedientespagos, relevamientos, rendicioncuentasfinal, rendicioncuentasmensual, centrodefamilia, celiaquia, audittrail. Evidencia: config/settings.py:64-83.
- Apps de debug/performance agregadas solo con `DEBUG=True`: debug_toolbar y silk. Evidencia: config/settings.py:359-366.

## URL principales
- Router raíz incluye auth, users, core, dashboard, comedores, organizaciones, centrodeinfancia, duplas, audittrail, ciudadanos, admisiones, centrodefamilia, healthcheck, acompanamientos (prefijo), expedientespagos (prefijo), rendicioncuentasfinal, relevamientos, rendicioncuentasmensual (prefijo), celiaquia y APIs de `users`, `comedores` y `centrodefamilia`; expone Swagger/Redoc en `/api/docs` y `/api/redoc`. Evidencia: config/urls.py:12-47.
- Endpoint de salud `/health/` responde `OK`. Evidencia: healthcheck/urls.py:1-5 y healthcheck/views.py:1-4.

## API PWA (estado actual)

- Auth/contexto:
  - `POST /api/users/login/`
  - `GET /api/users/me/`
  - `POST /api/users/logout/`
  - `POST /api/users/password-change-required/`
  - `POST /api/users/password-reset/request/`
  - `POST /api/users/password-reset/confirm/`
- Comedores:
  - `GET /api/comedores/{id}/`
  - `GET /api/comedores/{id}/documentos/`
  - `GET /api/comedores/{id}/documentos/{documento_id}/download/`
  - `GET|POST /api/comedores/{id}/nomina/`
  - `PATCH /api/comedores/nomina/{id}/`
  - `GET /api/comedores/{id}/prestacion-alimentaria/`
  - `GET /api/comedores/{id}/prestacion-alimentaria/historial/`
  - `GET /api/comedores/{id}/rendiciones/`
  - `GET /api/comedores/{id}/rendiciones/{rendicion_id}/`
  - `POST /api/comedores/{id}/rendiciones/{rendicion_id}/comprobantes/`
  - `POST /api/comedores/{id}/rendiciones/{rendicion_id}/presentar/`
  - `GET|POST /api/comedores/{id}/usuarios/`
  - `PATCH /api/comedores/{id}/usuarios/{user_id}/desactivar/`
- PWA complementaria:
  - `GET /api/pwa/health/`
  - `GET /api/pwa/push/config/`
  - `POST|DELETE /api/pwa/push/subscriptions/`
  - `GET|POST /api/pwa/espacios/{comedor_id}/colaboradores/`
  - `GET /api/pwa/espacios/{comedor_id}/colaboradores/generos/`
  - `GET /api/pwa/espacios/{comedor_id}/colaboradores/actividades/`
  - `POST /api/pwa/espacios/{comedor_id}/colaboradores/preview-dni/`
  - `PATCH|DELETE /api/pwa/espacios/{comedor_id}/colaboradores/{id}/`
  - `GET /api/pwa/espacios/{comedor_id}/actividades/catalogo/`
  - `GET /api/pwa/espacios/{comedor_id}/actividades/dias/`
  - `GET|POST /api/pwa/espacios/{comedor_id}/actividades/`
  - `GET|PATCH|DELETE /api/pwa/espacios/{comedor_id}/actividades/{id}/`
  - `GET /api/pwa/espacios/{comedor_id}/actividades/{id}/inscriptos/`
  - `GET /api/pwa/espacios/{comedor_id}/mensajes/`
  - `GET /api/pwa/espacios/{comedor_id}/mensajes/{id}/`
  - `PATCH /api/pwa/espacios/{comedor_id}/mensajes/{id}/marcar-visto/`
  - `GET|POST /api/pwa/espacios/{comedor_id}/nomina/`
  - `GET /api/pwa/espacios/{comedor_id}/nomina/generos/`
  - `POST /api/pwa/espacios/{comedor_id}/nomina/preview-dni/`
  - `POST /api/pwa/espacios/{comedor_id}/nomina/asistencia-alimentaria/`
  - `GET|PATCH|DELETE /api/pwa/espacios/{comedor_id}/nomina/{id}/`
  - `POST /api/pwa/espacios/{comedor_id}/nomina/{id}/registrar-asistencia/`
  - `GET /api/pwa/espacios/{comedor_id}/nomina/{id}/historial-asistencia/`
- Scope:
  - usuarios PWA: por `AccesoComedorPWA` activo;
  - usuarios no PWA: se mantiene filtrado legacy de `ComedorService`.
- Fuente de verdad funcional ampliada: `docs/implementaciones/pwa_backend.md`.
