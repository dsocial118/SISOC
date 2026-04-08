# Ajuste de centrado vertical en login web

## Contexto

La pantalla principal del login web había quedado desplazada hacia arriba luego de incluir header y footer fijos.

## Cambio realizado

- Se ajustó `static/custom/css/login.css` para que la vista de login reserve la altura ocupada por el header y el footer.
- Se agregó un alto mínimo a `.login-row` calculado sobre el espacio visible restante, manteniendo el formulario centrado verticalmente.
- En mobile se redujo el ajuste para evitar recortes y mantener el comportamiento responsivo.

## Impacto esperado

- El formulario principal del login vuelve a quedar centrado en desktop.
- No cambia la lógica del login ni sus validaciones.
