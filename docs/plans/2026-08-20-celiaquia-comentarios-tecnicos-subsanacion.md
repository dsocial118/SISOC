# Documento funcional: comentarios técnicos y subsanación en Celiaquía

## 1. Objetivo

Reestructurar el flujo de revisión de legajos de Celiaquía para que los comentarios técnicos sean registros estructurados, reutilizables en las acciones de `SUBSANAR` y `RECHAZAR`, y correctamente segmentados según el rol del usuario.

El objetivo principal es evitar que el técnico deba repetir manualmente en la acción final los motivos que ya registró durante la revisión interna.

## 2. Situación actual

Actualmente conviven dos mecanismos independientes:

- `Comentarios Técnicos`, almacenados en el historial de comentarios del legajo.
- Motivos ingresados al momento de ejecutar `SUBSANAR` o `RECHAZAR`.

Esta separación genera los siguientes problemas:

- El técnico repite información.
- Pueden existir diferencias entre la observación interna y el motivo comunicado.
- La Provincia puede acceder a comentarios que todavía forman parte de la revisión interna.
- No existe una clasificación cerrada y homogénea de las observaciones.

## 3. Actores y permisos

### Técnico

- Puede crear comentarios técnicos en legajos de expedientes asignados.
- Puede consultar el historial completo de comentarios técnicos del legajo.
- Puede ejecutar `VALIDAR`, `SUBSANAR` y `RECHAZAR` según el estado vigente.

### Coordinador

- Puede crear y consultar comentarios técnicos de cualquier legajo habilitado.
- Puede ejecutar las acciones de revisión permitidas por el flujo actual.

### Provincia

- No puede crear, editar ni eliminar comentarios técnicos.
- No visualiza comentarios técnicos durante la revisión interna.
- Visualiza las observaciones publicadas al solicitar una subsanación.
- Mantiene el flujo actual para cargar y enviar la respuesta de subsanación.

### Administrador

Conserva los privilegios administrativos existentes. La visibilidad funcional de los comentarios debe respetar igualmente la separación entre información interna y provincial.

La autorización debe validarse en backend. Ocultar botones en la interfaz no reemplaza los controles de permisos.

## 4. Comentarios Técnicos

Al presionar **Comentarios Técnicos**, el sistema debe mostrar un formulario con los siguientes campos:

1. **Tipo de revisión**: desplegable obligatorio con opciones cerradas.
2. **¿Tiene observaciones?**: desplegable obligatorio con valores `Sí` y `No`.
3. **Observaciones**: desplegable obligatorio sólo cuando la respuesta anterior sea `Sí`.
4. **Guardar Comentario**: botón para confirmar el registro.

### Reglas de alta

- Cada alta crea un nuevo comentario asociado al `ExpedienteCiudadano` correspondiente.
- Los comentarios anteriores no se sobrescriben.
- Pueden registrarse tantos comentarios como sean necesarios.
- Luego de guardar, el formulario vuelve a estar disponible para ingresar otro comentario.
- El backend debe validar que la combinación de opciones sea válida.
- Si `¿Tiene observaciones? = No`, el campo `Observaciones` debe quedar vacío.
- Si `¿Tiene observaciones? = Sí`, debe seleccionarse una observación válida.
- El registro debe conservar usuario, fecha, legajo y estado del legajo al momento de la creación.

### Catálogos

Los valores definitivos deben ser definidos y aprobados por negocio antes del desarrollo. Como mínimo se necesitan:

- Catálogo de tipos de revisión.
- Catálogo de observaciones relacionadas con cada tipo de revisión.

La observación debe depender del tipo de revisión para evitar combinaciones incorrectas. No se debe aceptar texto libre como reemplazo de las opciones cerradas.

## 5. Visibilidad

Los comentarios técnicos se guardan inicialmente como información interna.

### Técnico y Coordinador

Pueden consultar el historial completo, incluyendo:

- Tipo de revisión.
- Indicador de existencia de observaciones.
- Observación seleccionada, cuando corresponda.
- Usuario que registró el comentario.
- Fecha y hora.
- Estado de publicación a Provincia.

### Provincia

- Antes de una solicitud de subsanación, no recibe comentarios técnicos.
- No puede consultar ni modificar el historial interno.
- Al solicitar una subsanación, recibe sólo los comentarios que tengan `¿Tiene observaciones? = Sí`.
- Los comentarios con respuesta `No` permanecen internos.
- Los comentarios publicados no pueden editarse ni eliminarse desde la interfaz provincial.

La publicación debe quedar registrada mediante fecha, usuario o evento de auditoría.

## 6. Acción Validar

El flujo de validación continúa sin cambios funcionales:

- No requiere comentarios técnicos con observaciones.
- Mantiene las validaciones y transiciones actuales.
- No publica comentarios técnicos a la Provincia.

## 7. Acción Subsanar

Al presionar **Subsanar**, debe dejar de mostrarse el formulario actual de motivo independiente.

En su reemplazo, el sistema debe mostrar:

- La concatenación de las observaciones técnicas del legajo que tengan respuesta `Sí`.
- Un cuadro de texto libre opcional para agregar información complementaria.
- La acción de confirmación.

### Al confirmar

El sistema debe:

