# Análisis del diseño de las planillas actuales

Observaciones sobre el diseño de los archivos entregados, con el objetivo de
mejorar la calidad de los datos y facilitar la carga a las provincias. Cada una
incluye una propuesta de resolución.

**Estas propuestas modifican lo que el requerimiento define.** No se aplican sin
validación de la DNPYPI. El requerimiento lo establece: cualquier eliminación,
cambio de nombre, agrupación o modificación de opciones debe validarse
previamente.

---

## 1. Datos personales repetidos entre archivos

### Situación

Los cuatro archivos nominales —MPI, MPE, MPJ y DAE— incluyen cada uno los datos
personales completos del niño, niña o adolescente: identidad, educación, salud,
discapacidad y seguridad social. Un chico alcanzado por más de una medida se
informa completo en cada archivo, y también en cada período.

Tres efectos:

- **Multiplica el trabajo provincial.**
- **Genera datos contradictorios.** La misma persona puede tener apellido, fecha
  de nacimiento o nivel educativo distintos según el archivo, sin forma
  automatizada de saber cuál es el correcto.
- **Traslada el problema a la consolidación.**

El requerimiento establece en su estructura mínima que una persona *"se registra
una sola vez"*. Las plantillas actuales la registran hasta cuatro veces por
período.

### Alternativas

La elección corresponde a la DNPYPI, porque afecta el modo de trabajo de las
jurisdicciones. **Se recomienda consultar a las provincias si ya cuentan con un
universo consolidado de niños, niñas y adolescentes.**

**A — Conservar los archivos y definir un criterio de precedencia.** Cuando una
persona aparece en más de uno con datos distintos, SISOC aplica una regla: por
jerarquía fija entre archivos, por antigüedad (el último informado), o tomando
los datos de identidad de RENAPER cuando el documento esté disponible. Toda
diferencia queda en el historial, y un analista con permisos puede revisar la
decisión automática; el sistema conserva ese criterio para futuras importaciones.

*Ventaja:* no modifica plantillas ni modo de trabajo. Es la más rápida.
*Desventaja:* no elimina el trabajo duplicado ni las contradicciones; sólo define
cómo resolverlas.

**B — Archivo de universo separado.** Un archivo adicional con un registro por
persona y sus datos completos. Los archivos de medidas dejan de repetirlos y se
vinculan por el identificador provincial. Para evitar transcribirlo, la hoja de
desplegables de cada archivo de medidas incluye una lista con identificador y
nombre, que la provincia copia del universo.

*Ventaja:* elimina la duplicación y las contradicciones, conservando la
estructura de archivos separados.
*Desventaja:* la provincia debe copiar la lista de referencia en cada archivo.

**C — Archivo único de nóminas con hoja de universo.** Los cuatro archivos
nominales se consolidan en un libro con una hoja por tipo de medida, más una de
universo y otra de desplegables. Hay antecedente: MPJ y DAE ya se entregan juntos.

*Ventaja:* elimina la duplicación, no requiere copiar listas y reduce la cantidad
de archivos.
*Desventaja:* es el cambio de mayor alcance.

| | A | B | C |
|---|---|---|---|
| Modifica las plantillas | No | Sí | Sí, en profundidad |
| Elimina el trabajo duplicado | No | Sí | Sí |
| Elimina las contradicciones | No, las resuelve | Sí | Sí |
| Trabajo adicional de la provincia | Ninguno | Copiar la lista | Ninguno |
| Esfuerzo de adopción | Nulo | Medio | Alto |

**No son excluyentes en el tiempo:** puede adoptarse A para el primer período y
avanzar hacia B o C una vez que el circuito esté en funcionamiento.

<!-- COMENTARIO: el prototipo funciona hoy con los archivos como están, que
     equivale a la alternativa A sin criterio de precedencia implementado. Si se
     adopta B o C hay que rehacer plantillas y el orden de carga pasa a tres
     momentos.

     Límite técnico a tener presente: la validación de datos de Excel (los
     desplegables) NO funciona entre libros distintos, y una fórmula que busca
     datos en otro archivo se rompe en cuanto el archivo viaja por correo. Todo
     lo que deba ser desplegable tiene que vivir en el mismo libro. Por eso la
     alternativa B copia la lista en vez de referenciarla. -->

---

## 2. Vinculación entre medidas y dispositivos

### Qué archivos requieren vinculación

