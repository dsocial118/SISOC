# VAT: Oferta Materia con vouchers filtrados por programa

Fecha: 2026-03-31

## Cambio

En el formulario de Nueva Oferta Materia se agrega un selector multiple de vouchers habilitados para la oferta.

- El campo aparece cuando se marca Usa Voucher.
- Las opciones de vouchers se filtran por el programa seleccionado.
- Se valida que todos los vouchers elegidos pertenezcan al programa de la oferta.

## Persistencia

Se agrega una relacion many-to-many entre OfertaInstitucional y VoucherParametria para guardar los vouchers habilitados por oferta.

## Impacto en inscripciones

Al crear una inscripcion para una oferta que usa voucher:

- Si la oferta tiene vouchers seleccionados, se acepta solo un voucher activo del ciudadano que este dentro de ese conjunto.
- Si no hay voucher activo compatible, la inscripcion falla con mensaje de validacion.
