# TESTING.md

Guía de testing para cambios hechos por IA en SISOC.

Fuente de verdad general: `../../AGENTS.md`.

## Stack y herramientas detectadas

- `pytest`
- `pytest-django`
- `pytest-xdist` (`-n auto`)
- `pytest-mock`
- `pytest-cov` (disponible)

Configuración relevante:
- `pytest.ini` define `DJANGO_SETTINGS_MODULE=config.settings`
- `python_files = tests.py test_*.py *_tests.py`
- `addopts = --reuse-db`
- marker `smoke`

## Regla obligatoria de cobertura mínima

- Toda funcionalidad nueva debe incluir testing mínimo.
- Todo bugfix debe incluir test de regresión cuando sea viable.
- Si no se agrega test, explicar por qué en la entrega.

## Pirámide de tests (pragmática para este repo)

## 1) Tests de unidad/servicio (prioridad alta)

Usar para:
- parsing,
- normalización,
- validaciones de negocio,
- helpers y services con reglas claras.

Ventajas:
- rápidos,
- menos frágiles,
- más fáciles de mantener.

## 2) Tests de integración de views/API (prioridad alta)

Usar para:
- permisos,
- status codes,
- payloads,
- side effects básicos,
- transacciones/rollback.

Patrón frecuente en repo:
- `client` / `APIClient`
- fixtures de usuario/grupos
- `monkeypatch` para aislar side effects

## 3) Smoke tests (prioridad selectiva)

Usar marker `smoke` para checks rápidos de integraciones o flujos críticos.

CI ejecuta:
- `smoke`: `docker compose run --build --rm --no-deps -T django pytest -m smoke`
- `migrations_check`: `docker compose exec -T django python manage.py makemigrations --check --dry-run` con MySQL
- `pytest`: `docker compose run --build --rm --no-deps -T django pytest -n auto --cov=. --cov-report=term-missing --cov-fail-under=75` en PRs
- `mysql_compat`: `docker compose exec -T django pytest -m mysql_compat -q` en PRs
- `deploy_guard`: exige checks requeridos (`encoding_check`, `black`, `djlint`, `pylint`, `smoke`, `pytest`, `migrations_check`, `mysql_compat` y `release_sanity` cuando el PR apunta a `main`)

## Qué testear (checklist por tipo de cambio)

## Bugfix

- Caso que rompía antes.
- Resultado esperado después del fix.
- Edge case relacionado si fue la causa raíz.

## Feature nueva

- Caso feliz.
- Caso inválido / validación.
- Permisos (si aplica).
- Compatibilidad con comportamiento anterior (si aplica).

## Refactor seguro

- Tests existentes deberían cubrirlo.
- Agregar tests solo si el refactor expone huecos críticos.

## Qué NO testear (o testear mínimo)

- Implementaciones triviales sin lógica.
- HTML exacto completo cuando alcanza validar fragmentos o estados relevantes.
- Detalles visuales frágiles que cambian fácil sin impacto funcional.

## Naming y estructura

- Ubicar tests en `app/tests/` cuando exista patrón.
- Nombres: `test_*.py`.
- Nombres de test descriptivos (`test_create_rechaza_registro_sin_montos`).
- Reutilizar fixtures de `conftest.py` local/global antes de crear fixtures duplicadas.

## Fixtures y mocking

## Fixtures

- Preferir fixtures pequeñas y reutilizables.
- Mantener datos mínimos para el caso.
- Reutilizar fixtures globales (`user`, `api_client`, etc.) cuando existan.

## Mocking / monkeypatch

Usar para:
- integraciones externas,
- servicios de terceros,
- side effects costosos,
- fallas controladas (rollback, excepciones).

Patrón observado en repo:
- `monkeypatch.setattr(...)` para forzar error/retorno.

## Permisos, status codes y rollback (importante)

Agregar tests de:
- acceso sin permisos (403/401 según caso)
- payload inválido (400)
- conflicto de negocio (409 cuando aplica)
- rollback/transacción si el flujo tiene side effects acoplados

## Entorno de tests (nota importante)

Según `config/settings.py`, durante tests:
- puede usarse SQLite en memoria (`:memory:`) si no hay `DATABASE_HOST` o `USE_SQLITE_FOR_TESTS=1`
- `SECRET_KEY` de test se define si falta

Implicancia:
- no asumir comportamiento específico de MySQL en tests unitarios/integración liviana sin necesidad.

## Comandos (local / CI)

## Local (recomendado)

```bash
# Suite completa

docker compose exec django pytest -n auto

# Smoke

docker compose exec django pytest -m smoke

# Un archivo o subset (ejemplo)

docker compose exec django pytest -n auto core/tests/test_monto_prestacion_views.py
```

## CI (referencia)

- `.github/workflows/tests.yml` ejecuta smoke, migrations check, pytest con cobertura, compatibilidad MySQL y deploy guard.
- `.github/workflows/lint.yml` ejecuta autofix acotado en PRs internos, `encoding_check`, `black`, `djlint` y `pylint`.

## Cómo evitar tests frágiles en templates/views

- Validar status code y contenido clave, no el HTML completo.
- Verificar permisos y redirects más que whitespace/markup exacto.
- Mockear integraciones externas para evitar flakes.

## Ejemplos concretos

## Ejemplo A - test de regresión (bugfix)

```python
def test_endpoint_retorna_400_si_page_no_es_numerica(client, user):
    client.force_login(user)
    response = client.get("/ruta/?page=abc")
    assert response.status_code == 400
```

## Ejemplo B - rollback por excepción

```python
with pytest.raises(RuntimeError):
    client.post(url, data=payload)
obj.refresh_from_db()
assert obj.estado == estado_original
```
