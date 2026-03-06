# 2026-03-06 - Regla de lectura y documentacion obligatoria para asistentes

## Contexto
- Se solicito reforzar los archivos de documentacion para IA para que:
  - sea obligatorio leer la documentacion en `docs/`,
  - sea obligatorio documentar cambios y decisiones importantes en la misma carpeta.

## Cambios aplicados
- Se actualizo `AGENTS.md` con politica obligatoria de spec-as-source.
- Se sincronizaron reglas en `CODEX.md`, `CLAUDE.md` y `LLM.md`.
- Se actualizo `docs/ia/CONTRIBUTING_AI.md` con el flujo de registro.
- Se actualizo `docs/indice.md` y `docs/agentes/guia.md` con la nueva seccion/ruta.
- Se creo estructura base:
  - `docs/registro/README.md`
  - `docs/registro/cambios/README.md`
  - `docs/registro/decisiones/README.md`

## Impacto esperado
- Los agentes deberian trabajar con lectura documental obligatoria y dejar trazabilidad minima por cambio/decision importante.

## Validacion
- Revision manual de consistencia y rutas dentro de los archivos tocados.

## Riesgos y rollback
- Riesgo principal: sobre-documentacion en cambios triviales.
- Mitigacion: se permite excepcion con justificacion explicita para cambios sin impacto funcional.
