# Integración de Resend vía SMTP

## Qué cambió

- Se dejó documentada la configuración recomendada para usar Resend como proveedor SMTP global de Django.
- La validación de `config/settings.py` ahora exige `EMAIL_HOST_USER` y `EMAIL_HOST_PASSWORD` cuando se elige el backend SMTP.
- Si la configuración SMTP está incompleta o inválida, SISOC vuelve al backend de consola para no romper desarrollo local ni tests.

## Decisión principal

Se mantuvo el uso del backend SMTP estándar de Django en lugar de incorporar SDK o dependencias nuevas. Así, los flujos actuales que llaman a `send_mail` siguen funcionando sin cambios de negocio y el proveedor queda desacoplado del código de aplicación.

## Configuración operativa recomendada

Variables de entorno para Resend:

- `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`
- `EMAIL_HOST=smtp.resend.com`
- `EMAIL_PORT=587`
- `EMAIL_HOST_USER=resend`
- `EMAIL_HOST_PASSWORD=<RESEND_API_KEY>`
- `EMAIL_USE_TLS=true`
- `EMAIL_USE_SSL=false`
- `DEFAULT_FROM_EMAIL=SISOC <onboarding@resend.dev>`

## Validación

- Test unitario para conservar SMTP cuando la configuración está completa.
- Test unitario para volver a consola cuando falta una credencial SMTP.
- Regresión existente de password reset mantenida sobre backend Django.

## Prueba manual

1. Configurar las variables SMTP de Resend en el entorno activo.
2. Levantar SISOC.
3. Solicitar un reset desde `/password_reset/` o `POST /api/users/password-reset/request/`.
4. Verificar recepción del correo y que el enlace apunte al dominio configurado.
5. Quitar `EMAIL_HOST_PASSWORD` y repetir para confirmar que la app no falla y usa salida por consola.
