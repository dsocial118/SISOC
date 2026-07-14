# CDI: rediseño visual de detalle y nómina

## Fecha
2026-07-13

## Objetivo
Aplicar al módulo Centro de Desarrollo Infantil (`/centrodeinfancia/`) la
propuesta de rediseño con el lenguaje visual SISOC (navy `#232D4F` / teal
`#3B8681` / dorado `#E7BA61`), el mismo que ya usan VAT y CDF.

## Lenguaje visual
- Se reutiliza `static/custom/css/cdf.css` (lenguaje compartido: hero, pills,
  botones, cards con cabecera teal, tablas, info-grid, skin de componentes
  compartidos) envolviendo las páginas en `.cdf-page`.
- Nuevo stylesheet `static/custom/css/centrodeinfancia.css`, scopeado bajo
  `.cdi-page`, solo con los componentes que la propuesta agrega y cdf.css no
  tiene: kicker y franja de stats dentro del hero, carpeta con solapas
  laterales verticales, tarjetas de métricas con punto de color y
  distribución por edad con barras.
- Nota: `static/custom/css/cdi.css` ya existía pero contiene estilos legacy
  de comedores/relevamiento; por eso el archivo nuevo se llama
  `centrodeinfancia.css`.

## Páginas rediseñadas
- `centrodeinfancia_detail.html`: hero con kicker, pills (código CDI +
  estado) y stats integradas (nómina, trabajadores, formularios, año de
  inicio); carpeta con solapas laterales (Información general + mapa +
  referente / Funcionamiento / Usuarios del centro, esta última condicionada
  a `puede_ver_usuarios_cdi`); resumen de nómina con tarjetas de stats y
  acceso a la nómina completa; cards con cabecera teal para Trabajadores
  (con búsqueda client-side, tabla sin paginación), Formularios y
  Seguimiento (pestañas Intervenciones / Observaciones sobre los
  `data_table` compartidos). Se eliminó el acordeón horizontal con loader y
  el bloque JS muerto de `trabajador_modal_open` (la vista nunca setea esa
  variable y referenciaba `trabajadorModalElement`, que no existe).
- `nomina_detail.html`: hero con kicker y ubicación; tarjetas de métricas
  (asistentes, hombres, mujeres, género X, menores, lista de espera);
  "Distribución por edad" colapsable con barras y porcentajes (marca
  `is-zero` los rangos vacíos); card de nómina con búsqueda y filtros
  client-side por estado y sala (las opciones de sala se arman desde las
  filas de la página actual), columna unificada "Apellido y nombre" con link
  al ciudadano, acciones planas (Ver / Editar / Derivar / Borrar) y
  paginación con el mismo `?page=`.

## Ajuste posterior (mismo día)
- La sección "Seguimiento" usa el componente compartido `data_table.html`,
  que envuelve la tabla en su propio `.row.mt-5 > .col > .card > .card-body`.
  Dentro de `.cdf-page` esa `.card` se re-estilizaba a navy con sombra y
  aparecía como una tarjeta flotante anidada con un hueco grande sobre las
  pestañas Intervenciones / Observaciones. Se agregó CSS scopeado en
  `centrodeinfancia.css` (`.cdi-page .cdf-card .tab-content ...`) que aplana
  ese wrapper (sin `.card`, sin sombra, sin márgenes/padding extra) para que
  la tabla quede al ras de la card de Seguimiento. No se tocó el componente
  compartido ni la vista.

## Ajuste posterior 2 (mismo día)
- Las pestañas Intervenciones / Observaciones se veían como lozenges
  gigantes (forma de estadio). Causa raíz: reglas globales de `main.css`
  para el sidebar/header (`.nav-item { min-height: 60px }` y
  `.nav-item .nav-link { height: 60px }`) se filtraban al componente
  compartido `.cdf-tabs` y estiraban los pills a 60px. Se corrigió en el
  propio componente (`cdf.css`): `.cdf-tabs .nav-item { min-height: 0 }` y
  `.cdf-tabs .nav-link { height: auto; min-height: 0 }`, más
  `align-items: center` en el riel y padding/line-height afinados. Beneficia
  también a CDF, que usaba el mismo componente con el mismo bug latente.

