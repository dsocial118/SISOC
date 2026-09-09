# Arquitectura

RUNAC es un **módulo de SISOC**: comparte autenticación, navegación, permisos,
despliegue e identidad visual. Se construye en dos etapas.

**Etapa 1 — Prototipo.** Se está armando un prototipo navegable fuera del
repositorio, para mostrar el circuito funcionando y resolver las definiciones
pendientes frente a una pantalla en vez de frente a un texto, mediante
depuraciones iterativas validadas con la contraparte. En esta etapa se trabaja
con una base MySQL separada.

Se arranca afuera por dos motivos: las planillas provinciales y el propio
circuito están en continuo cambio y todavía no hay un formato definitivo, y
modificar el repositorio por cada ajuste implica migraciones y revisiones que no
aportan mientras el diseño no esté cerrado.

Mientras el prototipo esté fuera se trabaja **exclusivamente con datos
ficticios** y con identificación visible en pantalla de que se trata de un
prototipo. Las demostraciones se hacen publicándolo temporalmente con ngrok,
siempre con acceso protegido por usuario y contraseña.

**Etapa 2 — Integración.** Cuando la contraparte dé el visto bueno, se integran a
SISOC el código y las tablas, y allí queda en producción.

<!-- COMENTARIO: "PWA" se usa en el proyecto como sinónimo de "aplicación web
     autónoma y fácil de mostrar". Se descartó como requisito técnico: RUNAC no
     tiene caso de uso sin conexión —subir un Excel la requiere— y la app `pwa`
     de SISOC es el backend de una app móvil, sin service worker ni manifest. -->

---

## Qué implica la integración

Al incorporarse al repositorio, RUNAC queda sujeto a las reglas que SISOC aplica
a todo módulo nuevo (`docs/ia/MODULAR_BOUNDARIES.md`):

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
| Nombre del dominio | `runac` |
| Clasificación | **Vertical extraíble.** No es cambio de kernel: no toca `Ciudadano` ni los domicilios embebidos. No es parte de un contexto existente: padrón y dispositivos propios |
| Entidades propias | Padrón (persona, dispositivo, familia), eventos (medida, DAE) y las tres capas |
| Dependencias al kernel | `ciudadanos.Ciudadano` **por vínculo opcional**, nunca obligatorio. Territorio a confirmar según el nomenclador |
| Dependencias a otros verticales | Ninguna. Los dispositivos son propios: no requiere fachada de `dispositivos` |

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
(`ciudadanos/api.py`). RUNAC utilizará ese mecanismo y no creará ciudadanos por
su cuenta.

**Sobre la confidencialidad:** RUNAC **no escribe** en las tablas del resto del
sistema. Los datos que llegan por este programa quedan dentro del módulo y no
modifican información de otras áreas. La lectura del registro de ciudadanos es
sólo para identificar a la persona.

> **Definición pendiente.** ¿RUNAC debe dar de alta ciudadanos en SISOC a partir
> de las importaciones provinciales? Una presentación trimestral puede incorporar
> miles de personas al padrón general. Existe precedente en sentido contrario:
> VAT mantiene deliberadamente por fuera a los profesores, para no sumarlos al
> padrón que alimenta la validación de identidad y la revisión de duplicados.

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

---

## Nomenclatura de tablas

Todas las tablas del módulo llevan el prefijo `runac_`, que es el comportamiento
por defecto de SISOC: el nombre de la aplicación encabeza el de cada tabla. No
requiere configuración adicional —se verificó que el repositorio usa el
comportamiento por defecto, con sólo cuatro excepciones en todo el proyecto.

Dentro del módulo, el prefijo distingue las tres capas:

- `runac_c1_*` — definición de los archivos esperados y sus reglas
- `runac_c2_*` — importaciones, datos recibidos y gestión de observaciones
- `runac_c3_*` — base consolidada
