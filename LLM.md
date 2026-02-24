# LLM.md

Entrada rápida para cualquier IA que trabaje en SISOC.

## Fuente de verdad

Leer primero `AGENTS.md`.

## Reglas críticas (resumen)

- Buscar referencias reales en el repo antes de escribir código.
- No inventar APIs, modelos, campos ni endpoints.
- Hacer cambios mínimos (`small diffs`) y revisables.
- Mantener compatibilidad hacia atrás salvo pedido.
- No tocar configs de lint/format/test/CI sin pedido.
- Agregar tests mínimos en features nuevas.
- Agregar test de regresión en bugfixes cuando sea viable.
- Explicitar supuestos si falta información.
- Respetar seguridad/permisos y no loggear secretos/PII.
- Podés proponer mejoras cercanas, pero no implementarlas fuera de alcance sin aprobación.

## Comandos principales

```bash
docker compose up
docker compose exec django pytest -n auto
docker compose exec django pytest -m smoke
black .
djlint . --configuration=.djlintrc --reformat
pylint **/*.py --rcfile=.pylintrc
```

## Guías detalladas

- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/CONTRIBUTING_AI.md`
- `docs/ia/STYLE_GUIDE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/ia/SECURITY_AI.md`
- `docs/ia/ERRORS_LOGGING.md`

## Mini-template de prompt correcto

```md
Necesito [bugfix/feature/refactor] en `[path]`.
Alcance: [qué tocar] / [qué no tocar].
Criterio de aceptación: [resultado esperado].
Checks: [tests/lint].
Podés proponer mejoras cercanas: sí/no.
```

## Mejores prácticas de entrega

Incluir siempre:
- qué cambió,
- archivos tocados,
- validación ejecutada,
- supuestos,
- mejoras cercanas detectadas (opcional).
