# Expedientes de pago vinculados a la admisión

## Fecha

2026-08-21

## Problema

El expediente del convenio de cada expediente de pago se cargaba a mano, como
texto libre, sin ninguna relación con la admisión a la que corresponde. Nada le
avisaba al usuario si el número existía, si era el correcto, ni si ya había una
admisión con ese expediente.

Producto pidió vincularlos, y que los que no se puedan vincular queden en la
misma vista, señalados y filtrables.

## Diagnóstico previo (producción, 2026-08-18)

Antes de diseñar se midió sobre los datos reales:

| Métrica | Valor |
|---|---|
| Total de expedientes de pago activos | 3.266 |
| Matchean con una sola admisión del mismo comedor | 2.124 (65%) |
| Matchean con más de una (ambiguos) | 38 |
| No matchean | 1.104 (34%) |
| De esos, **no existen en admisiones** | 1.090 |
| Sin comedor asignado | 8 |
| `expediente_convenio` vacío | 0 |
| `expediente_convenio` igual a `expediente_pago` | 0 |

Dos conclusiones que cambiaron el diseño:

- **La calidad de carga es buena.** Ningún campo vacío y ningún caso del fallback
  del formulario. La hipótesis de que ese fallback estaba ensuciando el dato era
  falsa.
- **Los 38 ambiguos hacen obligatoria la asignación manual.** Ninguna
  automatización puede resolverlos: hay más de una admisión candidata en el
  mismo comedor.

## Normalización: qué se probó y qué quedó

La comparación normaliza ambos lados con `TRIM`, mayúsculas y quitando espacios,
guiones, barras y puntos.

Se probó también una normalización "GDE" —extraer año y número del expediente,
descartando los ceros a la izquierda y el sufijo de dependencia— bajo la
hipótesis de que los ceros inconsistentes estaban impidiendo matches. **Medida
contra producción, da 2.160 contra 2.162 de la normalización simple: no recupera
nada.** Se descartó. El error de análisis fue comparar una muestra de fallidos
contra las 30 admisiones más recientes, que son poblaciones distintas.

## Cambio

- `ExpedientePago` suma `admision` (FK nullable a `Admision`, `SET_NULL`). Se
  conserva `expediente_convenio` con lo que tipeó el usuario.
- `expedientespagos/vinculacion.py`: normalización, resolución y asignación.
- La resolución se acota a las admisiones **del mismo comedor**. Medido: atarlo
  al comedor cuesta 16 casos de 2.178 (0,7%) y evita vincular contra el comedor
  equivocado.
- Con cero o con más de una coincidencia queda **sin asignar**. No se adivina.
- **Selector de admisión en el formulario**, acotado a las del comedor y
  etiquetado por número de expediente. La elección manual siempre gana; la
  resolución automática solo completa el vacío. Queda opcional para no bloquear
  la carga cuando la admisión todavía no está en SISOC.
- Listado: columna **Admisión** con alerta "Sin admisión", cartel con el total
  de sueltos, y filtros combinables por expediente de pago, expediente del
  convenio, expediente de la admisión, vínculo, mes y año.

## Por qué el selector y no solo el botón de reparación

La propuesta original era alerta más botón para asignar a mano. Eso resuelve el
síntoma pero deja intacta la causa: se sigue tipeando a ciegas. El selector
ataca el alta; la asignación manual queda como red para el histórico y los casos
ambiguos.

## Arreglos incidentales

- **El paginador contaba sobre todos los expedientes del sistema.**
  `ExpedientesPagosListView.get_queryset` devolvía `ExpedientePago.objects.all()`
  y el contexto lo pisaba con los del comedor. Ahora el queryset es el del
  comedor y la tabla usa `object_list`.
- **El formulario de alta perdía los datos y los errores.**
  `get_context_data` reemplazaba `context["form"]` por un `ExpedientePagoForm()`
  nuevo, así que al fallar la validación el usuario veía el formulario vacío y
  sin errores.
- **`actualizar_expediente_pago` era código muerto.** La UpdateView guardaba con
  `super().form_valid()`. Ahora pasa por el servicio, que es lo que permite
  revincular al editar.

## Fase 3 — el histórico (2026-08-24)

La distribución por año de los que no matchean cambió el diagnóstico:

| Año | Total | Matchean | No matchean | % éxito |
|---|---|---|---|---|
| 2024 | 13 | 6 | 7 | 46% |
| 2025 | 1.311 | 1.281 | 30 | **97,7%** |
| 2026 | 1.940 | 875 | 1.065 | **45,1%** |
| (basura) | 2 | 0 | 2 | — |

