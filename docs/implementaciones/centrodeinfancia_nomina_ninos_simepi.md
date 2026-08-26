# Centro de Infancia: nómina provincial de niños SIMEPI

## Alcance

La descarga provincial de nómina está disponible para superadministradores y
usuarios del grupo `SIMEPI - EGP`. No es una descarga libre para cualquier rol
CDI ni para alcances territoriales parciales.

- Un `SIMEPI - EGP` debe tener exactamente un alcance completo de provincia;
  la provincia se toma del alcance efectivo del usuario y se ignora cualquier
  provincia enviada por el cliente.
- Un superadministrador debe elegir una provincia válida en el modal; una
  selección ausente o inválida responde `400` antes de consultar datos.
- Los demás roles, los alcances parciales y los perfiles EGP ambiguos reciben
  una denegación antes de consultar la nómina.

## Contrato del PDF

La acción `Descargar nómina de niños` agrupa por CDI, ordena por medida, edad,
apellido, nombre y DNI, repite encabezados y termina con el total provincial.
El PDF es A4 apaisado, incluye marca de agua, fecha, usuario, numeración y una
imagen JPEG por página. El archivo se entrega como `attachment` con
`Cache-Control: private, no-store` y no se persiste en `MEDIA_ROOT`.

La consulta incluye solo fichas activas de nómina y deduplica por ciudadano,
DNI e identidad compuesta para tolerar datos históricos. La provincia
domiciliaria del niño puede estar vacía: el alcance se toma del CDI.

Los datos de identidad y la validación RENAPER solicitados forman parte del
documento. Los mensajes de error son genéricos y los logs solo contienen
identificadores internos y cantidades; no deben incluir DNI, CUIL, nombres ni
payloads RENAPER.

## Datos obligatorios y formularios CDI

En el flujo SIMEPI/CDI vigente:

- el CUIT del niño y Lenguajes son obligatorios;
- los CUIT de responsables, talla, peso, longitud acostado y perímetro cefálico
  son opcionales, conservando validaciones cuando se informan;
- Función es obligatoria según el subcomponente y Sala es obligatoria para CDI;
- el departamento jurisdiccional se relaciona con `DepartamentoIpi`, se filtra
  por provincia y se valida en servidor;
- el correo solo es obligatorio al crear un trabajador para aprovisionar su
  usuario automático; las ediciones históricas pueden conservarlo vacío.

Los roles EGP, Referente CDI y Trabajador CDI fallan cerrados sin alcance
territorial u operativo. EGP queda limitado a sus provincias y los roles
locales a sus CDI vinculados. El enlace de Grupos solo se muestra con
`auth.view_group`; la protección del endpoint permanece vigente.

## Implementación y validación

- Endpoint y autorización: `centrodeinfancia/views_export.py` y
  `centrodeinfancia/access.py`.
- Servicio PDF: `centrodeinfancia/services_nomina_ninos_pdf.py`.
- Formulario y datos CDI: `centrodeinfancia/forms.py` y `centrodeinfancia/models.py`.
- Regresiones: `centrodeinfancia/tests/test_nomina_ninos_pdf.py`,
  `centrodeinfancia/tests/test_access_scope_centrodeinfancia.py`,
  `centrodeinfancia/tests/test_destinatario_form.py` y
  `centrodeinfancia/tests/test_trabajador_form.py`.

Antes de promover, validar autorización por rol y alcance, selección obligatoria
del superadministrador, aislamiento provincial, deduplicación, headers de
privacidad y la estructura final del PDF.

## Referencias

- `docs/registro/cambios/2026-08-18-issue-2304-urgentes-cdi.md`
- `docs/registro/cambios/2026-08-18-issue-2304-nomina-domicilio-sala.md`
- `docs/registro/cambios/2026-08-18-simepi-descarga-nomina-ninos.md`
- `docs/implementaciones/centrodeinfancia_nomina_renaper.md`
