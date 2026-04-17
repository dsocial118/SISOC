# 2026-04-17 - Migración inicial de selects a Select2 por impacto UX

## Objetivo

Aplicar `Select2` sólo en los selects donde mejora la búsqueda, el escaneo visual o la interacción con datos dependientes, evitando una migración masiva sin criterio.

## Decisión aplicada

- Se adoptó un patrón declarativo en frontend para inicializar y refrescar `Select2` con `data-*` attributes.
- Se migraron campos relacionales grandes o dependientes en VAT.
- Se alineó `users` para usar el mismo criterio ya existente en edición.
- En Celiaquía se aplicó sólo en el detalle y el modal de edición, no en la grilla masiva.

## Cambios implementados

### Infraestructura Select2

- `static/custom/js/custom.js`
  - Nuevo helper global `initSelect2Elements`.
  - Nuevo helper global `refreshSelect2Element`.
  - Soporte declarativo para `data-placeholder`, `data-width`, `data-allow-clear`, `data-dropdown-parent` y parámetros de búsqueda.

### VAT

- `VAT/forms.py`
  - Nuevo helper `_select2_attrs(...)` para normalizar widgets Select2.
  - Migración de campos relacionales relevantes en formularios de alta/inscripción/oferta/comisión/vouchers.
- `static/custom/js/centro_create_form.js`
  - Refresco de Select2 cuando cambian provincia, municipio y localidad.
- `static/custom/js/centro_form.js`
  - Misma estrategia para el formulario de edición.
- `VAT/templates/vat/institucion/ubicacion_form.html`
  - Refresco de Select2 al limpiar, cargar y repoblar localidades dependientes del centro.

### Users

- `users/forms.py`
  - `UserCreationForm.provincia` ahora usa `select2`, consistente con el formulario de edición.

### Celiaquía

- `celiaquia/templates/celiaquia/expediente_detail.html`
  - Select2 en asignación de técnico del detalle.
  - Select2 en municipio/localidad del modal de edición con `dropdownParent`.
- `static/custom/js/expediente_detail.js`
  - El filtro de localidades por municipio pasó de ocultar opciones con CSS a reconstruir opciones válidas, para compatibilidad real con Select2.

## Exclusiones explícitas

- `VAT referente`: se mantiene el buscador nativo documentado previamente por problemas históricos con Select2.
- `Comunicados comedores`: se mantiene el selector custom actual porque ya resuelve mejor el caso de uso que un multiselect estándar.
- `Celiaquía listado masivo`: no se migraron los selects por fila para evitar costo visual y de performance.

## Validación esperada

- Buscar opciones por texto en selects grandes.
- Ver refresco correcto en selects dependientes al cambiar el padre.
- Confirmar funcionamiento dentro de modales sin problemas de ancho o dropdown fuera de contexto.
