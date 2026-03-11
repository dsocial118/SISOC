## Cambio

Se agrego soporte PWA para exponer como mensajes los comunicados enviados a comedores desde la webapp.

## Alcance

- Nuevos endpoints PWA por espacio para listar y consultar mensajes.
- Accion para marcar mensaje como visto.
- Persistencia del estado de lectura por usuario y espacio dentro de `pwa`.
- Auditoria PWA del marcado de lectura.

## Implementacion

- Los mensajes PWA usan como fuente `comunicados.Comunicado`.
- Solo se consideran comunicados externos a comedores, publicados y vigentes.
- Se incluyen los dirigidos explicitamente al comedor y los marcados para todos los comedores.
- El estado de lectura se guarda en `pwa.LecturaMensajePWA`.

## Impacto

- Mobile puede consumir mensajes por espacio sin duplicar el dominio original de comunicados.
- Queda trazabilidad de lectura (`visto` y `fecha_visto`) dentro del dominio PWA.
- No cambia el flujo de creacion/publicacion de comunicados en la webapp.
