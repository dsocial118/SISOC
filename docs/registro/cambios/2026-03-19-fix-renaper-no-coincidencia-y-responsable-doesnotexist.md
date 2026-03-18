# 2026-03-19 - Ajustes de logging RENAPER y Responsable en Centro de Familia

## Qué se corrigió
- En la integración RENAPER de Centro de Familia, el caso funcional de "no se encontró coincidencia" dejó de escribirse como error en logs.
- En `buscar_responsable_renaper`, el caso `Responsable.DoesNotExist` dejó de loguearse como excepción; ahora se trata como flujo esperado y continúa con consulta RENAPER.

## Motivo
- Ambos casos son esperables del negocio (no siempre existe coincidencia o responsable previo) y no deben generar ruido de error/traceback en observabilidad.

## Validación
- Tests de regresión y cobertura de flujo:
  - `tests/test_beneficiarios_service_unit.py`
  - `tests/test_consulta_renaper_unit.py`
- Resultado local: `29 passed`.
