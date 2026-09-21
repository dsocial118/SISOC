# Ticketera: CDI del usuario en verificación de credenciales

`POST /api/ticketera/auth/verificar/` incorpora el campo aditivo `centros_cdi`.
Permite que la Ticketera enrute un ticket según los CDI a los que está vinculado
el usuario autenticado.

Cada entrada incluye identificador, nombre, código y vínculo (`referente` o
`trabajador`). Solo se informan referentes con acceso activo, trabajadores no
eliminados lógicamente y CDIs no eliminados lógicamente. El campo se devuelve
como lista vacía si no hay vínculos vigentes; si coinciden ambos roles en un
CDI, se incluyen dos entradas para conservar el rol.

Es una ampliación del contrato server-to-server protegida por la API key ya
existente. Expone pertenencia institucional limitada (sin datos de personas),
por lo que los consumidores deben usarla exclusivamente para el ruteo del
ticket.
