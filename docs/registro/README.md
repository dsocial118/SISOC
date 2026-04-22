# Spec-as-Source en SISOC

Este directorio define la convencion para documentacion operativa y de cambios.

## Reglas obligatorias

1. Antes de implementar, leer `AGENTS.md`, `docs/indice.md` y solo el contexto minimo necesario para la tarea.
2. Registrar en `docs/` cada cambio o decision importante.
3. No depender de herramientas externas de spec-driven development; la fuente de verdad vive en Markdown dentro del repo.

## Carga minima recomendada

Inicio:
- `AGENTS.md`
- `docs/indice.md`
- archivo objetivo
- tests del modulo
- una guia relevante de `docs/ia/`

Ampliar solo si el cambio toca reglas funcionales, permisos, seguridad o comportamiento observable.

## Convencion sugerida

- `docs/registro/cambios/`
- `docs/registro/decisiones/`
- `YYYY-MM-DD-<tema>.md`

## Cuando registrar

- cambios funcionales visibles,
- decisiones de arquitectura o diseno,
- cambios de seguridad, permisos o datos sensibles,
- trade-offs relevantes para mantenimiento.

## Cuando puede no aplicar

Si el cambio es trivial y sin impacto funcional, se puede omitir el archivo, pero debe quedar justificado en la entrega.
