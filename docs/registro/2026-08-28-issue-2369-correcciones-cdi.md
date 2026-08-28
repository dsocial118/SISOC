# Issue 2369: correcciones CDI y nómina

- EGP admite varios alcances provinciales y debe seleccionar uno autorizado para descargar la nómina PDF.
- Un referente CDI reutiliza una cuenta existente con el mismo email, sin regenerar credenciales ni enviar correo.
- El año de inicio acepta desde 1900; se incorporó la migración `0046`.
- Días de funcionamiento son obligatorios en los formularios CDI y las opciones `ns_nc` se muestran como «No sabe».
- Para mayores de 48 meses, el formulario de nómina exige estado Pendiente salvo SIMEPI Administrador o superusuario.
- El alcance excluye el punto 10, pendiente de definición funcional.
- Comunicados continúa accesible; el ítem del menú se oculta únicamente a roles CDI locales sin rol SIMEPI adicional.
