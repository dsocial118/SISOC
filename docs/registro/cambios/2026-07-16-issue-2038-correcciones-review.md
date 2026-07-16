# Issue #2038 — correcciones posteriores a revisión

- El grupo `CDI - Referente centro` incorpora `add_trabajador`, habilitando la cascada Referente → Trabajador desde la nómina real.
- Las altas y ediciones genéricas de usuarios EGP exigen una única provincia completa; la importación aplica el mismo contrato y sincroniza el scope territorial.
- La importación conserva una delegación vacía como alcance vacío y no modifica grupos fuera del alcance del actor.
- El alta y la edición de CDI fijan la provincia para EGP y usuarios territoriales, y fallan de forma cerrada si no tienen scope; Admin SIMEPI y Analista conservan alcance nacional incluso con perfiles provinciales heredados.
- El cambio de email del referente resuelve la cuenta por el email anterior y evita actualizar accesos ambiguos.
- El provisionamiento automático y el scope provincial de EGP se centralizaron en `centrodeinfancia/services_user_provisioning.py`.
- Se agregó cobertura de regresión y pruebas por URL para los alcances EGP, referente, trabajador, admin/analista y Auditoría.
