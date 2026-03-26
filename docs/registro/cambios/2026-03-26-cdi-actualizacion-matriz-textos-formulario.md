# Actualización de matriz de textos en Formulario CDI

## Fecha
- 2026-03-26

## Contexto
- Se aplicó una matriz de cambios de copy para preguntas/opciones del Formulario CDI.
- Se confirmó que la pregunta de Seguridad Eléctrica debe ocultarse condicionalmente cuando el acceso a energía es `No tiene electricidad`.

## Cambios implementados
- Actualización de labels de preguntas en `centrodeinfancia/formulario_cdi_schema.py` según la matriz.
- Actualización de textos de opciones en `centrodeinfancia/forms_formulario_cdi.py` mediante overrides por campo.
- Ajuste de `Uso Exclusivo del Espacio` para opción `Sí`.
- Corrección de texto a `Por cañería dentro del CDI`.
- Corrección de redacción en Acceso a Internet (`El CDI ...`).
- Ocultamiento condicional de `Seguridad Eléctrica` en `formulario_cdi_form.html` cuando `electricity_access == sin_electricidad`.
- Limpieza backend del valor `electrical_safety` en `FormularioCDIForm.clean()` bajo la misma condición.
- Actualización de encabezados de tabla de Organización de Salas:
  - `Cantidad de Salas (A)`
  - `Cantidad de Personal de Sala (B)`
  - `Cantidad de personal por sala (B/A)`
  - fila `Totales`

## Validación
- Se agregaron tests en `centrodeinfancia/tests/test_formulario_cdi_form.py` para:
  - limpieza de `electrical_safety` cuando no hay electricidad,
  - verificación de textos actualizados en labels/opciones clave.
