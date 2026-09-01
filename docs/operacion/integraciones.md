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
- GESTIONAR/AppSheet: sincronización asíncrona de comedores, referentes,
  observaciones y relevamientos mediante `requests` y `ThreadPoolExecutor`,
  usando claves `GESTIONAR_API_*` y `DOMINIO` para adjuntar imágenes.
  `GESTIONAR_INTEGRATION_ENABLED` es el interruptor único tanto para envíos
  como para pulls y comandos de sincronización: sin la variable queda activo
  en HML/PRD e inactivo en dev/QA; `true` lo habilita y `false` lo corta por
  completo. No usarlo como corte parcial ni definirlo vacío, porque todo valor
  presente distinto de `1`, `true`, `yes` u `on` deshabilita la integración.
  Para que tome efecto se debe actualizar el entorno del proceso Django y
  recargarlo según el runbook de la plataforma; no requiere un cambio de
  código. Para volver al comportamiento por ambiente, quitar la variable.
  Evidencia: `config/settings.py`, `comedores/tasks.py`,
  `comedores/services/territorial_service/impl.py`, `relevamientos/tasks.py`
  y `comedores/management/commands/sync_comedores_gestionar.py`.
- RENAPER: cliente HTTP compartido en `core/integrations/renaper.py`, con autenticación efímera por consulta y fachada compatible en `core/services/renaper.py`; credenciales `RENAPER_API_*`, timeout y retries/backoff configurables. No persiste tokens en cache ni registra DNI, tokens o payloads remotos.
- Google Maps: clave opcional `GOOGLE_MAPS_API_KEY`. Evidencia: config/settings.py:241.
- Correo saliente: Django usa `send_mail` y puede operar con backend SMTP. Para Resend, la configuración recomendada es `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`, `EMAIL_HOST=smtp.resend.com`, `EMAIL_PORT=587`, `EMAIL_HOST_USER=resend`, `EMAIL_HOST_PASSWORD=<API_KEY>`, `EMAIL_USE_TLS=true`, `EMAIL_USE_SSL=false` y un `DEFAULT_FROM_EMAIL` verificado en el proveedor. Si falta alguno de los datos críticos del SMTP, SISOC vuelve al backend de consola para no romper entornos locales. Evidencia: config/settings.py:189-242; users/services_auth.py:45-81.
- Recuperación PWA: `PWA_BASE_URL` debe ser la URL pública del frontend Mobile
  del ambiente, sin slash final. Se usa para construir enlaces de recuperación
  con `uid` y `token`; en HML/PRD configurarla explícitamente antes de habilitar
  el flujo y verificar que llegue al frontend esperado. Evidencia:
  `users/services_auth.py` y `config/settings.py`.
