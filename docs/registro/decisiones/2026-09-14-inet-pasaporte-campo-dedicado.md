# 2026-09-14 - Pasaporte en campo propio en lugar de cambiar el tipo de `Ciudadano.documento`

## Contexto

El REQ #2455 pide que la carga manual de inscriptos de INET/VAT permita elegir
entre DNI y Pasaporte. El pasaporte es **alfanumérico** (6 a 15 caracteres),
pero `Ciudadano.documento` es un `PositiveBigIntegerField`.

Ese campo es transversal a todo SISOC: más de 60 archivos fuera de VAT y
ciudadanos lo tratan como entero (`int(documento)`, `documento__in=[...]`,
`order_by("documento")`, `documento_prefix_filter`), en comedores, celiaquia,
centrodefamilia, pwa, encuestas y rendicioncuentasfinal, entre otros.

El alcance declarado del ticket es el módulo de legajo INET/VAT, y excluye
explícitamente la carga masiva y el catálogo de países.

## Decisión

Se agregan dos columnas nuevas a `Ciudadano`
(`ciudadanos/migrations/0032_ciudadano_documento_pasaporte_ciudadano_pais_emisor.py`):

- `documento_pasaporte` (`CharField(max_length=15, null=True, blank=True)`),
  usado **solo** cuando `tipo_documento == DOCUMENTO_PASAPORTE`;
- `pais_emisor` (`CharField(max_length=100, null=True, blank=True)`), sin
  catálogo y sin exposición en formularios en esta versión.

`documento` no cambia de tipo y conserva su semántica numérica. La alternativa
—convertirlo en `CharField`— obligaba a auditar y migrar esos +60 archivos de
módulos ajenos al ticket, con riesgo alto y sin pedido funcional que lo
respalde.

La lectura del número vigente se centraliza en la property
`Ciudadano.numero_documento`, que devuelve `documento_pasaporte` o `documento`
según el tipo. Para las filas de `.values()` del reporte —donde no hay
instancia del modelo— el equivalente es
`detalle_row_numero_documento()` en
`VAT/services/reportes_inscripciones_asistencia.py`.

### Unicidad

No se agregó un índice nuevo. La clave funcional `tipo_documento + número` ya
estaba resuelta por `documento_unico_key` (`unique=True`, ver
[2026-04-10-identidad-ciudadano](2026-04-10-identidad-ciudadano.md)); solo se
extendió `build_documento_unico_key()` para que tome el número del campo que
corresponda.

Dos detalles no obvios que condicionan el código:

1. **Compatibilidad hacia atrás.** `numero_documento` cae a `documento` cuando
   `documento_pasaporte` está vacío. Sin ese fallback, todo registro
   preexistente con `tipo_documento=PASAPORTE` y número en `documento` habría
   perdido su `documento_unico_key` (pasándola a `NULL`) en su siguiente
   guardado, degradando silenciosamente la unicidad de esos legajos.
2. **Borrados lógicos.** La constraint `unique` de la base alcanza también a
   las filas con baja lógica, que `Ciudadano.objects` oculta. La validación de
   duplicados del formulario consulta `Ciudadano.all_objects`; con el manager
   por defecto el alta terminaría en `IntegrityError` (500) en lugar de un
   error de formulario.

### Inmutabilidad del tipo de documento

El REQ exige que el tipo no se pueda modificar desde la aplicación, también a
nivel de servicio. Se implementó en `Ciudadano.save()`, que cubre todas las
rutas (formularios, servicios y API), usando el hook `from_db()` de Django para
recordar el valor persistido. Se descartó consultar la base dentro de `save()`:
agregaba una query por guardado sobre un modelo que se escribe en lotes durante
la importación masiva, y además no veía los registros con baja lógica.

Las correcciones de tipo de documento se siguen haciendo por intervención
directa en base, a cargo del área técnica, como define el ticket.

## Consecuencias

- Los módulos fuera de VAT/ciudadanos no requieren cambios y siguen operando
  sobre `documento` como entero.
- Un inscripto con pasaporte queda con `documento = NULL`, por lo que no
  aparece en las búsquedas por documento numérico de otros módulos. Es
  consistente con el estado previo, donde directamente no podía registrarse.
- El buscador por documento de VAT sigue siendo numérico, según el punto 8 del
  REQ ("la búsqueda por número de documento sigue funcionando sin indicar el
  tipo").
- Si a futuro se decide unificar la identidad en un único campo alfanumérico,
  esta decisión no lo bloquea: `documento_pasaporte` se migraría al campo
  unificado junto con el resto.

## Validación

- `pytest VAT/test_inscripcion_rapida_documento.py -v` cubre formatos por tipo,
  normalización, unicidad (incluidos legajos con baja lógica), inmutabilidad del
  tipo y conservación de la clave única en pasaportes históricos.
- `pytest VAT/ tests/ -n auto` sin regresiones.
