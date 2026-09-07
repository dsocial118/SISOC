# Daily standup SISOC

Plantilla viva para la daily de 15 minutos. Se actualiza cada día (no crear un archivo nuevo por día); lo cerrado se mueve a "Cerrado esta semana" y se limpia semanalmente.

## Cómo usar (15 min)

- **Antes de la daily**: cada persona completa su fila (Hoy / Bloqueos) en cada tarea que tenga, incluida la sección de tareas manuales.
- **Durante la daily**: recorrer persona por persona, leer bloqueos en voz alta. No resolver problemas ahí — anotar responsable de darle seguimiento fuera de la daily.
- **Después**: mover ítems resueltos a "Cerrado esta semana"; borrar bloqueos ya resueltos.
- Las ramas de GH sin autor identificable no se listan acá (ver nota al final) — si alguien las está trabajando, agregarse manualmente.

## Leyenda de estado

🟢 en curso sin problemas · 🟡 atención / riesgo · 🔴 bloqueado · ⚪ sin novedades hoy

## Por persona

### Juani
- 🟢 **Celiaquía** — rama `Celiaquia_Tk2254` — Hoy: ___ / Bloqueos: ___
- 🟡 **Arquitectura / boundaries** — rama `codex/issue-2309-executable-boundary` — Hoy: ___ / Bloqueos: ___
- Tareas fuera de GH: ___

### Victoria
- 🟢 **Celiaquía** — rama `Celiaquia_Tk1947` — Hoy: ___ / Bloqueos: ___
- 🟢 **Admisiones** — rama `tk_2178FinalizacionAdmision` — Hoy: ___ / Bloqueos: ___
- Tareas fuera de GH: ___

### Matias
- 🟡 **Comedores / PWA territorial** — rama `feature/territorial-corte-appsheet` — Hoy: ___ / Bloqueos: ___
- Tareas fuera de GH: ___

### Roman
- Módulo — rama / tarea — Hoy: ___ / Bloqueos: ___
- Tareas fuera de GH: ___

### Esteban
- Módulo — rama / tarea — Hoy: ___ / Bloqueos: ___
- Tareas fuera de GH: ___

### Juan Cruz
- Módulo — rama / tarea — Hoy: ___ / Bloqueos: ___
- Tareas fuera de GH: ___

### Camilo
- Módulo — rama / tarea — Hoy: ___ / Bloqueos: ___
- Tareas fuera de GH: ___

### Wanda
- Módulo — rama / tarea — Hoy: ___ / Bloqueos: ___
- Tareas fuera de GH: ___

### (agregar otra persona)
- Módulo — rama / tarea — Hoy: ___ / Bloqueos: ___
- Tareas fuera de GH: ___

> Sumar acá a cualquiera del equipo que no tenga actividad de rama reciente (soporte, QA manual, reuniones con áreas, tareas administrativas, etc.) — el listado de arriba solo cubre lo que quedó registrado en git.

## Bloqueos activos (para escalar)

| Persona | Módulo | Bloqueo | Desde | Próxima acción |
|---|---|---|---|---|
| | | | | |

## Cerrado esta semana

- (mover acá los ítems resueltos, con fecha y persona)

## Nota sobre el origen de los datos

Poblado el 2026-08-31 a partir de `git log` (últimos ~14 días) y `git branch -r` (ramas remotas activas). Sin acceso a `gh`/GitHub en este entorno, así que no hay estado real de PRs/issues — la asignación es una aproximación por autor de rama.

Por pedido explícito, **no se listan ramas de GH sin autor identificable** (creadas o commiteadas por `github-actions[bot]` / `sisoc-release-automation[bot]` sin persona asociada). Si alguien del equipo está trabajando alguna de estas, agregarse manualmente en "Por persona":

- `codex/fix-cdi-ci-regression` (Centro de Infancia, 28/08)
- `codex/issue-2369-correcciones-cdi` (Centro de Infancia, 28/08)
- `fix/territorial-scope-borrados` (Comedores / PWA territorial, 30/08)
- `fix/territorial-feedback-qa` (Comedores / PWA territorial, 30/08)
- `hotfix/territorial-dropdown-appsheet` (Comedores / PWA territorial, 27/08)
- `feature/modulo-encuestas` (módulo nuevo, aún no integrado a `development`, 30/08)
- `pwanueva` (Comedores / PWA territorial, integración general, 27/08 — antes atribuida a `dsocial118`, quitada por no ser una persona confirmada)

Últimos avances mergeados que no tienen rama activa asociada hoy (para contexto, no requieren seguimiento salvo novedad): Rendición de Cuentas Mensual (reconciliación de comprobantes legacy, 25/08), Relevamientos (fix de scope territorial/IDOR, 26/08), VAT (búsqueda de centros por CUE, 26/08).
