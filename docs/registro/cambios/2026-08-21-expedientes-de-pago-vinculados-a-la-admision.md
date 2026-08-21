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

## Pendiente

**Fase 3 — el histórico.** Los 1.090 que no existen en admisiones no los puede
resolver ni la automatización ni el botón manual: no hay a qué asignarlos. Antes
de escribir la data migration hace falta la distribución por año de esos casos
(consulta enviada, sin respuesta). Si son de 2024/2025 es deuda histórica; si hay
muchos de 2026 hay un agujero de proceso vigente. Eso define si el vínculo es
opcional o si hay que cargar las admisiones faltantes.

También queda pendiente decidir qué hacer con los 8 expedientes sin comedor.

## Validación

- `tests/test_expedientespagos_vinculacion_db.py` (nuevo, 20 tests): normalización
  con los formatos reales de producción, resolución acotada al comedor, rechazo
  de ambiguos, alta y edición, revinculación al cargar la admisión después,
  anotación y filtros del listado, y los dos arreglos incidentales.
- Migración `0003_expedientepago_admision`: aditiva, un campo nullable, sin
  backfill.
