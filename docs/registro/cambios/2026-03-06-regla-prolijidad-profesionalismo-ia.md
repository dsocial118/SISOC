# 2026-03-06 - Regla explícita de prolijidad y profesionalismo para IAs

## Contexto
Se reforzó la documentación operativa para asistentes de IA con una regla explícita de prolijidad y profesionalismo general antes de programar.

## Cambios realizados
- Se actualizó `AGENTS.md` en la sección de calidad para exigir explícitamente:
  - foco en prolijidad técnica general (cohesión, bajo acoplamiento, responsabilidades claras y consistencia arquitectónica),
  - evitar sobreingeniería o fragmentación innecesaria,
  - tratar la creación de apps nuevas como ejemplo de decisión estructural que debe justificarse,
  - exigir documentación de código prolija: docstrings en español y comentarios no redundantes.
- Se actualizó `docs/ia/CONTRIBUTING_AI.md` para incorporar este criterio en el flujo de trabajo (delimitación e implementación).
- Se actualizó `docs/ia/CONTRIBUTING_AI.md` (checklist pre-PR) para validar explícitamente docstrings en español y comentarios no redundantes.

## Impacto esperado
- Menor fragmentación del monolito por apps innecesarias.
- Menor sobreingeniería y mejor consistencia técnica general.
- Mayor consistencia estructural entre cambios hechos por distintos asistentes.
- Mejor revisabilidad técnica de PRs.

## Compatibilidad
Sin impacto funcional en runtime. Cambio documental/procesual.
