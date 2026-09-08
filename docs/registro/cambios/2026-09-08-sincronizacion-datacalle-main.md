# Recuperar la sincronizacion de DataCalle desde main

## Evidencia y alcance

Los PRs #2452 y #2453 fueron fusionados directamente en main el 2026-09-06.
El workflow de sincronizacion descendente existe, pero la ejecucion 34264732085
fallo al fusionar hacia development y homologacion. config/urls.py expone la API
de DataCalle en main; en las otras ramas falta, y HML responde 404.

Esta entrega fusiona main en una rama basada en development y resuelve los tres
conflictos de usuarios. Conserva la historia de ambos lados para que la promocion
posterior vuelva al flujo development -> homologacion -> main. No inventa una
API ni sustituye la sincronizacion por copias de archivos de produccion.

## Resolucion

- users/forms.py conserva CoordinadorEquipoTecnicoPWA y el acceso seguro a
  Profile de development, sumando el rechazo de relevadores DataCalle en login
  de backoffice y los campos/validaciones de main.
- La plantilla conserva el controlador externo user_mobile_access.js. Se agrega
  alli la visibilidad del detalle DataCalle. No se recupera el JavaScript viejo
  que desmarcaba otros accesos automaticamente: la seleccion maestra de mobile
  conserva el contrato de development, y las combinaciones incompatibles siguen
  rechazadas por los formularios del servidor.
- Se conservan los tests de ambos lados. Una prueba JS adicional comprueba la
  visibilidad de DataCalle sin modificar el checkbox maestro de mobile.
- users/0051_merge_mobile_configuration_and_datacalle une las dos hojas 0050
  existentes. No tiene operaciones de schema ni de datos. Los cambios de schema
  de DataCalle ya versionados en main se aplicaran normalmente donde falten.

## Validacion y limites

- 96 tests de formularios PWA, login y DataCalle: pasan en Docker local aislado,
  con SQLite de pruebas en memoria. Incluyen permisos, alcance provincial,
  exclusividad de roles y contratos de API.
- 23 tests JS del formulario de usuarios: pasan.
- makemigrations users datacalle --check --dry-run: sin cambios pendientes.
- La reproduccion especifica del fallo MySQL verifica la forma de la consulta
  bajo SQLite; no sustituye los checks de compatibilidad MySQL de CI.
- La validacion de HML requiere el despliegue habitual de SISOC y sus migraciones.
  Este PR no modifica datos reales ni instala rutas Nginx. El empaquetado/activacion
  de las PWA y la correccion de los tres tests de Admisiones estan en #2474.
