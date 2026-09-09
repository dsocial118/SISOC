# RUNAC — Registro Único Nacional de Medidas de Protección y Medidas Penales Juveniles

> **Estado: análisis en curso.** Este material refleja el estado del análisis al
> 8 de septiembre de 2026. **El trabajo continúa fuera del repositorio**, sobre un
> prototipo navegable. No es todavía una especificación cerrada: cuando el módulo
> se integre, esta documentación se actualiza y se incorpora al índice general.

Documentación funcional y técnica del módulo. Es el material que el equipo de
desarrollo va a necesitar para implementarlo, y el registro de por qué las cosas
están definidas como están.

**Área requirente:** Dirección Nacional de Promoción y Protección Integral (DNPYPI).
**Programa:** Federal de Protección de Niñez y Adolescencia (PFPNYA).

---

## Cómo leer esta carpeta

| Documento | Qué contiene | Para quién |
|---|---|---|
| [01-alcance.md](01-alcance.md) | Qué es RUNAC, qué entra y qué no | Todos |
| [02-actores-y-roles.md](02-actores-y-roles.md) | Los cuatro roles del sistema y qué puede cada uno | Todos |
| [03-arquitectura.md](03-arquitectura.md) | Cómo se construye y cómo se integra a SISOC | Desarrollo |
| [04-modelo-de-datos.md](04-modelo-de-datos.md) | Las tres capas, el versionado y por qué | Desarrollo |
| [05-circuito.md](05-circuito.md) | Los nueve pasos, de la carga a la consolidación | Todos |
| [06-proceso-de-importacion.md](06-proceso-de-importacion.md) | Plantillas, orden, control de admisión, trazabilidad | Desarrollo |
| [07-reglas-de-validacion.md](07-reglas-de-validacion.md) | Los tipos de regla y cómo se declaran | Desarrollo |
| [08-analisis-de-las-planillas.md](08-analisis-de-las-planillas.md) | Propuestas de rediseño de los Excel provinciales | DNPYPI |
| [09-alcance-primera-version.md](09-alcance-primera-version.md) | Qué entra en el MVP y qué queda para después | Todos |
| [decisiones/](decisiones/) | Registro de decisiones, con fecha y motivo | Desarrollo |
| [modelo/](modelo/) | Los scripts del modelo de tres capas, **de referencia: no se ejecutan contra SISOC** | Desarrollo |

---

## Estado

**Fase de análisis funcional, con prototipo navegable.** El módulo todavía no
existe en el repositorio de SISOC: se está construyendo un prototipo fuera, para
resolver las definiciones pendientes mostrando el circuito en funcionamiento.
Ver [03-arquitectura.md](03-arquitectura.md).

Lo que está implementado y probado en el prototipo:

- las tres capas del modelo de datos, con versionado de la estructura;
- el motor de importación, que lee la configuración y la ejecuta sin saber qué
  es el MPI;
- el circuito completo de nueve pasos, con los cuatro roles;
- la corrección de datos dentro del sistema, con historial;
- los informes de errores, incluido el archivo propio con las celdas marcadas;
- la consulta de qué se espera en cada columna, por archivo y hoja;
- permisos por rol verificados en cada pantalla, no sólo ocultos en el menú;
- diseño que arranca en teléfono y suma tablet y escritorio.

La Capa 3 está **modelada y creada en la base** —23 tablas— pero sin datos: el
proceso de consolidación no está implementado y no forma parte de la primera
entrega.

---

## Cómo leer las marcas del texto

Este material combina definiciones cerradas con cuestiones abiertas. Se
distinguen así:

> **Definición pendiente.** Algo que todavía no está resuelto y necesita
> respuesta de la DNPYPI, de la coordinación o del equipo. Está escrito como
> pregunta.

<!-- COMENTARIO: las notas internas van como comentarios de Markdown. No se ven
     al leer el documento renderizado, pero quedan en el archivo para quien
     trabaje sobre él. -->

**Cuando el texto y el prototipo difieren, vale el prototipo.** El código es la
definición más reciente: si un documento describe algo de otro modo, es que quedó
atrás y hay que corregirlo.

---

## Convenciones del repositorio

Este material sigue `docs/registro/README.md` de SISOC: las decisiones
importantes se registran con fecha en `decisiones/`, y los cambios funcionales
visibles quedan asentados.

El nombre interno del módulo es `runac`, y **se elige una sola vez**: define el
prefijo de todas sus tablas y después no se cambia sin renombrarlas todas.
