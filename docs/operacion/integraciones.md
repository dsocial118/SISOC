# Integraciones y dependencias

## Base de datos
- Motor principal MySQL configurado vía variables `DATABASE_*`; modo pruebas usa SQLite en memoria cuando corre pytest. Evidencia: config/settings.py:153-174.

## Cache
- Backend `LocMemCache` con ubicación única y TTLs declarados por módulo (dashboard, comedor, ciudadano, etc.). Evidencia: config/settings.py:175-189.

## Archivos estáticos y media
- `STATIC_URL` y `MEDIA_URL` servidos desde el filesystem del proyecto (`static_root`, `media`). Evidencia: config/settings.py:122-128.

## Logging
- Directorio `logs/` creado automáticamente; handlers diarios por nivel (info/error/warning/critical) y un handler JSON para datos. Evidencia: config/settings.py:246-344.

## Servicios externos
- GESTIONAR: sincronización asíncrona de comedores, referentes, observaciones y relevamientos mediante `requests` y `ThreadPoolExecutor`, usando claves `GESTIONAR_API_*` y `DOMINIO` para adjuntar imágenes. Evidencia: comedores/tasks.py:11-125 y relevamientos/tasks.py:13-85; config/settings.py:236-241.
- RENAPER: cliente HTTP con token cacheado (50 minutos) para consultar ciudadanos; credenciales `RENAPER_API_*`. Evidencia: centrodefamilia/services/consulta_renaper.py:13-170.
- Google Maps: clave opcional `GOOGLE_MAPS_API_KEY`. Evidencia: config/settings.py:241.
- Correo saliente: Django usa `send_mail` y puede operar con backend SMTP. Para Resend, la configuración recomendada es `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`, `EMAIL_HOST=smtp.resend.com`, `EMAIL_PORT=587`, `EMAIL_HOST_USER=resend`, `EMAIL_HOST_PASSWORD=<API_KEY>`, `EMAIL_USE_TLS=true`, `EMAIL_USE_SSL=false` y un `DEFAULT_FROM_EMAIL` verificado en el proveedor. Si falta alguno de los datos críticos del SMTP, SISOC vuelve al backend de consola para no romper entornos locales. Evidencia: config/settings.py:189-242; users/services_auth.py:45-81.
