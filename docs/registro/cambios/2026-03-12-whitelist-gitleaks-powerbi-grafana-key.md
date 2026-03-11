# 2026-03-12 - Whitelist puntual en gitleaks para embed de Power BI

## Resumen

Se agregó una excepción puntual de `gitleaks` para un falso positivo detectado por la regla `grafana-api-key` en el template del dashboard.

## Detalle técnico

- Archivo agregado: `.gitleaksignore`
- Fingerprint permitido:
  - `dashboard/templates/dashboard.html:grafana-api-key:32`

La excepción se aplicó por fingerprint para limitar el alcance a ese hallazgo específico, evitando una allowlist amplia por archivo o regla.

## Impacto

- Desbloquea el job de GitHub Actions `gitleaks` para este caso conocido.
- Mantiene el escaneo activo para el resto de secretos potenciales.
