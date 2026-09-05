# Parte II — Requerimientos nuevos (definidos con el usuario, 2026-09-03)

Todo lo que sigue es **diseño funcional a implementar**, no comportamiento
actual. Se referencia evidencia del repo donde existe una base parcial sobre
la que construir (asignación territorial, permisos), y se marca explícitamente
como "no encontrado" lo que hay que crear desde cero.

## 10) Instancia inicial: alcance confirmado

Ver aclaración agregada en §2.1. Los formularios de Excepción y Punto de
Entrega **no cambian** con este trabajo: siguen siendo sub-bloques de la
instancia de relevamiento inicial, con la misma independencia de carga a
nivel de experiencia de usuario. Este punto se deja escrito explícitamente
porque las instancias de seguimiento (§11) introducen su propia acta de
excepción, y no debe confundirse una con otra.

## 11) Instancias de seguimiento

El seguimiento deja de ser un único formulario (§4, `PrimerSeguimiento`) y
pasa a componerse de varios tipos, todos anclados a un `Relevamiento` inicial
ya existente (mismo patrón de herencia de territorial que el primer
seguimiento actual):

1. **Primer seguimiento** — el realizado inmediatamente después del inicial.
    Se mantiene igual salvo por quedar sujeto al nuevo
   ciclo de validación del coordinador (§14) y a las reglas de autocompletado
   de §13.
2. **Seguimiento posterior** — del segundo seguimiento en adelante. Se repite
   para cada seguimiento sucesivo sobre el mismo comedor/relevamiento ancla.
3. **Acta de excepción de seguimiento** — funciona igual que `Excepcion` del
   inicial (§3), pero aplicada a una instancia de seguimiento.
4. **Seguimiento virtual** — formulario que reemplaza al formulario normal de
   seguimiento cuando la modalidad de la visita es virtual.

(El acta complementaria/extraordinaria, si bien puede usarse durante un
seguimiento, no es exclusiva de esta sección — ver §12.)

### 11.1) Numeración de seguimientos posteriores

Los seguimientos posteriores llevan **número de orden explícito** (2º, 3º,
4º...), a diferencia del primer seguimiento que no necesita numerarse por ser
único. Este número:

- Reemplaza al reservado "Segundo seguimiento" de §1 (que quedaba
  deshabilitado en UI y rechazado en el servicio).
- Es la clave para la cadena de autocompletado (§13.2): cada seguimiento
  posterior hereda de "el seguimiento con el número inmediato anterior", no
  necesariamente del inicial ni del primer seguimiento.

**Pendiente de definir:** si el set de preguntas/bloques de un seguimiento
posterior es idéntico al del primer seguimiento (mismo modelo de datos,
distinto número de instancia) o si difiere en contenido. No se relevó
evidencia ni definición del usuario sobre esto — a confirmar antes de
modelar.

### 11.2) Acta de excepción de seguimiento

- Se completa cuando la visita de una instancia de seguimiento (primer o
  posterior) no pudo concretarse/relevarse normalmente — mismo criterio que
  la excepción del inicial (§3).
- Es un **registro separado** del `Excepcion` del inicial (ver aclaración de
  §10): una excepción de seguimiento no debe persistirse en el mismo modelo
  que la excepción del relevamiento inicial.
- Al completarse, la instancia de seguimiento correspondiente queda en un
  estado **análogo a `Finalizado/Excepciones`** del inicial (mismo patrón:
  motivo, descripción, geolocalización, adjuntos, firma), sujeto igual que
  cualquier otro cierre a la validación del coordinador (§14).

### 11.3) Seguimiento virtual

- Cuando la modalidad de la visita es virtual, el formulario de seguimiento
  virtual **reemplaza completamente** al formulario normal de esa instancia
  (son excluyentes) — aplica indistintamente a que sea primer seguimiento o
  un seguimiento posterior.
- **Pendiente de definir:** en qué momento y de qué manera se determina que
  una instancia es "virtual" (¿selección explícita antes de iniciar la carga,
  igual que la selección de tipo comedor/punto de entrega en §3, o una
  pregunta dentro del propio flujo que deriva a otro set de preguntas?). No
  hay definición del usuario sobre este punto todavía.

## 12) Acta complementaria - extraordinaria

Formulario transversal, distinto de la excepción de inicial (§3) y de la
excepción de seguimiento (§11.2):

- **Siempre disponible, sin depender de una instancia de relevamiento
  activa**: a diferencia de todos los formularios anteriores (que cuelgan de
  un `Relevamiento` o de un seguimiento), el acta complementaria/
  extraordinaria se liga directamente al **comedor**, y puede completarse en
  cualquier momento, exista o no un relevamiento/seguimiento en curso.
- **Disparador**: registrar novedades o situaciones puntuales del comedor que
  no están atadas a ninguna visita de relevamiento en curso — a diferencia de
  la excepción, que específicamente documenta que una visita programada no
  pudo concretarse con normalidad.
- Funciona de forma similar a Excepciones en cuanto a estructura de datos
  (motivo/descripción, geolocalización, adjuntos, firma), pero **no** hereda
  su ciclo de vida de ningún `Relevamiento.estado`.
- Al ser un dato que impacta sobre el comedor, también queda sujeta a la
  regla general de validación del coordinador antes de impactar en SISOC
  (§14) — no es una excepción a esa regla por ser standalone.
- Implica un modelo nuevo en SISOC, con FK directa a `Comedor` (no a
  `Relevamiento`). No se encontró ningún modelo existente en el repo que
  cubra este caso (`Excepcion` requiere `Relevamiento`).

## 13) Reglas de autocompletado y persistencia de datos entre instancias

### 13.1) Formularios iniciales (comportamiento ya implementado, ver §2.3)

Los datos de localización del comedor y datos del referente se muestran tal
como están cargados en SISOC al iniciar el formulario, son editables, y al
finalizar (ahora: al ser **validado por el coordinador**, ver §14) la
información vuelve a SISOC y actualiza `Comedor`/`Relevamiento`.

### 13.2) Formularios de seguimiento

- **Localización y referente**: siguen la misma lógica que el inicial — se
  muestran tal como están en SISOC (`Comedor`) al momento de iniciar el
  seguimiento, son editables, y al validarse por el coordinador la
  información **también actualiza el maestro `Comedor`** en SISOC, igual que
  hoy hace la validación del inicial. No hay tratamiento especial para
  seguimiento en este punto: el seguimiento tiene el mismo privilegio de
  actualizar el dato maestro que el inicial.
- **Preguntas que se repiten entre inicial y primer seguimiento**: el primer
  seguimiento trae precargada la información cargada en el relevamiento
  inicial para esas preguntas puntuales, permitiendo editarla.
