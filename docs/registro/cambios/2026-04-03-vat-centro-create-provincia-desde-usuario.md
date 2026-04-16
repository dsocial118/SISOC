# VAT: alta de centros toma jurisdicción desde el usuario creador

- En el alta de centros (`/vat/centros/nuevo/`) se dejó de pedir manualmente el campo `Jurisdicción`.
- La provincia del centro ahora se asigna automáticamente desde la provincia configurada en el `Profile` del usuario creador.
- Si el usuario no tiene provincia asignada en su perfil, el alta queda bloqueada con error de validación.
- La edición de centros no cambia: sigue mostrando el campo de jurisdicción dentro del formulario extendido.