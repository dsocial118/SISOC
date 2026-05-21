# Formulario moderno de dispositivos

## Objetivo

Documentar el comportamiento vigente del formulario de dispositivos para evitar drift entre reglas de UI, validacion de backend y carga documental.

## Comportamiento implementado

- Las secciones del formulario son colapsables por click y teclado.
- Los campos `_otro` y `_otra` se muestran solo cuando la opcion correspondiente esta seleccionada.
- La documentacion del dispositivo muestra un archivo principal y hasta cuatro adicionales de forma progresiva con el boton `Anadir archivo`.
- Los previews de archivos permiten quitar una seleccion nueva o marcar para eliminar un archivo guardado.
- CUIT, DNI responsable y telefono de contacto filtran caracteres no numericos mientras se tipea.
- CUIT exige 11 digitos; DNI responsable exige 7 u 8 digitos.
- `infraestructura_accesibilidad` y otras listas pueden usar la opcion `Ninguna de las anteriores` como valor explicito.

## Backend y compatibilidad

- `DispositivoForm` mantiene la validacion server-side de campos `otro`, CUIT y DNI aunque el JavaScript los oculte o sanee en cliente.
- Los campos de archivo adicionales siguen siendo campos independientes del modelo, no una entidad versionada.
- La UI no cambia permisos ni rutas; solo ajusta presentacion y validacion de entrada.

## Puntos de prueba manual

- Seleccionar y deseleccionar `Otro` en cada lista con campo asociado.
- Cargar archivos hasta exponer los cinco slots.
- Marcar un archivo existente para eliminar y desmarcarlo.
- Pegar CUIT, DNI o telefono con puntos, guiones o espacios y confirmar que se guardan como digitos.
