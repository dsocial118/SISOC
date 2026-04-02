# VAT - ajuste de access scope por roles reales

Fecha: 2026-04-02

## Qué cambió

- Se alineó `VAT/services/access_scope.py` con los roles efectivos que existen hoy en la base para VAT.
- El chequeo provincial ahora reconoce explícitamente `auth.role_provincia_vat` además del permiso `VAT.view_centro` y del `Profile` con provincia asignada.
- El chequeo de referente ahora reconoce ambos codenames legacy detectados en producción/local:
  - `auth.role_referentecentrovat`
  - `auth.role_centroreferentevat`

## Motivo

Había una diferencia entre los grupos/permisos reales de VAT y los codenames usados por `access_scope.py`, lo que volvía frágil la clasificación de usuarios provinciales y referentes.

## Validación prevista

- Test de scope provincial filtrando centros por provincia.
- Test de reconocimiento del alias legacy de referente.