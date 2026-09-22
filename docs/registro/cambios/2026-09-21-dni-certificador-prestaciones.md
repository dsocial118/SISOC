# DNI certificador en certificaciones de prestaciones

La conformidad mensual de prestaciones de espacios de Alimentar Comunidad ahora
requiere el DNI de la persona certificadora, con exactamente siete u ocho dígitos.

- El DNI se recibe solamente en el POST autenticado de conformidad y se persiste
  junto al usuario, período y resultado de la certificación.
- La generación del PDF usa ese DNI después de validar y crear la conformidad.
  Si falla la generación, la transacción revierte el registro.
- El DNI no se expone en las respuestas de detalle ni historial para evitar una
  ampliación innecesaria de datos personales.
- La descarga del PDF conserva su comportamiento de sólo lectura: los query
  parameters no pueden cambiar el DNI ni regenerar el documento.
- Los demás programas mantienen el payload histórico sin `dni_certificador`.
