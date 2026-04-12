# PR 1509 - permiso para borrar certificados de capacitaciones

## Contexto

Durante la revisión del PR `#1509` se detectó que el endpoint mobile
`POST /api/comedores/<id>/capacitaciones/eliminar/` había quedado sin la
restricción `IsPWARepresentativeForComedor`, a diferencia de los endpoints
hermanos para listar y subir certificados.

## Cambio realizado

- Se agregó `permission_classes=[IsPWARepresentativeForComedor]` a la acción
  `eliminar_capacitacion` en `comedores/api_views.py`.
- Se sumó una regresión en `tests/test_pwa_comedores_api.py` para verificar que
  un usuario con rol `operador` no pueda borrar certificados del espacio.

## Impacto

- Se evita que usuarios PWA con acceso al espacio, pero sin rol de
  representante, puedan modificar certificados de capacitaciones.
- No cambia el comportamiento para representantes.

## Validación

- `pytest tests/test_pwa_comedores_api.py -k 'test_operador_cannot_delete_capacitacion_certificate' -q`
- `pytest tests/test_urls_no_500.py::test_urls_no_500[/vat/institucion/ubicaciones/nuevo/-vat_institucion_ubicacion_create] celiaquia/tests/test_registros_erroneos_obligatorios.py::test_detalle_expediente_muestra_campos_responsable_para_registros_erroneos -q`
