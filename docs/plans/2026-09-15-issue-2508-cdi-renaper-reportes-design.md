# Issue 2508: campo RENAPER de nómina CDI + módulo de reportes

## Objetivo

1. Corregir el indicador de validación RENAPER de las nóminas CDI, que hoy
   informa "No" para casi todas las fichas.
2. Agregar un módulo de Reportes en Centro de Infancia, al mismo nivel que
   "Ver Centros de Infancia", que emita el listado de CDI, Trabajadores y
   Nómina, con el indicador RENAPER incorporado a la hoja de Nómina.

## Diagnóstico del punto 1

El PDF provincial de nómina infantil calcula sus dos columnas RENAPER así:

- `RENAPER niño/a`: `ciudadano.estado_validacion_renaper == VALIDADO`
  (`centrodeinfancia/services_nomina_ninos_pdf.py:316`).
- `RENAPER adulto 1`: busca un `Ciudadano` por el DNI del responsable legal 1
  y exige coincidencia única y validada
  (`centrodeinfancia/services_nomina_ninos_pdf.py:157`).

El único punto del repositorio que escribe `estado_validacion_renaper =
VALIDADO` es la importación masiva de ciudadanos
(`ciudadanos/services_importacion_masiva.py:414`). El alta de nómina CDI crea
el `Ciudadano` sin tocar ese campo (`centrodeinfancia/views.py:1740`), incluso
cuando los datos se precargaron desde RENAPER, por lo que queda en
`NO_CONSULTADO`. Los responsables legales, además, no se persisten como
`Ciudadano`: son campos planos de la nómina.

Causa raíz: el circuito de alta de nómina consume RENAPER solo para precargar
el formulario y nunca registra el resultado de esa consulta en el modelo de
identidad. El indicador no está "mal calculado": nunca se alimenta.

Riesgo de integridad asociado: en el alta de nómina, `origen_dato` llega en un
`<input type="hidden">` del POST (`centrodeinfancia/views.py:1695`) y se guarda
tal cual en `Ciudadano.origen_dato`. El alta de Trabajador ya resuelve esto con
un token firmado por CDI y usuario (`centrodeinfancia/views.py:1655-1680`). La
marca de validación no puede apoyarse en un dato controlado por el cliente.

## Decisiones tomadas

- El síntoma a corregir es el indicador del PDF provincial que da "No" siempre.
- Alcance del arreglo: hacia adelante en el alta, más un comando de
  revalidación por lotes para las fichas ya cargadas.
- El módulo de reportes respeta el alcance del usuario
  (`aplicar_scope_centros_cdi`), no expone un dump nacional a roles
  territoriales. Los roles SIMEPI nacionales y el superusuario siguen
  obteniendo el universo completo, que es el caso del archivo adjunto al issue.
- La hoja de Nómina lleva indicador RENAPER de niño/a y de ambos responsables
  legales.

## Límite conocido de la decisión sobre responsables legales

Hoy no existe `Ciudadano` para los responsables legales salvo que la persona
haya entrado al sistema por otro circuito. Las columnas de adulto van a
informar "No" para la mayoría de las filas hasta que se decida, como cambio
aparte, crear o vincular `Ciudadano` para responsables legales en el alta de
nómina. Ese cambio implica creación de personas, riesgo de duplicados y una
decisión de privacidad, y no entra en este issue.

## Alcance

### Fase 1 — Validación RENAPER (PR 1)

1. Extraer a un helper reutilizable el payload de validación que hoy arma
   `ciudadanos/services_importacion_masiva.py:405-420` (estado, fecha, datos
   crudos, origen). La importación masiva pasa a consumirlo, sin cambiar su
   comportamiento.
2. Extraer el cálculo del indicador a un único servicio compartido (por
   ejemplo `centrodeinfancia/services_renaper_estado.py`), consumido por el PDF
   provincial y por el reporte nuevo. Es lo que garantiza que ambos coincidan;
   el PDF mantiene sus etiquetas "Sí"/"No" actuales.
3. Alta de nómina (`NominaCentroInfanciaCreateView`): replicar el token firmado
   del alta de Trabajador. Solo cuando el token valida (mismo CDI, mismo
   usuario, dentro de la ventana) el `Ciudadano` nuevo se persiste con
   `estado_validacion_renaper=VALIDADO`, `fecha_validacion_renaper`,
   `datos_renaper` y `origen_dato="renaper"` resuelto en el servidor. El
   `origen_dato` del POST deja de decidir estado de validación.
4. Cuando el niño/a ya existe como `Ciudadano` local, el alta no altera su
   estado de validación: eso queda para el comando del punto 5.