- **Preguntas que se repiten entre seguimientos posteriores**: siguen una
  **cadena**, no vuelven siempre al inicial — cada seguimiento posterior trae
  precargado lo cargado en el seguimiento con el número de orden inmediato
  anterior (ver numeración en §11.1). Ejemplo: el 3er seguimiento hereda del
  2do, no del inicial ni del 1er seguimiento.
- **Persistencia por instancia**: cada instancia de seguimiento persiste su
  propia snapshot de estos datos de forma independiente. Editar un valor en
  un seguimiento **no modifica** el registro de la instancia anterior ya
  finalizada/validada — ni el inicial, ni un seguimiento posterior previo.

## 14) Rol coordinador y ciclo de validación en SISOC web

Este ciclo **reemplaza** al descripto en §6 (ciclo interno de AppSheet,
invisible para SISOC). Aplica a **toda instancia y todo formulario**: inicial,
primer seguimiento, seguimientos posteriores, actas de excepción (de inicial
y de seguimiento), seguimiento virtual y acta complementaria/extraordinaria.
Ningún dato relevado en territorio impacta en SISOC antes de ser revisado y
validado por este rol.

### 14.1) Rol nuevo

Se define un rol **Coordinador** en SISOC web, distinto de los roles
existentes en el repo. Aclaración por evidencia encontrada al investigar (no
es parte de la decisión, es una observación para tener en cuenta al
implementar): ya existe declarado — pero **no aplicado en ningún lugar del
código** — un permiso `relevamientos.review_relevamiento` ("Puede revisar y
finalizar relevamientos"), asignado al grupo `Revisor Relevamientos`
(evidencia: `relevamientos/models.py:1128-1129`,
`users/bootstrap/groups_seed.py:106-110`). Se definió con el usuario que el
rol Coordinador es un concepto **nuevo**, no una reutilización de ese
permiso — queda como nota para quien implemente, para decidir si conviene
reemplazar/eliminar ese permiso sin uso o dejarlo en desuso junto al nuevo rol.

### 14.2) Estados nuevos

- **Estado intermedio genérico** (nombre tentativo: `Pendiente validación
  coordinador`): cuando el territorial "finaliza" cualquier formulario en la
  app, la instancia correspondiente queda en este estado — visible en SISOC,
  sin impactar todavía ningún dato maestro. Es un único estado genérico,
  válido para cualquier tipo de instancia/formulario (no uno distinto por
  cada tipo).
- **Estado de rechazo** (nombre tentativo: `A subsanar`): si el coordinador,
  desde SISOC web, no valida la instancia y pide correcciones, pasa a este
  estado. El territorial lo ve reflejado en la app, corrige y reenvía —
  puede repetirse **N veces** hasta que el coordinador valide.
- **Validación positiva**: el coordinador valida → la instancia pasa a
  `Finalizado` / `Finalizado con Excepciones` (según corresponda) y **recién
  en ese momento** se disparan los efectos de impacto (actualización de
  `Comedor`, geolocalización, datos de "Datos generales" — ver §2.3 y §13).

### 14.3) Diagrama actualizado (reemplaza el ciclo de §6)

```
Territorial completa y "finaliza" en la app
                │
                ▼
      Pendiente validación coordinador  ◀────────────┐
                │                                     │
                │ (coordinador revisa en SISOC web)   │
                ▼                                     │
        ┌───────┴────────┐                            │
        │                │                            │
     valida           pide correcciones                │
        │                │                            │
        ▼                ▼                            │
  Finalizado /       A subsanar ──(territorial corrige)┘
  Finalizado con
  Excepciones
   (impacta en SISOC:
   Comedor, geolocalización,
   datos generales)
```

El nombre definitivo de los dos estados nuevos queda pendiente de definición
(los usados arriba son tentativos, para dejar clara la mecánica).

### 14.4) Nota de compatibilidad con §5

`Relevamiento.estado` (§5) tendrá que incorporar el nuevo estado intermedio y
el de rechazo (hoy es un `CharField` libre sin choices, por lo que técnicamente
no requiere migración de esquema, solo de valores usados y de la lógica que
los interpreta). Las reglas de §5 sobre unicidad de relevamiento
`Pendiente`/`Visita pendiente` por comedor y sobre reasignación de territorial
deberán revisarse para contemplar estos nuevos estados.

## 15) Disponibilidad de comedores y relevamientos por zona territorial

### 15.1) Comportamiento actual (evidencia del repo)

Ya existe una asignación territorial↔zona, pero a nivel **solo provincia**:
`TerritorialComedorProvincia` (evidencia: `users/models.py:308-323`). El
filtrado de qué relevamientos ve un territorial ya combina, con `OR`, esta
asignación por zona con la asignación puntual directa
(`Relevamiento.territorial_user`): evidencia,
`_scope_relevamientos_for_authenticated_user` en
`relevamientos/views/api_views.py:20-44`. Es decir, la convivencia entre
"acceso por zona" y "asignación puntual" **ya está resuelta a nivel de
filtrado de datos** — lo que falta es la granularidad y las acciones
disponibles sobre esos comedores.

### 15.2) Requerimiento nuevo

- Extender la granularidad de la asignación territorial de **provincia** a
  **provincia + municipio + localidad**. Pendiente de definir el modelo
  concreto (extensión de `TerritorialComedorProvincia` o modelo nuevo) y si
  un mismo territorial puede tener múltiples combinaciones asignadas.
- Dentro de esa zona asignada, el territorial debe poder:
  - **Ver** todos los comedores de la zona, no solo los que ya tienen un
    relevamiento activo.
  - **Activar autónomamente** un relevamiento (inicial o, si corresponde,
    una instancia de seguimiento) sobre cualquiera de esos comedores.
- La activación autónoma **arranca directo**: mismo flujo que un relevamiento
  asignado puntualmente desde SISOC (queda en estado inicial habilitado para
  carga), sin pasos de aprobación previos.
- La asignación puntual de relevamientos desde SISOC (mecanismo actual)
  **se mantiene** y convive con el acceso por zona — no la reemplaza.
- Los relevamientos asignados puntualmente desde SISOC deben **destacarse/
  priorizarse** frente a los que el territorial activó de forma autónoma
  dentro de su zona. Pendiente de definir si esto es solo un tratamiento
  visual/de orden en el listado, o si implica lógica adicional (plazos,
  notificaciones, reportes).

## 16) Pendientes abiertos (a confirmar antes de modelar)

- Set de preguntas/bloques de "seguimiento posterior": ¿idéntico al primer
  seguimiento o distinto? (§11.1)
- Momento y mecanismo de determinación de "seguimiento virtual": ¿selección
  previa o pregunta derivadora dentro del flujo? (§11.3)
- Nombres definitivos de los estados nuevos `Pendiente validación
  coordinador` y `A subsanar` (§14.2), y si aplican tal cual a
  `Relevamiento.estado` o requieren un campo/modelo nuevo.
- Modelo concreto para la asignación territorial a nivel municipio/localidad
  y si admite múltiples zonas por usuario (§15.2).
- Tratamiento de "destacado/priorizado" para relevamientos asignados desde
  SISOC: ¿solo visual o con lógica de negocio adicional? (§15.2)
- Qué ocurre con el permiso `relevamientos.review_relevamiento` /grupo
  `Revisor Relevamientos` ya declarado y sin uso, frente al rol Coordinador
  nuevo (§14.1): mantener sin uso, deprecar, o consolidar.
## 17) Observaciones y hallazgos sobre el formulario de Relevamiento Inicial

Relevado por el usuario sobre el formulario actual en AppSheet (numeración de
pasos propia de AppSheet, no de este repo). Todos corresponden al
Relevamiento Inicial:

- **Paso 4 (Espacio/Cocina)**: falta la pregunta condicional "¿Dónde
  almacenan los alimentos secos?", que debería activarse si se responde que
  no hay lugar para almacenarlos. SISOC ya tiene un campo preparado para esa
  respuesta — `EspacioCocina.almacenamiento_alimentos_secos_otro`, cuyo
  `verbose_name` es literalmente *"2.2.2.1 Si respondió 'No', especificar
  dónde almacenan"* (evidencia: relevamientos/models.py:206-214) — el campo
  existe en SISOC pero la pregunta condicional no está implementada en el
  formulario de AppSheet.
- **Paso 5 (Espacio)**: falta la pregunta condicional "Otra frecuencia de
  limpieza", que debería activarse si se elige "Otra" en la pregunta de
  frecuencia de limpieza de las instalaciones. El campo
  `Espacio.frecuencia_limpieza_otro` ya existe en el modelo (evidencia:
  relevamientos/models.py:399-402), listo para recibir esa respuesta; falta
  la pregunta condicional en AppSheet.
- **Paso 10 (Anexo)**: falta una pregunta gate "¿Recibió o no insumos?"
  previa al detalle de insumos. El modelo `Anexo` solo tiene
  `veces_recibio_insumos_2024` (cantidad de veces en el año), sin un campo
  booleano dedicado a esa pregunta sí/no (evidencia:
  relevamientos/models.py:905-910) — a definir si conviene inferir la
  respuesta de la cantidad (0 = no recibió) o si hace falta agregar un campo
  nuevo.
- **Paso 10 (Anexo)**: la etiqueta "Espacio para Huerta" debería decir
  "Espacio para actividades". El campo subyacente es `Anexo.espacio_huerta`
  (evidencia: relevamientos/models.py:903) — es un cambio de etiqueta/copy en
  AppSheet, no de modelo.
- **Paso 12 (cierre del Relevamiento Inicial)**: falta la firma del
  responsable del comedor; hoy solo se pide la firma del relevador/técnico
  territorial. A diferencia del Primer Seguimiento, que en su bloque
  `CierreSeguimiento` ya tiene dos firmas (`firma_entrevistado` y
  `firma_tecnico`, evidencia: relevamientos/models.py:1543-1544), el
  Relevamiento Inicial no tiene un bloque de cierre equivalente: la única
  firma modelada en SISOC para el relevamiento inicial es `Excepcion.firma`
  (evidencia: relevamientos/models.py:954), y esa solo aplica al camino de
  excepción, no al cierre normal en `Finalizado`. Si se agrega la firma del
  responsable en el paso 12, probablemente haga falta un campo nuevo en el
  modelo — hoy no hay dónde persistirla para el flujo normal de `Finalizado`.

## 18) Anexo: transcripción fiel de los formularios de referencia (modelos oficiales del Programa Alimentar Comunidad)

El usuario aportó los 5 modelos de formulario en papel/PDF que usa hoy el
Programa Alimentar Comunidad para las instancias descriptas en §11 y §12.
Esta sección transcribe **cada formulario pregunta por pregunta**, con su
numeración, opciones y lógica de salto tal como figuran en el PDF original,
para que pueda usarse como especificación de implementación sin volver a
consultar la fuente. Fuente: PDFs aportados por el usuario el 2026-09-03, no
versionados en este repo.

Convenciones de esta transcripción:
- `☐` representa cualquier casilla de selección del original (el extractor
  de texto del PDF usaba glifos inconsistentes entre formularios — el
  símbolo se unificó, pero el texto, orden y agrupación de las opciones se
  preservan tal como están impresos).
- `(→ pasa a X.X.X)` indica una instrucción de salto condicional impresa en
  el propio formulario.
- `___` indica un campo de texto libre sin opciones.
- Las tablas se transcriben con su misma estructura de filas/columnas.

### 18.1) "FORMULARIO DE PRIMER VISITA DE SEGUIMIENTO DE COMEDOR / MERENDERO"

**Archivo fuente:** `1-Formulario Primer Visita Seguimiento.pdf` — **Corresponde a §11, ítem 1 (Primer seguimiento).**

> REGISTRO FOTOGRÁFICO: se sugiere cocina, salón comedor, elaboración/servido, lugar de guardo.

**FUNCIONAMIENTO** — *Dado que el objetivo de la visita es constatar el funcionamiento del comedor/merendero de referencia, marcar con una X según corresponda, en caso de no funcionar o cerrado indicar motivo.*
☐ Abierto, en funcionamiento　☐ Abierto, sin funcionamiento　☐ Cerrado
Motivo: ___

**1. DATOS DEL COMEDOR / MERENDERO**

*1.1 IDENTIFICACIÓN DEL COMEDOR/MERENDERO (Datos que saldrían del sistema)*
- 1.1.1 Fecha y horario de la visita (hh:mm) (Día/mes/año)
- 1.1.2 Nombre del Comedor/Merendero
- 1.1.3 ID SISOC
- 1.1.4 Código del Comedor

*1.2 DOMICILIO DEL COMEDOR/MERENDERO*
- 1.2.1 Calle
- 1.2.2 Número
- 1.2.3 Barrio
- 1.2.4 Localidad
- 1.2.5 Municipio
- 1.2.6 Departamento/Partido
- 1.2.7 Provincia

*1.3 DATOS DEL REFERENTE/RESPONSABLE DEL COMEDOR / MERENDERO*
- 1.3.1 Nombre y Apellido
- 1.3.2 Mail del referente / responsable
- 1.3.3 Celular del referente / responsable
- 1.3.4 Función que cumple en el comedor *(si cumple más de una función marcar las que corresponden)*: ☐Responsable de cocina ☐Cocinero/a ☐Responsable de compras ☐Referente del comedor ☐Otro (especificar)

**2. DATOS SOBRE EL ESPACIO FÍSICO DONDE FUNCIONA EL COMEDOR / MERENDERO**

*2.1 SEGURIDAD E HIGIENE:*
- 2.1.1 ¿Cuentan con agua potable dentro del espacio donde se cocinan los alimentos? Sí / No
- 2.1.2 ¿Cuál es el tipo de combustible que utilizan para cocinar? *(Opción múltiple, indicando el que más se usa con el n°1 y sucesivamente 2, 3, etc.)*: Gas de red / Electricidad / Gas Envasado en garrafa o tubo / Leña o carbón / Otros: ___
- 2.1.3 ¿Disponen de baño o letrina propias para el comedor/merendero? *(Indique la ubicación espacial del baño)*: Dentro del establecimiento / Fuera del establecimiento / No disponen
- 2.1.4 ¿Se observa recipiente de residuos?: Con tapa / Sin tapa / Con bolsa / Sin bolsa / Desbordado / No hay / Otro: ___
- 2.1.5 ¿Se observan animales en el espacio donde se preparan y sirven los alimentos? Sí / No
- 2.1.6 Los elementos de limpieza, ¿se encuentran guardados en el mismo lugar que los alimentos? Sí / No
- 2.1.7 Los alimentos secos que NO estén en uso en el preciso instante de la visita se encuentran: *(Opción múltiple, indicando el que más se observa con el n°1 y sucesivamente 2, 3, etc.)*: Cerrados / En uso, cerrado en condiciones adecuadas / Desparramados / No se observan alimentos / Otros: ___
- 2.1.8 Indicar la existencia en el comedor de heladeras y freezer *(marcar con una cruz)*: Heladera / Freezer
- 2.1.9 ¿Cómo son las condiciones de almacenado de los alimentos refrigerados? *(Opción múltiple, indicando el que más se observa con el n°1 y sucesivamente 2, 3, etc.)* — tabla con columnas **Heladera** y **Freezer** para cada opción: Cerrados / En uso, cerrados en condiciones adecuados / Derramados / Etiquetados (fecha de vencimiento) / No se observan alimentos / Otro (especificar)
- 2.1.10 En el espacio donde se preparan los alimentos, ¿se observan condiciones de higiene y limpieza de instalaciones? — tabla con columnas **Limpieza** (Adecuada / Medianamente adecuada / Inadecuada) y **Orden** (Adecuado / Medianamente adecuado / Inadecuado), para cada fila: Piso, Mesada, Mesas, Piletas (bachas), Equipamiento de cocina* (*Horno, cocina, anafe, etc.), Utensilios
- 2.1.11 En caso de entregar viandas ¿en qué estado entregan los recipientes los destinatarios para retirar la vianda?: Adecuado / Medianamente adecuado / Inadecuado

**3. DATOS SOBRE LAS PERSONAS QUE REALIZAN TAREAS EN EL COMEDOR / MERENDERO**

*3.1 PERSONAS QUE REALIZAN TAREAS EN EL COMEDOR / MERENDERO (Indique con una X la opción que corresponda)*
- 3.1.1 ¿Qué cantidad de personas realizan tareas en el Comedor / Merendero? ☐ 1 a 3　☐ 4 a 7　☐ 8 o más
- 3.1.2 Las personas que realizan tareas en el Comedor/Merendero ¿recibieron capacitación sobre alimentación saludable? ☐ Sí　☐ No (→ pasa a 3.1.8)
- 3.1.3 ¿En qué año? (formato AAAA)
- 3.1.4 ¿Quién la dictó? (especificar organismo o institución)
- 3.1.5 ¿Decidieron realizar cambios en la composición del menú luego de la capacitación? ☐Sí　☐No (→ pasa a 3.1.7)
- 3.1.6 ¿Cuáles?
- 3.1.7 ¿Por qué? (motivo/s)
- 3.1.8 ¿Sobre qué temas le gustaría recibir capacitación? *(respuesta múltiple)*: ☐Alimentación saludable ☐Diseño de menús y recetarios ☐Higiene y conservación de alimentos ☐Cocina económica (optimización de recursos) ☐Otro (especificar)

**4. DATOS SOBRE RECURSOS DEL COMEDOR / MERENDERO**

*4.1 ORIGEN Y TIPO DE RECURSOS (Respuesta múltiple)* — tabla con columnas **Fuente / Sí-No / Frecuencia / Qué recibe**, para cada fuente: 4.1.1 Estado Nacional, 4.1.2 Estado Provincial, 4.1.3 Estado Municipal, 4.1.4 Donaciones. Para cada una: Sí/No; si Sí, frecuencia (1 vez por mes / 2 a 4 meses / 5 o más / sin frecuencia específica) y qué recibe (Transferencia monetaria / Mercadería); si No, opción Ns/Nc también disponible.
- 4.2 Si marcó más de una opción en la pregunta anterior ¿Cuál es el financiamiento más importante para brindar la prestación principal? *(respuesta única)*: ☐Fondos propios ☐Donaciones ☐Financiamiento en dinero del Estado Nacional ☐Alimentos del Estado Nacional ☐Financiamiento en dinero del Estado Provincial ☐Alimentos del Estado Provincial ☐Financiamiento en dinero del Estado Municipal ☐Alimentos del Estado Municipal ☐Recibimos módulos de alimentos secos ☐Ns/Nc ☐Otros: ___
- 4.3 Además de los fondos para comprar alimentos, ¿reciben financiamiento para otras necesidades del espacio comunitario? ☐Sí　☐No (→ Pasa a bloque 5)　☐Ns/Nc (→ Pasa a bloque 5)
  - 4.3.1 ¿Para qué? ___
- 4.4 ¿Con qué frecuencia?: 1 vez por mes / 2 a 4 meses / 5 o más / Sin frecuencia específica

**5. DATOS SOBRE LA REALIZACIÓN DE COMPRAS PARA ABASTECER EL COMEDOR / MERENDERO**

*5.1 LUGARES DONDE SUELE REALIZAR LAS COMPRAS PARA ABASTECER EL COMEDOR / MERENDERO (Respuesta múltiple)*, cada una Sí/No: 5.1.1 Negocio de cercanía, 5.1.2 Verdulería, 5.1.3 Granja/pollería, 5.1.4 Carnicería, 5.1.5 Pescadería, 5.1.6 Supermercado/Hipermercado, 5.1.7 Mercado central, 5.1.8 Ferias comunales/Cooperativas, 5.1.9 Mayoristas, 5.1.10 Otro
- 5.2 ¿Con qué frecuencia hacen las compras?: ☐Todos los días/casi todos los días ☐1 vez por semana ☐Cada 15 días ☐1 vez por mes ☐Ns/Nc ☐Otro (especificar) ___
- 5.3 ¿Quién hace las compras de los alimentos para el comedor?: ☐Organización ☐Referente del comedor ☐Equipo de la cocina ☐Otros (especificar) ___ ☐Ns/Nc
- 5.4 Usted, ¿tiene posibilidad de elegir qué alimentos comprar?: ☐Siempre ☐A veces ☐Nunca
- 5.5 ¿Con qué frecuencia recibe o compra los siguientes alimentos? *(Diariamente / Semanalmente / Quincenalmente / Mensualmente / No sabe-No contesta)*, para cada uno: 5.5.1 Hortalizas y Frutas, 5.5.2 Leche/Yogurth/Queso, 5.5.3 Carne, 5.5.4 Legumbres, 5.5.5 Alimentos secos *(número no legible en el PDF fuente, se infiere por posición — a confirmar contra el original en papel)*, 5.5.6 Pan, 5.5.7 Huevos, 5.5.8 Otros

**6. DATOS SOBRE LA PRESTACIÓN ALIMENTARIA**

*6.1 DÍAS, MODALIDAD Y TIPO DE PRESTACIÓN* — tabla por cada día de la semana (Lunes a Domingo), con columnas **PRES** (AP: aprobadas / DE: declarado por el entrevistado) y sub-columnas **P** (Presencial) / **V** (Vianda), y filas DES (Desayuno) / ALM (Almuerzo) / MER (Merienda) / CEN (Cena).
- 6.1.1 En caso de que lo aprobado no coincida con lo declarado, indicar el motivo: ___
- 6.2 Indique el menú que sirvieron la semana pasada *(indicar el de la prestación principal y aclarar también si dan pan y postre)*: Lunes / Martes / Miércoles / Jueves / Viernes / Sábado / Domingo (campo libre c/u)
- 6.3 Este menú, ¿está preestablecido/planificado? ☐Sí　☐No (→ pasa a 6.7)　☐Ns/Nc (→ pasa a 6.7)
- 6.4 ¿Por quién?: ☐Gobierno nacional ☐Gobierno provincial ☐Gobierno municipal ☐Comedor ☐Ns/Nc
- 6.5 ¿Con qué frecuencia cumplen con el menú preestablecido? ☐Siempre (→ Pasa a 6.7)　☐A veces　☐Nunca　☐Ns/Nc (→ Pasa a 6.7)
- 6.6 ¿Por qué? ___
- 6.7 ¿Llevan un registro de asistencia/presentismo? *(marcar con X según corresponda)*: 6.7.1 Registro de asistencia (Sí/No); 6.7.2 Quién lo registra; 6.7.3 Método de registro
- 6.8 ¿Asisten al comedor/merendero y/o entregan viandas a personas en situación de calle? ☐Sí (cantidad)　☐No　☐Ns/Nc
- 6.9 Cantidad de personas asistidas por día *(sumar la cantidad total de personas que asisten a la prestación principal — almuerzo o cena¹)*: ___
  - ¹ *En el caso de brindar almuerzo y cena, tener en cuenta la prestación con mayor cantidad de asistentes. Si sólo brindan desayuno, merienda y/o merienda reforzada contar la de mayor concurrencia.*
- 6.10 Detalle del menú brindado al momento de la visita *(Listar todos los alimentos utilizados y las respectivas cantidades)*: 6.10.1 Marcar la prestación que corresponda (desayuno/almuerzo/merienda/cena); 6.10.2 Menú; 6.10.3 Cantidad de personas para las que se preparó este menú; tabla **Ingredientes / Cantidades totales utilizadas (litros, kg, unidades)**
- 6.11 Modalidad de la prestación del día de la visita *(consignar cantidad según corresponda)*: Presencial: ___ / Vianda: ___
- 6.12 ¿Con qué frecuencia sirven los siguientes alimentos en el almuerzo y/o cena? *(5-7 veces por semana / 3-4 veces por semana / 1-2 veces por semana / Cada 15 días / 1 vez al mes / Nunca)*, para: 6.12.1 Frutas, 6.12.2 Verduras, 6.12.3 Carne vacuna, 6.12.4 Pollo, 6.12.5 Pescado, 6.12.6 Fideos/Arroz/Polenta, 6.12.7 Legumbres, 6.12.8 Ultraprocesados, 6.12.9 Huevos
- 6.13 ¿Con qué frecuencia sirven los siguientes alimentos en el desayuno y/o merienda? *(misma escala que 6.12)*, para: 6.13.1 Leche, 6.13.2 Té, 6.13.3 Mate cocido, 6.13.4 Yogurth, 6.13.5 Queso, 6.13.6 Fruta, 6.13.7 Pan, 6.13.8 Galletitas, 6.13.9 Mermelada/Dulce de leche

**7. PERCEPCIONES SOBRE LA PRESTACIÓN ALIMENTARIA**
- 7.1 ¿Considera que el menú es variado? ☐Sí ☐No ☐Ns/Nc
- 7.2 ¿Considera que el menú es saludable/nutritivo? ☐Sí ☐No ☐Ns/Nc
- 7.3 ¿Por qué? ___
- 7.4 ¿Considera que el tamaño de las porciones es suficiente? ☐Sí ☐No ☐Ns/Nc
- 7.5 ¿Cree que las personas que acuden al comedor están conformes con la comida que reciben? ☐Sí ☐No ☐Ns/Nc
- 7.6 ¿Por qué? ___
- 7.7 ¿Qué le gustaría mejorar en la alimentación que ofrecen? ___

**8. DATOS SOBRE ACTIVIDADES EXTRA-ALIMENTARIAS**

*8.1 Se realizan actividades (tildar "sí" o "no" según lo que corresponda en cada caso)* — tabla con columnas **Sí / No / ¿Dónde? (En el espacio del comedor / En otro espacio asociado) / Frecuencia (5-7 veces por semana / 3-4 veces por semana / 1-2 veces por semana / Cada 15 días / 1 vez al mes)**, para cada actividad:
8.1.1 Talleres recreativos/artísticos; 8.1.2 Apoyo educativo/alfabetización; 8.1.3 Charlas o encuentros/grupos de contención; 8.1.4 Actividades deportivas; 8.1.5 Talleres de oficios/capacitación laboral; 8.1.6 Huerta; 8.1.7 Actividades culturales (talleres de lectura, escritura, etc.); 8.1.8 Actividades religiosas; 8.1.9 Actividades para personas con discapacidad; 8.1.10 Ayuda para trámites/Documentos; 8.1.11 Servicios legales o de protección de derechos; 8.1.12 Terminalidad Educativa (FINES, etc.); 8.1.13 Emprendimientos productivos/de servicios (ej: elaboración de panificados, dulces y conservas, textil, peluquería, etc.); 8.1.14 Promoción de la salud; 8.1.15 Otro

**9. INFORMACIÓN ADICIONAL**

*9.1 TARJETA*
- 9.1.1 ¿Es usted la persona responsable de la tarjeta? Sí / No (→ pasa a bloque 9.2)
- 9.1.2 ¿Le notificaron sobre la llegada de la tarjeta? Sí / No
- 9.1.3 ¿La tarjeta le llegó en el mes en que fue notificado que le iba a llegar? Sí / No
- 9.1.4 ¿Está conforme con usar la tarjeta como medio de pago para comprar los alimentos? Sí / No
- 9.1.5 ¿Por qué?

*9.2 RENDICIÓN DE CUENTAS (NO APLICA PARA ABORDAJE COMUNITARIO)*
- 9.2.1 ¿Es usted la persona encargada de la rendición de cuentas? Sí / No (→ fin de la encuesta)
- 9.2.2 ¿Recibió usted la capacitación inicial sobre rendición de cuentas? Sí / No (→ pasa a 9.2.4)
- 9.2.3 ¿Le sirvió la capacitación inicial sobre rendición de cuentas? Sí (→ pasa a 9.2.4) / No
  - 9.2.3.1 ¿Por qué?
- 9.2.4 ¿Le parece sencillo usar la plataforma para la rendición de cuentas? Sí (→ pasa a 9.2.5) / No
  - 9.2.4.1 ¿Por qué?
- 9.2.5 ¿Tiene inconvenientes con la carga de tickets en la plataforma? Sí / No (→ pasa a bloque 9.3)
  - 9.2.5.1 ¿Por qué?

*9.3 ASISTENCIA TÉCNICA*
- 9.3.1 ¿Se identifican situaciones que requieren de asistencia técnica en los siguientes aspectos? *Se responde por apreciación técnica (opción múltiple, indicando el de mayor necesidad con el n°1 y sucesivamente 2, 3, etc.)*: 9.3.1.1 Socio-Organizativos; 9.3.1.2 Alimentario-Nutricionales; 9.3.1.3 Seguridad e Higiene; 9.3.1.4 Administrativo-Contables/Rendición de Cuentas; 9.3.1.5 Otro

**10. COMENTARIOS FINALES**
*Este espacio está reservado para que el entrevistador incluya las observaciones que considere pertinentes, teniendo en cuenta que el objetivo de esta visita es evidenciar el funcionamiento general del comedor* — campo libre.

Cierre: **Firma del entrevistado** / **Nombre y apellido del técnico** / **Firma** (del técnico).

### 18.2) "FORMULARIO DE SEGUIMIENTO DE COMEDOR / MERENDERO" (a partir de la 2ª visita)

**Archivo fuente:** `2-Formulario de Seguimiento-a partir 2 visita.pdf` — **Corresponde a §11, ítem 2 (Seguimiento posterior).**

**Resuelve el pendiente de §11.1/§16:** el set de preguntas **no es idéntico**
al del primer seguimiento (§18.1) — es una versión considerablemente más
acotada, como se ve punto por punto abajo.

**FUNCIONAMIENTO** — *Dado que el objetivo de la visita es constatar el funcionamiento del comedor/merendero de referencia, marcar con una X según corresponda, en caso de no funcionar o cerrado indicar motivo.*
☐ Abierto, en funcionamiento　☐ Abierto, sin funcionamiento　☐ Cerrado

**1. DATOS DEL COMEDOR / MERENDERO**

*1.1 IDENTIFICACIÓN DEL COMEDOR/MERENDERO*
- 1.1.1 Fecha y horario de la visita (hh:mm) (Día/mes/año)
- 1.1.2 Nombre del Comedor/Merendero
- 1.1.3 ID SISOC
- 1.1.4 Código del Comedor

*1.2 DOMICILIO DEL COMEDOR/MERENDERO*
- 1.2.1 Calle / 1.2.2 Número / 1.2.3 Barrio / 1.2.4 Localidad / 1.2.5 Municipio / 1.2.6 Departamento/Partido / 1.2.7 Provincia

**2. DATOS DEL ENTREVISTADO (REFERENTE /RESPONSABLE DEL COMEDOR / MERENDERO)**
- 2.1. Nombre y Apellido
- 2.2. Mail del referente / responsable
- 2.3. Celular del referente / responsable
- 2.4. Función que cumple en el comedor *(si cumple más de una función marcar las que corresponden)*: ☐Responsable de cocina ☐Cocinero/a ☐Responsable de compras ☐Referente del comedor ☐Otro (especificar)

**3. DATOS SOBRE LAS PERSONAS QUE REALIZAN TAREAS EN EL COMEDOR / MERENDERO**

*3.1 PERSONAS QUE REALIZAN TAREAS EN EL COMEDOR / MERENDERO (Indique con una X la opción que corresponda)*
- 3.1.1 ¿Qué cantidad de personas realizan tareas en el Comedor / Merendero? ☐1 a 3　☐4 a 7　☐8 o más
- 3.1.2 Las personas que realizan tareas en el Comedor/Merendero ¿recibieron capacitación sobre alimentación saludable? ☐Sí　☐No (→ pasa a 3.1.8)
- 3.1.3 ¿En qué año? (formato AAAA)
- 3.1.4 ¿Quién la dictó? (especificar organismo o institución)
- 3.1.5 ¿Decidieron realizar cambios en la composición del menú luego de la capacitación? ☐Sí　☐No (→ pasa a 3.1.7)
- 3.1.6 ¿Cuáles?
- 3.1.7 ¿Por qué? (motivo/s)
- 3.1.8 ¿Sobre qué temas le gustaría recibir capacitación? *(respuesta múltiple)*: ☐Alimentación saludable ☐Diseño de menús y recetarios ☐Higiene y conservación de alimentos ☐Cocina económica (optimización de recursos) ☐Otro (especificar)

> **Nota:** acá termina el bloque de "personas que realizan tareas" — este
> formulario **no** repite el bloque "2. Datos sobre el espacio físico"
> (seguridad e higiene, 11 preguntas) de §18.1.

**4. ¿CUÁL FUE EL FINANCIAMIENTO MÁS IMPORTANTE PARA BRINDAR LA PRESTACIÓN PRINCIPAL EN EL ÚLTIMO MES?** *(RESPUESTA ÚNICA)*
☐Fondos propios ☐Donaciones ☐Financiamiento en dinero del Estado Nacional ☐Alimentos del Estado Nacional ☐Financiamiento en dinero del Estado Provincial ☐Alimentos del Estado Provincial ☐Financiamiento en dinero del Estado Municipal ☐Alimentos del Estado Municipal ☐Recibimos módulos de alimentos secos ☐Ns/Nc ☐Otros: ___

> **Nota:** reemplaza a la matriz completa "4.1 Origen y tipo de recursos" de
> §18.1 por esta única pregunta de respuesta única.

**5. LUGARES DONDE SUELE REALIZAR LAS COMPRAS PARA ABASTECER EL COMEDOR / MERENDERO** *(Respuesta múltiple)*, cada una Sí/No: 5.1 Negocio de cercanía, 5.2 Verdulería, 5.3 Granja/pollería, 5.4 Carnicería, 5.5 Pescadería, 5.6 Supermercado/Hipermercado, 5.7 Mercado central, 5.8 Ferias comunales/Cooperativas, 5.9 Mayoristas, 5.10 Otro

**6. ¿CON QUÉ FRECUENCIA HACEN LAS COMPRAS?**
☐Todos los días/casi todos los días ☐1 vez por semana ☐Cada 15 días ☐1 vez por mes ☐Ns/Nc ☐Otro (especificar) ___

> **Nota:** a diferencia de §18.1, este formulario **no** pregunta "quién
> hace las compras" ni "posibilidad de elegir qué comprar" ni la matriz de
> frecuencia por tipo de alimento (5.5 de §18.1).

**7. DATOS SOBRE LA PRESTACIÓN ALIMENTARIA**

*7.1 Días, Modalidad y Tipo de Prestación* — misma estructura de tabla que 6.1 de §18.1 (PRES: AP/DE, P/V, por día de la semana, filas DES/ALM/MER/CEN).
- En caso de que lo aprobado no coincida con lo declarado, indicar el motivo: ___
- 7.2 Detalle del menú brindado al momento de la visita *(Listar todos los alimentos utilizados y las respectivas cantidades)*: marcar la prestación (Desayuno/Almuerzo/Merienda/Cena); Menú: ___; Cantidad de personas para las que se preparó este menú: ___; Modalidad de la prestación del día de la visita: Vianda / Presencial; tabla **Ingredientes / Cantidades totales utilizadas**
- 7.3 ¿Le gustaría modificar o mejorar algo de la alimentación que ofrecen? ¿Qué? ___

> **Nota:** a diferencia de §18.1, este formulario **no** incluye "menú de
> la semana pasada" (6.2), ni las matrices de frecuencia de alimentos
> (6.12/6.13), ni el bloque "7. Percepciones sobre la prestación
> alimentaria" completo.

**8. DATOS SOBRE ACTIVIDADES EXTRA-ALIMENTARIAS**
- 8.1 ¿Iniciaron nuevas actividades este último mes? Sí / No　¿Cuáles? (indicar frecuencia) ___
- 8.3 ¿Tuvieron alguna dificultad en el uso de la tarjeta en este último mes? Sí / No　¿Cuál? ___
- 8.4 ¿Tuvieron algún inconveniente en el uso de la plataforma en este último mes? Sí / No　¿Cuál? ___

> **Nota (fiel al original):** la numeración salta de 8.1 a 8.3 — **no existe
> un ítem 8.2** en el PDF fuente. No se corrige acá; se deja registrado tal
> cual, a confirmar si es un error de origen del formulario en papel antes
> de modelarlo en SISOC. Además, este bloque **no repite** las 15 categorías
> de actividad de §18.1 (talleres, huerta, actividades religiosas, etc.), ni
> las preguntas de tarjeta/rendición de cuentas del bloque 9 de §18.1.

**9. ASISTENCIA TÉCNICA**
- 9.1 ¿Se identifican situaciones que requieren de asistencia técnica en los siguientes aspectos? *Se responde por apreciación técnica (opción múltiple, indicando el de mayor necesidad con el n°1 y sucesivamente 2, 3, etc.)*: 9.1.1 Socio-Organizativos; 9.1.2 Alimentario-Nutricionales; 9.1.3 Seguridad e Higiene; 9.1.4 Administrativo-Contables/Rendición de Cuentas; 9.1.5 Otro

**10. COMENTARIOS FINALES** — campo libre.

Cierre: **Firma del entrevistado** / **Nombre y apellido del técnico** / **Firma** (del técnico).

### 18.3) "ACTA COMPLEMENTARIA DE SEGUIMIENTO DE COMEDOR / MERENDERO"

**Archivo fuente:** `3-Acta complementaria de Seguimiento (excepcion).pdf` — **Corresponde a §11.2 (Acta de excepción de seguimiento).** El usuario nombró el archivo fuente aclarando entre paréntesis "(excepción)", confirmando que es el equivalente, para instancias de seguimiento, del `Excepcion` del inicial (§3) — pero es un formulario propio, no el mismo.

**1. DATOS DEL COMEDOR / MERENDERO**

*1.1 IDENTIFICACIÓN DEL COMEDOR/MERENDERO*
- 1.1.1 Fecha y horario de la visita (hh:mm) (Día/mes/año)
- 1.1.2 Nombre del Comedor/Merendero
- 1.1.3 ID SISOC
- 1.1.4 Código del Comedor

*1.2 DOMICILIO DEL COMEDOR/MERENDERO*
- 1.2.1 Calle / 1.2.2 Número / 1.2.3 Barrio / 1.2.4 Localidad / 1.2.5 Municipio / 1.2.6 Departamento/Partido / 1.2.7 Provincia

> No hay bloque de "datos del entrevistado" — consistente con que la visita
> no se pudo concretar.

**2. MOTIVO** *(selección, una casilla por opción)*: ☐ Espacio cerrado　☐ Dirección no encontrada　☐ Abierto pero sin posibilidad de realizar la entrevista　☐ Otro

**3. OBSERVACIONES** — campo libre.

Cierre: **Nombre y Apellido del técnico** / **Firma** (una sola firma — no hay firma de entrevistado).

**Observación:** el catálogo de motivos es **distinto** al `MotivoExcepcion`
del inicial (`No existe` / `Revisita` / `Punto de entrega` / `Otros`, ver
§3) — otra confirmación de que debe modelarse como catálogo/registro propio,
no reutilizar `Excepcion`.

### 18.4) "REGISTRO DE ENTREVISTA DE SEGUIMIENTO VIRTUAL DE COMEDORES / MERENDEROS"

**Archivo fuente:** `4-Modelo Entrevista Virtual.pdf` — **Corresponde a §11.3 (Seguimiento virtual).**

> REGISTRO FOTOGRÁFICO: se sugiere cocina, salón comedor, elaboración/servido, lugar de guardo.

**1. DATOS DEL COMEDOR / MERENDERO**

*1.1 IDENTIFICACIÓN DEL COMEDOR/MERENDERO*
- 1.1.1 Fecha y horario de la visita (hh:mm) (Día/mes/año)
- 1.1.2 Nombre del Comedor/Merendero
- 1.1.3 ID SISOC
- 1.1.4 Código del Comedor

*1.2 DOMICILIO DEL COMEDOR/MERENDERO*
- 1.2.1 Calle / 1.2.2 Número / 1.2.3 Barrio / 1.2.4 Localidad / 1.2.5 Municipio / 1.2.6 Departamento/Partido / 1.2.7 Provincia

*1.3 DATOS DEL ENTREVISTADO COMEDOR / MERENDERO*
- 1.3.1 Nombre y Apellido
- 1.3.2 Mail del referente / responsable
- 1.3.3 Celular del referente / responsable
- 1.3.4 Función que cumple en el comedor *(si cumple más de una función marcar las que corresponden)*: ☐Responsable de cocina ☐Cocinero/a ☐Responsable de compras ☐Referente del comedor ☐Otro (especificar)

**2. REGISTRO DE LA ENTREVISTA:**

*2.1. DATOS SOBRE LA PRESTACIÓN ALIMENTARIA*

*2.1.1. DÍAS, MODALIDAD Y TIPO DE PRESTACIÓN* — misma estructura de tabla que en §18.1/§18.2 (PRES: AP/DE, P/V, por día de la semana, filas DES/ALM/MER/CEN) — **sin** desglose de ingredientes ni menú.
- 2.2. Días y horario y tipo de prestación del llamado: ___ (campo libre)
- 2.3. ¿Tuvo problemas/dificultades en algunos de los siguientes temas?:
  - 2.3.1 Utilización de la tarjeta: ☐Sí ¿Cuál? ___　☐No
  - 2.3.2 Uso de la plataforma/carga de comprobantes: ☐Sí ¿Cuál? ___　☐No
  - 2.3.3 Compra de alimentos: ☐Sí ¿Cuál? ___　☐No
  - 2.3.4 Armado de menú: ☐Sí ¿Cuál? ___　☐No

**3. COMENTARIOS FINALES** *(Este espacio está reservado para que el entrevistador incluya los comentarios que considere pertinentes, teniendo en cuenta que el objetivo del llamado es evidenciar el funcionamiento general del comedor)* — campo libre.

Cierre: **Nombre y apellido del técnico** / **Firma** (una sola firma — no hay firma de entrevistado, consistente con la modalidad remota).

**Observación (posible inconsistencia del formulario original, a confirmar
si se replica en SISOC):** el encabezado trae la leyenda de registro
fotográfico ("se sugiere cocina, salón comedor, elaboración/servido, lugar
de guardo"), igual que en el formulario presencial de primera visita
(§18.1) — llamativo para una entrevista declarada como virtual/remota. No
se interpreta ni se corrige acá; se deja como observación para validar con
el usuario si corresponde mantenerla, quitarla, o si aplica solo cuando el
entrevistado puede enviar fotos por otro medio.

### 18.5) "ACTA COMPLEMENTARIA EXTRAORDINARIA"

**Archivo fuente:** `5-Acta complementaria - Extraordinaria-.pdf` — **Corresponde a §12 (Acta complementaria - extraordinaria).**

**FUNCIONAMIENTO** — *Marcar con una X según corresponda, en caso de no funcionar o cerrado indicar motivo.*
☐ Abierto, en funcionamiento　☐ Abierto, sin funcionamiento　☐ Cerrado
Motivo: ___

**1. DATOS DEL COMEDOR / MERENDERO**

*1.1 IDENTIFICACIÓN DEL COMEDOR/MERENDERO*
- 1.1.1 Fecha y horario de la visita (hh:mm) (Día/mes/año)
- 1.1.2 Nombre del Comedor/Merendero

> A diferencia de §18.1/§18.2/§18.4, **no** tiene campos de ID SISOC ni
> Código del Comedor.

*1.2 DOMICILIO DEL COMEDOR/MERENDERO*
- 1.2.1 Calle / 1.2.2 Número / 1.2.3 Barrio / 1.2.4 Localidad / 1.2.5 Municipio / 1.2.6 Departamento/Partido / 1.2.7 Provincia

*1.3 DATOS DEL ENTREVISTADO COMEDOR / MERENDERO*
- 1.3.1 Nombre y Apellido
- 1.3.2 Celular del referente / responsable

> A diferencia de los demás formularios de este anexo, **no** pide mail del
> referente.

- 1.3.3 Función que cumple en el comedor *(si cumple más de una función marcar las que corresponden)*: ☐Responsable de cocina ☐Cocinero/a ☐Responsable de compras ☐Referente del comedor ☐Otro (especificar)

**2. DATOS SOBRE LA PRESTACIÓN ALIMENTARIA**

*Resumen de prestaciones actuales y en lista de espera informadas por el comedor / merendero (Detalle de la información obtenida en la visita territorial)* — tabla con una columna por día de la semana (Lunes a Domingo), cada una con dos sub-columnas: **Cantidad actual de personas** y **Cantidad de personas en espera**, y filas Desayuno / Almuerzo / Merienda / Cena.

> El formulario trae impreso, debajo de la tabla, el texto: *"La presente
> Acta actualiza los datos de las prestaciones brindadas por el comedor en
> atención a la visita realizada en fecha: __ / __ / __ "*.

**3. OBSERVACIONES** — campo libre.

Cierre: **Nombre y Apellido del técnico** / **Firma** (una sola firma — no hay firma de entrevistado).

**Precisión sobre el disparador (más específica que la definición general de
§12):** por el texto impreso citado arriba, en su uso actual en papel esta
acta está pensada específicamente para **actualizar los datos de
prestaciones** (cantidad de personas actuales/en espera por día y tipo de
prestación) en referencia a una visita anterior ya realizada — no para
cualquier novedad genérica del comedor. Al definir el modelo en SISOC,
evaluar si el alcance funcional se mantiene acotado a prestaciones o se
amplía (la definición de §12 la describe en términos más generales,
"novedades o situaciones puntuales del comedor").
