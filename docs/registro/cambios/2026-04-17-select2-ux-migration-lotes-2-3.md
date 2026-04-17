# 2026-04-17 - Migración Select2 lotes 2 y 3

## Objetivo

Extender la migración Select2 después del lote inicial, enfocando:

- filtros y selectores client-side de alto uso,
- modales con selects dependientes,
- formularios VAT con relaciones medianas donde la búsqueda reduce fricción.

## Decisión aplicada

- Se priorizaron flujos donde el usuario busca entre opciones numerosas o dependientes.
- Se evitó aplicar Select2 a enums chicos (`estado`, `tipo`, `page size`, etc.) para no sumar peso visual sin beneficio.
- Cuando un select se repuebla dinámicamente, el cambio incluye refresco explícito de Select2 y sincronización de UI.

## Cambios implementados

### Lote 2 - Filtros y modales

- `VAT/templates/vat/centros/partials/centro_cursos_panel.html`
  - `comisionesFilterCurso` usa Select2.
  - `planCurricularSelectorSector` usa Select2 dentro del modal de selector de planes.
- `VAT/templates/vat/centros/centro_detail.html`
  - Se inicializa Select2 en esos filtros.
  - Se refresca Select2 al repoblar sectores y subsectores dinámicos.
  - Se sincroniza el valor visual de Select2 cuando el filtro de curso se actualiza por click en filas o por carga de datos en modal.
- `celiaquia/templates/celiaquia/expediente_form.html`
  - Los filtros `provincia`, `municipio` y `localidad` del modal de localidades usan Select2 con `dropdownParent`.
- `static/custom/js/localidades_modal.js`
  - Refresco de Select2 al repoblar opciones.
  - El filtro por `localidad` ahora impacta la tabla.
  - Se preservan selecciones válidas al recargar datos.
- `celiaquia/templates/celiaquia/expediente_detail.html`
  - `editar-nacionalidad` usa Select2 dentro del modal de editar legajo.
- `static/custom/js/expediente_detail.js`
  - Se refresca Select2 al cargar el valor de nacionalidad en edición.

### Lote 3 - Formularios VAT con relaciones medianas

- `VAT/forms.py`
  - `SubsectorForm.sector`
  - `TituloReferenciaForm.plan_estudio`
  - `PlanVersionCurricularForm.sector`
  - `PlanVersionCurricularForm.subsector`
  - `PlanVersionCurricularForm.modalidad_cursada`
  - `ComisionHorarioForm.comision`
  - `ComisionCursoHorarioForm.comision_curso`
  - `EvaluacionForm.comision`
  - `ResultadoEvaluacionForm.evaluacion`
  - `ResultadoEvaluacionForm.inscripcion`

## Soporte de testing

- Se ampliaron tests unitarios de widgets en `tests/test_vat_forms_unit.py`.
- Se reforzaron asserts de render en `VAT/tests.py` para verificar que los filtros nuevos del panel salen con atributos Select2.

## Exclusiones explícitas

- No se migraron enums chicos del panel VAT (`estado`, `ver`, etc.).
- No se tocó `sexo` en el modal de editar legajo de Celiaquía porque no tiene suficiente cardinalidad para justificar Select2.
- No se amplió el alcance a grillas con selects por fila ni a formularios de bajo volumen fuera de VAT/Celiaquía.
