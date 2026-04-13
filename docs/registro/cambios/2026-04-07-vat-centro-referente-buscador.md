# 2026-04-07 - VAT centros: referente con buscador

## Contexto
- El campo `Referente` en el alta y edición de centros VAT debía listar usuarios válidos del sistema para asociarlos al centro.
- La mejora previa con `select2` introdujo inconsistencias visuales y un fallo de renderizado en el navegador donde el campo mostraba `No results found` aun teniendo opciones válidas.

## Cambio aplicado
- Se reemplazó el `select` visible por un buscador nativo simple (`input` con sugerencias) sin usar `Select2`.
- La selección sigue siendo única: el valor persistido y validado continúa saliendo del `ModelChoiceField` `referente`, ahora oculto en la UI.
- Las opciones del buscador muestran `username` y nombre completo cuando está disponible para mejorar la identificación del usuario.
- El queryset del campo quedó restringido nuevamente solo a usuarios del grupo `CFP`.
- Se agregó sincronización JavaScript entre el texto buscado y el `select` oculto para mantener las validaciones existentes del formulario.
- Se agregó una regresión en `VAT/tests.py` para validar la configuración del buscador, el `empty_label`, el formato de etiqueta de opciones y que los grupos legacy no aparezcan.

## Impacto esperado
- En `vat/centros/nuevo/` y `vat/centros/<id>/editar/`, el campo `Referente` permite buscar usuarios `CFP` sin depender de `Select2`.
- En bases con datos legacy, los usuarios fuera de `CFP` ya no aparecen en el selector.
- La mejora no cambia el contrato del formulario ni la validación existente del referente.

## Validación
- `docker compose exec django pytest VAT/tests.py -k "test_centro_alta_form_configura_referente_como_buscador_simple or test_centro_alta_form_no_incluye_grupos_legacy_de_referente" -q`