1. Cambiar el estado del legajo a `SUBSANAR`.
2. Generar el motivo a partir de las observaciones técnicas concatenadas.
3. Agregar el texto libre sólo si fue informado.
4. Publicar a Provincia las observaciones técnicas con respuesta `Sí`.
5. Mantener los campos legacy necesarios para no romper reportes ni flujos existentes.
6. Mantener las reglas actuales de cupo, archivos y subsanación.
7. Registrar usuario, fecha, estado anterior y estado nuevo.

La concatenación debe realizarse en backend, en orden cronológico y sin duplicados. El contenido mostrado en pantalla debe funcionar como previsualización, no como fuente de verdad.

### Sin observaciones registradas

Si el legajo no tiene comentarios técnicos con observaciones:

- Se permite continuar sólo si el técnico completa el texto libre.
- Si ambos valores están vacíos, se devuelve un error de validación.
- No se modifica el estado del legajo.

## 8. Acción Rechazar

Al presionar **Rechazar**, debe reemplazarse el formulario actual por una vista con:

- La concatenación de las observaciones técnicas registradas.
- Un cuadro de texto libre opcional.
- La acción de confirmación.

### Al confirmar

El sistema debe:

1. Cambiar el estado del legajo a `RECHAZADO`.
2. Generar el motivo con las observaciones concatenadas y el texto libre opcional.
3. Registrar usuario, fecha, estado anterior, estado nuevo y motivo resultante.
4. Mantener las reglas actuales de liberación de cupo y validación RENAPER.

### Regla de visibilidad propuesta

El pedido define explícitamente la publicación de observaciones para `SUBSANAR`, pero no para `RECHAZAR`. Por lo tanto, la propuesta funcional inicial es:

- Los comentarios técnicos permanecen internos.
- El detalle del rechazo queda disponible para Técnico, Coordinador y auditoría.
- Provincia visualiza el estado `RECHAZADO`, pero no el detalle técnico.

Si negocio requiere que Provincia vea el motivo del rechazo, deberá definirse como una publicación específica del rechazo, sin exponer todo el historial interno.

## 9. Persistencia

Se recomienda reutilizar el historial de comentarios existente y agregar los datos estructurados necesarios:

- `tipo_revision`.
- `tiene_observaciones`.
- `observacion`.
- `es_interno`.
- `publicado_provincia_en`.
- `publicado_por`.

Cada registro debe conservar como asociación principal el ID del legajo.

Los campos actuales de subsanación no deben eliminarse en la primera versión. Deben continuar sincronizándose para preservar compatibilidad con reportes, pantallas e integraciones existentes.

Los comentarios históricos de texto libre deben seguir siendo visibles para los roles que ya tienen acceso. No deben convertirse automáticamente a opciones cerradas sin una regla de equivalencia aprobada.

## 10. Integridad y concurrencia

- Un comentario con `tiene_observaciones = No` no puede tener observación seleccionada.
- Un comentario con `tiene_observaciones = Sí` debe tener una observación válida.
- El legajo debe pertenecer al expediente indicado en la URL.
- El técnico debe estar asignado al expediente, conforme a la regla actual.
- No se pueden ejecutar acciones incompatibles con el estado actual.
- `SUBSANAR` y `RECHAZAR` deben ejecutarse dentro de una transacción.
- Ante doble envío, sólo una transición válida debe producir efecto.
- Los motivos deben generarse en backend.

## 11. Criterios de aceptación

- El técnico puede guardar múltiples comentarios para un mismo legajo.
- Cada comentario queda asociado al ID correcto.
- No se pueden guardar combinaciones inválidas de desplegables.
- Técnico y Coordinador visualizan el historial completo.
- Provincia no visualiza comentarios internos antes de `SUBSANAR`.
- Al solicitar `SUBSANAR`, Provincia recibe sólo las observaciones marcadas como existentes.
- Los formularios de `SUBSANAR` y `RECHAZAR` muestran la concatenación de observaciones.
- El texto libre de ambas acciones es opcional.
- El técnico no necesita copiar nuevamente los motivos.
- Se mantienen los efectos actuales sobre estado, cupo, archivos y RENAPER.
- Los datos históricos continúan siendo legibles.
- Los accesos no autorizados devuelven `403`.
- Las combinaciones inválidas y transiciones no permitidas devuelven `400`.

## 12. Plan de implementación posterior

1. Confirmar los catálogos de tipo de revisión y observaciones.
2. Confirmar si el detalle del rechazo será visible para Provincia.
3. Definir si se publican automáticamente todas las observaciones o si el técnico puede seleccionar algunas.
4. Diseñar la migración compatible con los comentarios existentes.
5. Adaptar el servicio de comentarios para crear registros estructurados.
6. Adaptar los endpoints de consulta y publicación según rol.
7. Adaptar las acciones `SUBSANAR` y `RECHAZAR` para reutilizar el historial.
8. Actualizar los modales y formularios de la interfaz.
9. Agregar tests de permisos, validaciones, visibilidad, concatenación y compatibilidad histórica.
10. Ejecutar validaciones de migraciones, tests, formato y templates.

## 13. Definiciones pendientes de negocio

- Lista oficial de tipos de revisión.
- Lista oficial de observaciones.
- Relación entre tipos y observaciones.
- Visibilidad del detalle del rechazo para Provincia.
- Posibilidad de publicar sólo un subconjunto de observaciones.
- Tratamiento del texto libre: si se guarda sólo en el evento de acción o también como comentario independiente.
