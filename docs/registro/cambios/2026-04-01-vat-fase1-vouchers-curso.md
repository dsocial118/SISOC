# VAT - Fase 1 vouchers en Curso

Fecha: 2026-04-01

## Objetivo
Alinear el dominio de Curso con la politica de vouchers ya existente en Oferta Institucional, sin modificar aun la logica de consumo unificada ni reversas.

## Cambios implementados
1. Modelo `Curso`:
- Se agrega `programa` (FK a `core.Programa`, nullable para compatibilidad de datos existentes).
- Se agrega `usa_voucher` (bool).
- Se agrega `voucher_parametrias` (M2M con `VAT.VoucherParametria`).
- Se agrega `costo_creditos` (entero positivo, default 1).
- Validaciones de modelo:
  - Si `usa_voucher` esta activo, `programa` es obligatorio.
  - `costo_creditos` debe ser mayor a 0.

2. Formulario `CursoForm`:
- Se incorporan los campos de politica de vouchers (`programa`, `usa_voucher`, `voucher_parametrias`, `costo_creditos`).
- Validaciones de formulario:
  - Si `usa_voucher`, debe haber `programa`.
  - Si `usa_voucher`, debe haber al menos una `voucher_parametria`.
  - Todas las `voucher_parametrias` deben pertenecer al `programa` seleccionado.

3. API de cursos:
- `CursoSerializer` expone `programa`, `programa_nombre`, `usa_voucher`, `voucher_parametrias`, `costo_creditos`.
- `CursoViewSet` agrega filtro por `programa_id` y optimiza queryset con `programa` y `voucher_parametrias`.

4. UI en detalle de centro:
- Tabla de cursos muestra columna `Programa`.
- Se muestra badge de `Voucher` cuando el curso tiene `usa_voucher` activo.
- Se inicializa comportamiento de selector de vouchers en el modal de Curso (reutilizando la logica de Oferta).
- En `Nuevo Curso`, el bloque de `Vouchers` ahora se renderiza con el mismo patron visual y funcional que `Nueva Oferta Materia` (switch, selector multiple y filtrado por programa en tiempo real).
- La seleccion o hover sobre una fila de `Cursos` ahora filtra en el momento la tabla `Comisiones de Curso` del mismo centro, sin filtros manuales adicionales.
- La tabla `Comisiones de Curso` agrega un boton explicito de `Gestionar Comisión` en acciones, ahora con vista de detalle propia (`vat/cursos/comisiones/<id>/`) para replicar la navegacion de gestion del catalogo sin mezclar modelos.

5. Migracion:
- `VAT/migrations/0026_curso_costo_creditos_curso_programa_and_more.py`

6. Gestion operativa de `ComisionCurso`:
- `ComisionCurso` pasa a reutilizar la misma pantalla de gestion visual que `Comision`.
- Se habilita alta de horarios, generacion de sesiones y toma de asistencia para comisiones de curso.
- Se habilita inscripcion rapida y cambio de estado de inscripciones para comisiones de curso.
- Se agregan relaciones opcionales sobre `ComisionHorario`, `SesionComision` e `Inscripcion` para soportar tanto `Comision` como `ComisionCurso`.
- Se agrega `VAT/migrations/0028_comisionhorario_comision_curso_and_more.py`.

7. Plan de Estudio por usuario provincial:
- `PlanVersionCurricular` incorpora `provincia` (FK nullable a `core.Provincia`).
- Al crear un Plan de Estudio desde `PlanVersionCurricularCreateView`, si el usuario autenticado es provincial, se asigna automaticamente su provincia en el plan creado.
- Las vistas web de planes curriculares (`list/create/detail/update/delete`) quedan restringidas a usuario provincial VAT y scopeadas por provincia del perfil.
- Se agrega regresion `test_plan_estudio_create_usuario_provincial_asigna_provincia`.
- Se agrega regresion `test_plan_curricular_list_usuario_no_provincial_recibe_403`.
- Se agrega `VAT/migrations/0029_planversioncurricular_provincia.py`.

## Validacion ejecutada
- `black` sobre archivos Python modificados.
- `pylint` sobre archivos VAT modificados: 10.00/10.
- `pytest VAT/tests.py -k "curso and voucher" -q`: 2 tests en verde.
- `pytest VAT/tests.py -k "comision_curso_detail_muestra_gestion_equivalente or comision_curso_horario_create_genera_sesiones or inscripcion_rapida_comision_curso_crea_inscripcion" -q`: 3 tests en verde.

## Supuestos
1. En Fase 1 no se modifica aun la logica de consumo de voucher en inscripcion de Curso/ComisionCurso.
2. El campo `programa` en Curso queda nullable por compatibilidad retroactiva; se podra endurecer en una fase posterior cuando se complete la migracion funcional.

## Siguientes pasos sugeridos (Fase 2+)
1. Unificar consumo de voucher en un solo servicio para Carrera y Curso.
2. Implementar reversa auditable de consumo en anulaciones.
3. Endurecer API para que no existan entrypoints con validaciones divergentes.
