# 2026-04-23 - Análisis pre-deploy development -> main

## Contexto

- Se actualizó el estado remoto del repo y se comparó `origin/main` contra `origin/development`.
- El PR previo `#1567` (`development -> main`, 2026-04-16) ya estaba cerrado sin merge, por lo que este análisis toma como fuente de verdad el delta actual entre ramas.
- El trabajo se hizo en la worktree aislada `C:\Users\Juanito\Desktop\Repos-Codex\worktrees\predeploy-development-main-20260423`, sobre la branch `task/predeploy-development-main-20260423`.

## Alcance observado

- Distancia entre ramas: `311` commits del lado `development` y `0` del lado `main` en `git rev-list --left-right --count origin/main...origin/development`.
- Diff agregado: `267` archivos, `17696` inserciones y `1694` eliminaciones.
- Módulos con mayor movimiento: `docs`, `tests`, `celiaquia`, `ciudadanos`, `VAT`, `centrodeinfancia`, `core`, `acompanamientos`, `comedores`, `admisiones` y `relevamientos`.

## Riesgos bloqueantes

- La release sigue incorporando la migración `acompanamientos/0007_hitos_cleanup_comedor.py`, que borra hitos huérfanos y exige tratamiento operativo/manual sobre datos reales antes de producción.
- `ciudadanos` mantiene como requisito operativo el backfill `python manage.py backfill_identidad ...`, con backup y ventana coordinada antes de ejecutarlo en producción.
- Se detectó un bug real en `.env.example`: el bloque de Resend dejaba líneas activas con prefijo `- `, lo que rompía `docker compose config` y el bootstrap de cualquier worktree nueva. Este saneamiento debe entrar en `development` antes de considerar GO.
- No hay todavía evidencia concluyente de checks verdes para un PR nuevo `development -> main`; debe validarse sobre ese PR exacto.

## Riesgos no bloqueantes

- El corte mezcla funcionalidades, migraciones, performance, CI, documentación y tooling, con riesgo de interacción mayor que un deploy chico.
- El entorno local no puede levantar Docker porque `dockerDesktopLinuxEngine` no está disponible en esta máquina; por eso la validación completa depende de GitHub Actions y de checks puntuales locales con `uv`.
- El host local no tiene `pytest` global instalado, aunque sí fue posible correr regresiones focales con `uv run`.

## Saneamiento aplicado

- Se corrigió `.env.example` para dejar el ejemplo de Resend comentado y restaurar defaults válidos de email por defecto.
- Se agregó una regresión en `tests/test_settings_env_parsing.py` para evitar que vuelvan a entrar asignaciones inválidas en la sección de email.
- Se actualizó `CHANGELOG.md` para reflejar el corte completo que hoy viaja de `development` hacia `main` con fecha `2026-04-23`.

## Seguimiento de pytest

- Los cuatro fallos observados en GitHub Actions no respondían a una regresión nueva de runtime sino a tests desalineados respecto de contratos ya mergeados en `development`.
- `relevamientos`: `update_territorial()` ya había recuperado el contrato de validación estricta y el mensaje `"Debe seleccionar un territorial válido."`; dos asserts seguían matcheando la variante sin tilde.
- `comedores/nomina`: desde `fix(comedores): ordenar bajas y contar asistentes activos` la vista usa `cantidad_activos` para la tarjeta de asistentes y el resumen agrega ese campo explícitamente; los mocks de tests seguían modelando el contrato previo.

## Validaciones ejecutadas

- `powershell -ExecutionPolicy Bypass -File scripts/ai/codex_bootstrap.ps1`
  - Falló primero por `.env.example` inválido; luego del fix quedó bloqueado únicamente por Docker Desktop apagado.
- `uv run --python 3.11 --with-requirements requirements.txt pytest tests/test_settings_env_parsing.py::test_env_example_declares_valid_email_assignments -q`
  - OK (`1 passed`)
- `uv run --python 3.11 --with-requirements requirements.txt python -m black --check tests/test_settings_env_parsing.py`
  - OK
- `docker compose config -q`
  - OK
- `powershell -ExecutionPolicy Bypass -File scripts/ai/codex_doctor.ps1`
  - OK para `.env` y `compose-config`; pendiente Docker engine en esta máquina

## Resultado

- Recomendación actual: **NO-GO** hasta que el PR de saneamiento a `development` entre, se revisen los riesgos de datos de `acompanamientos` y `ciudadanos`, y el PR exacto `development -> main` muestre checks concluyentes.
