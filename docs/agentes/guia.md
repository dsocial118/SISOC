# Guia para asistentes (IA)

- Fuente de verdad: `AGENTS.md`.
- Lectura obligatoria antes de implementar: `docs/indice.md`, `docs/ia/*` y documentación del dominio afectado dentro de `docs/`.
- Registro obligatorio de trabajo importante: documentar cada cambio o decisión importante en `docs/` usando la subcarpeta temática que corresponda (crearla si no existe). En caso de existir documentacion escrita del codigo que se esta modificando, actualizar la documentacion
- Enfoque: spec-as-source con archivos Markdown del repo (sin depender de herramientas específicas).
- Commits generados por IA: mensaje en español y patrón obligatorio `<type>(<scope>): <subject>` (detalle y plantilla en `docs/ia/CONTRIBUTING_AI.md`).
- Comandos base: `docker compose up` levanta servicios; `docker compose exec django pytest -n auto` corre tests; `black .`, `pylint **/*.py --rcfile=.pylintrc` y `djlint . --configuration=.djlintrc --reformat` formatean código/plantillas. Evidencia: AGENTS.md.
- Buenas prácticas de código: agregar docstrings descriptivas; mantener estructura por app; pruebas en `tests/`. Evidencia: AGENTS.md:10-13.
- Setup: copiar `.env.example` a `.env`; agregar ejemplos/scripts de datos en `docker/mysql`. Evidencia: AGENTS.md:15-17.
- Arranque minimo: `AGENTS.md`, `docs/indice.md`, archivo objetivo, tests y una sola guia relevante de `docs/ia/`.
- Expandir contexto solo si la evidencia lo requiere.
- Registrar cambios o decisiones importantes en `docs/`.
- Commits de IA: mensaje en espanol con patron `<type>(<scope>): <subject>`.
- Validar primero sobre archivos y tests tocados.
- Crear worktrees de tarea fuera del checkout principal, en `../worktrees/<slug>`.
