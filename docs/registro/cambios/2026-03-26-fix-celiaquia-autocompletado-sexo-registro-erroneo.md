# Fix Celiaquía: autocompletado de sexo en registros erróneos

## Fecha
2026-03-26

## Contexto
En el detalle de expediente de Celiaquía, cuando la importación de Excel fallaba por otra columna (por ejemplo `localidad`), el formulario de `RegistroErroneo` no preseleccionaba `sexo` si el valor original venía abreviado (`M` o `F`).

## Cambios aplicados
- Se ajustó el template de edición de registros erróneos para mapear abreviaturas `M/F` a opciones `Masculino/Femenino` tanto para beneficiario como para responsable.
- Se agregó test de regresión para validar que, ante error en otra columna, el formulario mantiene preseleccionados los campos `sexo` y `sexo_responsable` cuando llegan como `M/F`.
- Se ajustó el endpoint de actualización de `RegistroErroneo` para persistir los cambios de formulario incluso si la validación global todavía falla (guardado parcial con error de validación).
- Se ajustó el JS de registros erróneos para forzar guardado de cambios pendientes antes de ejecutar `Reprocesar`, evitando condiciones de carrera por debounce.
- Se corrigió la visibilidad del botón `Reprocesar Todos` para perfiles con gestión (provincial, coordinador o admin) y se unificaron permisos de endpoints de actualización/reproceso/eliminación de registros erróneos.
- Se agregó fallback de carga de `municipios` y `localidades` para gestión central cuando no hay provincia resoluble en el expediente (evita combos vacíos).
- Se reemplazó `localidad_responsable` de texto libre a selector para reducir errores de validación y se robusteció el resolver para aceptar formatos como `Localidad (Municipio)`.

## Impacto
- Mejora de UX en corrección de registros erróneos: se preserva y muestra más información válida durante la subsanación.
- Se mantiene la misma validación de negocio y obligatoriedad, pero sin perder correcciones parciales del operador.
