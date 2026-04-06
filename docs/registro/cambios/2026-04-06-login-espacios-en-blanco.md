# Login web: espacios en blanco como campos vacíos

## Contexto

Se ajusta el login web de SISOC para que los campos `username` y `password`
compuestos únicamente por espacios en blanco se interpreten como vacíos.

## Cambio realizado

- Se normalizan ambos campos con `strip()` en `BackofficeAuthenticationForm`
  antes de ejecutar la validación estándar de Django.
- Se mantiene la validación backend para impedir autenticaciones con valores
  vacíos aunque el request llegue por fuera del navegador.
- Se actualiza el template `users/templates/user/login.html` para:
  - mostrar errores por campo;
  - conservar el valor ingresado del usuario;
  - marcar ambos inputs como obligatorios;
  - recortar espacios antes del submit para que la validación del navegador
    también bloquee el envío cuando solo se ingresan blancos.
- Se ajusta el layout del login para que el footer no tape el botón `Ingresar`
  cuando aparecen mensajes de error y la tarjeta crece en altura.
- Se unifica el mensaje de credenciales inválidas del login web a un texto
  genérico y conciso para no exponer información sensible.
- Se agrega foco automático inicial en el campo usuario al cargar la pantalla
  de login.
- Se agrega estado de loading al botón `Ingresar` durante el submit válido:
  spinner a la izquierda, texto `Ingresando` y bloqueo de reenvíos múltiples.

## Validación esperada

- Si usuario y contraseña contienen solo espacios, el formulario no debe
  iniciar sesión.
- El backend debe devolver errores de campo obligatorios en `username` y
  `password`.
- El navegador debe tratar esos valores como vacíos al enviar el formulario.

## Cobertura

- Se agrega test de regresión para `POST /login/` con ambos campos compuestos
  solo por espacios.
- Se agrega cobertura para `POST /login/` con usuario válido y espacios al
  inicio, verificando que el sistema haga trim del usuario y permita acceder.
- Se agrega cobertura para preservar contraseñas válidas con espacios
  significativos, evitando recortarlas durante la autenticación.
- Se agrega cobertura para credenciales inválidas en web, verificando un
  mensaje de error genérico.
- Se agrega cobertura para verificar que, tras un login fallido, el usuario
  permanezca visible y la contraseña no se reinyecte en el formulario.
- Se agrega cobertura para verificar que el campo usuario renderice con foco
  inicial automático.
- Se agrega cobertura de render para el botón de submit con spinner e
  identificadores del estado de loading.
