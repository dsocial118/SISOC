# 2026-09-14 - INET/VAT: baja de visualización de Modalidad y tipo de documento en carga manual

Implementa los REQ #2457 y #2455 sobre el módulo de legajo INET/VAT.

## REQ #2457 - Modalidad, Sector y Subsector fuera de la vista

El campo Modalidad quedó obsoleto y confundía a los usuarios. Se dejó de
mostrar en las vistas donde era **solo informativo**:

- selector de Plan Curricular del legajo del Centro
  (`centro_cursos_panel.html`): se quitaron las columnas Sector y Modalidad y
  el filtro de Sector; el buscador por texto pasó a "plan o normativa";
- detalle de Curso y detalle de Comisión de Curso;
- nota del wizard de comisión;
- filtro Modalidad del Reporte de Inscripciones y Asistencia.

**La base de datos no se toca.** `Curso.modalidad`,
`PlanVersionCurricular.sector/subsector/modalidad_cursada` y los datos
históricos quedan intactos, según lo acordado ("solo dejar de mostrarlo").

### Límite de alcance

Se mantuvieron sin cambios los **catálogos de gestión** (Sector, Subsector,
Modalidad de Cursado y Plan Curricular, con sus formularios y listados). Ahí
esos campos son atributos obligatorios de definición del plan, no un dato de
visualización: quitarlos impediría dar de alta un plan curricular.

Como el filtro dejó de renderizarse, se eliminó también la agregación
`modalidades` de `_build_filter_options()`, que calculaba un `DISTINCT` sobre
el scope de inscripciones para alimentar un desplegable ya inexistente. El
parámetro `modalidad_id` del backend se conservó, de modo que las URLs
guardadas siguen resolviendo.

## REQ #2455 - Tipo de documento en la carga manual de inscriptos

El alta rápida de ciudadano desde una comisión asumía DNI de forma implícita
(campo oculto), lo que dejaba afuera a los inscriptos extranjeros.

- `CiudadanoInscripcionRapidaForm` expone ahora un selector **DNI / Pasaporte**
  (los únicos dos valores habilitados por el REQ, aunque el modelo admita más).
- Validación por tipo: DNI de 7 u 8 dígitos sin separadores; pasaporte
  alfanumérico de 6 a 15 caracteres, normalizado a mayúsculas sin espacios.
- Ante un duplicado, el error de formulario indica el legajo en conflicto en
  lugar de fallar con un error 500.
- El tipo de documento pasa a ser de solo lectura una vez creado el legajo,
  tanto en el formulario general de ciudadano como a nivel de modelo.
- El tipo se muestra junto al número en el detalle del ciudadano, las grillas
  de comisión, la nómina Excel y el detalle nominal del reporte. El país emisor
  se muestra solo si tiene valor.

Fuera de alcance, sin cambios: carga masiva, catálogo de países, y el alta
pública de postulantes (que ya rechaza documentos no numéricos antes de
persistirlos).

El almacenamiento del número de pasaporte y la inmutabilidad del tipo se
detallan en
[2026-09-14-inet-pasaporte-campo-dedicado](../decisiones/2026-09-14-inet-pasaporte-campo-dedicado.md).

## Migración

`ciudadanos/migrations/0032_ciudadano_documento_pasaporte_ciudadano_pais_emisor.py`
agrega dos columnas nullable. Es aditiva: no modifica ni borra datos
existentes.

## Validación

- `pytest VAT/test_inscripcion_rapida_documento.py -v` (nuevo, 15 casos).
- `pytest VAT/ tests/ ciudadanos/ celiaquia/ centrodefamilia/ comedores/ pwa/ encuestas/ -n auto`
  sin regresiones.
- Se actualizó
  `test_centro_cursos_panel_renderiza_selector_de_planes_en_modal_nuevo_curso`,
  que afirmaba la presencia del filtro de Sector que este cambio elimina.
