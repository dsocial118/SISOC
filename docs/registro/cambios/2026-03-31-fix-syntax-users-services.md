# Fixes de sintaxis en users/services.py y users/views.py

## Contexto

El arranque de Django quedaba bloqueado durante `python manage.py makemigrations`
por dos errores de sintaxis consecutivos en el modulo `users`:

- `users/services.py` tenia un `Case(...)` sin cerrar dentro de
  `UsuariosService.get_usuarios_queryset()`.
- `users/views.py` tenia un bloque incompleto dentro de
  `UserUpdateView.get_context_data()`.

## Que se corrigio

- Se cerro correctamente la anotacion `password_reset_requested_indicator`.
- Se mantuvo la anotacion `is_active_display` en el mismo queryset, sin cambios de
  contrato ni de comportamiento esperado.
- Se recompuso `UserUpdateView.get_context_data()` para que:
  - lea primero la contrasena temporal desde sesion;
  - use `profile.temporary_password_plaintext` como fallback;
  - exponga `temporary_password_visible` segun ese valor final.

## Impacto

- Django vuelve a poder importar `users.services` y `users.views` durante
  `django.setup()`.
- El comando `makemigrations` deja de fallar por `SyntaxError` en esos modulos.

## Validacion

- `python -m py_compile users/services.py`
- `python -m py_compile users/views.py`
