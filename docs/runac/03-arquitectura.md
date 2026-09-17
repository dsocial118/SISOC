# Arquitectura

RUNAC **no es un sistema**: es una **implementación** de un módulo reusable.
Entenderlo en esos términos es lo que explica casi todas las decisiones que
siguen.

```
MIR      el módulo. Define qué archivo se espera, lo recibe, lo valida,
         permite corregirlo y lo consolida. No sabe qué es una MPI.
RUNAC    una implementación: su definición, sus usuarios, sus datos.
```

MIR —**Módulo de Importaciones Recurrentes**— es un nombre interno, para el
equipo. Hacia afuera cada implementación lleva el suyo: hoy RUNAC.

## Por qué el módulo no conoce el negocio

La definición de cada archivo —hojas, columnas, tipos, listas de valores y
reglas de validación— **vive en filas de la base**, no en el código. El motor
las lee y las ejecuta.

Eso no es una aspiración: es verificable. De las menciones a «runac» en
`services/motor/`, todas son nombres de tabla o comentarios. Se buscó lógica de
negocio —MPI, MPE, dispositivos, niño, medida de protección— y lo único que
aparece es un ejemplo dentro de un comentario.

La consecuencia práctica: **cuando una provincia cambia una planilla, se cambian
datos, no programas**. Y el día que otro programa reciba novedades periódicas de
las jurisdicciones, el motor sirve sin tocarlo.

---

## Las próximas implementaciones, con nombre

No es una hipótesis. En la reunión del **27 de agosto de 2026** se planteó
incorporar a SISOC tres programas más, interrelacionados con RUNAC:

| Programa | Universo | Cómo se gestiona hoy |
|---|---|---|
| **Decreto 5/2023** | El mismo que el MPE | Nómina en Excel |
| **PAE** — Programa de Acompañamiento para el Egreso | El mismo que el MPE | Excel y PDF por TAD |
| **RENNYA** | Distinto: NyA que sufrieron violencia intrafamiliar o un femicidio. Pueden estar en el MPE, pero no es excluyente | Excel, ~1.400 casos |

**Dos de los tres comparten universo con RUNAC.** El MPE ya se recibe: las mismas
provincias, el mismo período, la misma persona. Eso es lo que vuelve razonable
que compartan motor y no que se construyan tres veces.

### Qué de esto cubre el módulo tal como está

La minuta describe, sin nombrarlo, el circuito que MIR ya hace:

> «En una segunda instancia las provincias serán las que cargarán las novedades.
> Queda definir si se remite nómina completa o altas, bajas y novedades. La
> información podría ser adjuntada como csv.»

Recibir un archivo periódico de cada jurisdicción, validarlo contra una
definición, devolver los errores y consolidarlo **es exactamente el motor**.
Cambia el contenido, no el mecanismo: son filas nuevas en la Capa 1.

### Y qué no cubre, que es lo que hay que estimar

- **Documentos adjuntos con vigencia.** DDJJ de responsables de cobro,
  constancias de alumno regular. Hoy llegan como PDF sin identificar y se
  verifican a mano, periódicamente. El módulo recibe planillas, no expedientes.
- **Alertas por el paso del tiempo.** «Alguien está en etapa 1, cumplió 18 y la
  provincia no pidió el pase a etapa 2.» Las reglas de MIR validan **una fila
  contra su definición**, no el estado de una persona a lo largo del tiempo.
- **RENNYA no encaja en el molde.** No participan las provincias: es una gestión
  tripartita entre ANSES, el Ministerio de Justicia y la SNNAyF, caso por caso y
  con un trámite de 140 días hábiles. Eso es gestión de expedientes, no
  importación recurrente. Conviene decirlo ahora y no descubrirlo después.

### Lo que esto cambia para el diseño

Nada, y ése es el punto: las condiciones para que sirvan ya están —cada
implementación con su definición y sus datos separados, y el motor sin lógica de
ninguna—. Lo que sí adelanta es **la decisión de una base o varias**, más abajo:
con RUNAC sola no se nota; con cuatro programas compartiendo universo, sí.

