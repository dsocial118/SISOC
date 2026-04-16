# Fix CSRF en login de homologacion local

Fecha: 2026-04-13

## Que cambio

- Se corrigio la construccion de `CSRF_TRUSTED_ORIGINS` en `config/settings.py`.
- Ahora los origenes confiables para CSRF:
  - siguen derivandose de `DJANGO_ALLOWED_HOSTS`,
  - agregan `DOMINIO` cuando viene configurado con esquema real,
  - aceptan overrides explicitos desde `DJANGO_CSRF_TRUSTED_ORIGINS`,
  - y contemplan `localhost` / `127.0.0.1` con el puerto publicado por Docker (`DOCKER_DJANGO_PORT_FORWARD`).
- Se agrego un test de regresion en `tests/test_settings_env_parsing.py` para cubrir el caso `ENVIRONMENT=homologacion` accedido por `http://localhost:8001`.

## Decision principal

No se toco el flujo de login ni el template. El problema estaba en configuracion: el entorno de homologacion arma origenes CSRF con perfil productivo (`https`) pero el compose local sigue exponiendo la app por `http://localhost:8001`.

La correccion se hizo en `settings` para mantener el hardening de homologacion/produccion y, a la vez, permitir el arranque local del mismo perfil sin deshabilitar CSRF.

## Impacto operativo

- Homologacion real sigue aceptando su dominio HTTPS configurado.
- Homologacion local deja de fallar en login por mismatch de `Origin`/`Referer` cuando se usa `localhost:8001`.
- Si un entorno usa un origen adicional no cubierto por `DJANGO_ALLOWED_HOSTS` o `DOMINIO`, ahora puede declararlo en `DJANGO_CSRF_TRUSTED_ORIGINS`.

## Validacion esperada

- Acceder al login del entorno levantado con perfil homologacion desde `http://localhost:8001/`.
- Enviar usuario y contrasena validos.
- Verificar que ya no aparezca `403 Verificacion CSRF fallida. Peticion abortada`.
