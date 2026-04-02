# Fix review findings PR 1419

## Contexto

Se corrigieron tres riesgos detectados durante la revisión del PR 1419 antes de promoverlo a producción:

- pérdida de datos al remover columnas legacy de `Curso`
- falta de constraints de base para el flujo `comision_curso`
- regresión de navegación en el sidebar de VAT

## Cambios

- se reforzó `VAT/migrations/0024_remove_curso_cupo_fechas.py` para crear una `ComisionCurso` legacy por cada `Curso` con datos operativos antes de eliminar `cupo_total`, `fecha_inicio` y `fecha_fin`
- se agregó `VAT/migrations/0030_add_comision_curso_integrity_constraints.py` con constraints `CHECK` y `UNIQUE` para `ComisionHorario`, `SesionComision` e `Inscripcion` en la rama `comision_curso`
- se actualizaron los modelos para reflejar esas garantías a nivel ORM
- se restauraron las entradas de VAT ocultadas en `templates/includes/sidebar/opciones.html`
- se agregaron tests de regresión para backfill, integridad y navegación

## Decisión clave

Se priorizó preservar compatibilidad con datos existentes de producción antes que asumir una base vacía. Por eso el backfill ocurre dentro de la migración destructiva, en el único punto donde todavía existen las columnas legacy.

## Riesgo residual

- si algún entorno no productivo ya ejecutó la versión vieja de `0024`, esos datos ya no pueden reconstruirse automáticamente porque las columnas legacy ya fueron eliminadas allí
- para producción, el camino de migración del branch queda protegido mientras `0024` no se haya ejecutado previamente
