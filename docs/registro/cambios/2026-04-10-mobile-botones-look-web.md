# 2026-04-10 - Mobile: unificación visual de botones con look web

## Contexto

Se alineó el estilo de los botones de acción de mobile con el look and feel de los botones web de SISOC, tomando como referencia los listados y acciones principales del backoffice.

## Cambios realizados

- Se consolidó una base compartida de estilos en `mobile/src/ui/buttons.tsx` con variantes `primary`, `secondary`, `outline-secondary`, `success`, `danger` y `outline-danger`.
- Se aplicó la base compartida a botones de acción en modales y en los flujos mobile de:
  - Nómina general.
  - Nómina alimentaria.
  - Alta/edición/detalle de personas de nómina.
  - Actividades.
  - Rendición.
- Se mantuvieron los colores semánticos:
  - Azul para acciones principales.
  - Verde para altas/confirmaciones/guardado positivo.
  - Rojo para bajas o eliminación.
- Se preservó el redondeo propio de mobile:
  - Botones chicos y acciones inline con forma pill.
  - CTA grandes con radios amplios ya usados en la app.
- Los FAB circulares de alta (`+`) quedaron visualmente alineados con la nueva base, preservando su formato flotante.

## Alcance

- El ajuste apunta a botones de acción y confirmación.
- No se reinterpretaron como botones web los controles de navegación, expansión/colapso, tabs o chips de filtro que cumplen otro rol visual.

## Validación

- `npm run build` en `mobile/`