<!-- COMENTARIO: el requerimiento técnico que acompaña a la minuta es de mayo de
     2026 y estaba en revisión al 27 de agosto. Los números y las etapas de acá
     salen de la minuta, no del requerimiento. Material en
     `C:\CNCPS\RUNAC\Dec5-RENNYA-PAE\`. Chubut sería el piloto: está por firmar
     convenio, y en total serían diez provincias. -->

---

## Cómo se construye

**Hoy: fuera del repositorio, y funcionando.** Se trabaja sobre una
implementación navegable con base MySQL propia, que se clona y se levanta con
dos comandos. Se arrancó afuera por dos motivos que siguen vigentes: las
planillas provinciales y el circuito cambian seguido, y modificar el
repositorio por cada ajuste implica migraciones y revisiones que no aportan
mientras el diseño no esté cerrado.

Mientras esté afuera trabaja **exclusivamente con datos ficticios**, con aviso
visible en pantalla. Las demostraciones se publican temporalmente con ngrok,
siempre con acceso por usuario y contraseña.

**Después: integración.** Cuando la contraparte dé el visto bueno, el código y
las tablas se incorporan a SISOC.

<!-- COMENTARIO: "PWA" se usa en el proyecto como sinónimo de "aplicación web
     autónoma y fácil de mostrar". Se descartó como requisito técnico: RUNAC no
     tiene caso de uso sin conexión —subir un Excel la requiere— y la app `pwa`
     de SISOC es el backend de una app móvil, sin service worker ni manifest. -->

---

## Qué implica la integración

Al incorporarse al repositorio, el módulo queda sujeto a las reglas que SISOC
aplica a todo módulo nuevo (`docs/ia/MODULAR_BOUNDARIES.md`):

- se define el **nombre interno de la aplicación una sola vez**, porque después
  no puede modificarse sin renombrar todas sus tablas;
- se publica una **interfaz propia** (`api.py`) para que otros módulos lo
  consulten sin acceder a sus tablas;
- se declara su **contrato de dependencias** en el control automático de
  arquitectura, que bloquea la incorporación de código si se incumple;
- las **migraciones son aditivas** y coordinadas.

### Ficha de clasificación

| Campo | Valor |
|---|---|
| Nombre del dominio | `mir` |
| Clasificación | **Vertical extraíble.** No es cambio de kernel: no toca `Ciudadano` ni los domicilios embebidos. No es parte de un contexto existente: padrón y dispositivos propios |
| Entidades propias | Padrón (persona, dispositivo, familia), eventos (medida, DAE) y las tres capas |
| Dependencias al kernel | `ciudadanos.Ciudadano` **por vínculo opcional**, nunca obligatorio. Territorio a confirmar según el nomenclador |
| Dependencias a otros verticales | Ninguna. Los dispositivos son propios: no requiere fachada de `dispositivos` |

---

## Nomenclatura de tablas, y una pregunta que hay que responder antes de integrar

Todas las tablas llevan el prefijo **`mir_`**, y dentro del módulo el prefijo
distingue las tres capas:

- `mir_c1_*` — definición de los archivos esperados y sus reglas
- `mir_c2_*` — importaciones, datos recibidos y gestión de observaciones
- `mir_c3_*` — base consolidada

El prefijo dice el nombre del **módulo**, no el de la implementación. Se
renombró desde `runac_` a propósito y antes de integrar, justamente porque
después «no puede modificarse sin renombrar todas sus tablas».

> **Definición pendiente, y hay que tomarla antes de integrar.**
>
> Hoy, fuera del repositorio, **cada implementación tiene su propia base de
> datos**. Eso es lo que permite que dos implementaciones no se pisen los
> catálogos ni las definiciones.
>
> SISOC es **una sola base**. Al integrar, las implementaciones dejan de
> separarse por base y tienen que separarse por dato: una columna que diga a qué
> implementación pertenece cada archivo, cada período y cada presentación.
>
> No es difícil, pero **cambia el modelo** y conviene decidirlo antes de escribir
> las migraciones, no después. Mientras haya una sola implementación la
> diferencia no se nota; el día que haya dos, sí.

---

## La pieza que falta: el administrador de instancias

Un módulo con varias implementaciones necesita algo que sepa **cuáles existen**:
sus datos de conexión, sus generalidades, y qué tableros y funcionalidades se le
habilitan a cada una.

**Todavía no existe, y es deliberado**: la prioridad es que RUNAC funcione. Pero
las dos condiciones para que siga siendo posible ya se cumplen y conviene no
perderlas de vista:

1. Cada implementación tiene su definición y sus datos separados de las demás.
2. El motor no tiene lógica de ninguna implementación en particular.

Mientras eso se mantenga, el administrador se puede construir después sin
rehacer nada.

---

## Datos personales

RUNAC guarda **su propio padrón**, con la información tal como la entregan las
provincias. Tres motivos:

- El requerimiento pide **trazabilidad del origen de cada dato** y prevé un
  identificador provincial además del interno. Cumplirlo exige conservar lo que
  informó cada archivo, coincida o no con lo que ya figura en el sistema y en
  RENAPER.
- Un niño o adolescente **puede no tener DNI** y aun así debe poder registrarse;
  en esos casos el identificador provincial es el único modo de reconocerlo entre
  entregas.
- La provincia suele tener el **domicilio real**, que no siempre coincide con el
  del documento.

El padrón alcanza a los **tres tipos de persona** que informan las provincias:
niños y adolescentes, referentes y responsables.

Se vincula con el registro de ciudadanos de SISOC **siempre que sea posible**,
para no duplicar personas y para enriquecer las vistas consolidadas con
información de otras fuentes del sistema, sujeta a habilitación.

Cuando la persona no exista en el registro de ciudadanos, SISOC ya cuenta con un
mecanismo que la da de alta con datos de RENAPER, validando la identidad
(`ciudadanos/api.py`). Se utilizará ese mecanismo y no se crearán ciudadanos por
cuenta propia.

**Sobre la confidencialidad:** el módulo **no escribe** en las tablas del resto
del sistema. Los datos que llegan por este programa quedan dentro del módulo y
no modifican información de otras áreas. La lectura del registro de ciudadanos
es sólo para identificar a la persona.

> **Definición pendiente.** ¿Debe dar de alta ciudadanos en SISOC a partir de las
> importaciones provinciales? Una presentación trimestral puede incorporar miles
> de personas al padrón general. Existe precedente en sentido contrario: VAT
> mantiene deliberadamente por fuera a los profesores, para no sumarlos al padrón
> que alimenta la validación de identidad y la revisión de duplicados.

> **Definición pendiente.** En los casos sin DNI, ¿hay alguna otra forma de
> establecer el vínculo con el registro de ciudadanos?

---

## Habilitaciones que dependen de la coordinación

No las resuelve la DNPYPI: son información existente en SISOC que hay que
habilitar para este módulo.

> ¿Se puede validar la identidad con RENAPER?

> ¿Se pueden aportar datos de seguridad social —cobro de asignaciones,
> discapacidad— a las vistas consolidadas? Es lo que sostiene el control de que
> la asignación por un niño acogido la perciba quien ejerce su cuidado.

> ¿La información sobre pueblos originarios y discapacidad puede servir a otros
> programas?

> ¿Qué nomenclador de localidades usa SISOC?

<!-- COMENTARIO: la última ya tiene respuesta verificada sobre el código:
     ninguno. core.Provincia, core.Municipio y core.Localidad tienen sólo un
     nombre en texto libre, sin código INDEC ni BAHRA. Si RUNAC adopta un
     nomenclador, va a tener un catálogo territorial más preciso que el resto
     del sistema. Ver 08-analisis-de-las-planillas.md. -->
