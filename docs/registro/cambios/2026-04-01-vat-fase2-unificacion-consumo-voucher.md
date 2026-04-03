# VAT - Fase 2: Unificacion de consumo de vouchers

Fecha: 2026-04-01
Area: VAT / Inscripciones

## Objetivo
Unificar la logica de consumo de vouchers para inscripciones web y API en una sola capa de servicio, eliminando duplicacion y comportamiento inconsistente.

## Cambios implementados

1. Servicio unificado en `VAT/services/inscripcion_service.py`
- Se agrego seleccion robusta de vouchers candidatos por ciudadano + programa + parametria habilitada.
- Se centralizo el debito en `_debitar_voucher_para_oferta(...)`.
- Se corrigio el escenario de multiples vouchers activos: ahora intenta candidatos por orden de vencimiento en lugar de cortar con el primero.
- `crear_inscripcion(...)` pasa a usar la logica centralizada de debito.
- Se agrego `crear_inscripcion_oferta(...)` para cubrir el flujo `InscripcionOferta` con la misma regla de consumo.

2. Vista web de InscripcionOferta
- `VAT/views/oferta.py` ahora crea inscripciones via `InscripcionService.crear_inscripcion_oferta(...)`.
- Se elimino el debito fijo de 1 credito y la logica duplicada en la vista.
- Se mantienen mensajes de exito/error usando el resultado del servicio.

3. API de InscripcionOferta
- `VAT/api_views.py` (`InscripcionOfertaViewSet`) incorpora `perform_create(...)` y delega en `InscripcionService.crear_inscripcion_oferta(...)`.
- API y web quedan alineadas en reglas de consumo.

4. Ajustes de integracion
- `VAT/views/persona.py` y `VAT/views/oferta.py` leen atributos transitorios de debito/saldo sin usar miembros protegidos.

## Validacion ejecutada

- `black` sobre archivos tocados.
- `pylint` sobre archivos tocados (10.00/10).
- `pytest VAT/tests.py -q` -> 16 passed.

## Alcance de la fase

- Incluido: unificacion de consumo y seleccion de voucher para flujos de inscripcion existentes (web/API).
- No incluido: reversa/auditoria de anulacion y modelado completo de vouchers para inscripciones de cursos operativos.
