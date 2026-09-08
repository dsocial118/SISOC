# Usuarios: DNI, CUIL y tipo informativo

Se incorporan DNI, CUIL y Tipo de usuario al ABM de usuarios. Los tres datos
se persisten en `users.Profile`; el tipo admite Interno, Provincial o Externo y
es obligatorio únicamente en los formularios de alta y edición.

La clasificación es informativa. No modifica grupos, permisos, acceso mobile,
roles ni alcances territoriales. El checkbox existente `Es usuario provincial`
mantiene su semántica de configuración territorial.

DNI y CUIL se conservan como texto opcional, sin validar formato ni unicidad,
porque el alcance funcional no define esas reglas.
