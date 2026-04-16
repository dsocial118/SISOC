# VAT - validacion de fechas en comision de curso

- Se reforzo la carga de `Nueva Comision de Curso` para impedir en el modal que `Fecha de Fin` quede antes de `Fecha de Inicio`.
- El submit AJAX del detalle de centro ahora respeta `checkValidity()` antes de enviar.
- Se agrego test de regresion para el POST invalido en la creacion de comisiones de curso.