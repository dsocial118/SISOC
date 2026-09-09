# Alcance de la primera versión

El documento describe **el sistema completo**. Este capítulo dice qué de eso se
construye primero.

Se separan a propósito: el análisis funcional describe cómo funciona el sistema y
lo valida la contraparte; el recorte depende de tiempo y recursos y puede cambiar
sin que el análisis cambie. Si se diseñara sólo para el recorte, cada agregado
obligaría a rehacer lo anterior.

---

## Dos recortes que no son el mismo

Conviene distinguirlos, porque se los confunde con facilidad:

| | Qué comprende |
|---|---|
| **Primera entrega técnica** | El componente de importación: recibir un archivo, validarlo contra la definición de la Capa 1 y almacenarlo ordenadamente en la Capa 2 |
| **Primera versión funcional** | Lo anterior **más** el informe de errores, la corrección de datos dentro del sistema y el circuito de presentación completo |

La primera es el escalón; la segunda, el piso sobre el que se para el período de
carga. La entrega técnica se describe abajo; la versión funcional, en
[01-alcance.md](01-alcance.md).

<!-- COMENTARIO: esta distinción resuelve una contradicción real que tenía el
     borrador funcional, donde el alcance prometía el circuito completo y el
     capítulo del MVP decía que no estaba. Ambos eran correctos, pero hablaban
     de recortes distintos. -->

---

## Qué se construye primero

Con el objetivo de comenzar la implementación lo antes posible, la primera
entrega **se concentra en el componente de importación**, sin abordar todavía las
complejidades del circuito de revisión y aprobación ni la consolidación
definitiva.

Este componente debe permitir que, a partir de un esquema de importación
previamente definido y versionado en la Capa 1, se reciban y procesen los
archivos Excel y se registren sus datos en la Capa 2.

En esta primera instancia el objetivo **no es resolver la vinculación o
consolidación definitiva** de personas, medidas, eventos y dispositivos, sino
contar con un mecanismo que permita **recibir, validar y almacenar ordenadamente**
la información importada.

Se propone implementarlo como un **componente independiente dentro de SISOC**, con
separación clara entre el mecanismo general de importación y las reglas
particulares de cada archivo de RUNAC. Esto permitiría que, en el futuro, el
componente se reutilice para otros proyectos que necesiten importar información a
partir de estructuras y reglas previamente definidas.

Esta primera versión permite **validar tempranamente el funcionamiento de las
Capas 1 y 2**, empezar a trabajar con archivos reales y avanzar después sobre el
circuito funcional y la base consolidada con mayor conocimiento de los datos
recibidos.

---

## Creación inicial de las tablas receptoras

Dado que los archivos Excel están en proceso de rediseño y no hay una versión
final, se propone **desacoplar el inicio del desarrollo de su estructura
definitiva**. Para ello, los archivos, hojas, campos, tipos de datos y
validaciones esperadas se definen en las tablas de configuración de la Capa 1.

A partir de esa definición se ejecuta, **por única vez**, un script de
inicialización que crea las tablas receptoras correspondientes en la Capa 2. De
este modo, cualquier modificación sobre los Excel antes de su aprobación
definitiva se resuelve actualizando la Capa 1 y volviendo a ejecutar el script.

Esto establece una correspondencia unívoca entre cada campo que se busca
importar, su ubicación en las tablas receptoras y las validaciones que deben
aplicarse, sin mantener el desarrollo atado a una versión provisoria.

El script es una **herramienta técnica de la implementación inicial** y no forma
parte de las funcionalidades operativas de SISOC. Una vez aprobada la estructura
definitiva y creadas las tablas, estas se consideran parte estable del modelo.

Si más adelante se modifica la estructura de los archivos, **la adecuación de las
tablas receptoras la realiza el equipo de desarrollo de manera controlada**. En
esta primera versión no se contempla automatizar modificaciones posteriores de la
estructura: agregaría una complejidad innecesaria para empezar a importar los
archivos actuales.

<!-- COMENTARIO: el modelo sí prevé el versionado de la estructura (ver
     04-modelo-de-datos.md). No hay contradicción: el modelo lo contempla, y esta
     primera versión no automatiza la migración de las tablas receptoras cuando
     nace una versión nueva. Esa parte queda a cargo del equipo. -->

---

## Importación

En esta versión la importación es **restrictiva**: si hay validaciones
bloqueantes se informan y quedan registradas, y **no hay importación parcial**.

---

## Qué entra y qué no

| | Primera versión | Etapa siguiente |
|---|---|---|
| Definición de archivos y reglas en la Capa 1 | ✓ | |
| Versionado de la estructura | parcial | automatización completa |
| Motor de importación con validaciones | ✓ | |
| Informes de errores | ✓ | |
| Corrección de datos dentro del sistema | ✓ | |
| Generación de plantillas desde el sistema | | ✓ |
| Roles y permisos definitivos | | ✓ |
| Circuito de revisión y presentación | | ✓ |
| Consolidación a la Capa 3 | | ✓ |
| Gestión continua entre períodos | | ✓ |
| Reportes y alertas | | ✓ |
| Conexión por API a sistemas provinciales | | evaluación |

<!-- COMENTARIO: el prototipo tiene implementado más que la primera versión: el
     circuito completo con los cuatro roles, la corrección de datos y los
     informes de errores. Está así a propósito: el prototipo existe para mostrar
     el circuito y destrabar definiciones, no para marcar el alcance del
     desarrollo. Lo que se construye en SISOC es lo que dice esta tabla. -->

---

## Cómo leer este recorte

Conviene distinguir tres situaciones, porque no se resuelven igual:

- **Confirmado.** Entra en la primera versión.
- **Candidato.** Entra *si* se resuelve determinada definición a tiempo. Es la
  columna que hace visible que algunas funcionalidades dependen de respuestas que
  no están del lado del equipo.
- **Etapa siguiente.** Queda fuera por decisión, no por falta de tiempo.

El recorte se va a mover: si una definición se destraba antes de lo previsto, se
mueve un renglón y no se reescribe el análisis.
