# Bloqueantes CDI del issue 2417

## Cambio funcional

- El alta automática de referentes y trabajadores informa por separado la
  creación del usuario y el envío de credenciales. Una falla de correo conserva
  el usuario y muestra una advertencia.
- Se oculta del sidebar el acceso a **Alta de referente EGP** sin eliminar su
  vista ni su URL.
- El listado de usuarios se pagina de a 25 registros con el componente común.
- Tipo de barrio, jurisdicción, municipio y localidad pasan a ser obligatorios
  en el formulario de trabajadores.
- Las preguntas obligatorias solicitadas de trabajadores y niños incorporan la
  respuesta **No sabe**. En multiselects, esa respuesta no puede combinarse con
  otras opciones.

## Datos y migración

La migración `0048_issue_2417_respuestas_no_sabe` reemplaza
`calendario_vacunacion_al_dia` por una respuesta textual para representar
`si`, `no` y `no_sabe`. La copia preserva booleanos existentes y evita depender
de coerciones distintas entre SQLite y MySQL.

Al revertir, `si` y `no` recuperan sus booleanos; `no_sabe` vuelve a nulo porque
el esquema anterior no podía representarlo.

## Validación esperada

- Alta de trabajador desde la interfaz con intento de correo cubierto por test.
- Formularios de trabajador y nómina infantil con casos válidos, requeridos y
  opciones excluyentes.
- Paginado y sidebar cubiertos por pruebas de vista.
- Estado de migraciones, tests focalizados, Black, Pylint y djLint.

La reparación operativa de textos históricos con problemas de codificación no
forma parte de este cambio.
