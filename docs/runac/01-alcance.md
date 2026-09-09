# Alcance

## Objetivo

Conformar un **Registro Único Nominal Nacional dentro de SISOC** que se
constituya como pilar del RUNAC —Registro Único Nacional de Medidas de Protección
y Medidas Penales Juveniles—, permitiendo importar y procesar la información
provista por las provincias respecto de niños, niñas y adolescentes con medidas
de protección y medidas penales juveniles, en el marco del Programa Federal de
Protección de Niñez y Adolescencia (PFPNYA).

**Área requirente:** Dirección Nacional de Promoción y Protección Integral
(DNPYPI).

---

## Qué se necesita

SISOC debe transformar los archivos Excel provinciales en un registro ordenado y
relacionado: una misma persona puede tener varias medidas a lo largo del tiempo,
y una misma medida puede estar vinculada a un dispositivo determinado.

Se requiere **recibir, revisar, consolidar y consultar** la información que envían
las provincias, en una base de datos relacional que conserve el historial y
permita saber de dónde provino cada dato: provincia, período, archivo, hoja, fila
y versión.

El sistema debe permitir:

- cargar los archivos Excel sin modificar su estructura básica;
- detectar errores, campos incompletos, duplicados e inconsistencias;
- relacionar a cada niño o adolescente con sus medidas y, cuando corresponda, con
  un dispositivo;
- guardar las sucesivas presentaciones trimestrales de cada provincia;
- permitir la revisión nacional y la subsanación provincial;
- generar reportes, indicadores y alertas sin exponer datos identificatorios
  innecesariamente.

**No debe pensarse como una planilla en línea.**

---

## Los archivos que se reciben

| Archivo | Qué informa | Qué representa cada fila |
|---|---|---|
| **MPI** | Niños y adolescentes con medidas de protección integral | Un NyA con una MPI informada en el corte |
| **MPE** | NyA con medidas de protección excepcional y su modalidad de cuidado | Un NyA con una MPE informada en el corte |
| **MPJ** *(hoja del archivo MPJ DAE)* | NyA alcanzados por medidas penales juveniles | Un NyA con una medida penal o permanencia en dispositivo penal |
| **DAE** *(hoja del mismo archivo)* | Ingresos y egresos de CAD o guardias especializadas | Un evento de admisión o permanencia transitoria |
| **Dispositivos SCP** | Dispositivos de cuidado residencial | Un dispositivo residencial |
| **Dispositivos PENAL** | CRC, CRSC, MPT, CAD, guardias especializadas y categorías de prisión domiciliaria | Un dispositivo penal o equipo especializado, según la hoja |

Son **cinco archivos con once hojas de datos y 368 columnas en total**:

- **Tres archivos con las cuatro nóminas**: MPI y MPE en un archivo cada uno, y
  MPJ y DAE compartiendo un mismo libro en dos hojas.
- **Dos archivos de dispositivos**: el penal, con **seis** hojas según el tipo de
  dispositivo, y el de cuidado residencial, con una.

<!-- COMENTARIO: los números están verificados contra la Capa 1 cargada.
     Disp-Penal 121 campos en 6 hojas · Disp-SCP 61 · MPI 64 · MPE 41 ·
     MPJ_DAE 81 en 2 hojas. La hoja "categ prision domi" tiene sólo 3 columnas
     y por su nombre parece una tabla de categorías, pero es una hoja de datos:
     si se la excluyera serían 10 hojas y 365 columnas. -->

Que un archivo tenga seis hojas y otro una sola es lo que vuelve significativo el
orden de importación: no es una formalidad, es lo que permite saber en todo
momento qué entró y qué falta.

Las hojas denominadas *DESPLEGABLE*, *Desplegables* o *Categorías* no contienen
casos: son catálogos de opciones y se usan para construir las listas cerradas y
las reglas de validación.

---

## Cómo se relaciona cada archivo

