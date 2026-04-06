## 2026-03-29 - Mensajes mobile por secciones

### Contexto

Se alineó el módulo de Mensajes de SISOC Mobile con el alcance del MVP de mensajería unidireccional desde Web hacia Mobile.

### Cambios

- El backend PWA de mensajes ahora incluye en la misma bandeja:
  - `Notificaciones Generales` (`subtipo=institucional`)
  - `Comunicaciones a Espacios` (`subtipo=comedores`)
- El listado por espacio agrega:
  - `seccion`
  - `fecha_creacion`
  - contadores `unread_general_count` y `unread_espacio_count`
  - agrupación `secciones.generales` y `secciones.espacios`
- La lectura de mensajes institucionales pasó a reflejarse para el mismo usuario en todos sus espacios accesibles, evitando que una notificación general vuelva a figurar como no leída al cambiar de espacio.
- El detalle de mensajes expone `fecha_creacion` y, por cada adjunto, `nombre_original`, `fecha_subida` y `url`.
- En mobile:
  - la bandeja del espacio quedó dividida en dos secciones
  - la bandeja organizacional deduplica notificaciones generales y mantiene separadas las comunicaciones a espacios
  - el detalle permite visualización embebida de imágenes y PDFs, y descarga sin alterar el archivo original

### Validación esperada

- Un comunicado institucional debe verse en todos los usuarios mobile.
- Una comunicación a espacio debe verse solo en usuarios con acceso a ese espacio.
- Marcar como leído un institucional en un espacio debe reflejarse como leído para el mismo usuario al abrir otro espacio.
