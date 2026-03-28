# CONTRIBUTING_AI.md

Proceso recomendado para trabajar con IA en este repo (pedido, implementación, validación y PR).

Fuente de verdad general: `../../AGENTS.md`.

## Objetivo

Estandarizar cómo se piden y revisan cambios hechos por IA para mantener:
- diffs pequeños,
- PRs revisables,
- menos regresiones,
- menor variabilidad entre asistentes.

## Política spec-as-source (obligatoria)

- Antes de implementar, leer `docs/indice.md`, `docs/ia/*` y documentación de `docs/` del dominio afectado.
- Cada cambio y decisión importante debe registrarse en Markdown dentro de `docs/` usando la subcarpeta que corresponda al dominio/tema.
- Si la subcarpeta no existe, debe crearse.
- Convención sugerida (no obligatoria): `docs/registro/cambios/` y `docs/registro/decisiones/`.
- El objetivo es trabajar en modo spec-as-source sin depender de herramientas específicas.

## Cómo pedir cambios a la IA (brief operativo)

Todo pedido debería incluir:
- Contexto: qué módulo/flujo toca.
- Objetivo: qué problema resuelve.
- Alcance: qué se puede tocar y qué no.
- Restricciones: compatibilidad, performance, permisos, UX, etc.
- Criterio de aceptación: casos esperados.
- Validación esperada: tests/checks.
- Si se permite o no proponer mejoras cercanas.

## Template corto para pedir cambios

```md
Necesito [bugfix/feature/refactor] en `[path o app]`.

Contexto:
- ...

Alcance:
- Tocar: ...
- No tocar: ...

Criterio de aceptación:
- ...

Checks:
- ...

Podés proponer mejoras cercanas: sí/no
```

## Proceso sugerido de implementación (con IA)

## 1) Explorar

- Revisar código real del módulo (`views`, `models`, `services`, `tests`).
- Buscar implementaciones similares.
- Confirmar contratos existentes antes de escribir.
- Revisar documentación vigente en `docs/` para el dominio afectado.

## 2) Delimitar alcance

- Definir el cambio mínimo viable.
- Identificar el test mínimo necesario.
- Separar refactor de comportamiento cuando sea posible.

## 3) Implementar

- Reutilizar patrones existentes de la app.
- Mantener compatibilidad hacia atrás por defecto.
- Evitar cambios masivos no solicitados.

## 4) Validar

- Ejecutar checks puntuales primero (tests del módulo afectado).
- Ejecutar formato/lint sobre archivos tocados antes de probar comandos globales.
- Ejecutar checks más amplios si el impacto lo requiere.
- Si no se pudo validar, dejarlo explícito.

Secuencia recomendada para reducir fricción:

1. Formatear o chequear solo archivos editados (`black path.py`, `djlint template.html --reformat`, `pylint app/archivo.py`).
2. Correr tests puntuales del módulo o flujo afectado.
3. Escalar a checks globales solo si el cambio toca superficies compartidas, varios archivos o fue pedido explícitamente.

## 5) Entregar

- Resumen de cambios.
- Archivos tocados.
- Validación ejecutada.
- Supuestos.
- Riesgos.
- Registro spec-as-source en `docs/<subcarpeta>/...` (si aplica).
- Mejoras cercanas detectadas (opcional).

## PRs pequeños y revisables (regla)

Preferir PRs con una sola intención principal:
- `fix`: corrige bug.
- `feat`: agrega capacidad.
- `refactor`: mejora estructura sin cambiar comportamiento.
- `test`: agrega/mejora pruebas.
- `docs`: documentación.
- `chore`: tareas de mantenimiento acotadas.

Evitar PRs que mezclen:
- refactor + feature + formateo global,
- cambios funcionales en múltiples dominios sin relación,
- limpieza masiva sin criterio de aceptación claro.

## Convenciones de commits (obligatorias)

Reglas obligatorias para commits hechos por IA:
- Mensaje en español.
- Primera línea obligatoria con patrón: `<type>(<scope>): <subject>`.
- Usar `scope` semántico y concreto (app, módulo o área real afectada).

Plantilla:

