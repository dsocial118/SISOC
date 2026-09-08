# Alcance de nómina PWA por admisión vigente

## Fecha

2026-08-13

## Problema

La nómina PWA consolidaba registros activos de todas las admisiones de un
comedor. La marca `vigente_pwa` no limitaba el listado, por lo que personas que
solo pertenecían a admisiones anteriores continuaban visibles.

## Cambio

- Los programas que organizan su nómina por admisión usan exclusivamente la
  admisión resuelta por `ComedorService.get_admision_vigente_pwa`.
- Los programas con nómina directa conservan los registros asociados al comedor
  con `admision_id` nulo.
- El mismo alcance se aplica al listado PWA, cupos y validaciones, asistencia y
  generación del PDF mensual de destinatarios.

## Compatibilidad

Si no existe una marca `vigente_pwa`, se conserva el fallback existente del
servicio: la admisión activa de mayor ID y, en última instancia, la admisión de
mayor ID.

## Validación

- Se agregó una regresión con dos admisiones activas que verifica que el endpoint
  exponga solamente la nómina de la admisión marcada como vigente.
- `pwa/tests.py` y `tests/test_pwa_nomina_api.py`: 18 tests aprobados.
