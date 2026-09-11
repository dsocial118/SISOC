# Rendiciones #2377: secuencia, acta de auditoría y confirmación de lectura

Fecha de revisión: 2026-09-11

El issue #2377 define el resultado esperado pero deja abiertos varios puntos
materiales. Se registran acá antes de implementarlos para no convertir supuestos
en reglas de negocio silenciosas.

## 1. Qué registros participan en la secuencia del número de rendición

### Decisión

La secuencia se calcula sobre el mismo conjunto que ya usaba la validación de
unicidad: `RendicionCuentaMensualService._get_project_queryset(comedor, proyecto)`
filtrado por convenio. En consecuencia:

- **Participan** los borradores (`estado = elaboracion`), las presentadas y las
  finalizadas. El número se reserva desde el alta.
- **No participan** las rendiciones con baja lógica (`deleted_at` no nulo). Dar
  de baja la rendición 3 libera el número 3.
- No existe un estado "anulada" en el modelo; la baja lógica es el único
  mecanismo de anulación vigente.
- La primera rendición de un convenio debe ser `1`.
- El tope sigue siendo `6`: con 6 rendiciones vigentes no se admite una nueva.

### Motivo

Cualquier otro conjunto haría que unicidad y secuencia discreparan y permitiría
estados imposibles (por ejemplo, un número único pero fuera de secuencia).
Reutilizar el queryset existente mantiene una sola definición de "scope" y
respeta el mecanismo de baja lógica ya implementado.

## 2. Edición de una rendición cuyo número ya rompe la secuencia

### Decisión

Al editar, si el número **no cambia** respecto del valor persistido, se admite
aunque no sea el siguiente de la secuencia. Si el número **cambia**, debe ser el
siguiente de la secuencia calculado excluyendo la propia rendición.

### Motivo

La regla de secuencia es nueva y hay datos históricos cargados antes de que
existiera. Exigirla sobre un número que no se está modificando dejaría
rendiciones preexistentes imposibles de editar, que es justamente el bloqueo que
el issue pide destrabar en su punto 11.

## 3. Protección de concurrencia sin constraint de base

### Decisión

La asignación del número se serializa con `select_for_update()` sobre la fila
ancla del scope —`ProyectoOrganizacion` cuando la rendición tiene proyecto, o
`Comedor` en el camino legado— dentro de la transacción que crea o edita la
rendición. **No** se agrega un `UniqueConstraint` de base.

### Motivo

El scope real no es expresable como una tupla de columnas: cuando `proyecto` es
nulo, el alcance se resuelve por `comedor.codigo_de_proyecto` más organización.
Un constraint sobre `(proyecto, convenio, numero_rendicion)` no cubriría ese
camino y además podría chocar con datos históricos que hoy no lo cumplen.
El bloqueo protege la invariante identificada sin arriesgar una migración que
falle en producción.

### Consecuencias

- Dos creaciones concurrentes en el mismo proyecto se serializan; la segunda ve
  el número de la primera y es rechazada con error de secuencia.
- Sobre SQLite (tests) `select_for_update` es un no-op silencioso de Django; la
  protección real aplica en MySQL.
- Si en el futuro se normaliza `proyecto` como obligatorio, conviene revisar esta
  decisión y evaluar el constraint.

## 4. Obligatoriedad de "Indique rendiciones incluidas"

### Decisión

Cuando la auditoría de una rendición de Línea Tradicional responde **Sí** a
"¿Se genera acta de auditoría?", la selección de rendiciones incluidas es
**opcional**: se admite finalizar con la lista vacía.

### Motivo

Ni el issue ni el flujo existente exigen un mínimo. Un acta puede cubrir
únicamente a la rendición que la genera. Exigir al menos una impediría emitir la
primera acta de un proyecto, cuando todavía no hay rendiciones con "No".

### Consecuencias

- La validación del servidor verifica la elegibilidad de lo que se seleccione,
  no que se seleccione algo.
- Si el área funcional define después un mínimo, el cambio es aditivo.

## 4 bis. Qué rendiciones son elegibles para incluirse en un acta

### Decisión

Confirmada con el usuario el 2026-09-11. Son elegibles las rendiciones que
cumplen **todas** estas condiciones:

- mismo código de proyecto que la que genera el acta;
- `linea_programatica = tradicional`;
- `genera_acta_auditoria = False`, es decir que ya respondieron "No" al
  finalizar su propia auditoría;
- distintas de la propia rendición.

### Motivo

`genera_acta_auditoria` solo se completa al finalizar la auditoría de esa
rendición, así que "respondió No" es lo único que el flujo actual permite
determinar con evidencia. Quedan afuera las rendiciones con el campo en `NULL`
(todavía no auditadas): su decisión no se tomó y no corresponde darla por hecha.

Se descartó excluir además las ya incluidas en otra acta: eso es elegibilidad
retroactiva y contradice la decisión 5.

### Consecuencias

- Autorreferencia, otro proyecto y rendiciones que generan su propia acta quedan
  excluidas por construcción del queryset, no por una comprobación aparte.
- El servidor revalida contra ese mismo queryset antes de asociar: no se confía
  en las opciones que manda el navegador.

## 4 ter. Acta ya cargada cuando el campo deja de ser obligatorio

### Decisión

Confirmada con el usuario el 2026-09-11. Si al guardar la auditoría no se
adjunta archivo, el acta ya cargada **se conserva**. No adjuntar significa "no lo
toqué", no "borralo".

### Motivo

Es la misma semántica de actualización parcial que el issue pide para la edición
de datos generales, y evita perder un archivo por omisión. Ningún archivo
histórico se elimina.

## 5. Reversión de elegibilidad de rendiciones ya incluidas en un acta

### Decisión

Las rendiciones asociadas a un acta se conservan aunque después dejen de ser
elegibles (por ejemplo, si cambia su propio `genera_acta_auditoria`). La
validación de elegibilidad se aplica **al momento de asociar**, no de forma
retroactiva.

### Motivo

El acta es un hecho administrativo ya emitido. Borrar la relación en silencio
falsearía el registro histórico de qué cubrió esa acta.

## 6. Etiquetas: no se altera el casing vigente de los estados

### Decisión

El renombre de la etapa `revision_auditoria` cambia únicamente
"Revisión de Auditoría" por "Revisión para Carga". El estado compuesto se sigue
construyendo como `"<Etapa> <subestado en minúscula>"`, por lo que se lee
"Revisión para Carga pendiente" y no "Revisión para Carga Pendiente".

### Motivo

El issue escribe los estados con mayúscula inicial, pero ese casing no es el que
SISOC usa hoy para ninguna etapa. Capitalizar solo esta etapa la desalinearía de
"Revisión Territorial pendiente"; capitalizarlas todas excede el alcance pedido.
El valor persistido `revision_auditoria` no cambia en ningún caso.

## 7. Alcance del health-check

### Decisión

`GET /api/pwa/health/` verifica proceso Django y base de datos. No verifica el
storage de archivos ni RENAPER.

### Motivo

La PWA necesita distinguir "SISOC no responde" de "SISOC responde"; la base de
datos es la dependencia que efectivamente se cae junto con el envío. Verificar
storage en cada poll implicaría E/S por consulta. La limitación queda escrita en
el contrato para no prometer más de lo que comprueba: un `200` no garantiza que
una carga con adjunto se complete.
