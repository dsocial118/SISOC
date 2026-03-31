# Codex Docker aislado por worktree

## Qué cambió

- Se formalizó que Codex debe ejecutar Django, pytest y comandos de `manage.py` dentro de Docker Compose, no en el host.
- Se agregó `docker-compose.codex.yml` para despublicar puertos y permitir múltiples stacks simultáneos por worktree.
- Se endurecieron los scripts `scripts/ai/codex_*.ps1` para:
  - derivar un nombre de proyecto Compose único por worktree,
  - invocar Compose con `-p <project>` y el override de Codex,
  - usar `run --rm django ...` para comandos puntuales,
  - levantar `mysql` solo cuando el comando realmente lo necesita,
  - fallar si Docker no está disponible en lugar de caer al host.
- Se actualizaron `AGENTS.md`, `CODEX.md`, `.codex/rules.md` y `.codex/environments/environment.toml` para reflejar el flujo Docker-first aislado.

## Motivación

Codex seguía intentando validar con Python del host o compartiendo el mismo proyecto Compose entre worktrees. Eso generaba falsos negativos (`django` no instalado en el host) y riesgo de colisión entre agentes.

## Uso recomendado

```powershell
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 test
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 smoke
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 manage makemigrations --check --dry-run
```

## Impacto esperado

- Cada worktree usa su propia red/volúmenes/contendedores Compose.
- Codex deja de depender de Python local para validar el repo.
- Se reduce el riesgo de conflictos de puertos al correr varios agentes en paralelo.
