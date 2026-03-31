# 2026-03-31 - Agentes IA ajustados para resolver pylint sin atajos

## Contexto

Los agentes venían teniendo una política demasiado laxa frente a `pylint`: en
la práctica, eso facilita resolver avisos con supresiones o ignorados en lugar
de corregir la causa raíz. El objetivo de este ajuste es que trabajen bajo las
reglas reales del repositorio y privilegien mejores prácticas antes que
`ignore` o `disable`.

## Cambios aplicados

- `AGENTS.md`: se explicitó que `.pylintrc` es un contrato y que `ignore` /
  `disable` quedan como último recurso, local y justificado.
- `docs/ia/STYLE_GUIDE.md`: se reforzó la estrategia de corrección primero y
  la política de supresiones mínimas.
- `docs/ia/CONTRIBUTING_AI.md`: se agregó el orden recomendado para resolver
  hallazgos de `pylint` sin atajos.
- `docs/agentes/guia.md`: se alineó la guía rápida con la misma política.

## Impacto esperado

- Menos supresiones innecesarias de `pylint`.
- Código más legible y mantenible.
- Menor deuda técnica escondida detrás de ignores locales o ampliaciones de
  configuración.

## Validación

- Revisión documental de las guías actualizadas.
- No se ejecutaron tests porque el cambio es solo de documentación.

## Riesgos y rollback

- Riesgo principal: algunos arreglos pueden requerir más trabajo inicial que un
  `disable` rápido.
- Rollback: revertir los archivos de documentación modificados.
