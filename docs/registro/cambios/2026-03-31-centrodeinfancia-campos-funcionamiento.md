# CentroDeInfancia: campos de ubicación, gestión y funcionamiento

## Qué cambió

- Se amplió `CentroDeInfancia` con:
  - `codigo_postal`
  - `ambito`
  - `latitud` y `longitud`
  - `mail`
  - `meses_funcionamiento`
  - `dias_funcionamiento`
  - `tipo_jornada` y `tipo_jornada_otra`
  - `oferta_servicios`
  - `modalidad_gestion` y `modalidad_gestion_otra`
  - `cuit_organizacion_gestiona`
- `organizacion` dejó de ser FK y pasó a texto libre bajo la etiqueta "Denominación del organismo u organización que gestiona".
- `telefono_referente` dejó de ser obligatorio.

## Decisión de diseño

- Los horarios de funcionamiento por día no se guardan en un `JSONField`.
- Se modelaron como tablas hijas:
  - `CentroDeInfanciaHorarioFuncionamiento`
  - `FormularioCDIHorarioFuncionamiento`
- Esto permite validar un horario por día, mantener unicidad por día y simplificar la edición incremental desde formulario.

## Consistencia con FormularioCDI

- Se alinearon opciones y labels compartidos entre `CentroDeInfancia` y `FormularioCDI`.
- Los meses pasaron a nombres completos (`enero`, `febrero`, etc.) en lugar de abreviaturas legacy.
- Los días de funcionamiento usan claves homogéneas en minúscula (`lunes`, `martes`, etc.).
- El CUIT se normaliza a 11 dígitos en backend y la máscara `##-########-#` queda sólo en UI.

## Migración de datos

- La migración preserva el nombre de la organización previa tomando el `nombre` de la FK legacy.
- Normaliza meses, días, CUIT y modalidad de gestión en formularios existentes.
- Migra el horario legacy único de `FormularioCDI` hacia registros por día para cada día seleccionado.

## Impacto de UI

- El formulario de `CentroDeInfancia` agrega la sección "Funcionamiento".
- El formulario de `FormularioCDI` autocompleta desde `CentroDeInfancia` los campos homólogos y deja los valores editables.
- Los horarios por día muestran sólo los días seleccionados y copian por defecto el primer horario cargado a los demás días aún no editados.
