# Diseño: FormularioCDI en Centro de Infancia

## Resumen
- Se incorpora `FormularioCDI` dentro de `centrodeinfancia`.
- Cada instancia queda vinculada a un único `CentroDeInfancia`.
- El detalle del CDI expone una card `Formularios` con las últimas 3 instancias y accesos a listado/alta.

## Decisiones principales
- Persistencia tipada en ORM para campos escalares.
- Multi-selects en `JSONField` con códigos estables.
- Tablas repetibles como modelos hijos:
  - `FormularioCDIRoomDistribution`
  - `FormularioCDIWaitlistByAgeGroup`
  - `FormularioCDIArticulationFrequency`
- Geografía fase 1:
  - `Provincia`, `Municipio`, `Localidad` reutilizan catálogos actuales.
  - `department` queda como texto.
- `cdi_code` se agrega a `CentroDeInfancia` como identificador estable y se snapshottea en cada formulario.

## UX web
- Nuevas pantallas:
  - listado de formularios por CDI
  - alta de formulario
  - detalle de instancia
  - edición de instancia
- El alta y edición usan una sola pantalla con secciones y tres grillas fijas.

## Validaciones
- Campos `*_other` son obligatorios cuando la opción principal seleccionada lo requiere.
- `meals_provided` no admite `ninguna` junto con otras opciones.
- `opening_time` debe ser menor que `closing_time`.
- Los campos ocultos por skip logic pueden persistirse como `null`.

## Testing esperado
- Validaciones de form.
- Scope por provincia en vistas nuevas.
- Card del detalle del CDI limitada a 3 formularios.
