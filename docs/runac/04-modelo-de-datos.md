# Modelo de datos

La información atraviesa tres situaciones distintas antes de convertirse en un
dato consultable: lo que se espera recibir, lo que efectivamente llegó, y la
realidad que se quiere describir. Cada una tiene exigencias propias y no pueden
resolverse en una única estructura.

| | Qué contiene | Pregunta que responde |
|---|---|---|
| **Capa 1** | La definición de los archivos que se esperan y las reglas que deben cumplir | *¿Qué se espera recibir, y qué es correcto?* |
| **Capa 2** | Los archivos recibidos, sus validaciones, observaciones y correcciones | *¿Qué informó cada provincia en cada período?* |
| **Capa 3** | La base consolidada: personas, medidas, eventos y dispositivos | *¿Cuál es la situación, y cómo llegó a serlo?* |

Todas las tablas llevan el prefijo `runac_`, que es el comportamiento por defecto
de SISOC —el nombre de la aplicación encabeza el de cada tabla—, y dentro del
módulo el prefijo distingue la capa: `runac_c1_*`, `runac_c2_*`, `runac_c3_*`.

---

## Enfoque del diseño

El esquema **no contiene definiciones propias de RUNAC**. Las Capas 1 y 2 no
saben qué es una medida de protección, un dispositivo ni un niño: describen
archivos, campos, reglas, importaciones y observaciones. Sólo la Capa 3
representa el dominio específico del registro.

En consecuencia, el mecanismo es aplicable a **cualquier proceso que reúna
información periódica de jurisdicciones, áreas u organismos**, que es una
necesidad recurrente en el ámbito del CNCPS: se reciben planillas, se validan, se
corrigen, se presentan formalmente y se consolidan. Cambia el contenido, no el
circuito.

Tres consecuencias:

- **No se requiere modificar el código ante un cambio de estructura.** Definir la
  estructura como dato —en lugar de programarla— es lo que permite acompañar la
  evolución de las planillas sin desarrollos sucesivos.
- **Reduce el costo de los requerimientos futuros.** Otro programa que reciba
  información periódica usa el mismo mecanismo, definiendo sus archivos y reglas
  desde la administración.
- **Constituye el insumo de un desarrollo paralelo.** Puede dar origen a un
  **Módulo de Presentaciones Periódicas**: un panel para definir nuevos
  relevamientos sin desarrollo específico. Existe antecedente en SISOC: la
  Ticketera se construyó para un requerimiento puntual y después se generalizó.

---

## Capa 1 — Definición de los archivos esperados

Describe la estructura que deben tener los archivos de cada período y las reglas
que deben cumplir:

- qué archivos se esperan y en qué orden se importan;
- qué hojas contiene cada uno y dónde están los encabezados;
- qué campos, en qué orden y agrupados en qué dimensiones;
- tipo, longitud y obligatoriedad de cada dato;
- catálogos y valores admitidos;
- las reglas de validación con sus parámetros, su severidad y su mensaje.

**La lógica de validación reside en estas definiciones y no en el programa.** El
proceso de importación no conoce el MPI ni el MPE: lee la definición del período
y la aplica.

### Versionado de la estructura

Un archivo importado en el primer trimestre fue validado contra una definición
determinada. Si esa definición se modifica, deja de poder explicarse por qué ese
archivo se aceptó, o por qué se rechazó una fila.

El archivo y su estructura se separan:

```
runac_c1_archivo            La identidad del archivo: MPI, MPE, MPJ_DAE,
                            DISP_PENAL, DISP_SCP. No cambia nunca.
     │
runac_c1_archivo_version    Cada versión de la estructura, con su estado
     │                      (borrador, vigente, histórica).
     ├── hojas
     ├── dimensiones
     ├── campos
     └── reglas             Cuelgan de la versión, no del archivo.
```

Cada período registra **qué versión utiliza de cada archivo**:

| Período | MPI | MPE | MPJ_DAE | DISP_PENAL | DISP_SCP |
|---|---|---|---|---|---|
| 2026-T2 | v3 | v2 | v1 | v1 | v1 |
| 2026-T3 | v3 | v2 | v1 | v1 | v1 |
| 2026-T4 | **v4** | v2 | v1 | v1 | v1 |

Entre el segundo y el tercer trimestre no hubo cambios: usan las mismas versiones
y **no se duplica ninguna definición**. En el cuarto se modificó el MPI, de modo
que se creó la versión 4. Un archivo del segundo trimestre puede seguir
explicándose con la versión 3, que permanece intacta.

**Una versión ya utilizada por un período no se modifica.** Si hace falta un
cambio, se crea otra. La regla de que la definición no se altera con el período
abierto queda garantizada por el modelo y no por una restricción operativa.

El versionado se realiza **por archivo y no por hoja**, aun cuando un archivo
contenga varias —como MPJ y DAE—. Replicar la hoja que no cambió supone algunas
decenas de filas y evita que un mismo archivo tenga versiones distintas
conviviendo.

