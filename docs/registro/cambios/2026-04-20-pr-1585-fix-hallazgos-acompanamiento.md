# 2026-04-20 - Fix hallazgos review PR 1585 en acompañamientos

## Contexto

Durante la revisión del PR `#1585` se detectaron dos problemas en el flujo
de disponibilización a acompañamiento:

1. `AcompanamientoService.importar_datos_desde_admision` intentaba poblar
   `InformacionRelevante` usando campos que pertenecen a `InformeTecnico`,
   no a `Admision`.
2. `_procesar_post_disponibilizar_acomp` marcaba la admisión como enviada
   antes de crear `Acompanamiento` e `Hitos`, dejando estado parcial si la
   importación fallaba.

## Qué cambió

- `acompanamientos/acompanamiento_service.py`
  - `InformacionRelevante` ahora toma `if_relevamiento` y
    `fecha_vencimiento_mandatos` desde el `InformeTecnico` más reciente de la
    admisión.
- `admisiones/services/admisiones_service/impl.py`
  - La disponibilización a acompañamiento ahora corre dentro de una transacción.
  - Primero se importa el acompañamiento y recién después se marca la admisión
    como enviada y se actualiza su estado.
  - Si falla la actualización del estado, se aborta la operación.
- `tests/test_acompanamiento_service_helpers_unit.py`
  - Se agregó regresión para validar que `InformacionRelevante` se arma con el
    contrato real (`InformeTecnico`).
- `tests/test_admisiones_service_helpers_unit.py`
  - Se agregó regresión para validar que no se persiste estado parcial cuando
    falla la importación.

## Decisión clave

La fuente de verdad para `InformacionRelevante` es la combinación:

- datos administrativos desde `Admision`
- datos técnicos desde `InformeTecnico`

Además, la creación del acompañamiento debe completarse antes de mover la
admisión fuera de su bandeja operativa.

## Validación

- `docker compose exec -T django pytest tests/test_acompanamiento_service_helpers_unit.py -q`
- `docker compose exec -T django pytest tests/test_admisiones_service_helpers_unit.py -q`

## Riesgo / rollback

- Riesgo bajo: cambio acotado a dos services y tests unitarios.
- Rollback simple: revertir este commit en la branch del PR.