```text
Obligatorio:
<type>(<scope>): <subject>

Opcional:
<why> (por qué se hace; contexto del problema)
<what> (qué cambió; bullets si aplica)
<how>  (cómo se resolvió; opcional, sólo si aporta)

<impact> (impacto / migraciones / flags / backwards-compat)
<tests>  (cómo se probó)

<refs>   (Refs #123 / Closes #123)
<breaking> (BREAKING CHANGE: ...)
```

Ejemplos:

```text
fix(core): corregir 500 al parsear page en load_organizaciones

why: el endpoint devolvía 500 ante valores no numéricos en `page`.
what:
- valida `page` antes de convertirla a entero
- responde 400 con mensaje de error controlado
tests:
- docker compose exec django pytest -n auto core/tests/test_views.py
refs: Refs #123
```

```text
feat(comunicados): agregar filtro opcional por estado en API

what:
- agrega parámetro `estado` en query params
- mantiene comportamiento previo cuando no se envía
impact: sin migraciones; backward compatible
tests:
- docker compose exec django pytest -n auto comunicados/tests/
```

## Supuestos explícitos (obligatorio si faltan datos)

Si la IA avanza con supuestos, deben quedar documentados.

Ejemplo:

```md
Supuestos:
- Se mantiene el serializer actual porque el payload no cambia.
- Se usa permiso existente `IsAuthenticated` por compatibilidad.
```

## Riesgos y rollback (cuando aplica)

En cambios con más impacto (M/L), documentar:
- Riesgo principal (compatibilidad, migración, performance, permisos).
- Cómo revertir (archivo/commit/migración).
- Qué monitorear después del merge.

## Mejoras cercanas detectadas por IA (opcional)

La IA puede proponer mejoras cercanas al cambio solicitado, pero no debe implementarlas fuera de alcance sin aprobación.

Formato recomendado para PR/comentario:

```md
## Mejoras cercanas detectadas (opcional)
- [Impacto alto | costo bajo] Agregar test de permiso faltante en `...`.
- [Impacto medio | costo bajo] Reemplazar manejo genérico de excepción por `logger.exception(...)` en `...`.
```

## Checklist pre-PR (IA + dev)

- Cambio cumple el alcance pedido.
- Diff pequeño y revisable.
- No se tocaron configs de tooling/CI sin pedido.
- Tests mínimos agregados cuando aplica.
- Test de regresión agregado en bugfix cuando aplica.
- Lint/formato ejecutado si corresponde.
- Docs actualizadas si cambia comportamiento.
- Decisiones/cambios importantes registrados en `docs/` (subcarpeta temática) o justificación de excepción.
- Supuestos y riesgos documentados.

## Comandos locales y referencia a CI

### Local (frecuentes)

```bash
docker compose up
docker compose exec django pytest -n auto
docker compose exec django pytest -m smoke
black .
black path/al/archivo.py --config pyproject.toml
djlint . --configuration=.djlintrc --reformat
djlint templates/ruta.html --reformat --configuration=.djlintrc
pylint **/*.py --rcfile=.pylintrc
pylint app/archivo.py --rcfile=.pylintrc
```

### Reglas operativas para escribir con menos fricción

- Python nuevo o modificado debe escribirse ya compatible con `black`; evitar “después lo formateo”.
- `pylint` se usa contra la configuración real del repo. No introducir patrones que generen warnings obvios y después compensarlos con cambios de formato.
- En templates, preferir estructura clara para que `djlint` haga ajustes mínimos y no rehaga bloques completos.
- Evitar ejecutar `black .`, `djlint .` o `pylint **/*.py` como primer paso si el cambio está acotado a uno o pocos archivos.

### CI (referencia)

- Lint/formato: `.github/workflows/lint.yml`
- Tests/smoke: `.github/workflows/tests.yml`

CI usa `docker compose` y ejecuta smoke + tests automáticos.

## Ejemplos concretos

## Ejemplo A - Bugfix pequeño (buen pedido)

```md
Fix mínimo en `core/views.py` para evitar 500 cuando `page` no es numérica en `load_organizaciones`.
No refactorizar otras vistas.
Agregar test de regresión en `core/tests/`.
Podés proponer mejoras cercanas: sí.
```

## Ejemplo B - Refactor seguro (buen pedido)

```md
Refactor seguro en `core/services/favorite_filters.py` para reducir duplicación en validaciones.
Sin cambiar payload ni contratos públicos.
Si detectás un bug cercano, reportalo como mejora opcional, no lo implementes sin aprobación.
```
