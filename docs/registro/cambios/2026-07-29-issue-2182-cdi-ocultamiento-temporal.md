# Issue 2182: ocultamiento temporal de funcionalidades CDI

## Alcance

Se ocultan de la pantalla de detalle del Centro de Desarrollo Infantil:

- el acceso para tomar asistencia de nómina;
- el módulo de Formularios;
- la sección, lista y alta rápida de Intervenciones.

La sección de Observaciones permanece disponible. No se modifican modelos,
permisos, datos existentes ni rutas directas: el cambio es exclusivamente de
visibilidad de interfaz.

## Configuración y reversión

Las funcionalidades se controlan en `config/settings.py` mediante las variables
de entorno `CDI_ASISTENCIA_NOMINA_VISIBLE`, `CDI_FORMULARIOS_VISIBLE` y
`CDI_INTERVENCIONES_VISIBLE`. Todas quedan en `false` por defecto.

Cuando el programa autorice una reactivación, establecer en `true` únicamente
la variable correspondiente y reiniciar la aplicación. No requiere migración ni
modificación de datos.
