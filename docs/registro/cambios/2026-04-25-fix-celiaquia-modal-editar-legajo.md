# Fix: modal editar legajo — carga de datos, municipio vacío y guardar cambios

## Fecha
2026-04-25

## Módulo
`celiaquia` — vista `EditarLegajoView`, JS `expediente_detail.js` / `expediente_detail_config.js`

## Problema reportado
Al intentar editar un legajo desde el expediente (`/celiaquia/expedientes/<pk>/`):
1. El modal mostraba "Error al cargar los datos del legajo."
2. El select de municipio aparecía vacío aunque el legajo tuviera municipio/localidad válidos.
3. Al intentar guardar se mostraba "La URL de edición del legajo no está configurada."

## Causa raíz (tres bugs independientes)

### Bug 1 — `EDITAR_LEGAJO_URL_TEMPLATE` nunca se inicializaba
`expediente_detail_config.js` inicializaba todas las URLs de la página excepto la del modal de edición. El meta tag `editar-legajo-url-template` existía en el template pero nadie lo leía en el config. El JS de `expediente_detail.js` tenía un fallback interno dentro del `DOMContentLoaded`, pero ese fallback solo corría si `window.EDITAR_LEGAJO_URL_TEMPLATE` era falsy — y como el config no lo seteaba, el fallback tampoco funcionaba porque la condición era `if (editarLegajoUrlTemplate && !window.EDITAR_LEGAJO_URL_TEMPLATE)` (siempre falsa cuando ambos eran null).

### Bug 2 — Sección EDITAR LEGAJO fuera del `DOMContentLoaded` principal
El `DOMContentLoaded` principal (arrow function `() =>`) cerraba su `});` antes de las secciones CONFIRMAR SUBSANACIÓN, PAGINACIÓN, BUSCADOR y EDITAR LEGAJO. Esas secciones corrían inmediatamente al cargar el script, antes de que el DOM existiera, por lo que `document.getElementById('modalEditarLegajo')` devolvía `null` y ningún listener se registraba.

### Bug 3 — `renderLocalidadesDisponibles` fuera de scope del listener `show.bs.modal`
La función `renderLocalidadesDisponibles` estaba declarada con `const` dentro del bloque `if (selectMunicipio && selectLocalidad)`. El listener `show.bs.modal` se registra después del cierre de ese `if`, en el scope del `if (modalEditarLegajo)`, por lo que no podía acceder a la función → `ReferenceError: renderLocalidadesDisponibles is not defined`.

Como el `show.bs.modal` fallaba antes de setear `formEditarLegajo.dataset.actionUrl`, el submit posterior no encontraba la URL → "La URL de edición del legajo no está configurada."

## Archivos modificados

| Archivo | Cambio |
|---|---|
| `static/custom/js/expediente_detail_config.js` | Agregar inicialización de `window.EDITAR_LEGAJO_URL_TEMPLATE` desde el meta tag |
| `static/custom/js/expediente_detail.js` | Mover sección EDITAR LEGAJO dentro del `DOMContentLoaded` principal; elevar `renderLocalidadesDisponibles` al scope de `if (modalEditarLegajo)`; agregar check `!response.ok` en GET; mostrar error real del servidor en GET y POST |
| `celiaquia/views/legajo_editar.py` | Devolver mensaje específico del `ValidationError` en lugar del genérico |
| `celiaquia/templates/celiaquia/expediente_detail.html` | Agregar query string de versión a los scripts modificados para cache busting |

## Comportamiento nuevo

- El modal de edición carga correctamente los datos del legajo incluyendo municipio y localidad.
- El select de municipio se pre-selecciona con el valor del legajo; las localidades se filtran por ese municipio.
- Los errores de validación del servidor se muestran con el mensaje específico (ej. "Fecha de nacimiento es obligatoria.") en lugar del genérico.
## Validación
- 38 tests pasando: `celiaquia/tests/test_legajo_editar.py` (4) + `tests/test_legajo_editar_view_unit.py` (5) + `tests/test_celiaquia_expediente_view_helpers_unit.py` (29).
- Verificado manualmente en browser con cache limpio.

## Supuestos
- El meta tag `editar-legajo-url-template` con `legajo_id=0` genera `/celiaquia/expedientes/<pk>/legajos/0/editar/`; el replace `/0/` → `/{id}/` es correcto para todos los expedientes.
- No se modificaron modelos, migraciones ni permisos.

## Fuera de scope (pendiente de definición)
- La regla de negocio sobre si los legajos en estado APROBADO o RECHAZADO deben poder editarse **no está definida**. No se implementó ninguna restricción al respecto. Cuando se defina, deberá agregarse la validación en `EditarLegajoView` (GET y POST) y el test de regresión correspondiente en `celiaquia/tests/test_legajo_editar.py`.
