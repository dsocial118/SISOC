#!/usr/bin/env bash
# Solo root. Simula por defecto y conserva las entradas ajenas a PAS.
set -Eeuo pipefail
apply=0
[[ "${1:-}" == "--apply" ]] && apply=1
[[ "$EUID" -eq 0 ]] || { echo 'Ejecutar como root'; exit 1; }
backup="/var/backups/sisoc/pas-cron/$(date +%Y%m%d_%H%M%S)"
pattern='^[[:space:]]*[^#[:space:]].*manage\.py[[:space:]]+sincronizar_supervivencia_pas([[:space:]]|$)'
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
while IFS=: read -r user _; do
  crontab -u "$user" -l > "$work/cron" 2>/dev/null || continue
  if grep -Eq "$pattern" "$work/cron"; then
    printf 'Entrada PAS encontrada en el crontab del usuario: %s\n' "$user"
    if [[ "$apply" -eq 1 ]]; then
      install -d -m 700 "$backup"
      install -m 600 "$work/cron" "$backup/user-$user"
      grep -Ev "$pattern" "$work/cron" > "$work/after" || true
      crontab -u "$user" "$work/after"
    fi
  fi
done < /etc/passwd
for file in /etc/crontab /etc/cron.d/*; do
  [[ -f "$file" && ! -L "$file" ]] || continue
  if grep -Eq "$pattern" "$file"; then
    printf 'Entrada PAS encontrada en el archivo: %s\n' "$file"
    if [[ "$apply" -eq 1 ]]; then
      install -d -m 700 "$backup"
      cp -p -- "$file" "$backup/file-$(basename "$file")"
      grep -Ev "$pattern" "$file" > "$work/after" || true
      cat "$work/after" > "$file"
    fi
  fi
done
echo 'Revisar envoltorios y temporizadores por separado; habilitar Beat solo después de verificar el servidor.'
