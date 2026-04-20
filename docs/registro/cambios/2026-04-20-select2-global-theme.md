# 2026-04-20 - Tema global de Select2

## Objetivo

Unificar la apariencia de los campos `Select2` con buscador para evitar combinaciones de fondo claro y texto de bajo contraste en modales y formularios del sistema.

## Decisión aplicada

Se definió un tema global de `Select2` reutilizable, cargado desde la base común del proyecto, para que todos los selects con autocompletado compartan el mismo criterio visual sin depender de overrides locales por pantalla.

## Cambios implementados

### `templates/includes/base.html`

Se incorporó la carga de una hoja de estilos global dedicada a `Select2`.

### `static/custom/css/select2_theme.css`

Se agregó una hoja de estilos con el tema visual global para `Select2` en contexto `dark-mode`, contemplando:

- fondo y borde del selector;
- color del texto seleccionado;
- contraste del placeholder;
- campo de búsqueda interno;
- dropdown de resultados;
- estados hover y selección;
- variantes `single` y `multiple`.

## Alcance

El cambio impacta a los componentes `Select2` renderizados en las vistas que utilizan la base común y el esquema visual oscuro del sistema.

## Exclusiones explicitas

- No se mantuvieron cambios particulares por modal o por pantalla.
- No se modificó logica de backend ni validaciones de formularios.
- No se alteró el comportamiento funcional de provincia, municipio o localidad.

## Validacion esperada

- Los campos `Select2` con buscador deben verse con la misma gama cromática del resto del sistema. Se toma como referencia: Comedores/editar - Organización
- El texto dentro del selector y dentro del buscador debe conservar contraste suficiente respecto del fondo.
- El dropdown de opciones debe respetar el mismo criterio visual en los distintos modales y formularios.
