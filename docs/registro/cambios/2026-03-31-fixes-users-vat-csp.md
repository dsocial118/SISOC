# 2026-03-31 - Correcciones de usuarios, grupos bootstrap, CSP y admin VAT

## Contexto

Durante la validación de regresiones aparecieron fallos en cuatro áreas distintas:

- `create_groups` estaba creando grupos VAT extra fuera de la semilla canónica.
- El listado/edición de usuarios había perdido la exposición de `is_active_display` y la
  visibilidad de la contraseña temporal.
- `VAT.VoucherAdmin` intentaba renderizar un campo no editable en el formulario del admin.
- Algunos templates VAT tenían scripts inline sin `nonce`, rompiendo la validación CSP.

## Qué se corrigió

- `users/management/commands/create_groups.py` ahora crea solo los grupos definidos en
  `users/bootstrap/groups_seed.py`.
- `users/services.py` vuelve a exponer `is_active_display` en el queryset de usuarios.
- `users/models.py`, `users/forms.py`, `users/views.py` y `users/services_auth.py` ahora
  persisten y limpian `temporary_password_plaintext` de forma consistente.
- `VAT/admin.py` marca `fecha_asignacion` como solo lectura.
- `VAT/templates/vat/centros/centro_detail.html` y
  `VAT/templates/vat/oferta_institucional/comision_detail.html` agregan `nonce` a los
  scripts inline detectados por el test de CSP.

## Validación esperada

- `pytest tests/test_create_groups_command.py`
- `pytest tests/test_users_auth_flows.py`
- `pytest tests/test_templates_inline_scripts_nonce_unit.py`
- `pytest tests/test_urls_no_500.py`
