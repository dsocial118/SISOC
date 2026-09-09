# Modelo de datos de RUNAC — scripts de referencia

> **Estos scripts no se ejecutan contra la base de SISOC.**
>
> Crean tablas directamente, por fuera del sistema de migraciones de Django.
> Están acá para **leer y revisar el modelo**, no para correrlos. Cuando el
> módulo se integre, estas tablas nacen como migraciones.

---

## Qué son

El modelo de tres capas, tal como está construido y verificado en el prototipo
que se mantiene fuera del repositorio.

| Script | Capa | Qué define |
|---|---|---|
| `01_capa1_definicion.sql` | Capa 1 | Qué archivos se esperan, sus hojas, campos, tipos, catálogos y reglas de validación. Con versionado de estructura |
| `02_capa2_control.sql` | Capa 2 | Presentaciones, importaciones, reglas incumplidas, errores de importación e historial de ediciones |
| `03_capa3_consolidada.sql` | Capa 3 | La base consolidada: personas, caracterizaciones, medidas, dispositivos, normalización y trazabilidad |

La explicación de por qué el modelo está organizado así está en
[../04-modelo-de-datos.md](../04-modelo-de-datos.md). Este directorio es el
detalle; ese documento es el fundamento.

---

## Lo que no está acá

**Las tablas receptoras de la Capa 2 no figuran en estos scripts, y es a
propósito.** Son las que reciben las filas de cada hoja importada, y **se generan
a partir de la definición de la Capa 1**: una por archivo, hoja y versión de
estructura. Escribirlas a mano sería contradecir el diseño, porque cuando cambie
una planilla habría que volver a escribirlas.

Las genera un script de inicialización que se ejecuta una vez y se vuelve a
ejecutar si la definición cambia antes de la aprobación. Ver
[../09-alcance-primera-version.md](../09-alcance-primera-version.md).

**Tampoco están los INSERT de la definición.** Los 368 campos, 81 catálogos y 708
opciones relevados de las cinco planillas se cargan con scripts generados
automáticamente desde los Excel, que pesan cientos de kilobytes y se regeneran
cada vez que llega una versión nueva de una planilla. No tiene sentido
versionarlos acá.

---

## Convenciones

Todas las tablas llevan el prefijo `runac_`, que es el comportamiento por defecto
de SISOC: el nombre de la aplicación encabeza el de cada tabla.

Dentro del módulo, el prefijo distingue además la capa:

- `runac_c1_*` — definición de los archivos esperados y sus reglas
- `runac_c2_*` — importaciones, datos recibidos y gestión de observaciones
- `runac_c3_*` — base consolidada

<!-- COMENTARIO: la Capa 3 es la única que necesariamente convive con el resto
     de la base de SISOC. Las Capas 1 y 2 son específicas del proceso de
     importación y podrían vivir en un espacio aparte; es una definición
     técnica pendiente. -->
