# Centro de Infancia: módulo de reportes

## Alcance

El módulo entrega un único archivo XLSX con seis hojas —`Resumen`, `CDI`,
`Trabajadores`, `Nomina`, `Diccionario` y `Metadatos`— pensado para análisis
fuera del sistema. No reemplaza las exportaciones CSV de los listados, que
siguen respondiendo a columnas configurables y filtros de pantalla.

Las tres hojas de datos replican exactamente lo pedido en el issue. Las otras
tres son agregados que no alteran ninguna de ellas.

La pantalla ofrece un filtro opcional por provincia, con "Todas" por defecto.
El filtro solo acota sobre el alcance ya resuelto: pedir una provincia ajena no
devuelve nada de más.

Todas las hojas abren con la fila de encabezados fija y autofiltro sobre el
rango escrito: con 99 columnas, navegar sin eso es impracticable.

## Hoja Resumen

Formato largo de tres columnas —`seccion`, `detalle`, `cantidad`— para que sea
filtrable y sirva de base a una tabla dinámica. Cubre totales de las tres hojas,
CDI sin nómina y sin trabajadores, nómina por estado, validación RENAPER de
niños y niñas, y CDI y fichas por provincia. Se calcula con agregados en la base,
no recorriendo las filas de las otras hojas, y respeta el mismo alcance.

## Hojas Diccionario y Metadatos

`Diccionario` traduce los códigos que publican las tres hojas de datos
(`hoja`, `columna`, `codigo`, `etiqueta`). Se arma por introspección de los
`choices` de cada campo del modelo y, para los campos JSON multivaluados que no
los declaran, desde `CAMPOS_OPCIONES` y `CAMPOS_OPCIONES_MULTIPLES`. Al
generarse sola, una opción nueva en el modelo aparece sin tocar este código.

`Metadatos` declara cuándo se generó el archivo, quién lo generó, con qué
alcance, si hubo filtro de provincia, cuántas filas quedó teniendo cada hoja y
la advertencia de datos personales. Va última porque usa las filas realmente
escritas, sin volver a contarlas.

## Contrato de columnas

Las columnas y su orden replican el archivo que el equipo validó en el issue
#2508. La hoja de `Nomina` agrega tres columnas **al final**, para no desplazar
las que ya estaban:

| Columna | Significado |
| --- | --- |
| `renaper_nino` | El `Ciudadano` de la ficha está validado por RENAPER. |
| `renaper_responsable_1` | Existe un único `Ciudadano` con el DNI del responsable legal 1 y está validado. |
| `renaper_responsable_2` | Ídem para el responsable legal 2. |
| `renaper_nino_motivo` | Por qué el indicador del niño/a no dice "Sí". Vacío cuando está validado. |

Las primeras tres se calculan con
`centrodeinfancia/services_renaper_estado.py`, el mismo servicio que usa el PDF
provincial de nómina infantil. Por eso coinciden con él para las columnas que
ambos publican.

`renaper_nino_motivo` distingue los dos casos que se accionan distinto: "No
consultado" significa que la ficha nunca pasó por RENAPER y la resuelve el
comando de revalidación; cualquier otro texto viene de
`Ciudadano.motivo_no_validacion_descripcion` o del motivo tipificado, y señala
una discrepancia de datos que alguien tiene que mirar.

Límite conocido: los responsables legales se guardan como campos planos de la
nómina, no como `Ciudadano`. Mientras no exista una decisión para crearlos o
vincularlos, sus columnas informan "No" en la mayoría de las filas. No es un
error de cálculo: es la ausencia del dato con el que se valida.

Diferencias de formato respecto del archivo del issue, que se generó con una
consulta SQL directa:

- Los valores vacíos se escriben como celda vacía, no como el texto `None`.
- Las fechas se escriben como fechas de Excel, no como texto.
- Los campos JSON se serializan con `json.dumps`, conservando acentos.

## Alcance de datos y permisos

El reporte nunca devuelve más de lo que el usuario ya puede ver en el sistema.
El alcance se resuelve con `aplicar_scope_centros_cdi`, el mismo del listado:

| Rol | Alcance del reporte |
| --- | --- |
| Superusuario y roles SIMEPI nacionales | Todos los centros. |
| EGP con alcance territorial | Los centros de su territorio. |
| Referente CDI | Los centros con `AccesoCDI` activo. |
| Trabajador CDI | Los centros donde está vinculado. |
| Rol CDI local sin vínculo operativo | Ninguna fila: falla cerrado. |

| Flujo | Ruta | Permiso |
| --- | --- | --- |
| Pantalla del módulo | `/centrodeinfancia/reportes/` | `auth.role_reportes_cdi` |
| Descarga del XLSX | `/centrodeinfancia/reportes/descargar/` | `auth.role_reportes_cdi` |

`auth.role_reportes_cdi` es un permiso **propio del módulo** y custodia tanto la
pantalla como la descarga; el superusuario lo saltea. La entrada del sidebar usa
la misma condición, así que a quien no lo tiene el módulo le queda invisible.

No se reutilizó el global `auth.role_exportar_a_csv`: ese habilita la
exportación de comedores, usuarios y el resto de los listados, así que dárselo a
los roles SIMEPI para que pudieran bajar este reporte les habría abierto todo lo
demás. Tenerlo tampoco alcanza para entrar acá.

Lo reciben SIMEPI Administrador, Analista de datos, Equipo Nacional, Auditoría y
EGP, más Admin para que los perfiles administrativos no pierdan el acceso
(`users/migrations/0052_bootstrap_reportes_cdi_permission.py`).

Los roles CDI locales —Referente centro y Trabajador— **no** lo reciben: el
módulo se pensó para el equipo nacional y provincial. Dárselo es una decisión
aparte; alcanza con agregar el permiso a esos grupos.

## Vista previa

La pantalla muestra la hoja `Resumen` completa antes de descargar, con las
mismas filas y el mismo alcance que el archivo. Se arma con `filas_resumen`, la
misma función que escribe esa hoja, y acompaña al filtro de provincia: el
selector y el botón de descarga comparten un formulario, donde "Actualizar
resumen" recarga la pantalla y el botón de descarga apunta a la otra ruta por
`formaction`.

La descarga responde con `Cache-Control: private, no-store`, como el PDF
provincial. El archivo concentra datos personales de niños, niñas y
responsables, incluidos salud y discapacidad.

## Generación y volumen

La generación es sincrónica. Con el universo del issue —125 centros, 1142
trabajadores y 3800 fichas de nómina— alcanza con un libro `write_only` de
openpyxl e `iterator()` sobre las hojas grandes. Los indicadores de adultos se
resuelven en una sola consulta por descarga, no una por fila. Si el universo
creciera de forma relevante, el primer paso es revisar la generación
asincrónica antes que optimizar consultas.

## Referencias de implementación

- `centrodeinfancia/services_reportes.py`: columnas, alcance y armado del libro.
- `centrodeinfancia/views_reportes.py`: pantalla, permiso de exportación y
  cabeceras de la descarga.
- `centrodeinfancia/tests/test_reportes.py`: contrato de columnas, alcance por
  rol, indicadores RENAPER y permisos.
- `docs/implementaciones/centrodeinfancia_nomina_renaper.md`: cómo se alimenta
  el estado de validación que estas columnas leen.
