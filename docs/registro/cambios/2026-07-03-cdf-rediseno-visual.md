# CDF: rediseño visual del módulo Centro de Familia

## Fecha
2026-07-03

## Objetivo
Modernizar el diseño del módulo CDF manteniendo la identidad SISOC, tomando
como referencia el lenguaje visual del módulo VAT (navy/teal/dorado).

## Lenguaje visual
Nuevo stylesheet compartido `static/custom/css/cdf.css`, todo scopeado bajo
`.cdf-page` para no afectar otros módulos:
- Superficies navy `#232D4F` con cabeceras teal `#3B8681` y texto blanco
  (mismas que VAT); acentos dorados `#E7BA61`; verde `#6EA015` / rojo
  `#C62828` para estados.
- Tipografías: Lora (títulos y cifras, como VAT), Montserrat (cabeceras de
  sección), Source Sans Pro (cuerpo, la estándar de SISOC).
- Componentes: hero de página con acciones integradas, tarjetas de métricas
  con borde izquierdo de color, cards con cabecera teal, tablas con thead
  navy profundo, pills de estado, botones pill, pestañas dentro de card,
  estados vacíos y skin scopeado para los listados que usan componentes
  compartidos (search_bar, data_table, pagination, partial AJAX de filas).

## Páginas rediseñadas
- `centros/centro_detail.html`: hero con acciones, métricas (absorben la
  ex-card "Nómina Asistentes"), Información + Ubicación, card "Actividades"
  con pestañas En curso / Todas (antes dos cards separadas), Referente +
  Observaciones, card "Gestión del centro" con pestañas Centros adheridos /
  Informes CABAL. Se eliminó el acordeón horizontal de solapas verticales y
  los contenedores de gauges sin JS que los alimente (código muerto).
- `centros/actividadcentro_detail.html` y
  `centros/actividadcentro_asistencia.html`: hero + ficha + tablas del mismo
  lenguaje.
- Listados (`centro_list`, `actividadcentro_list`,
  `participanteactividad_list`): skin CSS scopeado sobre el markup compartido,
  sin tocar componentes globales ni el partial AJAX.

## Compatibilidad
- Todos los IDs que consume `static/custom/js/centrodefamilia.js` se
  mantienen (`filterCentros`, `tablaCentros`, `searchCurso`,
  `searchActividades`, `expedientes-container`, contenedores de paginación).
- Script nuevo con nonce en centro_detail: reactiva la pestaña "Todas las
  actividades" cuando la URL trae `page_act`/`search_actividades`.
- Los formularios siguen usando `components/form_card.html` (estándar SISOC).

## Validación
`pytest centrodefamilia/tests/ tests/test_centro_views_unit.py` (41 pasan),
djlint sobre los templates tocados y smoke con test client sobre las páginas
renderizadas.