| Archivo | Se vincula con | Carácter |
|---|---|---|
| **MPI** | — | **No requiere vinculación con otro archivo.** El espacio o equipo interviniente se informa dentro del propio archivo |
| **MPE** | Dispositivos de cuidado residencial | **Condicional**, sólo si la modalidad es residencial. Si es familiar, corresponde el identificador de familia |
| **MPJ** | Dispositivos penales juveniles | **Obligatorio** |
| **DAE** | Dispositivos penales, hojas de CAD y guardias | **Obligatorio** |

### Situación

El requerimiento propone que SISOC asigne un identificador a cada dispositivo en
la carga inicial y que las provincias lo transcriban en las plantillas
siguientes.

Esa solución tiene un riesgo: transcribir un código en cada registro es la tarea
más expuesta a error humano, y **un error de tipeo puede apuntar a otro
dispositivo existente**, produciendo un vínculo incorrecto que el sistema no
puede detectar. Además obliga a consultar un listado externo mientras se completa
la planilla.

### Propuesta

Que el dispositivo se informe **por su nombre**, y que SISOC resuelva
internamente el identificador.

| | Ventajas | Desventajas |
|---|---|---|
| **A. Código transcrito** *(propuesta del requerimiento)* | Identificación exacta y estable aunque cambie la denominación | Transcripción manual en cada registro. Un tipeo puede apuntar a otro dispositivo sin que el sistema lo detecte |
| **B. Nombre validado por el sistema** *(propuesta)* | El operador reconoce nombres, no números. Sin transcripción. SISOC verifica contra los dispositivos ya cargados por esa jurisdicción | Requiere que el nombre sea único dentro de la provincia y que los dispositivos se carguen antes |

**Doble control**, con funciones distintas:

- **En la planilla**, la columna se completa desde una **lista desplegable** en la
  hoja de desplegables del propio archivo, que la provincia completa copiando los
  dispositivos de la base que carga previamente. Evita el error de escritura.
- **En el sistema**, SISOC valida el nombre contra los dispositivos efectivamente
  cargados por esa jurisdicción. Es lo que **garantiza** que el vínculo exista.

El primero es una ayuda; el segundo, la garantía. Un nombre que no corresponda a
ningún dispositivo cargado es **error bloqueante**.

### Definiciones asociadas

- El **nombre del dispositivo es único dentro de cada provincia**. Cuando dos
  compartan denominación, se los distingue incorporando la localidad.
- Las **nóminas se importan después de las bases de dispositivos**.
- Si aparece un dispositivo nuevo, se lo da de alta y se vuelve a importar la
  nómina. **No se prevé campo de texto libre**: reintroduce los duplicados que el
  mecanismo evita.
- SISOC almacena el identificador y conserva además el texto tal como fue
  informado, de modo que un cambio de denominación posterior no altere los
  registros anteriores.

### Ajuste requerido

Incorporar en la hoja de desplegables de **MPE, MPJ y DAE** un rango destinado a
los dispositivos de la jurisdicción, con validación de lista sobre la columna
correspondiente.

Cuando las plantillas se generen desde el sistema, ese rango se completará
automáticamente.

---

## 3. Identificador provincial de la persona

### Situación

El requerimiento lo incluye entre los identificadores mínimos **recomendados**.
Las planillas no lo establecen como obligatorio ni definen sus condiciones.

### Por qué es determinante

Cumple dos funciones que ningún otro campo cubre:

- **Permite reconocer a la misma persona entre presentaciones sucesivas cuando no
  cuenta con DNI.** Sin otro identificador, cada período la registraría como una
  persona distinta.
- **Es la clave que vincula el universo con las medidas**, en las alternativas B
  y C del apartado 1.

### Propuesta

Que sea **obligatorio en todos los archivos nominales**. Para cumplir su función
debe reunir dos condiciones:

- **Estable en el tiempo.** La misma persona conserva el mismo identificador en
  todas las entregas. Un código que se genere nuevamente en cada corte no sirve:
  cada período la registraría como alguien distinto.
- **Único dentro de la jurisdicción.**

En términos de validación: campo obligatorio con efecto bloqueante, y unicidad
dentro del archivo.

> **Definición pendiente.** ¿Las jurisdicciones cuentan hoy con un identificador
> propio y estable para cada niño, niña o adolescente, o el número se genera al
> completar la planilla? En caso de no existir, corresponde definir cómo se
> construye y quién garantiza su permanencia entre períodos.

