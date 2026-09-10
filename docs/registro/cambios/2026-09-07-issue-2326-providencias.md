# Reemplazo de Disposición por Providencias en Admisiones - Legales

Fecha: 2026-09-07

Issue: 2326. Rama: `providencias_tk2326`.

## Alcance

Se elimina del proceso de Legales el **Proyecto de Disposición** y la
**Disposición**, tanto antes como después de la intervención de Jurídicos, y se
los reemplaza por **Primera Providencia** y **Segunda Providencia**.

No se modifica el proceso de Jurídicos ni la generación del Proyecto de Convenio
o del Convenio. El botón de Convenio sólo deja de exigir que exista una
Disposición cargada.

## Circuito resultante

```
IF Convenio Asignado
  -> Generar Primera Providencia      -> Formulario Primera Providencia Creado
  -> Cargar número de GDE PV          -> IF Primera Providencia Asignado
  -> Generar Segunda Providencia      -> Formulario Segunda Providencia Creado
  -> Cargar número de GDE Segunda PV  -> IF Segunda Providencia Asignado
  -> Intervención Jurídicos
  -> Convenio                         -> Acompañamiento Pendiente
```

Los cuatro estados nuevos se suman a `Admision.ESTADOS_LEGALES`. Los estados del
circuito viejo (`Formulario Disposición Creado`, `IF Disposición Asignado`,
`Disposición Firmada`) **se conservan en los choices**: hay admisiones en
producción que los tienen guardados y quitarlos rompería su display y el filtro
del listado.

### Por qué son cuatro estados y no seis

El punto 3 del ticket lista, por providencia, tres nombres: `Formulario ...
Creado`, `IF ... Asignado` y `... Cargada`. La sección funcional (1.3.1 a
1.3.10) describe en cambio **dos acciones por providencia**: generar el
documento y cargar el número de GDE PV. No existe una tercera acción que pueda
producir un tercer estado.

El origen de la diferencia es el mapeo del punto 3, que renombra uno a uno los
estados del circuito viejo. Ahí, `Primera Providencia Cargada` sale de
`Disposición firmada`, que era un estado **posterior a Jurídicos**. Ese tramo se
elimina por completo en este cambio (ver "Alcance"), así que los dos estados
`... Cargada` quedan sin ningún paso que representar.

Por eso se persisten los dos estados que corresponden a acciones reales:
`Formulario ... Creado` al generar el documento e `IF ... Asignado` al cargar el
número de GDE PV. Agregar los `... Cargada` implicaría declarar estados que
ningún paso del proceso puede alcanzar, y que aparecerían en el filtro del
listado sin devolver nunca resultados.

**Pendiente de confirmación funcional.** Si el área define que debe existir un
tercer paso por providencia, hay que especificar qué acción lo produce.

## Modelo

`Providencia` es un único modelo con campo `orden` (`primera` / `segunda`) y
`UniqueConstraint` sobre `(admision, orden)`. `tipo` y `es_judicializado` se
guardan como snapshot al generar, para que un documento ya emitido no se
contradiga si después se edita el legajo del comedor.

## Documentos

Siete templates `.docx` derivados de los originales de Legales
(`{tipo}_docx_primera_providencia_{base|cinco_comedores|judicializados}.docx` y
`segunda_providencia.docx`) y dos HTML espejo para el PDF
(`pdf/primera_providencia.html`, `pdf/segunda_providencia.html`).

Los seis documentos de Primera Providencia son el mismo texto y difieren en dos
párrafos condicionales e independientes: el de continuidad del financiamiento
(sólo renovación) y el de excepción al tope de la Resolución 151/2025, que tiene
dos formas mutuamente excluyentes según sea por antigüedad en el Programa o por
causa judicial.

Del lado del DOCX se mantienen los seis archivos porque son artefactos externos
que Legales edita en Word; del lado del PDF va un único HTML con los
condicionales, porque es código propio y seis copias del mismo texto se
desincronizan. La elección de variante vive **sólo en el service**, en
`_variante_providencia()`.

Los datos de los documentos salen del `InformeTecnico`, no del legajo del
comedor, igual que hacía el documento de Disposición: es la foto de lo que se
evaluó y aprobó.

## Validación del número de GDE PV

Formato `PV-<año>-<número>-APN-<repartición>#<organismo>`, por ejemplo
`PV-2025-103008562-APN-DPS#MCH`. Se carga en cuatro campos separados
(`NumeroPVMixin`), igual que el número de expediente, para que el usuario no
tipee los separadores y no pueda introducir espacios de más.

Dos diferencias respecto del expediente, indicadas por el área funcional:
el número admite de 1 a 9 dígitos en vez de exactamente 9, y **no se completa
con ceros a la izquierda** — se guarda tal como lo cargó el usuario.

