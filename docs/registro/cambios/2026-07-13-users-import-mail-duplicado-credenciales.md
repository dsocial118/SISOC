# Importación de usuarios: email duplicado y credenciales agrupadas

Issue: #2037.

## Cambios funcionales

- **Acción de grupos vacía crea usuarios nuevos.** En la importación, el
  `username` sigue teniendo prioridad para identificar usuarios existentes. Si
  no hay username coincidente y `Accion grupos` está vacía, un correo ya usado
  no identifica al usuario: se crea uno nuevo con el mismo email y un username
  autogenerado único.
- **Acción de grupos explícita conserva el fallback por correo.** Si la fila
  declara explícitamente `agregar`, `quitar` o `reemplazar` y no tiene username
  coincidente, el correo todavía se usa para actualizar al usuario existente.
  La acción efectiva de una celda vacía continúa siendo `agregar` al aplicar
  grupos.
- **Credenciales al cierre del lote.** Las filas que crean usuarios ya no envían
  correos individualmente. Al finalizar un lote se agrupan por email de destino
  y se usa `send_bulk_credentials_email` en modo `standard`, por lo que un mail
  puede incluir las credenciales de varios usuarios creados en el mismo lote.
- **Trazabilidad de envío.** `UserImportJobRow` ahora guarda `created_user` y
  `credentials_sent_at`. Las filas ya marcadas no se vuelven a enviar al
  reprocesar o reanudar un job. Si falta la contraseña temporal o falla el
  correo, se registra el motivo en la fila sin cambiar el estado del job.

## Compatibilidad

- No se modifica el módulo de credenciales masivas ni su lógica de agrupamiento;
  la importación reutiliza su API pública para los correos agrupados.
- Los updates por username mantienen el comportamiento previo, incluido que el
  username prevalece si username y correo apuntan a usuarios diferentes.