---

## 4. Identificador de familia y referente del cuidado

### Situación

Cuando la modalidad de cuidado de una MPE es familiar o de familia ampliada, la
medida no se vincula a un dispositivo sino a la familia de acogimiento. El
requerimiento establece que debe conservarse el identificador de familia.

La planilla MPE prevé cuatro campos —*ID familia*, *Familia*, *ID familia
ampliada*, *Familia ampliada*—, ninguno obligatorio, y no existe un archivo
maestro de familias.

<!-- COMENTARIO: verificado sobre la Capa 1 cargada: tres de esos cuatro campos
     están tipados como FECHA (columnas AC, AD y AE del MPE). Es el mismo
     problema de formato que afecta a 33 columnas de la hoja DAE. -->

### Requerimiento funcional adicional

La información sobre la familia tiene una finalidad concreta: **verificar que la
asignación correspondiente al niño, niña o adolescente sea percibida por quien
efectivamente ejerce su cuidado**, y no por su familia de origen cuando ya no
convive con ella.

Ese control exige identificar a **al menos un adulto de la familia de acogimiento
con su documento**, porque el cruce con seguridad social se realiza por persona.

### Propuesta

Registrar al **adulto referente del cuidado**, con tipo y número de documento.
Cumple dos funciones a la vez:

- **Identifica a la familia.** Su documento puede usarse como identificador,
  evitando crear un código adicional y garantizando estabilidad entre períodos
  sin depender de un criterio de asignación provincial.
- **Habilita el control de la asignación.**

Cuando varios niños estén acogidos por la misma familia, el identificador se
repite entre registros: es lo que permite reconocer grupos de hermanos y no
contarlos como acogimientos distintos.

El adulto referente **integra el universo de personas**, junto con los niños y los
referentes adultos de MPI.

### Ajustes requeridos

- Incorporar **tipo y número de documento del adulto referente**, obligatorios
  cuando la modalidad es familiar o de familia ampliada.
- **Corregir el tipo de dato** de los campos *Familia*, *ID familia ampliada* y
  *Familia ampliada*, hoy definidos como fecha.
- Definir la obligatoriedad condicionada a la modalidad informada.

> **Definición pendiente.** ¿Debe registrarse un único adulto referente por
> familia, o corresponde admitir más de uno? El control se realiza sobre la
> persona titular, que puede no ser la única a cargo del cuidado.

> **Definición pendiente.** El registro de datos identificatorios de adultos que
> no son destinatarios del programa requiere definir su tratamiento en el marco
> del régimen de confidencialidad y de la finalidad declarada.

<!-- COMENTARIO: para el cruce con seguridad social sirve el CUIL, no el
     documento. Si sólo se informa el documento, el sistema tiene que derivar el
     CUIL y eso no siempre es unívoco. Evaluar si conviene pedir directamente el
     CUIL o resolverlo contra RENAPER al importar. -->

---

## 5. Universo de medidas y fechas de finalización

### Composición del período

El requerimiento no precisa qué medidas integran cada corte. Se propone:
**integran el período todas las medidas y eventos que estuvieron vigentes en
algún momento del intervalo informado**, con independencia de cuándo se hayan
iniciado.

- una medida iniciada antes y aún vigente **integra el corte**;
- una iniciada antes y finalizada dentro del corte **lo integra**, con su fecha de
  finalización;
- una iniciada y finalizada dentro del corte **lo integra**;
- una finalizada antes del inicio del intervalo **no lo integra**.

### Fechas de finalización ausentes

Este criterio requiere que cada medida pueda informar su finalización, y hoy eso
no es posible en dos de los cuatro archivos:

| Archivo | Situación |
|---|---|
| **MPI** | Informa la fecha de la medida y las **causas de su cese**, pero **no la fecha del cese** |
| **MPE** | Informa la fecha de inicio y los **días de permanencia**, pero **no la fecha de finalización** |
| **MPJ** | Informa fecha de ingreso y de egreso |
| **DAE** | Informa fecha y hora de ingreso y de egreso |

En MPI la ausencia es contradictoria: se pregunta por qué cesó la medida sin
registrar cuándo. Una medida con causa de cese informada y sin fecha no puede
ubicarse en el tiempo ni atribuirse a un período.

