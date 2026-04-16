# Reorganización del menú entre Administración del sistema y Configuración de Comedores

## Contexto

El menú lateral mezclaba opciones de administración técnica del sistema con configuraciones operativas usadas por el módulo Comedores.

## Cambio realizado

- Se definieron dos raíces principales independientes en el menú: `Administración del sistema` y `Configuración de Comedores`.
- `Administración del sistema` conserva las opciones previas del menú, excepto `Equipos Técnicos` y `Monto de Prestaciones`, que fueron movidas.
- `Configuración de Comedores` quedó limitada a `Equipos Técnicos` y `Monto de Prestaciones`.
- Se mantuvieron las validaciones de visibilidad según permisos existentes para no exponer accesos que antes no correspondían.
- Se alineó la misma reorganización en el sidebar alternativo.
- `Novedades del sistema` se reemplazó por un acceso de versión ubicado al fondo del sidebar.
- Ese acceso muestra dinámicamente la última versión publicada a partir de `CHANGELOG.md`, con formato corto (`vdd.mm.aa`).

## Validación

- Se agregó un test de regresión del sidebar para verificar que ambas raíces existan por separado y contengan solo los accesos esperados.
- Se fijó además el orden visual de las raíces principales del menú como: `Inicio`, `Legajos`, `Tableros`, `Administración del sistema`, `Configuración de Comedores`, `Comunicados`.
