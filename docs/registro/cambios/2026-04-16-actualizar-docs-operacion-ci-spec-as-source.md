# 2026-04-16 - Actualizar docs de operacion, CI y superficies PWA

## Contexto

Se detecto drift documental entre el estado actual del repo y varias fuentes de verdad operativas:

- `README.md` seguia apuntando al repo `BACKOFFICE`, al puerto local `8000` y a ejemplos de API/deploy ya desalineados;
- `docs/operacion/instalacion.md` e `infraestructura.md` describian overrides de compose no versionados en el repo actual;
- `docs/ia/TESTING.md` no reflejaba el pipeline vigente de GitHub Actions;
- `docs/contexto/aplicaciones.md` resumía una superficie PWA incompleta;
- `docs/operacion/comandos_administracion.md` no inventariaba varios commands reales con impacto operativo.

## Cambios aplicados

- Se actualizo `README.md` para:
  - usar la URL real del repo `SISOC`;
  - documentar `localhost:8001` como puerto local por defecto;
  - evitar ejemplos de auth ambiguos en API;
  - apuntar a las docs canónicas de instalacion, infraestructura y comandos;
  - alinear la convencion de commits con `AGENTS.md`.
- Se corrigio `docs/operacion/instalacion.md` para reflejar:
  - el puerto local real;
  - el set de compose versionados hoy presente;
  - el uso de `.env` del servidor para entornos deploy.
- Se ajusto `docs/operacion/infraestructura.md` para que QA/homologacion/prd no refieran a overrides inexistentes.
- Se actualizo `docs/ia/TESTING.md` con los jobs reales de CI:
  - `smoke`
  - `migrations_check`
  - `pytest` con cobertura
  - `mysql_compat`
  - `deploy_guard`
  - checks de `lint.yml`
- Se amplio `docs/contexto/aplicaciones.md` con endpoints vigentes de auth/PWA complementaria.
- Se completo `docs/operacion/comandos_administracion.md` con commands faltantes de Comedores y Celiaquia.

## Decision principal

Se prefirio corregir las docs canónicas en lugar de seguir duplicando detalle en `README.md`.

La regla aplicada fue:

- `README.md`: onboarding y enlaces a fuentes de verdad;
- `docs/operacion/*`: detalle operativo real;
- `docs/ia/TESTING.md`: comportamiento vigente de CI para asistentes;
- `docs/contexto/aplicaciones.md`: mapa resumido de superficie;
- `docs/registro/cambios/`: trazabilidad del ajuste documental.

## Validacion

- Revision manual de evidencia contra:
  - `.github/workflows/tests.yml`
  - `.github/workflows/lint.yml`
  - `docker-compose.yml`
  - `docker-compose.deploy.yml`
  - `docker-compose.produccion.yml`
  - `.env.example`
  - `pwa/api_urls.py`
  - management commands inventariados
- Barrido de referencias obsoletas en los archivos tocados.

## Impacto esperado

- Menos drift entre onboarding, operacion y CI real.
- Menos ambiguedad para agentes y personas al ejecutar tests, levantar entornos y ubicar endpoints/comandos.
- Mejor trazabilidad spec-as-source para cambios documentales futuros.
