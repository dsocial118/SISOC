# Visibilidad global de importaciones de expedientes

## Cambio

El listado de `/importarexpedientes/listar` muestra todos los lotes importados,
sin limitar los resultados al usuario que realizo la carga. La busqueda por
archivo o nombre de usuario se mantiene tanto en la vista normal como en AJAX.

Los usuarios autenticados que ya acceden al modulo tambien pueden abrir el
detalle, consultar sus errores por AJAX, descargar el archivo, completar la
importacion y borrar los datos importados de lotes creados por otros usuarios.
Los permisos especificos existentes para actualizar fechas de acreditacion no
se modifican.

La actualizacion de fechas de acreditacion queda limitada a los comedores
incluidos en el archivo de acreditaciones. Los expedientes de otros comedores
del mismo lote conservan su fecha previa, incluso si fue cargada manualmente, o
permanecen sin fecha si estaban vacios.

## Validacion

Se agrego una prueba de integracion que crea un lote perteneciente a otro
usuario y verifica listado, busqueda, detalle, descarga, importacion y borrado.
Tambien se cubre que una actualizacion selectiva no sobrescriba la fecha manual
de un comedor omitido del archivo.
