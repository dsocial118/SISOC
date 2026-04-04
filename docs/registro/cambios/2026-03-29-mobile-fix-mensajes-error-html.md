# Mobile: normalización de errores HTML en respuestas API

## Qué cambió

- Se agregó un parser común en `mobile/src/api/errorUtils.ts` para normalizar errores de API.
- El parser ahora detecta respuestas HTML o payloads no válidos y evita mostrar el primer carácter (`<`) como mensaje.
- Se conectó este parser en las pantallas principales de Mobile que cargan módulos de espacios y mensajes.

## Problema corregido

- En algunos errores del backend/proxy, Mobile recibía HTML en vez de JSON.
- Las pantallas tomaban ese contenido como si fuera un mensaje y terminaban mostrando un card rojo con `<`.

## Criterio aplicado

- Si la respuesta no trae un mensaje usable, Mobile muestra el fallback funcional definido por la pantalla.
- Se mantienen mensajes específicos para timeouts donde ya existían, como validaciones contra RENAPER.
