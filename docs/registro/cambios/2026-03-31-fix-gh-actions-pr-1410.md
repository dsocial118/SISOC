# CI: corrección de checks de GitHub Actions para PR 1410

Fecha: 2026-03-31

## Cambio

Se corrigieron fallas que impedían pasar los checks de CI asociados al PR 1410:

- tests VAT ajustados al modelo académico invertido;
- `InscripcionService` tolera ofertas mockeadas sin `voucher_parametrias`;
- test de `centrodeinfancia` marcado correctamente para acceso a base de datos;
- templates VAT reformateados para cumplir `djlint`.

## Decisión clave

Los cambios sobre tests no alteran comportamiento funcional del sistema: corrigen supuestos inválidos del suite frente al esquema nuevo y a objetos mockeados mínimos usados en pruebas unitarias.

## Validación

Se reprodujeron localmente los checks relevantes del workflow:

- `pytest -m smoke`
- `pytest -n auto --cov=. --cov-fail-under=75`
- `pytest -m mysql_compat -q`
- `djlint` sobre los templates modificados
- `makemigrations --check --dry-run`
