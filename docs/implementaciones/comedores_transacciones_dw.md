# Transacciones Nacion Servicios en legajo de comedor

## Objetivo

Mostrar informacion historica de transacciones Nacion Servicios asociadas a un comedor, usando la vista externa `DW_sisoc.vw_EC_resumen_transacciones`.

## Contrato de datos

El modelo `DWECRResumenTransacciones` es `managed = False` y mapea una vista externa del Data Warehouse.

Campos usados:

- `comedor_id_sisoc`: identificador del comedor en SISOC.
- `periodo`: periodo `YYYYMM`.
- `cantidad_debitos`: cantidad de movimientos.
- `credito_total`: monto utilizado o gastado.
- `debito_total`: monto transferido al comedor.
- `cereo`: remanente al cierre del periodo.

La fuente se considera de solo lectura; SISOC no migra ni administra esa vista.

## Superficies

- Legajo del comedor: muestra el ultimo periodo disponible si el usuario tiene permiso de ver comedor.
- Detalle `/comedores/<id>/transacciones`: muestra historico paginado.
- Servicio `DWTransaccionesService`: consulta la vista con SQL directo y devuelve objetos de lectura para templates.

## Operacion

- Si la vista DW no existe, no responde o falla la consulta, el servicio registra error y devuelve ausencia de datos para no romper el legajo.
- La paginacion del historico usa `COUNT(*)` sobre la vista DW; si el volumen crece o la vista se vuelve costosa, revisar indice/materializacion en la fuente DW antes de cambiar la UI.
- Esta integracion requiere que el usuario de base configurado para SISOC tenga permisos de lectura sobre `DW_sisoc.vw_EC_resumen_transacciones`.

## Riesgos

- El schema `DW_sisoc` queda fuera del control de migraciones Django.
- Cambios de nombres o tipos en la vista externa impactan en runtime aunque los tests locales pasen sin esa fuente.