### Catálogos

Quedan **fuera del versionado**. Son listas vivas y en algunos casos extensas —el
nomenclador de localidades, entre otros—, de modo que replicarlas por período es
inviable y no aporta.

- las opciones se **agregan** cuando aparecen valores nuevos;
- se **dan de baja lógicamente** cuando dejan de admitirse, conservando el
  registro para que los datos anteriores sigan siendo legibles;
- **el código de cada opción permanece aunque cambie su denominación**: si
  *"Sin datos"* pasa a *"NS/NC"*, las series históricas no se rompen;
- cada opción registra **desde y hasta qué período estuvo vigente**.

Una lista que reaparece en varios archivos se reconoce como la misma y se define
en un único lugar, lo que evita versiones divergentes del mismo catálogo.

### Operación

Al habilitarse un nuevo período, el administrador declara si existen cambios
respecto del anterior.

- **Si no los hay**, el período apunta a las versiones vigentes. No se genera
  ninguna definición nueva.
- **Si los hay**, el sistema **copia la última versión** del archivo afectado y la
  abre para su edición. La versión anterior permanece intacta.

La nueva versión permanece en **borrador** mientras se edita, y pasa a **vigente**
al habilitarse la carga. La declaración queda registrada con usuario y fecha.

El versionado **no es visible para las jurisdicciones**: el operador carga sus
archivos y el sistema aplica la versión correspondiente.

---

## Capa 2 — Importación, validación y trabajo sobre los datos

Contiene la información tal como fue recibida de cada jurisdicción en cada
período, con el resultado de su validación, las observaciones y las correcciones.

### Tablas de control

Siete tablas fijas gobiernan el circuito, con independencia de los archivos:

| Tabla | Qué registra |
|---|---|
| `jurisdiccion` | Unidad que presenta, con su modalidad de trabajo |
| `periodo` | Los cortes |
| `periodo_archivo` | Qué versión de cada archivo rige en cada período |
| `presentacion` | La presentación de una jurisdicción, con su estado y su expediente |
| `importacion` | Cada intento, incluidos los fallidos. Nunca se elimina |
| `reglas_incumplidas` | Cada validación no superada, con su ubicación y severidad |
| `errores_de_importacion` | Por qué un archivo no pudo importarse |
| `observacion` | Los señalamientos del revisor nacional |
| `historial_cambios` | Las correcciones sobre los datos importados |

**La jurisdicción es una entidad, no un texto.** Es lo que permite que el mismo
mecanismo sirva a provincias, municipios u organismos.

### Tablas receptoras

Cada hoja de cada archivo tiene su tabla, **generada a partir de la Capa 1**. El
nombre no se guarda: se deduce por convención —archivo, versión y hoja—, y la
misma función la usan el que las crea y el que inserta.

Hay **una sola tabla por hoja**, no dos. Como la importación es restrictiva, un
archivo con errores bloqueantes no entra, así que todo dato incorporado pudo
convertirse a su tipo. El valor que provocó cada incumplimiento queda en
`reglas_incumplidas`, y los valores previos a cada corrección en
`historial_cambios`.

### Dos juegos de estados, separados

- **El estado de cada importación** —válida, anulada, fallida— describe qué
  ocurrió con un archivo.
- **El estado de la presentación** describe en qué punto del circuito está la
  jurisdicción.

Son planos distintos: una presentación puede tener importaciones anuladas y
fallidas y estar, aun así, en condiciones de cerrarse.

### Modalidades de trabajo

Esta capa admite dos modalidades, que **conviven y se eligen por jurisdicción**:

- **Presentación periódica.** La jurisdicción trabaja fuera de SISOC y aporta los
  archivos del período. Es la modalidad de la primera versión.
- **Gestión continua.** La jurisdicción registra sus novedades dentro de SISOC a
  medida que ocurren.

En ambos casos **la presentación es una fotografía**: al cierre se fija el estado
a la fecha establecida. Lo que cambia es cómo se llegó a ese estado.

La distinción tiene una consecuencia práctica: en modalidad de gestión continua,
una importación de reemplazo descartaría el registro acumulado de meses. La
modalidad determina si la importación **reemplaza** o **incorpora**.

<!-- COMENTARIO: la gestión continua no está implementada. Condiciona el diseño:
     la Capa 2 se concibe como espacio de trabajo permanente y no como depósito
     transitorio, y por eso la información no se descarta al consolidarse. -->

> **Definición pendiente.** Corresponde evaluar si se conserva una copia del
> archivo Excel tal como fue recibido, en un repositorio documental separado y
> con acceso restringido: constancia de la presentación, evidencia ante
> auditorías, documento asociado al trámite GDE.

