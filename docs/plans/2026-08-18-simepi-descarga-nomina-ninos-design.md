# Descarga provincial de nomina de ninos SIMEPI

Fecha: 2026-08-18

Estado: diseno aprobado

Rama base: `main`

Rama de trabajo: `codex/simepi-descarga-nomina-ninos`

## Objetivo

Permitir que un usuario con el rol exacto `SIMEPI - EGP` descargue un PDF con
la nomina activa y unica de ninos correspondiente exclusivamente a su
provincia. El documento debe seguir la especificacion funcional entregada en
`Descargable_Ninos.docx`, incluyendo datos del usuario, del CDI, del nino y de
su primer adulto responsable.

La funcionalidad se desarrolla desde `main`. La misma rama se presenta primero
contra `homologacion` para validar HML y, despues de esa validacion, contra
`main`. No interviene `development` y el segundo PR no debe incorporar commits
exclusivos de `homologacion`.

## Alcance funcional

- Mostrar `Descargar nomina de ninos` solamente a usuarios del grupo
  `SIMEPI - EGP`.
- Repetir la autorizacion en el servidor; ocultar el boton no es un control
  suficiente.
- Resolver una unica provincia completa desde el alcance territorial explicito
  del perfil EGP.
- Rechazar la descarga si el usuario no tiene exactamente una provincia
  completa.
- Incluir solo fichas `NominaCentroInfancia` activas y no eliminadas cuyos CDI
  pertenezcan a esa provincia.
- Omitir CDI sin ninos activos.
- Agrupar las filas por CDI y repetir el encabezado del CDI y de las columnas
  en cada pagina correspondiente.
- Agregar una ultima pagina con la cantidad total provincial.
- Generar el archivo en memoria o en un directorio temporal y no persistirlo en
  `MEDIA_ROOT`.

## Autorizacion y privacidad

El endpoint debe exigir autenticacion y pertenencia efectiva al grupo
`UserGroups.SIMEPI_EGP`. Otros roles SIMEPI, referentes CDI, trabajadores,
usuarios sin alcance y usuarios anonimos no pueden descargar el archivo.

El queryset debe quedar acotado por el alcance territorial antes de leer la
nomina. No se aceptan provincia, CDI ni identificadores de personas enviados
por el cliente.

La respuesta se entrega como attachment e incluye `Cache-Control: private,
no-store` y `Pragma: no-cache`. Los errores y logs pueden registrar solamente
identificadores internos, provincia, cantidad de filas y tipo de error; nunca
DNI, CUIL, nombres, payloads RENAPER ni contenido del PDF.

## Fuentes y reglas de datos

### Usuario EGP

- Provincia: unica provincia completa de `ProfileTerritorialScope`.
- Rol mostrado: literal `SIMEPI - EGP`.
- Usuario: `request.user.username`.
- Nombre: `first_name` y `last_name`.
- CUIT/CUIL: `request.user.profile.cuil`; si esta vacio, mostrar `-`.

### CDI

- Identificador: `CentroDeInfancia.codigo_cdi`.
- Nombre: `CentroDeInfancia.nombre`.
- Referente: `nombre_referente` y `apellido_referente`.
- CUIT/CUIL del referente: buscar un unico `AccesoCDI` activo cuyo email de
  usuario coincida con `CentroDeInfancia.email_referente` y usar
  `user.profile.cuil`. Ante ausencia o ambiguedad, mostrar `-`; no elegir un
  acceso arbitrariamente.
- Cantidad: cantidad de filas activas y unicas del CDI despues de aplicar la
  deduplicacion provincial.

### Nino

Los valores visibles siguen el contrato actual de la nomina CDI: valor de
`NominaCentroInfancia` y, cuando falte, fallback al `Ciudadano` vinculado.

- Apellido, nombre, DNI, fecha de nacimiento y sexo: valores resueltos con el
  fallback anterior.
- Edad: calculada a la fecha y hora de descarga.
- Medida: `Meses` o `Anos` segun `edad_unidad`. Si falta la unidad o la fecha de
  nacimiento, mostrar `-` sin inferir un dato nuevo.
- RENAPER: `Si` solo cuando el ciudadano tiene
  `estado_validacion_renaper == Ciudadano.RENAPER_VALIDADO`; en cualquier otro
  estado, `No`.

### Adulto responsable 1

