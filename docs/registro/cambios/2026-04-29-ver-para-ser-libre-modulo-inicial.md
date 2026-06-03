# Modulo inicial Ver Para Ser Libres

## Contexto

Se incorpora el modulo `ver_para_ser_libre` a partir de la documentacion funcional preliminar del programa VPSL.

## Cambio

- Nueva app Django con modelos de itinerario, jornada, checklist, registro nominal, caso de laboratorio, cierre diario e historial de estados.
- Servicios de workflow para presentar/aprobar itinerarios, habilitar jornadas, crear casos post-operativos y generar cierres diarios.
- Pantallas server-side para bandeja, detalle y carga operativa basica, reutilizando componentes visuales existentes.
- Integracion minima en `INSTALLED_APPS`, URLs globales y sidebar.
- Tests unitarios de reglas funcionales criticas.

## Supuestos

- La primera version implementa un MVP operativo y no una historia clinica completa.
- La carta de adhesion puede registrarse como adjunto o referencia administrativa.
- La unicidad obligatoria se aplica al numero de acta dentro de la jornada.
- Los permisos iniciales usan permisos Django automaticos por modelo.

## Ajustes funcionales del 2026-05-04

- Se agrega tabla `SedeVPSL` y selector multiple con autocompletado para sedes del itinerario.
- Las jornadas eligen una sede vinculada al itinerario y usan el rango de fechas aprobado.
- El checklist pasa a asociarse a la sede y guarda historial de cambios.
- El cierre diario compara cantidades ingresadas contra recuentos nominales y habilita subsanacion cuando no coinciden.
- Los casos de laboratorio avanzan por estado siguiente y guardan historial por fecha, responsable y usuario.
