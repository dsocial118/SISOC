# Issue 2339: reconciliación segura de comprobantes de rendiciones

## Alcance

Se incorporó la migración `rendicioncuentasmensual.0019` para completar la
reclasificación de `comprobantes` a `comprobantes_alimentario` en todos los
registros de `DocumentacionAdjunta`, incluidos los dados de baja lógica.

## Garantías

La migración modifica exclusivamente la categoría. Conserva archivo, estado,
relaciones, fechas, IDs y marcas de baja lógica. Los documentos creados por PWA
en `comprobantes_alimentario` o `comprobantes_siph` permanecen sin cambios.
La operación es idempotente y su reversa es `noop` para no mezclar documentos
legacy con cargas nativas de PWA.

## Despliegue

No aplicar mientras queden instancias antiguas capaces de escribir
`comprobantes`. Antes de ejecutar la migración en producción, tomar un backup
recuperable y registrar conteos agregados por categoría, estado y baja lógica.
Después, validar que no queden filas `comprobantes`, que SIPH conserve su conteo
y que Alimentaria haya aumentado exactamente por la cantidad legacy previa.
