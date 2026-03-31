# 2026-03-27 - Ajuste de documentación IA para black, pylint y djlint

## Contexto

Los asistentes venían recibiendo instrucciones demasiado genéricas sobre formato y lint. Eso generaba fricción repetida: código Python escrito con ancho o wrapping poco compatibles con `black`, validaciones arrancando por todo el repo en lugar de archivos puntuales y templates que `djlint` tenía que reestructurar por completo.

## Qué se actualizó

- `AGENTS.md`: se agregó una disciplina operativa explícita para escribir código y templates ya alineados con `black`, `pylint` y `djlint`.
- `CODEX.md`: se reforzó el criterio de diff mínimo incluyendo el check mínimo de formato/lint y la regla de escribir `black-first`.
- `docs/ia/STYLE_GUIDE.md`: se añadieron reglas concretas de compatibilidad con `black`, `pylint` y `djlint`, más ejemplos cortos.
- `docs/ia/CONTRIBUTING_AI.md`: se definió una secuencia de validación priorizando archivos tocados antes de checks globales.
- `docs/agentes/guia.md`: se aclararon comandos recomendados para validación acotada.

## Impacto esperado

- Menos cambios correctivos de formato al final de cada tarea.
- Menos ruido en diffs por reformateos innecesarios.
- Mejor alineación entre lo que escriben los agentes y lo que efectivamente exigen CI y la configuración versionada del repo.
