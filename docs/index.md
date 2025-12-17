# Documentación SISOC

## Mapa de documentos
- `docs/setup.md`: requisitos, variables de entorno y flujo de arranque en contenedores.
- `docs/apps.md`: listado de apps y rutas principales.
- `docs/integraciones.md`: bases de datos, cache, estáticos/media y servicios externos.
- `docs/management_commands.md`: comandos de administración disponibles.
- `docs/operaciones.md`: cron jobs y endpoints de health.
- `docs/agents.md`: guía rápida para asistentes/automatización.

## Contexto mínimo
- Stack: Django + MySQL con despliegue vía Docker Compose. Evidencia: README.md:1-4 y docker-compose.yml:1-34.
- Variables de entorno documentadas en `.env.example` (incluye DB, GESTIONAR, RENAPER, puertos y dominio). Evidencia: .env.example:1-51.
- Servicios externos activos: GESTIONAR (sincronización de comedores/relevamientos) y RENAPER (consulta de ciudadanos). Evidencia: comedores/tasks.py:11-125, relevamientos/tasks.py:13-85, centrodefamilia/services/consulta_renaper.py:13-170.
