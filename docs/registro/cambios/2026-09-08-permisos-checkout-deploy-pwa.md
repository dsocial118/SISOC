# Permisos de lectura del backend durante el deploy PWA

## Causa confirmada

El primer despliegue coordinado de HML conservaba `umask 077` al ejecutar el
helper del backend. Git creaba los archivos actualizados con permisos 600 y
directorios nuevos con 700. Django podia arrancar con su usuario, pero cuatro
workers que usan otro UID fallaban con `PermissionError` sobre
`/sisoc/config/settings.py`. El healthcheck HTTP no detectaba esos reinicios.

## Correccion

HML y PRD ejecutan exclusivamente el helper del backend en un subshell con
`umask 022`. El codigo actualizado queda legible por los usuarios de los
contenedores. El shell exterior conserva 077 para el estado privado de PWA y
sus herramientas. No cambia permisos ni contenido de `.env`, claves SSH o
datos de aplicaciones.

En HML se recuperaron los permisos de 116 archivos versionados cambiados por
ese despliegue y siete directorios de codigo. Los cuatro workers dejaron de
reiniciarse; el modo de `.env` quedo intacto.

## Evidencia y limites

La prueba ejecuta el bloque real del workflow con sustitutos de Git y del
coordinador. Antes de la correccion falla en ambos entornos porque el archivo
de backend queda con 600. Despues exige codigo 644, directorios 755, estado
privado 700 y archivos privados 600, incluso despues de regresar del helper.

La verificacion operativa debe incluir los workers ademas del healthcheck
HTTP: un deploy verde por si solo no demuestra que todos los procesos esten
estables. Una reversion de esta correccion requiere evitar que la umask
privada vuelva a afectar la actualizacion del checkout.
