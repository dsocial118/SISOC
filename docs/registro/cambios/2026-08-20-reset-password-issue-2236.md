# Recuperación de contraseña SISOC por usuario y email

Fecha: 2026-08-20  
Issue: `#2236`

## Cambio

El flujo web de recuperación selecciona una única cuenta mediante el `username`
exacto y utiliza el email como verificación secundaria. Sólo se genera el enlace
si la cuenta está activa y ambos valores coinciden, incluso si su contraseña
actual es inutilizable.

La pantalla final mantiene una respuesta genérica tanto para solicitudes
válidas como inválidas, evitando revelar si el usuario o el correo existen.

## Validación cubierta

- Dos usuarios pueden compartir email sin recibir ambos un reset.
- Una combinación incorrecta de usuario y email no envía correo.
- Una cuenta con contraseña inutilizable recibe el enlace de autoservicio.
- El enlace generado conserva el flujo web de SISOC y el administrador no
  interviene en la recuperación.
