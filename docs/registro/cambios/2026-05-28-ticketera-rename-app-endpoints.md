# 2026-05-28 - Rename app `integracion` → `ticketera` y endpoints sin `integracion`

## Contexto

Revisión del PR #1795: la app no debe llamarse `integracion` ni las rutas deben
contener esa palabra. Decisión y contratos de la integración en
[docs/registro/decisiones/2026-05-27-integracion-ticketera.md](../decisiones/2026-05-27-integracion-ticketera.md).

## Cambios aplicados

- **App** `integracion/` → `ticketera/` (`git mv`; `TicketeraConfig`,
  `name="ticketera"`). `INSTALLED_APPS` actualizado.
- **Endpoints** sin el segmento `integracion`: el montaje en `config/urls.py`
  pasa de `/api/integracion/` a `/api/ticketera/` y las rutas internas pierden el
  prefijo `ticketera/`:
  - `/api/integracion/ticketera/usuarios/` → `/api/ticketera/usuarios/`
  - `/api/integracion/ticketera/auth/verificar/` → `/api/ticketera/auth/verificar/`
  - `/api/integracion/ticketera/auth/cambiar-password/` → `/api/ticketera/auth/cambiar-password/`
- **Names de URL**: `integracion-ticketera-*` → `ticketera-*`.
- **Flag**: `INTEGRACION_TICKETERA_ENABLED` → `TICKETERA_ENABLED`
  (`config/settings.py`, `.env.example`). Default sigue `True`.
- **Audit source**: `audit_context(source="integracion:ticketera")` →
  `source="ticketera"`.
- **Tag OpenAPI**: `Integración Ticketera` → `Ticketera`.
- **Tests**: `tests/test_integracion_ticketera.py` → `tests/test_ticketera.py`;
  `integracion/tests.py` → `ticketera/tests.py`.

## Comentarios de Copilot resueltos

- **Idempotencia con `source` variante.** El alta persiste `Profile.source` del
  body (p.ej. `ticketera-qa`), pero `_existing_user_response` solo trataba como
  idempotente `source == "ticketera"`, devolviendo `409` en la segunda provisión
  del mismo username. Se agrega `_is_ticketera_source()` (acepta `ticketera` y
  variantes `ticketera-*`) y un test de regresión
  (`test_usuarios_idempotente_con_source_variante_ticketera_200`).
- Docstrings de `ticketera/api_views.py` y `tests/test_ticketera.py` ahora listan
  los **tres** endpoints (incluido `cambiar-password`).
- El ADR ya no dice "dos endpoints/operaciones": dice "tres", consistente con la
  tabla de contratos.

## Validación

- `black --check` sobre los archivos tocados: OK.
- `pytest ticketera/tests.py tests/test_ticketera.py` en la imagen Docker del
  feature con `--no-migrations` (SQLite): **34 passed**. Se usa `--no-migrations`
  porque el grafo de migraciones de `admisiones` está roto en `development`
  (`NodeNotFoundError ('admisiones', '0014_squashed_0020_complementary_flow')`),
  bug pre-existente y compartido por los PRs activos; no es de este cambio. La
  corrida con migraciones queda delegada a la CI.

## Notas

- Los archivos bajo `docs/registro/` conservan su nombre datado
  (`*-integracion-ticketera*.md`): son registros históricos. Su **contenido** sí
  se actualizó a `ticketera` / `/api/ticketera/`.
