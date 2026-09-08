# 2026-08-18 - Descarga provincial de nomina SIMEPI para superadmin

## Objetivo

Permitir que un superadministrador descargue la nomina de ninos desde el
listado de Centros de Desarrollo Infantil, eligiendo obligatoriamente una
provincia antes de generar el PDF.

Este alcance surge de la instruccion posterior del usuario y amplía la regla
original del documento funcional, que habilitaba la descarga solamente al rol
SIMEPI - EGP.

## Decision

- El EGP mantiene la descarga directa para su unico alcance provincial
  completo.
- El superadministrador ve el mismo llamado a la accion en el listado, pero el
  boton abre un modal sin abandonar la pagina.
- El modal contiene un selector obligatorio con las provincias disponibles y
  envia la seleccion por `GET` al endpoint de descarga existente.
- Los demas usuarios no ven el boton y continúan recibiendo `403` si intentan
  acceder directamente al endpoint.

## Interfaz

El listado reutiliza el modal Bootstrap ya usado por el modulo. El boton
adicional del buscador admitira opcionalmente un destino modal, sin cambiar el
comportamiento de los botones que siguen siendo enlaces.

El modal muestra:

- titulo `Descargar nomina de ninos`;
- selector `Provincia` con opcion inicial vacia;
- boton para cancelar;
- boton `Descargar` que envia el formulario.

No se agregara JavaScript propio: la validacion HTML `required` evita el envio
normal sin seleccion y la validacion del servidor protege el acceso directo o
manipulado.

## Autorizacion y seleccion territorial

El endpoint resuelve la provincia en este orden:

1. Si el usuario es superadministrador, exige el parametro `provincia`, valida
   que identifique una provincia existente y usa exclusivamente esa seleccion.
2. Si es EGP, ignora cualquier parametro territorial recibido y usa su unico
   alcance provincial completo.
3. En cualquier otro caso, rechaza la descarga con `403`.

Una seleccion ausente o invalida del superadministrador devuelve `400` y no
invoca el generador del PDF. Esto mantiene separados un error de entrada y una
falta de permisos.

## Datos e integridad

La generacion sigue usando el servicio provincial existente. Por lo tanto:

- el filtro se aplica por la provincia del centro, no por el domicilio del
  nino;
- se conserva la deduplicacion reforzada por ciudadano, DNI e identidad
  historica;
- el nombre y el encabezado del PDF corresponden a la provincia elegida;
- no hay cambios de esquema, migraciones ni dependencias.

## Validacion prevista

- Superadmin ve boton y modal con selector obligatorio.
- Superadmin descarga solamente la provincia seleccionada.
- Superadmin sin provincia o con provincia invalida recibe `400` y no genera
  archivo.
- EGP conserva su descarga directa e ignora una provincia inyectada por URL.
- Usuario comun no ve el boton y recibe `403` en acceso directo.
- La suite focal de nomina conserva los casos de filtro provincial y no
  duplicacion.