5. Comando `validar_renaper_nominas_cdi` (patrón de
   `ciudadanos/management/commands/backfill_identidad.py`), con `--dry-run`,
   `--batch-size`, `--limit` y contadores en la salida. Universo: ciudadanos
   vinculados a nóminas CDI no eliminadas, con documento y estado
   `NO_CONSULTADO`. Reglas:
   - Consulta con reintento por sexo como hace la importación masiva.
   - Éxito con coincidencia de apellido, nombre y fecha de nacimiento: marca
     `VALIDADO`.
   - Éxito con discrepancia en esos datos: marca `NO_VALIDADO` con
     `motivo_no_validacion_renaper`, sin pisar los datos cargados.
   - `no_match`: marca `NO_VALIDADO` con motivo.
   - Error sistémico (`is_systemic_renaper_error`): corta la corrida y no marca
     nada. Un timeout o un 5xx no puede convertirse en miles de "no validado".
   - Idempotente y reanudable.

### Fase 2 — Módulo de reportes (PR 2)

1. Navegación: nueva entrada "Reportes" en el bloque Centro de Infancia de
   `templates/includes/sidebar/opciones.html` (~línea 440), hermana de "Ver
   Centros de Infancia". `opciones.html` es el sidebar vivo; los `new_*` no se
   tocan.
2. Ruta y vista: `/centrodeinfancia/reportes/` con `ReportesCDIView` en
   `centrodeinfancia/views_reportes.py`. Pantalla simple con la descarga y, si
   hace falta, filtro por provincia dentro del alcance del usuario.
3. Servicio `centrodeinfancia/services_reportes.py` con las tres consultas
   resueltas por ORM, no por SQL cruda:
   - CDI: `select_related` de provincia, departamento IPI, municipio y
     localidad; `prefetch_related` de horarios de funcionamiento y oferta de
     servicios; `Exists` sobre `AccesoCDI` activo para
     `referente_con_acceso_activo`.
   - Trabajadores: filtrados por los centros del alcance, con `select_related`
     territorial. La columna `campos_verificados_renaper` se mantiene como está
     en el adjunto; significa otra cosa que el indicador de nómina y eso se
     documenta.
   - Nómina: filtrada por los centros del alcance, con las columnas del adjunto
     más `renaper_nino`, `renaper_responsable_1` y `renaper_responsable_2`
     calculadas por el servicio compartido de la Fase 1.
   - Los tres soportes usan el manager por defecto, que ya excluye borrados
     lógicos, e `iterator()` con `chunk_size` sobre un
     `Workbook(write_only=True)` de openpyxl, ya presente en
     `requirements/base.txt`.
4. Salida: un XLSX con las hojas `CDI`, `Trabajadores` y `Nomina`, con los
   mismos encabezados y el mismo orden de columnas del archivo adjunto al
   issue, para que lo ya validado por el equipo siga sirviendo. Encabezados
   nuevos solo al final de la hoja de Nómina.
5. Permisos y privacidad: `centrodeinfancia.view_centrodeinfancia` más el
   permiso de exportación que ya usa el listado CDI, alcance por
   `aplicar_scope_centros_cdi`, respuesta con `Cache-Control: private, no-store`
   como el PDF provincial, y registro en log de quién descargó qué y cuántas
   filas. El reporte contiene datos personales de niños, salud, discapacidad y
   responsables.

## Volumen y modo de generación

El adjunto tiene 125 CDI, 1142 trabajadores y 3800 fichas de nómina. Con
`write_only` e `iterator()` la generación sincrónica es adecuada. Se deja un
umbral logueado para revisar una generación asincrónica si el universo crece
de forma relevante.

## Validación

- Tests de alcance del reporte por rol: nacional, EGP territorial, referente
  CDI, trabajador CDI y auditoría.
- Test de paridad de encabezados y orden de columnas contra el contrato del
  adjunto.
- Test de coincidencia del indicador RENAPER entre el PDF provincial y el
  reporte, sobre los mismos datos.
- Tests del alta de nómina: token válido marca validado; `origen_dato`
  falsificado no marca nada; token de otro CDI o de otro usuario se ignora.
- Tests del comando con `consultar_datos_renaper` mockeado, incluidos el caso
  de discrepancia de datos y el de error sistémico que no debe marcar.
- `black .`, `pylint centrodeinfancia/`, `djlint templates/ --check`,
  `pytest centrodeinfancia/tests/ -v` y `makemigrations --check`.

## Riesgos

- La revalidación por lotes dispara hasta ~3800 consultas externas. Requiere
  ventana acordada, `--limit` y corrida previa con `--dry-run`.
- Marcar `VALIDADO` es afirmar identidad verificada. Por eso la comparación de
  apellido, nombre y fecha de nacimiento es parte de la regla y no un extra.
- Las columnas de responsables legales seguirán en "No" mientras no exista una
  decisión sobre persistirlos como ciudadanos.
- El reporte concentra datos personales sensibles en un archivo descargable.

## Documentación

- Actualizar `docs/implementaciones/centrodeinfancia_nomina_renaper.md` con el
  contrato de marcado de validación.
- Nuevo `docs/implementaciones/centrodeinfancia_reportes.md` con columnas,
  alcance y permisos.
- Registro en `docs/registro/cambios/` y actualización de `AGENT_REPO_MAP.md`.