<!-- COMENTARIO: parcialmente resuelto. La importación ya guarda la ubicación del
     archivo recibido (`ruta_archivo`), que es lo que permite devolverle al
     operador su propio Excel con las celdas marcadas. Falta decidir si además se
     conserva en un repositorio documental con retención definida. -->

---

## Capa 3 — Base consolidada

Una vez aceptada la presentación, los datos se incorporan a la base consolidada
para ser consultados por quienes tengan permiso.

**Cambia el eje.** Las dos capas anteriores se organizan por archivo y por
período: responden qué se esperaba recibir y qué informó cada jurisdicción en
cada corte. La Capa 3 se organiza **por objeto**, con independencia del archivo
del que provino cada dato y del período en que llegó. Un mismo chico informado en
cuatro archivos y en ocho presentaciones sucesivas es acá **un único registro con
su historia**.

### La identidad se separa de lo relevado

`runac_c3_persona` contiene **sólo la identidad**: el identificador de SISOC, el
vínculo con `ciudadanos`, el documento y el CUIL. Nada más.

Todo lo que las planillas relevan sobre alguien vive en su **caracterización**:
`nino_adolescente` o `referente_adulto`. Una misma persona puede tener las dos.

Esa separación resuelve un caso que de otro modo obligaría a duplicar: **un
hermano mayor puede ser a la vez referente de su hermano menor y estar alcanzado
por una medida propia**. Es una sola persona con dos caracterizaciones. Con los
datos de identidad repartidos dentro de cada una, quedaría registrada dos veces
sin forma de saber que es la misma.

### Una tabla de medida por tipo

`medida_mpi`, `medida_mpe`, `medida_mpj` y `medida_dae`, no una tabla genérica.
Su contenido no es comparable: la excepcional informa modalidad de cuidado y
adoptabilidad; la penal juvenil, causa y situación procesal; DAE, fuerza
interviniente y tiempo de permanencia. Reunirlas obligaría a un registro donde
cada fila usa una fracción de los campos.

Comparten el esqueleto: el chico, la jurisdicción, las fechas de inicio y cese,
el estado de vigencia y la presentación de la que provinieron.

**DAE es distinta de las otras tres**: describe un hecho ocurrido, no una
situación que evoluciona. Se acumula en lugar de actualizarse.

### Los dispositivos

Una tabla de **identificación común** —jurisdicción, denominación, tipo,
dependencia, localidad, dirección, teléfono, estado— que asigna un identificador
único cualquiera sea el tipo, y **una tabla por tipo** con el cuestionario propio
de cada uno. Las columnas de esas seis tablas se generan desde la definición de
la Capa 1, igual que las receptoras de la Capa 2.

Más `disp_alcance_territorial`, porque MPT, CAD y guardia informan **varias**
jurisdicciones de alcance: como campo de texto no se puede responder qué
dispositivos alcanzan a un municipio determinado.

### Normalización de los campos abiertos

`unidad_interviniente` es una tabla referencial que **no se completa por
adelantado**: se construye con lo que efectivamente se informa. El universo es
abierto —la intervención puede realizarse desde un servicio local, un equipo
territorial o un programa municipal— y un padrón cerrado exigiría un
mantenimiento que ninguna instancia puede sostener.

`unidad_alias` es el diccionario: asocia cada denominación recibida a una entrada
de esa tabla y **se perfecciona en cada importación**. Lo ya conocido se resuelve
solo; lo nuevo queda pendiente, y su resolución incorpora una entrada para la vez
siguiente.

### Cuatro tablas de trazabilidad

| Tabla | Qué responde |
|---|---|
| `origen` | De qué presentación, importación y fila salió cada dato |
| `cambio` | Qué cambió, desde qué valor y por qué |
| `precedencia` | Qué valor prevalece cuando dos archivos difieren |
| `coincidencia` | Identidades que no se pudieron decidir automáticamente |

**`cambio` no es un accesorio de auditoría: es la fuente de las series
históricas.** Como la base guarda una sola fila por chico con el dato vigente, el
estado a una fecha de corte anterior sólo se reconstruye desde ahí. Por eso
registra el valor **anterior** y no solamente que hubo un cambio.

<!-- COMENTARIO: el esquema está creado en la base (23 tablas, 45 claves
     foráneas) pero sin datos, y el proceso de consolidación no está
     implementado. La primera versión no lo incluye: ver
     09-alcance-primera-version.md. -->

### Historial de cambios: son dos, y no se superponen

| | Capa 2 | Capa 3 |
|---|---|---|
| Pregunta que responde | *"El Excel decía X y el operador puso Y"* | *"En el trimestre pasado el apellido era X y ahora es Y"* |
| Alcance | Dentro de una presentación | Cruza presentaciones, períodos y provincias |
| Para qué sirve | Evidencia del proceso de subsanación | Trazabilidad del dato consolidado |

Con una condición: el de la Capa 3 no repite la información, apunta al origen. Si
los dos guardan el mismo detalle, con el tiempo se despegan.
