# 2026-03-12 - Whitelist puntual en gitleaks para embed de Power BI

## Resumen

Se agregó una excepción puntual de `gitleaks` para un falso positivo detectado por la regla `grafana-api-key` en el template del dashboard.
Adicionalmente, se extendió la excepción para los enlaces de fixtures de tableros de Power BI, también detectados como falso positivo por la misma regla.

## Detalle técnico

- Archivo agregado: `.gitleaksignore`
- Fingerprint permitido:
  - `dashboard/templates/dashboard.html:grafana-api-key:32`
- Fingerprints permitidos adicionales (fixtures controlados):
  - `dashboard/fixtures/tableros.json:grafana-api-key:<linea>`
  - líneas actuales: `8, 23, 38, 53, 68, 83, 98, 113, 143, 158, 173, 188, 203, 218, 233, 248, 263, 278, 293, 308, 323, 338, 353, 368, 383, 398, 413, 428`

La excepción se aplicó por fingerprint para limitar el alcance a ese hallazgo específico, evitando una allowlist amplia por archivo o regla.

## Impacto

- Desbloquea el job de GitHub Actions `gitleaks` para este caso conocido.
- Mantiene el escaneo activo para el resto de secretos potenciales.
- Se evita una allowlist amplia por archivo/regla, manteniendo una excepción acotada por fingerprint.
