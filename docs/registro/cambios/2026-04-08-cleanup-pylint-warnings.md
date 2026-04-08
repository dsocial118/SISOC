# Limpieza de warnings de pylint

Se ajustaron varios módulos para eliminar warnings estructurales de pylint sin
cambiar el comportamiento funcional:

- `comedores.api_serializers` dejó de acceder a un helper protegido de
  `RendicionCuentaMensualService`.
- `pwa.api_serializers` implementó `create` y `update` en un serializer de
  configuración para satisfacer la clase base de DRF.
- `pwa.api_views` movió helpers de resumen y serialización a un módulo de apoyo
  para reducir complejidad del archivo.
- `rendicioncuentasmensual.services` delegó la construcción de documentación y
  la generación de PDFs a helpers externos para bajar el tamaño del módulo.
- `rendicioncuentasmensual.views` expuso un formatter público para reutilizarlo
  desde la vista de descarga PDF.

No hubo cambios de contrato observables ni modificaciones de payloads.
