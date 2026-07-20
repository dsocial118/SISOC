# Issue #2038 — correcciones posteriores a revisión

- El grupo `CDI - Referente centro` incorpora `add_trabajador`, habilitando la cascada Referente → Trabajador desde la nómina real.
- Las altas y ediciones genéricas de usuarios EGP exigen una única provincia completa; la importación aplica el mismo contrato y sincroniza el scope territorial.
- La importación conserva una delegación vacía como alcance vacío y no modifica grupos fuera del alcance del actor.
- El alta y la edición de CDI fijan la provincia para EGP y usuarios territoriales, y fallan de forma cerrada si no tienen scope; Admin SIMEPI y Analista conservan alcance nacional incluso con perfiles provinciales heredados.
- El scope territorial explícito prevalece sobre la provincia legacy al fijar la provincia de un CDI.
- El cambio de email del referente resuelve la cuenta por el email anterior y evita actualizar accesos ambiguos.
- El sync seguro de referente y trabajador solo corre cuando el campo email cambió en ese guardado y permite limpiarlo si quedó vacío.
- Cada trabajador con email recibe su propia cuenta aunque otra cuenta comparta la misma dirección.
- El provisionamiento automático y el scope provincial de EGP se centralizaron en `centrodeinfancia/services_user_provisioning.py`.
- Se agregó cobertura de regresión y pruebas por URL para los alcances EGP, referente, trabajador, admin/analista y Auditoría.
