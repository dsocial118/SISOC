# Guía para asistentes (IA)

- Comandos base: `docker-compose up` levanta servicios; `docker compose exec django pytest -n auto` corre tests; `black .`, `pylint **/*.py --rcfile=.pylintrc` y `djlint . --configuration=.djlintrc --reformat` formatean código/plantillas. Evidencia: AGENTS.md:5-8.
- Buenas prácticas de código: agregar docstrings descriptivas; mantener estructura por app; pruebas en `tests/`. Evidencia: AGENTS.md:10-13.
- Setup: copiar `.env.example` a `.env`; agregar ejemplos/scripts de datos en `docker/mysql`. Evidencia: AGENTS.md:15-17.
