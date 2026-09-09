# Proceso de importación

## Plantillas del período

Cada período de carga se realiza sobre una **estructura de archivos definida y
estable**. Una vez habilitada la carga, esa estructura no se modifica hasta el
cierre: alguna provincia pudo haber importado con la versión vigente al comenzar.

En la etapa actual las plantillas las provee la DNPYPI, y SISOC verifica que los
archivos recibidos se correspondan con la estructura declarada.

En una etapa posterior las plantillas se generarán desde el sistema a partir de
esa misma definición. Ello garantiza que la planilla que completa la provincia y
la que el sistema espera sean la misma, e incorpora automáticamente las listas
desplegables vigentes, los campos obligatorios señalados y las localidades y
dispositivos de cada jurisdicción.

> **Definición pendiente.** ¿Corresponde que la plantilla se distribuya
> nuevamente en cada período, aun cuando la estructura no haya cambiado? Las
> tablas de referencia pueden variar, y una planilla desactualizada ofrece
> valores que el sistema ya no admite.

<!-- COMENTARIO: la generación de plantillas desde el sistema ya está
     implementada en el prototipo y probada sobre los cinco archivos: título,
     grupos de campos, listas desplegables vigentes, obligatorios marcados, una
     hoja de instrucciones con la ayuda de cada campo y un comentario en cada
     título de columna. -->

---

## Modalidad de carga

Los archivos **se cargan de a uno**, indicando el operador de qué archivo se
trata al momento de subirlo. No se prevé, en esta etapa, la selección de una
carpeta con carga conjunta.

Fundamento:

- El operador declara qué archivo está cargando, de modo que **el sistema no
  necesita deducirlo del nombre**. Se elimina una causa de rechazo que no aporta
  al control de la información.
- Permite **volver a importar un solo archivo** cuando se corrige uno de ellos,
  sin disponer del conjunto completo.
- **El orden lo controla el sistema, no el operador**: si se intenta cargar un
  archivo cuyas dependencias no fueron cargadas, la operación se rechaza
  indicando qué falta.
- No depende de funciones de selección de carpetas, cuyo comportamiento varía
  según el navegador y suele estar restringido en equipos de organismos públicos.

El sistema informa en todo momento qué archivos fueron cargados y cuáles restan.

La carga conjunta mediante carpeta se evalúa para una etapa posterior. En ese
esquema el nombre del archivo pasa a ser el único modo de reconocerlo, y su
cumplimiento se vuelve obligatorio.

---

## Nombre del archivo

Se propone un formato de denominación uniforme, por ejemplo:

```
MPI_2026_T1_Chubut.xlsx
```

Es decir: código del archivo, año, período y jurisdicción.

Dado que el operador indica qué archivo carga, la denominación **no condiciona la
importación**: cumple tres funciones.

- Facilita la identificación durante la carga y permite a las jurisdicciones
  ordenar sus archivos y referirse a ellos sin ambigüedad.
- Queda registrada en la trazabilidad de cada importación.
- Habilita una **advertencia temprana**: si el nombre no se corresponde con el
  período o la jurisdicción en curso, el sistema lo señala antes de procesar. Es
  advertencia y no rechazo: el contenido puede ser correcto aunque el archivo
  esté mal nombrado.

---

## Control de admisión

Antes de procesar el contenido, SISOC verifica que el archivo se corresponda con
la estructura del período:

- que las **hojas** sean las esperadas y estén denominadas como fue definido;
- que los **nombres de las columnas** coincidan exactamente;
- que el **orden de las columnas** sea el establecido.

La primera fila de cada hoja debe contener los nombres de los campos exactamente
como fueron definidos.

Si alguna condición no se cumple, **no se realiza importación alguna**: el archivo
se rechaza por completo y el sistema informa qué no coincide. Esto evita que un
archivo incorrecto ingrese parcialmente y deba deshacerse después.

El rechazo queda registrado como **intento fallido**, con el archivo, el usuario,
la fecha y el motivo. Un archivo equivocado suele fallar por varias razones a la
vez: **se informan todas juntas**, para corregir una sola vez.

---

## Orden de importación

Los archivos se importan en un orden determinado, porque unos referencian a otros:

- las **bases de dispositivos** se cargan antes que las nóminas que los
  referencian;
