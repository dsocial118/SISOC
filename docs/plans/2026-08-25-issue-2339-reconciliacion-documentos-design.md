# Diseño aprobado: reconciliación de comprobantes de rendiciones (#2339)

## Estado

Aprobado el 2026-08-25 para implementación. El objetivo es preservar todos los
documentos de producción, incluso los dados de baja lógica.

## Contexto

La migración `rendicioncuentasmensual.0017` separó la categoría legacy
`comprobantes` en `comprobantes_alimentario` y `comprobantes_siph`, y trasladó
los registros visibles a la primera categoría. El manager `objects` usado en
esa migración excluye filas con `deleted_at` no nulo.

Cambiar `0017` no es seguro porque ya puede haber sido aplicada en homologación
u otros entornos. La reconciliación debe ser una migración nueva que también se
ejecute en esos entornos.

## Decisión

Crear `rendicioncuentasmensual.0019_reconciliar_comprobantes_legacy`, dependiente
de `0018_stage_permissions`.

La migración usa el manager histórico `all_objects` y el alias de conexión que
recibe Django para actualizar únicamente `comprobantes` a
`comprobantes_alimentario`.

No modifica IDs, archivos físicos o sus rutas, estados, relaciones de rendición
o subsanación, fechas ni información de bajas lógicas. Las categorías ya
creadas por PWA (`comprobantes_alimentario` y `comprobantes_siph`) no se tocan.
La operación es idempotente.

## Reversión

La reversa es intencionalmente `noop`. No existe una conversión inversa segura:
`comprobantes_alimentario` puede provenir tanto del registro legacy como de una
carga nativa PWA. Una reversa automática mezclaría ambos orígenes y podría
ocultar documentos SIPH al volver al código anterior.

El rollback operativo completo requiere una ventana sin escrituras y restaurar
el backup tomado antes de migrar junto con el código anterior.

## Validación

La prueba de regresión cubre documentos activos y dados de baja lógica, los tres
estados posibles, ruta de archivo, identificadores, relaciones de subsanación,
fechas y categorías PWA preexistentes. También confirma que una segunda
ejecución no cambia datos adicionales y que la reversa es `noop`.

La ejecución desde el estado histórico `0018` se marca `mysql_compat`: la suite
SQLite habitual desactiva las migraciones y no puede representar ese estado. El
job MySQL de CI mantiene el historial de Django y ejecuta esa cobertura.

## Rollout de producción

1. Verificar un backup recuperable antes de comenzar.
2. Detener temporalmente instancias que todavía escriban la categoría legacy.
3. Guardar conteos agregados por categoría, estado y condición de baja lógica.
4. Ejecutar las migraciones hasta `0019`.
5. Exigir cero filas `comprobantes`; el total de filas y los conteos por estado
   y baja lógica deben mantenerse. El incremento de Alimentaria debe equivaler
   al conteo legacy previo y SIPH debe permanecer constante.
6. Iniciar solo el código que reconoce ambas categorías nuevas y comprobar la
   visibilidad en SISOC de un documento legacy migrado, uno de Alimentaria PWA
   y uno de SIPH PWA.
