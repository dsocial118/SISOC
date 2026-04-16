# Diseño: defaults de importación de Celiaquía

## Fecha

2026-04-07

## Problema

En el formulario posterior a la importación de expedientes de Celiaquía todavía se mostraba `nacionalidad` como campo editable y la relación `localidad -> municipio` no se resolvía automáticamente en todos los puntos del flujo.

## Decisión

- Fijar `Argentina` como nacionalidad por defecto en registros erróneos y en el modal de edición de legajo.
- Ocultar el campo de nacionalidad en ambos formularios y enviar el valor resuelto en un input hidden.
- Derivar `municipio` desde `localidad` tanto en backend como en frontend para que el guardado y la UI queden alineados.

## Alcance

- `celiaquia/views/expediente.py`
- `celiaquia/views/legajo_editar.py`
- `celiaquia/templates/celiaquia/expediente_detail.html`
- `static/custom/js/registros_erroneos.js`
- `static/custom/js/expediente_detail.js`
- tests del flujo

## Validación prevista

- Regresión de render del detalle de expediente.
- Regresión de actualización de registro erróneo.
- Regresiones GET/POST del modal de edición de legajo.
- `black --check` sobre archivos Python tocados.
- `djlint --check` sobre el template tocado.