## Ajuste posterior 3 (mismo día)
- La página "Agregar a nómina" (`/centrodeinfancia/<pk>/nomina/crear/`,
  template `destinatario_form.html`) se veía rota. Dos causas:
  (1) el bloque de progreso usaba la clase `.progress-container`, que no
  existe en `comedorFormModerno.css` (la correcta es `.progress-indicator`,
  la que ya usa `trabajador_form.html`), así que quedaba sin su tarjeta;
  (2) ese bloque estaba fuera del `if` del formulario, por lo que en la
  carga inicial —antes de buscar un DNI— se mostraba una barra "0/10"
  suelta y sin estilo. Se movió el bloque dentro del `<form>` (con la clase
  correcta), replicando el patrón de `trabajador_form.html`. Ahora la carga
  inicial muestra solo la tarjeta de búsqueda por DNI y el progreso aparece
  junto con las secciones. El JS (`destinatarioForm.js`) usa los IDs
  `#progressBarFill` / `#completedSections`, no la clase del wrapper, así que
  no se vio afectado. Tests: `test_destinatario_views.py` +
  `test_destinatario_form.py` (34 pasan).

## Ajuste posterior 4 (mismo día)
- Los formularios `trabajador_form.html` y `destinatario_form.html` tenían el
  contenido pegado al borde izquierdo (título/breadcrumb/tarjeta de búsqueda
  cramped y algo cortados). Causa: a diferencia de `centrodeinfancia_form.html`
  —que envuelve su contenido en un `<div class="container-fluid">` extra— estos
  dos arrancaban el `block content` sin ese wrapper, quedando con la mitad del
  padding lateral. Se agregó el `<div class="container-fluid">` envolviendo el
  contenido en ambos, replicando el patrón del form de centro. Tests:
  `test_trabajadores_views.py` + `test_destinatario_views.py` +
  `test_destinatario_form.py` (41 pasan).

## Compatibilidad
- Se mantienen todos los contratos de JS existentes:
  `nomina_detail.js` (`.nomina-toggle-details`, `.nomina-toggle-icon`,
  `#detailedStatsContent`, `#editarNominaModal`/`#editarNominaForm`),
  `nomina_derivar.js` (`.nomina-derivar-btn` con `data-url`/`data-ciudadano`
  y los IDs del modal de derivación), `base.js` (`data-confirm-click`) y el
  script de detalle (subintervenciones AJAX, validación de fecha, filtro de
  tipos por programa, modal de eliminación de trabajador con
  `.trabajador-eliminar-btn`).
- Se conservan los textos que verifican los tests ("Trabajadores",
  "Apellido, Nombre", "Agregar trabajador" condicionado a permisos, clase
  `trabajador-eliminar-btn`).
- Los filtros nuevos de la nómina son client-side sobre la página actual
  (100 filas por página), igual criterio que la búsqueda previa.

## Validación
- `djlint --check` sobre los dos templates (0 issues tras reformat).
- `pytest centrodeinfancia/tests/` en Docker: 202 pasan. Se actualizaron dos
  asserts de `test_formulario_cdi_views.py` que estaban acoplados al markup
  del acordeón eliminado (`accordion-header--*`, "Informacion Basica",
  "Latitud:"), reemplazados por los marcadores del markup nuevo
  (`data-label="..."`, `<span>Formularios</span>`). Latitud y longitud se
  siguen mostrando en la grilla de información general.
- Nota de entorno: con el venv local (Python 3.14) 4 tests de
  `test_trabajadores_views.py` fallan por el bug de `copy(super())` en
  `django.template.context` — falla preexistente del entorno local, también
  ocurre sin estos cambios; en Docker (Python 3.11) no se reproduce.
