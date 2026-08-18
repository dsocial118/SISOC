# Confirmación de datos sin declaración

Fecha: 2026-08-14

## Cambio

El modal obligatorio de confirmación de datos personales y la pantalla
persistente **Mi cuenta** dejan de mostrar y exigir la declaración de
confidencialidad. También se retira de ambas vistas el texto sobre identificación
y auditoría interna.

El campo histórico se conserva en la base de datos, sin escrituras nuevas desde
este formulario, para mantener compatibilidad y evitar una migración destructiva
en el hotfix.

## Validación

- `pytest tests/test_users_mi_cuenta.py -q`
- `djlint users/templates/user/confirmar_datos.html users/templates/user/_mi_cuenta_campos.html --check`