- Apellido, nombre, CUIT/CUIL y fecha de nacimiento: campos
  `responsable_legal_1_*`.
- RENAPER: localizar en una unica consulta masiva los ciudadanos cuyo DNI
  coincida con `responsable_legal_1_dni`. Mostrar `Si` solo para una coincidencia
  validada; mostrar `No` si no existe, es ambigua o no esta validada.

## Unicidad y orden

La clave de deduplicacion pedida por la especificacion es la tupla normalizada:

1. apellido;
2. nombre;
3. DNI;
4. fecha de nacimiento;
5. sexo.

La normalizacion es solo para comparar: trim, espacios repetidos y
case-insensitive en texto. Los valores impresos conservan el dato resuelto.

La regla de vigencia actual evita nuevas fichas activas simultaneas en distintos
CDI. Para duplicados historicos, se conserva la ficha activa mas reciente por
`fecha` e `id`. Se registra solamente la cantidad de duplicados omitidos.

El orden es:

1. medida (`Meses`, luego `Anos`, luego sin dato);
2. edad numerica ascendente;
3. apellido;
4. nombre;
5. DNI;
6. `id` como desempate tecnico estable.

## Generacion del documento

Se recomienda un pipeline en dos etapas:

1. Crear un PDF vectorial intermedio con ReportLab.
2. Rasterizar cada pagina a JPEG mediante `pdf2image` y Poppler.
3. Crear el PDF final A4 horizontal colocando un unico JPEG a pagina completa
   en cada pagina.

El contenedor ya incluye ReportLab, Pillow, pdf2image, Poppler y Liberation
Sans. Liberation Sans se utiliza como alternativa metricamente compatible con
Arial; incorporar Arial requeriria una fuente licenciada y una decision
operativa adicional.

La pagina usa A4 horizontal, margenes minimos, texto general de 10 puntos y
tabla de 9 puntos. Un canvas numerado o una segunda pasada debe conocer el total
para dibujar en cada pagina:

- marca de agua diagonal gris clara;
- provincia;
- usuario;
- fecha y hora local de la descarga;
- `Pagina X de Y`;
- pie de pagina equivalente.

Las columnas y encabezados de CDI se repiten en cada pagina. Los textos extensos
se envuelven dentro de un maximo de lineas definido; no se truncan valores de
identidad sin una marca visual.

## Manejo de errores

- Alcance inexistente o invalido: `PermissionDenied` sin revelar provincias.
- Sin filas activas: generar un documento valido con total provincial cero.
- Error de render o rasterizacion: respuesta 503 con mensaje generico.
- Archivos temporales: `TemporaryDirectory`, siempre eliminado al terminar.
- Tiempo de rasterizacion: timeout explicito y un solo worker para acotar
  memoria.

## Integracion de interfaz

El boton se incorpora en el listado de Centro de Infancia porque la descarga es
provincial, no de un unico CDI. Se reutiliza el soporte de botones adicionales
de `components/search_bar.html` y se agrega al contexto solamente para EGP.

## Enfoques descartados

### HTML y WeasyPrint

Facilita CSS, pero ofrece menos control determinista sobre trece columnas,
encabezados repetidos, marca de agua y numeracion total antes de rasterizar.

### DOCX y LibreOffice

Existe un patron similar en el repositorio, pero editar tablas variables y
controlar los saltos de pagina es mas fragil y agrega un proceso externo que no
aporta valor en este caso.

### PDF vectorial como salida final

Es la opcion mas simple, pero no cumple el requisito literal de que cada pagina
del PDF sea una imagen JPEG.

## Flujo de ramas y release

1. La rama nace del `origin/main` vigente.
2. Primer PR: `codex/simepi-descarga-nomina-ninos -> homologacion`.
3. Merge y despliegue de HML solo despues de CI completa.
4. Validacion funcional y visual en HML con datos sinteticos.
5. Segundo PR, desde la misma rama: `codex/simepi-descarga-nomina-ninos -> main`.
6. Comparar el diff contra `main` y confirmar que contiene solo la feature.

Antes del segundo PR se debe verificar en vivo la ruleset de `main`. La
automatizacion versionada actual documenta `release_baseline` para promociones
`development -> main`; si continua siendo obligatorio y no soporta esta rama,
el release queda bloqueado hasta disponer de un camino formal. No se quitan
checks, no se hace bypass y no se simula un baseline.
