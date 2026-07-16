# Delegación SIMEPI/CDI - Fase 2

La delegación efectiva de grupos combina la configuración manual de
`Profile.grupos_asignables` con la cascada declarativa `GROUP_DELEGATION`, sin
escribir los grupos derivados en la base de datos. Los grupos que no participan
del mapa conservan exactamente su alcance manual previo.

Los formularios, el listado de usuarios, la generación delegada, los flujos
CDI/CDF/VAT y la importación de usuarios consumen ahora el alcance efectivo.
Los roles `auth.role_*` siguen siendo exclusivamente manuales.
