# Issue #2508 — Módulo de reportes CDI, Fase 2

## Resultado

Centro de Infancia suma una entrada **Reportes** en el sidebar, hermana de "Ver
Centros de Infancia", con una descarga XLSX de seis hojas: Resumen, CDI,
Trabajadores, Nómina, Diccionario y Metadatos. La hoja de Nómina incorpora los
indicadores RENAPER calculados con el servicio compartido de la Fase 1.

Las tres hojas de datos replican exactamente las consultas pedidas. Lo agregado
sobre eso —Resumen, Diccionario, Metadatos, el encabezado fijo con autofiltro,
la columna `renaper_nino_motivo` al final de Nómina y un filtro opcional por
provincia— no mueve ninguna columna existente.

No se cambió el modelo, no hacen falta migraciones y no se agregaron
dependencias: openpyxl ya estaba en `requirements/base.txt`.

## Archivos

| Archivo | Cambio |
| --- | --- |
| centrodeinfancia/services_reportes.py | Columnas, alcance, consultas y armado del libro XLSX. |
| centrodeinfancia/views_reportes.py | Pantalla del módulo y descarga con permiso de exportación. |
| centrodeinfancia/templates/centrodeinfancia/reportes.html | Pantalla del módulo. |
| centrodeinfancia/urls.py | Rutas `centrodeinfancia_reportes` y `centrodeinfancia_reportes_descargar`. |
| templates/includes/sidebar/opciones.html | Entrada Reportes dentro de Centro de Infancia. |
| centrodeinfancia/tests/test_reportes.py | Contrato de columnas, alcance por rol, indicadores, permisos, filtro y hojas nuevas. |
| core/permissions/registry.py | Alias del permiso `Reportes CDI`. |
| users/bootstrap/groups_seed.py | El permiso en los cinco roles SIMEPI. |
| users/migrations/0052_bootstrap_reportes_cdi_permission.py | Crea el permiso y lo asigna en entornos existentes. |
| docs/implementaciones/centrodeinfancia_reportes.md | Contrato, alcance, permisos y límites. |
| docs/indice.md, AGENT_REPO_MAP.md | Navegación del nuevo módulo. |

## Decisiones

- **Alcance por usuario, no dump nacional incondicional.** El reporte usa
  `aplicar_scope_centros_cdi`, el mismo scope del listado. Los roles nacionales y
  el superusuario siguen obteniendo el universo completo, que es el caso del
  archivo adjunto al issue, y los roles territoriales solo lo suyo.
- **Paridad de columnas con el archivo validado.** Se verificó
  programáticamente que las tres hojas tengan los mismos encabezados y el mismo
  orden que el adjunto del issue; las tres columnas RENAPER van al final de la
  hoja de Nómina para no desplazar nada.
- **Un solo cálculo del indicador RENAPER.** El reporte y el PDF provincial
  comparten `services_renaper_estado.py`. Es lo que sostiene el pedido de que
  ambos coincidan.
- **Permiso propio en vez de reutilizar el de exportación.** La primera versión
  usaba `auth.role_exportar_a_csv`, pero al revisar el seed se vio que ese
  permiso lo tienen solo ADMIN y "Comedores total": **ningún rol CDI ni SIMEPI
  podía descargar el reporte**. Dárselo habría abierto además la exportación de
  comedores, usuarios y todos los listados, porque es global. Se creó
  `auth.role_reportes_cdi`, asignado por migración a los cinco roles SIMEPI.
  Quien ya tiene el permiso global sigue pudiendo descargar. Los roles CDI
  locales quedaron afuera a propósito: es una decisión aparte.
- **Consultas ORM, no SQL cruda.** Las queries del issue se tradujeron a ORM para
  que el scope y el borrado lógico se apliquen por los mismos caminos que el
  resto del módulo.
- Generación sincrónica con `Workbook(write_only=True)` e `iterator()`. El mapa
  de indicadores de adultos se arma en una consulta por descarga, no una por
  fila.
