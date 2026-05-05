# VAT ubicaciones adicionales: localidades en modal de sede

## Que cambio

- El modal de `Ubicaciones Adicionales` en el detalle de centro renderiza los selects de centro/localidad con IDs propios y `dropdownParent` de Select2 apuntando al modal.
- Al abrir el modal, los selects Select2 se refrescan dentro del contexto visible para evitar estados visuales heredados de la carga inicial oculta.
- El queryset de localidades por centro se centralizo y ahora, si el municipio del centro no tiene localidades cargadas, usa como fallback las localidades de la provincia.
- El endpoint `vat_ajax_localidades_por_centro` usa el mismo criterio que el modal.

## Contexto

En centros VAT con municipio sin localidades asociadas, el selector de localidad para crear una sede secundaria quedaba sin opciones utiles. Ademas, el formulario de ubicacion compartia IDs genericos con otros formularios del detail, lo que podia romper el comportamiento de Select2 dentro del modal.

## Validacion esperada

- Entrar a `/vat/centros/<pk>/`.
- Abrir `Ubicaciones Adicionales > Agregar`.
- Verificar que `Localidad` esta habilitado y muestra opciones acordes al municipio del centro o, si ese municipio no tiene localidades, a la provincia del centro.
