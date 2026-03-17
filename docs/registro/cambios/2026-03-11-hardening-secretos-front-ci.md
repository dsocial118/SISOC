# 2026-03-11 - Hardening de secretos (frontend + CI)

## Resumen

Se aplicaron tres medidas de seguridad:

1. Se eliminó la exposición de `GESTIONAR_API_KEY` en contexto/template/JS del cliente.
2. Se sanitizó metadata sensible en `.env.qa` y `.env.prod` para dejar plantillas sin IPs/IDs reales.
3. Se incorporó escaneo automático de secretos con `gitleaks` en pre-commit y en CI.

## Detalle técnico

- `comedores/views/comedor.py`
  - Se quitó la inyección de `GESTIONAR_API_KEY` y `GESTIONAR_API_CREAR_COMEDOR` al contexto de `ComedorDetailView`.
- `comedores/templates/comedor/comedor_detail.html`
  - Se removieron variables JS con secretos.
  - Se dejó de cargar `static/custom/js/comedordetail.js` en esta pantalla (ya usa el script de cache territorial).
- `comedores/templates/comedor/new_comedor_detail.html`
  - Se removieron variables JS con secretos.
- `static/custom/js/comedordetail.js`
  - Se reemplazó llamada directa a AppSheet (con API key) por endpoint backend:
    - `GET /comedores/<id>/territoriales/?force_sync=true`
- `config/settings.py`
  - `SENTRY_DSN` pasa a venir de `os.getenv("SENTRY_DSN", "").strip()`.
- `.env.qa` y `.env.prod`
  - Se reemplazaron hosts/usuarios/IDs por placeholders.
  - Se agregó `SENTRY_DSN=""` como variable de entorno explícita.
- `.gitleaks.toml`
  - Config de gitleaks con allowlist acotada para valores dummy existentes.
- `.pre-commit-config.yaml`
  - Hook de `gitleaks`.
- `.github/workflows/secrets.yml`
  - Pipeline de escaneo de secretos sobre working tree (`--no-git`).

## Impacto

- Se reduce la superficie de exposición en frontend.
- Se reduce el riesgo de publicar metadata operativa en plantillas `.env`.
- Se institucionaliza control preventivo de secretos antes del push y en PR/CI.
