#!/usr/bin/env bash
set -euo pipefail

TASK_KIND="${1:-general}"
TARGET_PATH="${2:-}"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || (cd "$script_dir/../.." && pwd))"
cd "$repo_root"
git_available=true
if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
  git_available=false
fi

print_header() {
  printf '\n== %s ==\n' "$1"
}

print_header "SISOC AI Preflight"
printf 'Repo: %s\n' "$repo_root"
printf 'Task kind: %s\n' "$TASK_KIND"
if [[ -n "$TARGET_PATH" ]]; then
  printf 'Target path: %s\n' "$TARGET_PATH"
fi

branch="unknown"
commit="unknown"
if [[ "$git_available" == true ]]; then
  branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')"
  commit="$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
fi
printf 'Branch: %s\n' "$branch"
printf 'HEAD: %s\n' "$commit"

print_header "Cambios locales (no tocar sin pedirlo)"
if [[ "$git_available" != true ]]; then
  echo "Git no disponible desde este shell; usar PowerShell si hace falta status exacto."
elif git diff --quiet && git diff --cached --quiet; then
  echo "Working tree limpio"
else
  git status --short
fi

print_header "Lectura inicial recomendada"
echo "- AGENTS.md"
echo "- docs/indice.md"
echo "- memoria de contexto reutilizable aplicable (si existe)"
echo "- archivo objetivo + tests del modulo"
echo "- docs/ia/CONTEXT_HYGIENE.md"
echo "- una sola guia de docs/ia segun la tarea"

echo
print_header "Recordatorios criticos del repo"
echo "- Logica de negocio preferentemente en services/"
echo "- Coexisten Django views y DRF"
echo "- Logging custom en config/settings.py + core/utils.py"
echo "- No se usa Celery actualmente"
echo "- Crear worktrees de tarea fuera del repo principal"

print_header "Comandos utiles"
cat <<'CMDS'
docker compose up
docker compose exec django pytest -n auto
docker compose exec django pytest -m smoke
black . --config pyproject.toml
djlint . --configuration=.djlintrc --reformat
pylint **/*.py --rcfile=.pylintrc
python scripts/ai/context_memory.py preflight --target <path>
python scripts/ai/context_memory.py scaffold --slug <slug> --title <titulo> --summary <resumen> --path <path>
CMDS

print_header "Contexto minimo sugerido (por tipo)"
case "$TASK_KIND" in
  bugfix-view)
    echo "- AGENTS.md"
    echo "- docs/indice.md"
    echo "- view afectada"
    echo "- tests del modulo"
    echo "- docs/ia/TESTING.md"
    ;;
  bugfix-api|feature-api)
    echo "- AGENTS.md"
    echo "- docs/indice.md"
    echo "- api_views.py / serializers*.py del modulo"
    echo "- tests API del modulo"
    echo "- docs/ia/TESTING.md"
    echo "- docs/ia/ARCHITECTURE.md si el boundary no esta claro"
    ;;
  feature-service|refactor-service)
    echo "- AGENTS.md"
    echo "- docs/indice.md"
    echo "- service afectado"
    echo "- tests del flujo"
    echo "- docs/ia/STYLE_GUIDE.md"
    ;;
  logging|errores)
    echo "- AGENTS.md"
    echo "- docs/indice.md"
    echo "- archivo afectado"
    echo "- docs/ia/ERRORS_LOGGING.md"
    echo "- config/settings.py / core/utils.py si aplica"
    ;;
  migration|modelo)
    echo "- AGENTS.md"
    echo "- docs/indice.md"
    echo "- modelo(s)"
    echo "- migraciones cercanas"
    echo "- tests relacionados"
    echo "- docs/ia/ARCHITECTURE.md"
    ;;
  *)
    echo "- AGENTS.md"
    echo "- docs/indice.md"
    echo "- archivo(s) objetivo"
    echo "- tests del modulo"
    echo "- docs/ia/STYLE_GUIDE.md"
    ;;
esac

if [[ -n "$TARGET_PATH" && -e "$TARGET_PATH" ]]; then
  print_header "Sugerencia: archivos cercanos"
  if [[ -d "$TARGET_PATH" ]]; then
    find "$TARGET_PATH" -maxdepth 2 -type f | sort | head -30
  else
    dir="$(dirname "$TARGET_PATH")"
    find "$dir" -maxdepth 2 -type f | sort | head -30
  fi
fi

print_header "Memoria operativa reutilizable"
if command -v python3 >/dev/null 2>&1; then
  if [[ -n "$TARGET_PATH" ]]; then
    python3 scripts/ai/context_memory.py preflight --target "$TARGET_PATH"
  else
    python3 scripts/ai/context_memory.py preflight
  fi
elif command -v python >/dev/null 2>&1; then
  if [[ -n "$TARGET_PATH" ]]; then
    python scripts/ai/context_memory.py preflight --target "$TARGET_PATH"
  else
    python scripts/ai/context_memory.py preflight
  fi
else
  echo "No se encontro python/python3 para resolver memoria operativa."
fi

print_header "Fin"
echo "Usar mejoras cercanas solo como propuesta, sin scope creep."