| Archivo | Se vincula con |
|---|---|
| **MPI** | Una persona única y un episodio MPI. Cuando existe un programa, dispositivo o equipo formal, se relaciona con la unidad interviniente; si no, se conservan los datos del programa informados por la provincia |
| **MPE** | Una persona única, un episodio MPE y una modalidad de cuidado. Si es residencial, se enlaza con el registro maestro de dispositivos residenciales; si es familiar o de familia ampliada, corresponde el identificador de familia |
| **MPJ** | Una persona única, un episodio MPJ y el dispositivo penal correspondiente |
| **DAE** | Cada fila es un evento de ingreso y egreso. **No debe confundirse con el legajo de la persona ni con una medida penal prolongada.** Puede existir más de un evento para la misma persona |
| **Dispositivos** | Cada fila genera o actualiza un dispositivo único, que las nóminas referencian |

---

## Estructura mínima del registro

Para evitar duplicaciones y conservar el historial:

| Registro | Función |
|---|---|
| Jurisdicción y presentación | Identifica provincia, período de corte, fecha de presentación, archivo y versión |
| Persona / NyA | Identidad básica y un identificador interno único. **Una persona se registra una sola vez** |
| Medida o evento | Cada episodio MPI, MPE, MPJ o DAE con sus fechas y características. Una persona puede tener varios |
| Dispositivo | Registro maestro de residencias y dispositivos penales, con identificador único |
| Referente o familia | Referentes de MPI y familias vinculadas a modalidades de cuidado MPE |
| Observaciones y auditoría | Errores, observaciones, subsanaciones, decisiones y acciones de cada usuario |

**Relación principal:** provincia y período → persona → medida o evento →
dispositivo, referente o familia cuando corresponda.

**Identificadores mínimos:** identificador interno de persona, identificador
provincial de persona, de medida o evento, de dispositivo, de presentación y,
cuando corresponda, de familia.

---

## Criterio de aceptación

> El desarrollo será satisfactorio cuando una provincia pueda cargar las bases
> entregadas, recibir errores claros, corregir y presentar la información; y
> cuando Nación pueda revisarla, aceptarla y generar reportes sin duplicar
> personas ni dispositivos y con trazabilidad completa.

---

## Periodicidad

Actualización **trimestral**, parametrizable. El sistema conserva todas las
versiones y permite comparar el trimestre actual con el anterior.

---

## Fuera de alcance en esta etapa

Se identifican como ampliaciones posibles, no comprometidas:

- **Conexión por API a los sistemas provinciales.**
- **Gestión continua dentro de SISOC**, para que las provincias lleven su
  información día a día en lugar de aportar una fotografía periódica. Este
  esquema debe prever que existan *datos de presentación* y *datos de trabajo
  cotidiano*: se mantiene una instancia de presentación para armar el corte del
  período con datos verificados a una fecha determinada.

<!-- COMENTARIO: la segunda ya está contemplada en el diseño de la Capa 2, que
     se concibe como espacio de trabajo permanente. No está implementada, pero
     el modelo no la bloquea. Ver 04-modelo-de-datos.md. -->

---

## Entregables comprometidos

Del requerimiento original, a cargo del equipo:

- propuesta de arquitectura y modelo de datos → **[03](03-arquitectura.md)** y **[04](04-modelo-de-datos.md)**
- plantillas definitivas de importación y columnas obligatorias → **[08](08-analisis-de-las-planillas.md)**
- prototipo de pantallas de carga, revisión, observación y consulta → **implementado**
- matriz de reglas de validación y mensajes al usuario → **[07](07-reglas-de-validacion.md)**
- definición de roles, permisos y auditoría → **[02](02-actores-y-roles.md)**
- propuesta de reportes y alertas del MVP → pendiente
- plan de pruebas con al menos una provincia piloto → pendiente
- manual breve para usuarios provinciales y nacionales → pendiente
