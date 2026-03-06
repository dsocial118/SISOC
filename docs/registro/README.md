# Spec-as-Source en SISOC

Este directorio define una convención recomendada para documentación operativa que acompaña el desarrollo asistido por IA.

Objetivo:
- mantener una fuente de verdad versionada en el repo,
- reducir decisiones implícitas,
- facilitar revisión, auditoría y continuidad entre agentes/personas.

## Reglas obligatorias

1. Antes de implementar, leer `docs/indice.md`, `docs/ia/*` y la documentación del dominio afectado.
2. Registrar cada cambio o decisión importante en Markdown dentro de `docs/`, en la subcarpeta temática que corresponda.
3. No depender de herramientas específicas para spec-driven development; la práctica se resuelve con documentación en `docs/`.

## Convención sugerida

- `docs/registro/cambios/`: registro de cambios importantes realizados.
- `docs/registro/decisiones/`: registro de decisiones importantes (ADR livianas).

También se pueden crear subcarpetas por dominio fuera de `docs/registro/` (por ejemplo `docs/users/`, `docs/celiaquia/`, `docs/core/`) cuando convenga.

## Convención de nombres

- `YYYY-MM-DD-<tema>.md` (kebab-case, claro y corto).

## Cuándo registrar

- Cambios funcionales con impacto visible.
- Decisiones de diseño o arquitectura.
- Cambios de seguridad, permisos o datos sensibles.
- Trade-offs relevantes para mantenimiento futuro.

## Cuándo puede no aplicar

En cambios triviales sin impacto funcional (por ejemplo typo menor o ajuste no observable), se puede omitir el archivo, pero debe quedar justificado en la entrega/PR.
