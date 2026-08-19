# Issue 2304: urgentes CDI

Estado: aprobado por el solicitante el 2026-08-18.

## Objetivo

Corregir en una única entrega los alcances territoriales de SIMEPI/CDI, las
validaciones de las nóminas de niños y trabajadores, dos regresiones de interfaz
y la limpieza del comunicado obsoleto indicado en el issue 2304.

El desarrollo parte del SHA remoto vigente de `main` (`2feaec9246a5`) y se
publica en un único PR hacia `homologacion`. No interviene `development`; la
promoción posterior de `homologacion` a `main` queda fuera de esta entrega.

## Alcances y autorización

Los querysets de CDI, nóminas, trabajadores y usuarios deben aplicar el alcance
más restrictivo que resulte de combinar rol y vinculación territorial:

- los roles nacionales conservan alcance nacional;
- EGP ve y administra solamente entidades y usuarios de su provincia;
- Referente CDI y Trabajador ven solamente su CDI;
- un rol territorial sin provincia o sin vínculo CDI falla cerrado y no recibe
  un queryset global por omisión;
- listados y operaciones directas por URL usan el mismo alcance.

El alcance territorial se agrega como intersección del alcance de delegación de
roles ya existente en Usuarios. No se amplían permisos Django.

## Formularios y presentación

### Nómina de niños

- `cuit_nino` pasa a ser obligatorio; los CUIT de los responsables legales
  siguen siendo optativos por definición explícita del solicitante.
- Lenguajes se mantiene obligatorio tanto en servidor como en la presentación.
- Talla, peso, longitud acostado y perímetro cefálico son optativos. Si se
  informan, conservan las validaciones de formato y rango existentes.
- La pregunta `recibe_apoyo_desarrollo` se muestra en la sección Discapacidad,
  sin cambiar el campo persistido ni perder datos existentes.

### Nómina de trabajadores

- La función correspondiente al subcomponente elegido es obligatoria.
- Para subcomponente CDI, Sala también es obligatoria.
- El selector de Sala debe conservar y guardar el valor enviado; el JavaScript
  sincroniza visibilidad y atributo `required` sin deshabilitar el control
  activo.
- Lenguajes se mantiene obligatorio.
- Email es obligatorio al crear un trabajador para habilitar la provisión
  automática de su usuario. Las ediciones de registros históricos sin email
  siguen siendo posibles para no bloquear correcciones ajenas.

## Regresión 403 de Grupos

El menú de administración se muestra al EGP porque puede administrar usuarios,
pero el enlace hijo Grupos se renderiza sin comprobar `auth.view_group`. Se
condiciona ese enlace a su permiso específico en las variantes vigentes del
sidebar. El endpoint conserva el 403 ante acceso directo: ocultar la opción no
implica conceder al EGP acceso global a grupos.

## Comunicado obsoleto

El código vigente no crea comunicados con el título indicado. Se agrega una
migración de datos acotada que cambia de `publicado` a `archivado` los
comunicados internos cuyo título comience con `Importación de nómina`. Así dejan
de mostrarse al EGP sin una eliminación física irreversible.

El reverse de la migración es deliberadamente un no-op: republicar por título
podría reactivar comunicados que ya estaban archivados antes del despliegue. El
registro queda preservado y puede recuperarse de forma manual y selectiva.

## Validación

- tests de alcance para roles nacionales, EGP, Referente CDI y Trabajador,
  incluidos intentos por URL y roles sin vínculo;
- tests del alcance territorial del listado/ABM de usuarios;
- tests de formularios para obligatoriedad condicional, Sala persistida, CUIT
  del niño, lenguajes y antropometría optativa;
- test de render del sidebar para que EGP no vea Grupos y un usuario autorizado
  sí lo vea;
- test de la migración de datos para coincidencias y no coincidencias;
- formateo y lint acotados a los archivos modificados;
- pytest focalizado con base de pruebas, sin datos reales.

## Riesgos y rollback

El riesgo principal es filtrar de más a usuarios con configuración incompleta.
Ese comportamiento es intencional para evitar una fuga nacional y queda
cubierto por tests de fail-closed. La compatibilidad de formularios históricos
se conserva haciendo obligatorio el email solo en altas.

El rollback de código es revertir el PR. La migración no elimina filas ni cambia
el esquema; si hiciera falta recuperar un comunicado, se republica solamente el
registro confirmado por operación.
