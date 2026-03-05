# 2026-03-06 - Adopcion de disciplina spec-as-source para trabajo con IA

## Estado
- aceptada

## Contexto
- El repo ya tenia guias para asistentes (`AGENTS.md`, `CODEX.md`, `CLAUDE.md`, `LLM.md`), pero no existia una regla transversal y explicita para registrar sistematicamente cambios y decisiones importantes en `docs/`.

## Decision
- Se establece como obligatorio:
  - leer `docs/indice.md`, `docs/ia/*` y docs del dominio afectado antes de implementar,
  - documentar cada cambio o decision importante en `docs/` dentro de la subcarpeta necesaria.
- La practica adopta enfoque spec-as-source sin requerir herramientas especificas.

## Consecuencias
- Mejora trazabilidad tecnica y continuidad entre agentes/desarrolladores.
- Aumenta disciplina documental y reduce decisiones implicitas.
- Impone un costo bajo adicional de escritura por cambio relevante.

## Referencias
- https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html
