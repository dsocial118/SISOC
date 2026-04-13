#!/usr/bin/env bash
set -euo pipefail

TASK_KIND="${1:-general}"
TARGET_PATH="${2:-}"

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$repo_root"

print_header() {
  printf '\n== %s ==\n' "$1"
}

print_header "SISOC AI Preflight"
printf 'Repo: %s\n' "$repo_root"
printf 'Task kind: %s\n' "$TASK_KIND"
if [[ -n "$TARGET_PATH" ]]; then
  printf 'Target path: %s\n' "$TARGET_PATH"
fi

branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')"
commit="$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
printf 'Branch: %s\n' "$branch"
printf 'HEAD: %s\n' "$commit"

print_header "Cambios locales (no tocar sin pedirlo)"
if git diff --quiet && git diff --cached --quiet; then
  echo "Working tree limpio"
else
  git status --short
fi

print_header "Lectura inicial recomendada"
echo "- AGENTS.md"
echo "- docs/indice.md"
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

print_header "Fin"
echo "Usar mejoras cercanas solo como propuesta, sin scope creep."
