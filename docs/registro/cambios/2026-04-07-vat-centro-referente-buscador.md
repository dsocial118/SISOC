# 2026-04-07 - VAT centros: referente con buscador

## Contexto
- El campo `Referente` en el alta y edición de centros VAT mostraba un select plano con muchos usuarios CFP.
- Con catálogos grandes de usuarios, la selección manual se volvía lenta y propensa a errores.

## Cambio aplicado
- Se configuró el campo `referente` de `CentroAltaForm` como select buscable usando `select2`.
- Las opciones ahora muestran `username` y nombre completo cuando está disponible para mejorar la búsqueda.
- El queryset del campo incluye `CFP` y aliases legacy del mismo rol (`ReferenteCentroVAT`, `ReferenteCentro`) para compatibilidad con datos existentes.
- Se incorporó el CSS de `select2` y la inicialización del buscador en el template compartido de alta/edición de centros.
- Se agregó una regresión en `VAT/tests.py` para validar los atributos del widget y el formato de etiqueta de opciones.

## Impacto esperado
- En `vat/centros/nuevo/` y `vat/centros/<id>/editar/`, el campo `Referente` permite buscar rápidamente entre usuarios CFP.
- En bases con datos legacy, también aparecen los referentes históricos cargados bajo grupos equivalentes del mismo rol VAT.
- La mejora no cambia el contrato del formulario ni la validación existente del referente.

## Validación
- `pytest VAT/tests.py -k "test_centro_alta_form_configura_referente_como_buscador or test_centro_create_rechaza_referente_sin_grupo_cfp" -vv`