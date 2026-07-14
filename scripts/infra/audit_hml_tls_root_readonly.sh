#!/usr/bin/env bash
set -Eeuo pipefail

EXPECTED_HOSTNAME="${HML_EXPECTED_HOSTNAME:-ldmzssies-homolo}"
CERT_DIR="${HML_CERT_DIR:-/etc/apache2/certs}"
ACTIVE_CERT="${HML_ACTIVE_CERT:-$CERT_DIR/fullchain.crt}"
ACTIVE_KEY="${HML_ACTIVE_KEY:-$CERT_DIR/secretarianaf.gob.ar.key}"

log() {
  printf '[audit_hml_tls_root_readonly.sh] %s\n' "$*"
}

fail() {
  log "ERROR: $*" >&2
  exit 1
}

public_key_hash_from_cert() {
  openssl x509 -in "$1" -noout -pubkey 2>/dev/null \
    | openssl pkey -pubin -outform DER 2>/dev/null \
    | sha256sum | awk '{print $1}'
}

main() {
  local file cert_hash key_hash

  [[ "$EUID" -eq 0 ]] || fail "Ejecutar como root mediante sudo."
  [[ "$(hostname -s)" == "$EXPECTED_HOSTNAME" ]] || fail "Host inesperado."
  [[ -r "$ACTIVE_CERT" ]] || fail "Certificado activo no legible."
  [[ -r "$ACTIVE_KEY" ]] || fail "Key activa no legible."

  log "Auditoria read-only; no renueva certificados ni recarga NGINX."

  printf 'NGINX_REFERENCES\n'
  grep -RhsE '^[[:space:]]*ssl_certificate(_key)?[[:space:]]' \
    /etc/nginx/sites-enabled /etc/nginx/conf.d 2>/dev/null || true

  printf 'CERTIFICATES\n'
  while IFS= read -r -d '' file; do
    if openssl x509 -in "$file" -noout >/dev/null 2>&1; then
      stat -c 'path=%n owner=%U:%G mode=%a size=%s modified=%y' "$file"
      openssl x509 -in "$file" -noout -serial -subject -issuer -dates \
        -fingerprint -sha256
      printf 'public_key_sha256=%s\n' "$(public_key_hash_from_cert "$file")"
    fi
  done < <(
    find "$CERT_DIR" -maxdepth 1 -type f \
      \( -name '*.crt' -o -name '*.pem' \) -print0 | sort -z
  )

  cert_hash="$(public_key_hash_from_cert "$ACTIVE_CERT")"
  key_hash="$(
    openssl pkey -in "$ACTIVE_KEY" -pubout -outform DER 2>/dev/null \
      | sha256sum | awk '{print $1}'
  )"
  printf 'ACTIVE_KEY_MATCH\n'
  printf 'certificate_public_key_sha256=%s\n' "$cert_hash"
  printf 'private_key_public_part_sha256=%s\n' "$key_hash"
  if [[ "$cert_hash" == "$key_hash" ]]; then
    printf 'active_certificate_matches_key=yes\n'
  else
    printf 'active_certificate_matches_key=no\n'
  fi

  printf 'LETSENCRYPT_RENEWAL_FILES\n'
  find /etc/letsencrypt/renewal -maxdepth 1 -type f -name '*.conf' -print \
    2>/dev/null || true
  printf 'LETSENCRYPT_LIVE_DIRS\n'
  find /etc/letsencrypt/live -mindepth 1 -maxdepth 1 -type d -print \
    2>/dev/null || true

  printf 'CERTBOT_TIMERS\n'
  for unit in certbot.timer snap.certbot.renew.timer; do
    systemctl show "$unit" -p ActiveState -p UnitFileState \
      -p LastTriggerUSec -p NextElapseUSecRealtime --no-pager 2>/dev/null || true
  done

  log "Auditoria TLS read-only finalizada."
}

main "$@"
