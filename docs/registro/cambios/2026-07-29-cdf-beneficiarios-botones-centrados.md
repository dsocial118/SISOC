# Botones de acción centrados en listado de preinscriptos CDF

## Cambio

Los botones de acción del buscador de beneficiarios (Crear un nuevo
preinscripto, Filtrar, Resetear, Descargar CSV) vuelven a estar centrados,
como en el resto de los listados del sistema.

## Contexto

La exportación CSV (2026-07-27) corrió toda la fila de acciones a la derecha:
primero con `search_actions_justify="justify-content-end"` y luego con la
regla `.cdf-beneficiarios-search .search-actions { justify-content: flex-end
!important; }` en `cdf.css`. La intención original era que `Descargar CSV`
fuera el último botón del grupo, no desplazar el grupo completo.

## Resolución

Se elimina la regla CSS y el wrapper `cdf-beneficiarios-search` (existía solo
como hook de esa regla). El componente compartido `search_bar.html` ya centra
las acciones con `justify-content-center`; `Descargar CSV` sigue siendo el
último botón del grupo.
