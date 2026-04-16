# Optimizacion de listados pesados visibles

Fecha: 2026-04-14

## Alcance

Se optimizaron primero los listados web mas visibles y potencialmente mas pesados:

- `Comedores`
- `VAT / Centros`
- `Centro de Familia / Centros`
- `Organizaciones`

## Cambios aplicados

- Se agrego un helper compartido en `core/pagination.py` para paginar sin `COUNT(*)` exacto.
- Se actualizo `templates/components/pagination.html` para no renderizar el total cuando el paginador no lo expone.
- Se ajusto `templates/components/search_bar.html` para que los listados AJAX no muestren un contador invalido cuando `count` es `null`.
- `Comedores` ahora pagina sin count exacto y cachea la configuracion dinamica de filtros.
- `VAT / Centros` y `Centro de Familia / Centros` pasaron a paginar en dos pasos:
  - primero se consulta solo la lista de ids de la pagina,
  - luego se hidratan solo las filas visibles.
- En `VAT / Centros` y `Centro de Familia / Centros` se elimino el orden alfabetico del listado y se reemplazo por orden estable por `-id`.
- `Organizaciones` paso a usar paginacion sin count exacto, ids -> hydrate y el mismo criterio nuevo tanto en listado como en AJAX.
- Se actualizaron indices concretos para los patrones nuevos de scope y busqueda:
  - `VAT.Centro`: `(provincia, id)` y `(referente, id)`
  - `Centro de Familia.Centro`: `(referente, id)`
  - `Organizacion`: `(telefono)`

## Decision clave

Se eligio una estrategia hibrida:

- helper compartido para la paginacion sin count,
- tuning quirurgico por vista para no forzar un refactor transversal de todos los listados.

Esto deja mejoras reales de performance sin cambiar la UX visible ni mezclar refactors grandes.

## Supuestos

- En `VAT / Centros` y `Centro de Familia / Centros`, una busqueda numerica se interpreta como `codigo` o `id`.
- En `Organizaciones`, una busqueda numerica se interpreta como `CUIT`, `telefono` o `id` completos.
- No se intento mantener un total exacto de resultados en los listados optimizados.

## Validacion esperada

- Entrar a cada listado y navegar varias paginas.
- Probar busqueda textual y numerica.
- Verificar que ya no aparezca el total exacto de resultados cuando la vista usa paginacion sin count.
- Verificar que los endpoints AJAX sigan devolviendo HTML y paginacion sin errores.