- **Hoja Resumen en formato largo** (`seccion`, `detalle`, `cantidad`) en vez de
  un tablero con celdas fijas: así se filtra y alimenta una tabla dinámica sin
  rehacerla. Se calcula con agregados en la base, no recorriendo las filas ya
  escritas, lo que además permite ubicarla como primera hoja sin intercalar
  escrituras entre hojas.
- **`renaper_nino_motivo` en vez de solo "No".** El indicador decía que la ficha
  no está validada pero no por qué. Separar "No consultado" —que resuelve el
  comando de revalidación— de una discrepancia de datos —que necesita una
  persona— es lo que vuelve accionable el reporte, que es el problema que
  originó el issue.
- **Encabezado fijo y autofiltro** en todas las hojas. Se verificó que openpyxl
  los soporte en modo `write_only`.
- **Diccionario por introspección**, no por una tabla escrita a mano: se leen los
  `choices` de cada campo del modelo, con `CAMPOS_OPCIONES` como respaldo para
  los JSON multivaluados. Una opción nueva aparece sola. En la verificación
  manual produjo 408 entradas.
- **Filtro por provincia opcional**, con "Todas" por defecto y el selector
  poblado solo con las provincias del alcance del usuario. Se aplica sobre el
  alcance ya resuelto, así que acota pero nunca amplía; hay un test que pide una
  provincia ajena y verifica que no devuelva filas.

## Límite conocido

Los responsables legales no existen como `Ciudadano`: son campos planos de la
nómina. Sus dos columnas van a informar "No" en la mayoría de las filas hasta
que se decida crearlos o vincularlos, decisión que quedó fuera de este issue por
implicar creación de personas, riesgo de duplicados y privacidad.

## Validación

Verificado de forma estática, sin ejecución:

- Las tres listas de columnas resuelven contra campos reales de
  `CentroDeInfancia`, `Trabajador` y `NominaCentroInfancia`, incluidos los saltos
  por clave foránea.
- Los encabezados coinciden exactamente con el archivo adjunto al issue: 36, 47
  y 96 columnas, más las tres nuevas al final de Nómina.

Ejecutado con el stack Docker levantado:

~~~bash
docker compose exec django pytest centrodeinfancia/ tests/test_ciudadanos_renaper_validacion.py tests/test_ciudadanos_importacion_masiva.py -n auto
docker compose exec django black --check centrodeinfancia/ ciudadanos/
docker compose exec django pylint centrodeinfancia/services_reportes.py centrodeinfancia/views_reportes.py
docker compose exec django djlint centrodeinfancia/templates/centrodeinfancia/reportes.html templates/includes/sidebar/opciones.html --check
docker compose exec django python manage.py makemigrations --check --dry-run
~~~

Resultado: 763 tests en verde (1 skip), incluidos los 22 de este módulo; black y
djlint aplicados sobre los archivos tocados; pylint 10.00/10; sin migraciones
detectadas. `opciones.html` ya estaba conforme y no necesitó reformateo.

Verificación manual contra la app levantada, con datos de prueba creados y
borrados después: pantalla 200 con el selector de provincias del alcance,
descarga 200 con `Cache-Control: private, no-store` y nombre de archivo con
fecha, las seis hojas presentes con encabezado fijo y autofiltro, Nómina con sus
100 columnas, Diccionario con 408 entradas, filtro por provincia aplicado, la
entrada Reportes visible en el sidebar, y un usuario sin el permiso recibiendo
403 en la descarga y el aviso en la pantalla.

## Riesgos

- Volumen: la generación es sincrónica. Con el universo actual está bien; un
  crecimiento relevante pide revisar generación asincrónica antes que optimizar
  consultas.
- Privacidad: el archivo concentra datos personales de niños, niñas y
  responsables, incluidos salud y discapacidad. La descarga queda registrada en
  el log con usuario y cantidad de filas por hoja.
- Si alguien agrega columnas en el medio de las listas, rompe la paridad con el
  archivo que el equipo ya validó. El test de encabezados lo detecta.
