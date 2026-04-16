# PR 1446 - ajustes de jobs de listas y CI

## Contexto
- La branch del PR habia quedado con regresiones en tests unitarios de listados grandes: varios stubs seguian modelando un contrato anterior y no el flujo real de paginacion sin `COUNT(*)`.
- El workflow de lint asumía que las variables JSON siempre llegaban pobladas y fallaba con `JSONDecodeError` cuando no habia archivos detectados.
- `makemigrations --check` seguia proponiendo una migracion nueva en `acompanamientos` porque `0007` no reflejaba el `blank=True` del modelo.
- `VAT/forms.py` seguia usando `_default_manager`, que disparaba `pylint` por acceso a miembro protegido.
- El test `dashboard/tests.py` dependia de un fixture `superuser` definido solo dentro de `tests/conftest.py`, por eso en CI no encontraba el fixture.
- Los tests unitarios de inscripcion VAT usaban stubs incompletos frente al servicio actual.

## Cambios aplicados
- Se alinearon los tests unitarios de `centrodefamilia`, `VAT`, `organizaciones` y `comedores` con el contrato real de los listados:
  - los builders mockeados ahora devuelven querysets y no strings,
  - la paginacion sin `count` ya no afirma `is_paginated=True` cuando la pagina no tiene siguiente,
  - el stub de `comedores` ahora representa un queryset sliceable en vez de una lista de IDs.
- Se endurecio `VAT.views.persona.InscripcionCreateView` para leer tanto `voucher_debito`/`voucher_saldo` como los atributos legacy `_voucher_debito`/`_voucher_saldo`, sin perder el mensaje de lista de espera.
- Se completaron los stubs de `tests/test_vat_persona_views_unit.py` para reflejar el contrato actual del servicio, incluyendo `estado`, `exclude`, `count` y `cupo_total`.
- En `dashboard/tests.py` se reemplazo el fixture no disponible por `admin_client`, que si existe globalmente en `pytest-django`.
- En `.github/workflows/lint.yml` se cambio el parseo de variables JSON para tolerar valores vacios tanto en el autofix como en el check de `black`.
- En `VAT/forms.py` se reemplazo el acceso a `_default_manager` por un helper que usa `all_objects` o `objects`, ambos publicos.
- En `acompanamientos/migrations/0007_hitos_cleanup_comedor.py` se agrego `blank=True` al campo `acompanamiento` para evitar la migracion espuria `0008`.

## Impacto esperado
- Los jobs de tests vuelven a cubrir el contrato real de paginacion y scope en los listados afectados.
- El workflow de lint deja de caer cuando no hay archivos Python o templates detectados.
- `pylint` deja de marcar acceso a miembros protegidos en `VAT/forms.py`.
- El test de dashboard deja de depender de fixtures definidos fuera de su arbol de descubrimiento.
- `makemigrations --check` no deberia proponer una migracion nueva solo por desalineacion entre modelo y migracion previa.
- La vista de alta de inscripcion VAT mantiene compatibilidad con objetos de prueba o adapters que todavia exponen los atributos legacy del voucher.

## Validacion
- `py -m black --check` sobre archivos Python modificados.
- `docker compose run --build --rm --no-deps -T django pytest -q` sobre los 9 casos que estaban fallando en CI.
- `docker compose run --build --rm --no-deps -T django pylint VAT/forms.py --rcfile=.pylintrc`.
- `docker compose run --build --rm --no-deps -T django python manage.py makemigrations --check --dry-run`.

## Riesgos y rollback
- Riesgo principal: bajo. Los cambios de codigo quedaron acotados a compatibilidad de tests, fixture de dashboard, lint del formulario VAT y alineacion de una migracion existente.
- Rollback: revertir este commit en la branch del PR.
