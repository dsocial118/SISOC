# Centro de Infancia: oferta de servicios múltiple

- `CentroDeInfancia.oferta_servicios` pasó de un valor único a una relación ManyToMany contra un catálogo `OfertaServicio`.
- La data histórica de un solo valor se migra a la nueva relación mediante la migración `0026_oferta_servicio_multiple`.
- El detalle del CDI y el formulario de alta/edición ahora muestran y guardan múltiples servicios.
