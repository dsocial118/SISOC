# VAT - validacion de rango horario en comision de curso

- Se agrego validacion para impedir que `Hora Hasta` sea menor a `Hora Desde` en horarios de comision.
- El modal de horarios del detalle de comision de curso ahora bloquea ese caso antes del envio.
- Se agrego test de regresion para el POST invalido en la creacion de horarios de comision de curso.