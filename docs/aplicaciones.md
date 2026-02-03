# Apps y rutas

## Aplicaciones instaladas
- Apps Django/3ros: admin, auth, sessions, messages, staticfiles, admindocs, crispy_forms/bootstrap5, django_extensions, import_export, multiselectfield, auditlog, DRF/rest_framework_api_key, drf_spectacular, corsheaders. Evidencia: config/settings.py:42-63.
- Apps propias: users, core, dashboard, comedores, organizaciones, cdi, ciudadanos, duplas, admisiones, intervenciones, historial, acompanamientos, expedientespagos, relevamientos, rendicioncuentasfinal, rendicioncuentasmensual, centrodefamilia, celiaquia, audittrail. Evidencia: config/settings.py:64-83.
- Apps de debug/performance agregadas solo con `DEBUG=True`: debug_toolbar y silk. Evidencia: config/settings.py:359-366.

## URL principales
- Router raíz incluye auth, users, core, dashboard, comedores, organizaciones, cdi, duplas, audittrail, ciudadanos, admisiones, centrodefamilia, healthcheck, acompanamientos (prefijo), expedientespagos (prefijo), rendicioncuentasfinal, relevamientos, rendicioncuentasmensual (prefijo), celiaquia y API de centrodefamilia; expone Swagger/Redoc en `/api/docs` y `/api/redoc`. Evidencia: config/urls.py:12-44.
- Endpoint de salud `/health/` responde `OK`. Evidencia: healthcheck/urls.py:1-5 y healthcheck/views.py:1-4.
