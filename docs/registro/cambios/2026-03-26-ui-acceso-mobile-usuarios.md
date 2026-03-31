# 2026-03-26 - Mejora visual y aclaración de alcance en acceso mobile de usuarios

## Cambio aplicado

- Se mejoró la presentación visual de la sección `Acceso SISOC - Mobile` en el formulario de usuarios.
- Se reemplazó la selección visual básica por una navegación en tabs:
  - `Organizaciones`;
  - `Espacios`.
- Se agregó texto explicativo en la propia pantalla para dejar explícita la regla de negocio:
  - el usuario puede seleccionar una o más organizaciones;
  - luego todos o algunos de sus espacios;
  - y además espacios por fuera de esas organizaciones.
- En la pestaña `Organizaciones`:
  - se muestra el listado de organizaciones con filtro;
  - al seleccionar una organización se marcan automáticamente sus espacios;
  - debajo se muestra el listado de espacios de esas organizaciones para poder deseleccionar casos puntuales.
- En la pestaña `Espacios`:
  - se muestran solo espacios por fuera de las organizaciones seleccionadas;
  - no se repiten los espacios que ya aparecen dentro del alcance por organizaciones.
- Si ya hay organizaciones seleccionadas, ese bloque sigue visible aunque el usuario cambie a la pestaña `Espacios`, para mantener contexto del alcance ya construido.

## Regla validada

- Se mantiene el comportamiento de backend existente:
  - los espacios seleccionados dentro de una organización quedan asociados como `tipo_asociacion=organizacion`;
  - los espacios externos quedan asociados como `tipo_asociacion=espacio`;
  - no es obligatorio incluir todos los espacios de una organización seleccionada.

## Archivos

- `users/templates/user/user_form.html`
- `static/custom/css/user_form.css`

## Validación

- `docker-compose exec django pytest tests/test_users_pwa_forms.py`
