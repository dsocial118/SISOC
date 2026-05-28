# 2026-05-28 - Tours guiados (driver.js) para el modulo VAT

## Resumen

Se integra [driver.js](https://github.com/kamranahmedse/driver.js) (v1.3.5)
para ofrecer tours guiados dentro del modulo VAT: un tour general del modulo
y un tour especifico por pantalla (centros, oferta institucional, comisiones,
inscripciones a oferta y asistencia de sesion).

El usuario pidio referenciar el fork `nilbuild/driver.js`. La release v1.4.0
del fork no publica `dist/` en la rama; al ser API equivalente se uso la build
oficial v1.3.5 de npm/jsdelivr. Para forzar el fork basta con regenerar el
bundle (`npm run build` del repo) y reemplazar el iife.

## Archivos nuevos

- `static/custom/js/driver.js.iife.js` - bundle v1.3.5.
- `static/custom/css/driver.css` - estilos de la libreria.
- `static/custom/js/vat_tour.js` - wrapper. Expone `window.SisocVatTour` con
  `runGeneral()`, `runSection(name)` y `currentSection()`. Filtra steps cuyo
  selector no exista para que el mismo tour funcione aun cuando una pantalla
  oculta items por permisos.
- `VAT/templates/vat/partials/tour.html` - partial reutilizable. Inyecta
  CSS + JS, el dropdown "Tour de ayuda" (flotante) y la configuracion en
  `window.SISOC_VAT_TOUR`. Acepta `vat_tour_section` para fijar la seccion
  y `vat_tour_autostart=False` para deshabilitar el auto-launch.

## Templates modificados

Se incluyo el partial dentro de `{% block customJS %}` en:

- `centros/centro_list.html`, `centros/centro_form.html`, `centros/centro_detail.html`
- `oferta_institucional/oferta_list.html`, `oferta_institucional/oferta_form.html`,
  `oferta_institucional/comision_list.html`, `oferta_institucional/asistencia_sesion.html`
- `inscripcion_oferta/list.html`, `inscripcion_oferta/form.html`

Las dos ultimas y `asistencia_sesion.html` no tenian bloque `customJS`; se
agrego solo para el include.

## Comportamiento

- Auto-launch del tour general la primera visita a cualquier pantalla VAT.
  Se persiste en `localStorage` bajo la key `sisoc_vat_tour_general_seen_v2`.
- Boton flotante (esquina inferior derecha) con dropdown:
  - "Tour de esta pantalla" -> `SisocVatTour.runSection()`.
  - "Tour general del modulo VAT" -> `SisocVatTour.runGeneral()`.
- Los selectores apuntan a estructura ya existente (`#simple-search-form`,
  `.search-actions a.btn-primary`, `table.table`, `form`, etc.) para no
  obligar a marcar elementos en cada template.

## Decisiones / supuestos

- Se carga la libreria solo donde se incluyo el partial (no global) para
  evitar peso en pantallas fuera de VAT.
- El script inline del partial usa `nonce="{{ request.csp_nonce }}"` para
  respetar la CSP del proyecto.
- Compatibilidad hacia atras preservada: no se modifico ningun componente
  compartido (`components/search_bar.html`, sidebar, base.html).

## Como probar

1. Iniciar sesion con un usuario que tenga `VAT.view_centro`.
2. Entrar a `/vat/centros/` -> al cargar, se lanza el tour general
   automaticamente (primera vez). Cerrar.
3. Boton flotante "Tour de ayuda" -> "Tour de esta pantalla": se debe
   resaltar el buscador, el boton "Agregar" y la tabla.
4. Limpiar `localStorage["sisoc_vat_tour_general_seen_v2"]` y recargar para
   ver de nuevo el auto-launch.
  Para secciones, limpiar keys con prefijo `sisoc_vat_tour_section_v2_`.
5. Repetir en `oferta_list`, `comision_list`, `asistencia_sesion`,
   `inscripcion_oferta_list/form` y formularios de centro.

## Riesgos

- Si una pantalla VAT futura no incluye el partial, no tendra boton ni
  auto-launch. Documentar para que se sume al patron.
- El selector generico `form` en pantallas con multiples formularios
  resaltara el primero. Si hace falta precision se puede pasar un selector
  mas especifico via `vat_tour_section` y agregar la entrada en
  `vat_tour.js`.
