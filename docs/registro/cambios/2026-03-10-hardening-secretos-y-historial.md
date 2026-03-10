# 2026-03-10 - Hardening de secretos y limpieza de historial

## Contexto
Se detectó exposición de secretos en frontend y presencia histórica de credenciales reales en commits antiguos.

## Cambios aplicados
- Se eliminó la inyección de `GESTIONAR_API_KEY` y `GESTIONAR_API_CREAR_COMEDOR` en `ComedorDetailView` y templates de detalle.
- Se cambió `static/custom/js/comedordetail.js` para consumir el endpoint backend `/comedores/<id>/territoriales/` en lugar de llamar directo a GESTIONAR desde el navegador.
- Se agregaron asserts de regresión en tests para validar que esas claves no estén en contexto ni en HTML renderizado.
- Se ajustó `config/settings.py` para usar `SENTRY_DSN` desde entorno (`os.getenv`) y evitar DSN hardcodeado.
- Se añadió `.env.prod` y `.env.qa` al `.gitignore` y se desindexaron del repositorio para evitar versionado futuro.
- Se reescribió el historial git con `git-filter-repo` para purgar credenciales reales históricas (API keys, usuarios/passwords y credenciales embebidas en URLs).
- Se reemplazaron rutas hardcodeadas con usuario en scripts de logs por rutas dinámicas/neutras para evitar regresiones tras la purga.

## Impacto
- El frontend ya no expone credenciales de integración.
- El repositorio local queda con historia reescrita; para publicar, requiere `push --force-with-lease`.