- **MPE** requiere los dispositivos de cuidado residencial;
- **MPJ y DAE** requieren los dispositivos penales.

El operador no necesita recordar la secuencia: si intenta cargar un archivo cuyas
dependencias faltan, la operación se rechaza indicando cuáles.

<!-- COMENTARIO: en el prototipo la dependencia se deriva del orden de
     importación declarado en la Capa 1, y eso encadena todo con todo: DISP_SCP
     queda bloqueado por DISP_PENAL aunque sean independientes entre sí.
     Corresponde declarar las dependencias reales en la Capa 1 en lugar de
     inferirlas del orden. -->

Si se adopta un archivo de universo de personas, el orden comprende tres
momentos: dispositivos, universo y, por último, medidas y eventos.

---

## Alcance de la importación

Ante un archivo con errores bloqueantes existen dos criterios:

**A. Importación parcial o iterada.** Se importan los registros que superan las
validaciones y se rechazan los restantes.

**B. Importación restrictiva.** El archivo se importa únicamente cuando la
totalidad de sus registros supera las validaciones bloqueantes.

**Se adopta la alternativa B**, por tres motivos:

- **Consistencia temporal.** La información de un período corresponde a un mismo
  momento y no a cargas sucesivas separadas por días o semanas.
- **Ausencia de duplicados por reintento.** En la modalidad parcial la provincia
  debería cargar sólo los registros que faltan; si vuelve a subir el archivo
  completo —lo más probable—, el sistema necesita distinguir cuáles ya entraron,
  lo que exige un identificador de registro confiable que hoy las planillas no
  garantizan.
- **La desventaja está acotada.** El sistema informa cada error con su archivo,
  hoja, fila, columna y motivo: la provincia sabe con precisión qué corregir.

Un error bloqueante impide la importación completa y se corrige en la planilla.
Las advertencias no la impiden y se resuelven dentro del sistema.

---

## Corrección de datos dentro del sistema

Es la segunda forma del paso 5 del circuito, y la que evita que cada advertencia
obligue a rehacer el Excel.

- Se corrige **campo por campo**, sobre los datos ya importados.
- Cada corrección **respeta el tipo declarado en la Capa 1**: una fecha tiene que
  ser una fecha, un valor de catálogo tiene que estar entre los admitidos, un
  campo obligatorio no puede quedar vacío. Lo que no cumple, no se guarda.
- **Toda edición queda registrada** con usuario, fecha, valor anterior y valor
  nuevo.
- **Sólo la jurisdicción edita.** El nivel nacional observa.
- **Sólo mientras la carga está abierta.** Con la carga cerrada, primero hay que
  reabrirla.

---

## Trazabilidad y versiones

El requerimiento solicita poder establecer el origen de cada dato: provincia,
período, archivo, hoja, fila y versión. SISOC conserva de cada importación:

- el **archivo** cargado y su denominación original;
- la **fecha y hora** de carga y el **usuario**;
- la **hoja** y la **fila** de la que proviene cada registro;
- el **estado**: válida, anulada o fallida.

Cuando un archivo se importa nuevamente, la importación anterior **no se
elimina**: queda registrada como anulada, con quién la reemplazó y cuándo. Los
intentos rechazados en el control de admisión se registran como fallidos.

Toda edición posterior se conserva con usuario, fecha, valor anterior y nuevo. El
dato consolidado puede reconstruirse hasta su origen.

**Las versiones corresponden a la presentación**, no al archivo. Cada vez que una
presentación es retirada y vuelta a presentar, se genera una nueva versión, y la
anterior se conserva con sus observaciones.

---

## Informes de errores

El operador corrige **en el Excel**, no en la pantalla. Por eso hay dos salidas:

1. **Planilla de errores.** Un Excel nuevo, con portada de resumen, una hoja por
   cada hoja del archivo y una fila por error con su celda, su valor y qué
   corregir.
2. **El propio archivo con las celdas marcadas.** El mismo Excel que subió el
   operador, con las celdas problemáticas pintadas —rojo bloqueante, amarillo
   advertencia— y un comentario en cada una explicando qué corregir. Se le agrega
   adelante una hoja con instrucciones.

La segunda es la que sirve para trabajar: se abre, se ve qué está mal y dónde, se
corrige y se vuelve a importar.
