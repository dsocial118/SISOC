# PR #2322: correcciones de revisión

## Objetivo

Resolver los hallazgos de validación, trazabilidad y cobertura del flujo web
de recuperación de contraseña, sin retirar la gestión administrativa existente.

## Diseño aprobado

1. El formulario web seleccionará una cuenta activa por `username` exacto y
   verificará el email sin distinguir mayúsculas/minúsculas. Una contraseña
   inutilizable no impedirá que esa misma cuenta reciba el enlace de reset.
2. Las regresiones cubren el envío a una cuenta con contraseña inutilizable y
   la coincidencia de email con distinta capitalización, mediante el POST web
   de `password_reset` y `mail.outbox`.
3. El parser de metadata aceptará tanto las líneas con viñeta de la plantilla
   como las etiquetas sin viñeta usadas por el cuerpo actual del PR. Luego se
   regenerarán los dos artefactos de PR #2322 desde esa metadata.
4. La edición administrativa de usuarios queda fuera del cambio y conserva su
   comportamiento actual.

## Validación

Ejecutar los tests focalizados de autenticación y documentación, `black`,
`pylint`, `djlint` y `git diff --check` para los archivos modificados.
