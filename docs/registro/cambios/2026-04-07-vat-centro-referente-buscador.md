# 2026-04-07 - VAT centros: referente con buscador

## Contexto
- El campo `Referente` en el alta y edición de centros VAT debía listar usuarios válidos del sistema para asociarlos al centro.
- La mejora previa con `select2` introdujo inconsistencias visuales y un fallo de renderizado en el navegador donde el campo mostraba `No results found` aun teniendo opciones válidas.

## Cambio aplicado
- Se mantuvo el campo `referente` como `select` estándar para recuperar el mismo formato visual que el resto de los `form-control` del formulario.
- Las opciones muestran `username` y nombre completo cuando está disponible para mejorar la identificación del usuario.
- El queryset del campo quedó restringido nuevamente solo a usuarios del grupo `CFP`.
- Se amplió el queryset del campo para incluir usuarios asociados al grupo legacy `ReferenteCentro`, detectado en la base local, además de `CFP` y `ReferenteCentroVAT`.
- Se descartó esa ampliación por requerimiento funcional: `Referente` debe listar exclusivamente usuarios `CFP`, aunque existan grupos legacy en la base.
- Se agregó una regresión en `VAT/tests.py` para validar el formato estándar del widget, el `empty_label`, el formato de etiqueta de opciones y que los grupos legacy no aparezcan.

## Impacto esperado
- En `vat/centros/nuevo/` y `vat/centros/<id>/editar/`, el campo `Referente` vuelve a mostrarse igual que los demás selects del formulario.
- En bases con datos legacy, los usuarios fuera de `CFP` ya no aparecen en el selector.
- La mejora no cambia el contrato del formulario ni la validación existente del referente.

## Validación
- `docker compose exec django pytest VAT/tests.py -k "test_centro_alta_form_configura_referente_como_select_estandar or test_centro_alta_form_no_incluye_grupos_legacy_de_referente" -q`