`NumeroPVMixin` es independiente de `NumeroExpedienteMixin` a propósito:
generalizar este último implicaba tocar la caratulación de expedientes, que es
crítica y ajena a este cambio.

Repartición y organismo aceptan hasta 50 caracteres cada uno, así que el número
compilado puede alcanzar 123 caracteres. `numero_gde_pv` y `numero_pv_primera`
se amplían a 255 en la migración `0081` para que no haya truncamiento ni error
de persistencia en MySQL estricto. Hay un test de borde que compara el largo
máximo compilado contra el `max_length` real de ambos campos.

## Decisiones no explicitadas en el ticket

- **Precondición de Jurídicos.** `validar_juridicos()` exigía la existencia del
  `FormularioProyectoDisposicion` para pasar a `Pendiente de Validacion`. Como
  ese formulario deja de generarse, la condición se repunta a "Segunda
  Providencia con número de GDE PV cargado". Sin este cambio ninguna admisión
  podría volver a pasar a Jurídicos.
- **Cierre del circuito.** Antes, el último de los dos pasos (Disposición o
  Convenio) dejaba la admisión en `Acompañamiento Pendiente`. Eliminada la
  Disposición, el Convenio queda como último paso y asume ese rol.
- **Habilitación de Acompañamiento.** El botón "Comenzar Acompañamiento"
  dependía de `numero_disposicion`; pasa a depender de `numero_convenio`.
- **Judicializado con más de 5 espacios.** Casuística no contemplada por
  Legales. Se implementa con precedencia de judicializado, porque el párrafo de
  la causa judicial ya justifica por sí solo la excepción, y se deja un
  `logger.warning` para detectar el caso si aparece en producción.
- **Motivo de dictamen.** La etiqueta pasa a "Observación en providencia"; el
  valor almacenado sigue siendo `observacion en proyecto de disposicion` para no
  romper los rechazos históricos.
- **Validación de secuencia en servidor.** Las cuatro acciones de providencia
  verifican contra `get_botones_disponibles()` que la acción corresponda al
  estado actual antes de tocar datos. Sin esto, un POST directo con sesión
  válida podía reemitir una providencia o pisar un número de GDE ya asignado
  después de avanzar a Jurídicos, dejando documento, identificador externo y
  estado en contradicción. Se usa la misma función que gobierna la UI para no
  duplicar la definición de la secuencia.

## Datos que se conservan

Se elimina el paso, no el dato. Se mantienen el campo
`Admision.numero_disposicion`, el modelo `FormularioProyectoDisposicion` con su
tabla y su registro en el admin, y todas las pantallas que muestran esos valores
cuando existen.

El motivo es concreto: al 2026-09-07 hay en producción **1.704 admisiones con
número de disposición cargado, de 929 comedores distintos**, y ese número lo cita
el informe técnico cada vez que uno de esos comedores renueva
(`informe_tecnico_variables_service.py`, `admisiones_forms.py`). Borrar la
columna rompería la renovación de esos 929 comedores.

## Compatibilidad y despliegue

Al momento del análisis había en producción 5 admisiones en `IF Disposición
Asignado` y 2 en `Disposición Firmada`, todas activas y con menos de 66 días.
El área funcional definió **no migrarlas**: se les da un plazo para cerrarlas por
el circuito viejo y recién después se despliega.

Como red de seguridad, el estado `IF Disposición Asignado` sigue habilitando el
botón de Jurídicos y `Disposición Firmada` sigue habilitando el de Convenio, para
que ningún expediente rezagado quede sin acciones disponibles si el plazo no
alcanza.

## Pendiente

En Acompañamiento, el campo "Número de Resolución" se llena hoy con
`numero_disposicion` (`acompanamientos/acompanamiento_service.py`). En las
admisiones nuevas va a quedar vacío. Falta definición del área funcional sobre
qué mostrar en su lugar.

## Fuentes actualizadas

- `admisiones/models/admisiones.py`, `admisiones/migrations/0080_issue_2326_providencias.py`,
  `admisiones/migrations/0081_issue_2326_ampliar_numero_pv.py` (esta última además
  unifica el grafo de migraciones, que había quedado con dos hojas tras el merge
  de `development`)
- `admisiones/services/legales_service/impl.py`
- `admisiones/services/admisiones_service/impl.py`, `admisiones/services/docx_service/impl.py`
- `admisiones/forms/admisiones_forms.py`
- `admisiones/templatetags/admisiones_tags.py`, `admisiones/templatetags/estado_filters.py`
- `admisiones/templates/admisiones/` (modales de Legales, partial de número de PV, templates DOCX y PDF)