En MPE, los **días de permanencia no sustituyen a la fecha de finalización**: es
un valor calculado que varía día a día, informa la permanencia al momento del
relevamiento y no permite reconstruir la serie histórica. Además obliga a la
provincia a recalcularlo en cada corte.

### Propuesta

- Incorporar **fecha de cese** en MPI y **fecha de finalización** en MPE, en ambos
  casos como campo no obligatorio: vacío significa que la medida continúa vigente.
- Conservar los **días de permanencia** como campo **calculado por el sistema** a
  partir de las fechas, y no como dato a completar.
- Explicitar en las instrucciones el criterio de composición del período.

Con las fechas disponibles, el sistema determina por sí mismo qué medidas
estuvieron vigentes en cada corte, y la provincia deja de tener que interpretarlo.

Se habilitan además dos validaciones hoy imposibles: que la finalización sea
posterior al inicio, y que la medida se superponga con el período informado.

---

## 6. Identificación de localidades

### Situación

Los archivos requieren informar localidades en distintos campos sin criterio
unívoco de identificación. Una misma localidad puede escribirse de formas
distintas entre archivos, entre provincias y entre períodos, lo que impide
agrupar información territorial de manera confiable.

### Propuesta

Adoptar un **nomenclador oficial de localidades** como referencia común,
identificando cada una por un código y no por su denominación escrita.

Se propone **BAHRA** —Base de Asentamientos Humanos de la República Argentina—,
por ser la referencia oficial de asentamientos del país y la que las
jurisdicciones ya utilizan.

La identificación se realiza mediante la combinación de **código de provincia y
código de localidad**, que garantiza unicidad a nivel nacional.

Cada plantilla incluye en su hoja de desplegables **únicamente las localidades de
la provincia que corresponde**, lo que reduce la lista y elimina la posibilidad de
informar una localidad de otra jurisdicción.

**Si el nomenclador no se adopta**, será necesario construir y mantener un
diccionario de equivalencias que relacione cada variante de escritura con una
localidad única. Ese diccionario requiere revisión manual permanente y crece con
cada período.

> **Definición pendiente.** ¿Se adopta BAHRA como nomenclador de referencia? En
> caso afirmativo, corresponde confirmar que las jurisdicciones puedan informar
> sus registros con esa codificación.

<!-- COMENTARIO: verificado sobre el código de SISOC: core.Provincia,
     core.Municipio y core.Localidad tienen sólo un nombre en texto libre, sin
     código INDEC ni BAHRA. Si RUNAC adopta un nomenclador va a tener un
     catálogo territorial más preciso que el resto del sistema, y eso hay que
     resolverlo al integrar: o RUNAC mantiene el suyo, o se propone incorporar el
     código a core, que sería un cambio de kernel con su propia decisión. -->

---

## 7. Otras observaciones sobre las planillas

Surgen del relevamiento automático de los cinco archivos entregados. Cada una
requiere definición campo por campo, que se documenta en la matriz de reglas.

- **Ninguna planilla marca los campos obligatorios.**
- **35 listas se llaman igual y tienen contenido distinto** entre archivos. El
  listado de provincias aparece con 24 valores en unos archivos y 25 en otros.
- **16 catálogos se comparten** entre archivos y podrían unificarse. El de países,
  con 247 valores, aparece en tres.
- **En la hoja DAE hay formato de fecha aplicado a 33 columnas**, incluidas Género
  y País de nacimiento: alguien formateó la hoja entera.
- **Campos de provincia redundantes** en el archivo de dispositivos: la provincia
  del dispositivo se deriva de quién presenta, pero *Provincia (NyA)* y *Provincia
  del referente* no son redundantes —un chico puede estar alojado en otra
  jurisdicción o tener un referente que vive en otra.

<!-- COMENTARIO: 57 incongruencias detectadas sólo en el MPI. El detalle completo
     campo por campo está en los informes de anomalías que genera el análisis
     automático, y alimenta la matriz de reglas de validación. -->

---

## 8. Lo que ya está resuelto

Conviene decirlo antes que los problemas, porque es lo que hace posible todo lo
demás: **22 campos se relevan con el mismo nombre en los cuatro archivos
nominales** —apellidos, nombres, documento, situación de documentación, fecha de
nacimiento, género, país, nivel educativo, cobertura de salud, discapacidad y
varios más—.

No son cuatro relevamientos distintos: es el mismo, repetido cuatro veces. Eso es
lo que permite construir un total nacional sobre esas variables, y **ya está
resuelto**. Lo que sigue son los casos donde todavía no.

