# VAT: renombre de grupos VAT a nombres CFP

- Se renombró el grupo bootstrap visible `VAT SSE` a `CFPINET`.
- Se renombró el grupo bootstrap visible `Provincia VAT` a `CFPJuridicccion`.
- Se renombró el grupo bootstrap visible `ReferenteCentroVAT` a `CFP`.
- Se mantuvo sin cambios el permiso canónico `auth.role_vat_sse`, por lo que la lógica de acceso de VAT sigue funcionando igual.
- Se mantuvieron sin cambios los permisos canónicos `auth.role_provincia_vat` y `auth.role_referentecentrovat`.
- Se habilitó a `CFPJuridicccion` para crear y editar centros dentro de su provincia, manteniendo fuera de alcance cursos, comisiones, horarios, inscripciones y asistencia.
- Se amplió el grupo `CFP` con permisos operativos para gestionar cursos, comisiones de curso, horarios, asistencia e inscripciones dentro de sus centros.
- Se agregó una migración de datos para renombrar el grupo existente en bases ya pobladas y evitar que `create_groups` genere un grupo nuevo en paralelo.
- Se actualizó la documentación relevante, el filtro del referente por nombre de grupo y la cobertura mínima del comando de bootstrap de grupos.