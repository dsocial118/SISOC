# VAT - fix edicion de cursos y comisiones desde centro detalle

- Se ajustaron los querysets usados por los modales de `#cursos` para que en edición conserven el plan curricular, vouchers, curso y ubicación actualmente vinculados aunque hoy queden fuera de los filtros normales (por ejemplo, registros legacy o inactivos).
- Los endpoints AJAX de alta/edición de cursos y comisiones de curso ahora devuelven JSON explícito en éxito y error, evitando que el frontend cierre el modal como si hubiera guardado cuando el formulario fue rechazado.
- El JS del detalle de centro ahora limpia y muestra errores de formulario devueltos por backend antes de permitir recargar el panel.
- Se agregaron tests de regresión para el contexto del panel y para los rechazos AJAX en update de curso/comisión.
