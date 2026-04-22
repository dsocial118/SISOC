# Decision: memoria externa curada con invalidacion por commit

Fecha: 2026-04-16

## Contexto

Los asistentes releen con frecuencia el mismo contexto del repo para tareas donde no cambia nada relevante. Eso gasta tokens, agrega latencia y favorece reabrir archivos "por las dudas".

## Decision

Se adopta una memoria externa en dos capas:

- memoria durable y versionada en `docs/contexto/memoria/`
- cache local opcional y gitignored en `.codex/cache/context-memory/`

Cada memoria usa frontmatter TOML con:

- `paths` seguidos por la memoria,
- `validated_commit`,
- `validated_at`,
- `confidence`,
- `summary`

La frescura se calcula comparando cambios en esos paths desde `validated_commit` hasta `HEAD` mas cambios locales staged/unstaged.

## Por que esta opcion

- Aprovecha `docs/` como spec-as-source en lugar de inventar una base paralela.
- Mantiene trazabilidad humana y revisable en Git.
- Permite fast-path seguro: usar memoria fresca y revalidar cuando este vieja.
- La cache local cubre analisis efimeros sin contaminar el repo.

## Alternativas descartadas

### Solo memoria versionada

Se descarto como unica capa porque algunos analisis son efimeros y no justifican un commit.

### Solo cache local no versionada

Se descarto porque quita trazabilidad, comparte mal entre devs y tiende a degradarse sin revision.

### Embedding o vector store externo

Se descarto por complejidad operativa y porque el repo ya usa Markdown versionado como fuente de verdad.

## Consecuencias

- Hay que mantener memorias cuando el conocimiento reusable realmente aporta valor.
- La documentacion no reemplaza el codigo: si la memoria esta `stale` o `unknown`, se debe releer el codigo relevante.
- El flujo de arranque mejora sin relajar la disciplina de contexto minimo.