**No es deuda histórica: el 96% del problema (1.065 de 1.104) es de 2026.** En
2025 el circuito funcionaba casi perfecto, lo que confirma que la normalización,
el matcheo por comedor y el modelo de datos son correctos. Algo cambió en 2026.

La hipótesis más probable es de **tiempos**: el expediente de pago se carga antes
de que la admisión exista en SISOC. La alternativa es un cambio en la oficina que
genera el expediente (en las muestras, las admisiones recientes traen sufijo
`APN-CGDNAYF` y los pagos `APN-DDNAYF`). No se puede distinguir desde los datos
disponibles.

El diseño se resolvió para que funcione bajo cualquiera de las dos:

- **`post_save` en `Admision`** que reintenta vincular los expedientes sueltos de
  ese comedor. Si el problema es de tiempos, cada admisión que se carga engancha
  sola sus pagos huérfanos. Sin esto, una migración de una sola pasada los
  dejaría en `null` para siempre. Un fallo del reintento no impide guardar la
  admisión.
- **Comando `revincular_expedientes_pago`** (`--dry-run`, `--comedor N`) para el
  re-matcheo masivo.
- **Migración `0004`**, que es la primera corrida de esa misma lógica sobre el
  histórico.

Los tres comparten la regla: solo tocan los que están sin asignar, nunca pisan un
vínculo existente, y con cero o más de una coincidencia dejan sin asignar.

La migración lleva su propia copia de la normalización, como corresponde a una
data migration, y hay un test que verifica que no diverja de la del código vivo.
Al correr con `TEST MIGRATE=False` la migración no se ejecuta en tests, así que se
prueba su función directamente.

## La vinculación vive en el modelo, no en el servicio (2026-08-26)

Producto aclaró algo que cambia el diseño: **los expedientes de pago se cargan
por CSV**, de a uno o de a muchos, y esa es la vía habitual. El formulario es la
excepción, no la regla.

La importación (`importarexpediente`) instancia el modelo y guarda directo
(`ExpedientePago(**kwargs)` + `save()` en `importarexpediente/views.py`), sin
pasar por `ExpedientesPagosService`. Se verificó reproduciendo esa vía: el
expediente quedaba **sin vincular** aunque existiera la admisión que coincidía.

La resolución se movió al `save()` del modelo. Es el único punto por el que pasan
todas las puertas de entrada —formulario, importación por CSV, consola y lo que
venga después—, así que la vinculación corre siempre sin tener que acordarse de
llamarla en cada lugar. `asignar_admision` quedó sin uso y se eliminó.

Sigue sin pisar una admisión ya asignada: dejar el campo vacío es justamente lo
que significa "resolver automáticamente", y por eso vaciarlo en la edición pide
que se resuelva de nuevo.

Esto también corrige el peso relativo de una decisión anterior: el selector en el
alta se justificó como forma de "atacar el error humano de raíz", pero si la
carga real es por CSV, ese formulario casi no se usa. El selector sigue siendo
útil para corregir y para los casos ambiguos, que es donde de verdad hace falta.

## Etiquetas distinguibles en el selector

Dos admisiones del mismo comedor pueden compartir número de expediente —es
exactamente el caso ambiguo que el selector existe para resolver— y la etiqueta
mostraba solo ese número, así que aparecían **dos opciones idénticas** y no había
forma de elegir. Ahora la etiqueta suma el identificador de la admisión, el
convenio si lo tiene y el estado.

## Pendiente

**Pregunta de producto, no técnica:** en 2026 más de la mitad de los expedientes
de pago apunta a convenios que SISOC no tiene, cuando en 2025 pasaba en el 2% de
los casos. Hay que entender qué cambió. Si son 1.065 admisiones que alguien tiene
que cargar, es un proyecto en sí mismo.

Queda también decidir qué hacer con los 8 expedientes sin comedor y con los 2
registros basura (`#MCH#CONVENIO`).

## Validación

- `tests/test_expedientespagos_vinculacion_db.py` (nuevo, 20 tests): normalización
  con los formatos reales de producción, resolución acotada al comedor, rechazo
  de ambiguos, alta y edición, revinculación al cargar la admisión después,
  anotación y filtros del listado, y los dos arreglos incidentales.
- Migración `0003_expedientepago_admision`: aditiva, un campo nullable, sin
  backfill.