<!-- COMENTARIO: 22 es el recuento por nombre técnico en las cuatro hojas
     nominales. El borrador funcional menciona 17, que son los campos del chico:
     ambos son correctos, con alcances distintos. -->

---

## 9. Asimetrías entre archivos

### La misma pregunta con dos nombres

| Concepto | En un archivo | En los otros |
|---|---|---|
| Asistencia a la escuela | `asistencia_escolar` — MPI | `asiste_a_institucion_educativa` — MPE, MPJ, DAE |
| Pertenencia a pueblo originario | `pertenece_a_pueblo_originario` — MPE | `se_identifica_con_algun_pueblo_originario` — MPI, MPJ, DAE |

Con dos nombres quedan como dos campos distintos y no se puede construir una
serie ni un total nacional sobre ellos. Es un cambio de rótulo.

### Campos que están en unos archivos y no en otros

| Campo | Está en | Falta en |
|---|---|---|
| Nº de CUIL | MPI, MPE | MPJ, DAE |
| Asignación Universal por Hijo | MPJ | MPI, MPE, DAE |
| Seguridad social | MPI | MPE, MPJ, DAE |
| Problemática de salud | MPI | MPE, MPJ, DAE |

La consecuencia es acotada y conviene decirla como es: cualquier reporte sobre
esas variables sólo puede hacerse sobre el subconjunto de chicos que aparece en
el archivo que las pregunta.

<!-- COMENTARIO: es un pedido CONDICIONAL, no una omisión. Puede haber razones
     para preguntar la AUH en penal juvenil y no en protección integral.
     Conviene preguntar antes de pedir que se agreguen: son cuatro campos por
     tres archivos, o sea trabajo de carga real en cada provincia. -->

### Falta el identificador del NyA en el MPI

Está en MPE, MPJ y DAE —columna G de cada uno— y **no está en MPI**, que es el
padrón más numeroso. Ver el apartado 3.

---

## 10. Estructura de las planillas de dispositivos

**CRC y CRSC piden exactamente los mismos 36 campos**, con los mismos nombres. La
única diferencia entre un centro de régimen cerrado y uno semicerrado es en qué
hoja se carga.

**Los 9 campos de «Guardia Comisaría» están todos en CAD**, sin ninguno propio. Y
es **la única de las seis hojas sin Localidad ni Dirección**, siendo que los
reportes previstos piden eventos por dependencia: sin localidad no se puede
ubicar geográficamente un ingreso.

<!-- COMENTARIO: las dos primeras se llevan como CONSULTA, no como defecto.
     Que CRC y CRSC sean idénticas puede ser deliberado: si el objetivo es
     comparar los dos regímenes, tener los mismos campos es lo correcto. Lo
     único concreto es la falta de localidad y dirección en Guardia. -->

**El residencial comparte con los penales sólo 5 de sus 61 campos**, y son los de
identificación. Es correcto: son instrumentos que describen realidades distintas.
Se anota para que no se intente unificarlos.

---

## 11. Las listas de Sí / No y la opción que falta

**83 campos de cuatro archivos** comparten una lista con dos valores: Sí y No.

No hay forma de decir *"no lo sé"*. Una jurisdicción que no tiene el dato sólo
puede poner **No** o dejar vacío, y las dos cosas se confunden con la respuesta
real.

Se propone agregar **«Sin datos»**, que es el término que **las propias planillas
ya usan** en otros campos: *¿Presenta alguna discapacidad?*, *¿Posee CUD?* y
*Cobertura salud* lo ofrecen. El criterio existe; no se aplicó a estos 83.

<!-- COMENTARIO: aplicado en la definición de la Capa 1 y en las plantillas que
     genera el sistema. Al hacerlo, la lista quedó idéntica a la de
     "¿Presenta alguna discapacidad?", lo que confirma que el término elegido
     era el que ellos ya usaban. -->

---

## 12. Erratas de escritura

- **«Nombre del dispositvo»**, sin la *i*, en las **siete** hojas de los dos
  archivos de dispositivos.
- **«alcancce territorial»**, con tres *c*, en CAD y en Guardia Comisaría.
- **«El dipositivo participa…»** en Disp-SCP.

Se corrigen una vez y no vuelven a aparecer, porque las plantillas pasan a
generarse desde la definición.
