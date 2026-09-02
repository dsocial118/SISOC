# Issue 2417: bloqueantes CDI

## Objetivo

Resolver los seis puntos del issue sin incorporar cambios de `development` y
dejar un corte promovible desde `homologacion` hacia producción.

## Alcance aprobado

1. Cubrir el alta automática del usuario trabajador con una prueba que llegue
   hasta el envío de credenciales. Si el usuario se crea pero el correo falla,
   conservar el alta y mostrar una advertencia explícita en vez de informar un
   éxito completo.
2. Ocultar del sidebar el acceso **Alta de referente EGP**. La URL y la vista se
   mantienen para poder restaurar el acceso sin reimplementar el flujo.
3. Paginar el listado de usuarios de a 25 registros mediante el mecanismo
   estándar de Django y conservar filtros y búsqueda al cambiar de página.
4. Exigir en la nómina de trabajadores: tipo de barrio, jurisdicción,
   municipio y localidad.
5. Incorporar **No sabe** en las preguntas obligatorias de Formación y
   experiencia, y Cultura e identidad de trabajadores.
6. Incorporar **No sabe** en las preguntas obligatorias de Cultura e identidad,
   Discapacidad, Salud y antropometría, Nutrición y Asistencia ANSES de niños.
   En selecciones múltiples, **No sabe** es excluyente con cualquier otra
   respuesta.

## Persistencia y compatibilidad

`calendario_vacunacion_al_dia` deja de ser booleano para representar
`si`, `no` y `no_sabe`. Una migración de datos preserva `True` como `si`,
`False` como `no` y mantiene los valores nulos. Las demás opciones son cambios
de catálogo sobre campos de texto o JSON ya existentes.

No se agregan fixtures, dependencias, rutas ni permisos. La reparación de datos
históricos con problemas de codificación queda fuera de este cambio y requiere
una operación separada con respaldo y verificación.

## Validación

- Tests de regresión del alta automática y su resultado de correo.
- Tests del listado paginado y preservación de filtros.
- Tests de requeridos y de las nuevas respuestas, incluidos los multiselect
  excluyentes.
- Test de migración para los tres valores históricos del calendario.
- `makemigrations --check`, Black, Pylint y djLint focalizados en los archivos
  modificados.
- Prueba manual en producción únicamente con un CDI, identidad y correo de
  prueba controlados; confirmar inmediatamente antes del alta y de su eventual
  limpieza.

## Despliegue y reversión

El primer PR apunta a `homologacion`. No se mezcla `development`. La promoción
a `main` se hará solo después de validar el SHA y los checks requeridos. La
reversión de código es por revert del PR; la migración es reversible y recupera
`si`/`no` como booleanos, mientras `no_sabe` vuelve a nulo al regresar al esquema
anterior.
