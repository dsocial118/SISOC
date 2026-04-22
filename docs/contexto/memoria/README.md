# Memoria operativa para asistentes

Esta carpeta guarda memoria reusable y curada para reducir reconstruccion de contexto entre tareas de IA.

Objetivos:

- bajar consumo de tokens en tareas repetidas,
- acelerar el arranque de analisis sobre modulos estables,
- mantener trazabilidad e invalidacion explicita,
- evitar que cada agente relea el mismo codigo cuando no cambio nada relevante.

## Capas

- `docs/contexto/memoria/*.md`: memoria durable y versionada, util para el equipo.
- `.codex/cache/context-memory/*.md`: cache local opcional y gitignored para notas efimeras o experimentales.

## Regla de uso

1. Leer primero `AGENTS.md` y `docs/indice.md`.
2. Resolver memoria aplicable con `scripts/ai/context_memory.py preflight --target <path>`.
3. Si la memoria esta `fresh`, usarla como fast-path y abrir solo el codigo imprescindible.
4. Si la memoria esta `stale` o `unknown`, tomarla solo como pista y revalidar el codigo.
5. Cuando el analisis nuevo sea reusable, actualizar o crear memoria en esta carpeta.

## Formato

Cada documento usa frontmatter TOML delimitado por `+++` con al menos:

- `key`: identificador estable
- `title`: titulo visible
- `summary`: resumen corto para preflight
- `paths`: archivos o directorios seguidos por la memoria
- `validated_commit`: commit usado para invalidacion
- `validated_at`: fecha ISO de validacion
- `confidence`: alta/media/baja
- `default`: si debe aparecer aun sin target

Ver `TEMPLATE.md` para un ejemplo listo para copiar.

## Comandos utiles

```bash
python scripts/ai/context_memory.py preflight --target core/views.py
python scripts/ai/context_memory.py resolve --target core/views.py --format json
python scripts/ai/context_memory.py scaffold --slug core --title "Core" --summary "Resumen operativo de core" --path core/ --path tests/test_core_*.py
python scripts/ai/context_memory.py refresh --file docs/contexto/memoria/core.md
```

## Criterio de calidad

- Sintetizar solo hechos reutilizables y de alta senal.
- No copiar codigo ni duplicar documentacion larga.
- Registrar side effects, boundaries, invariantes y tests rapidos.
- Explicar cuando la memoria deja de ser segura para reutilizar.
