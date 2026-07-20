# Roles SIMEPI/CDI - Fase 1

Se incorporan los grupos SIMEPI y `CDI - Trabajador` con permisos Django sobre
los cuatro modelos CDI. `CDI - Referente centro` conserva sus permisos previos
y suma los permisos de trabajador y de creación/consulta de usuarios necesarios
para fases posteriores.

La migración de datos crea o extiende los grupos de forma aditiva e idempotente;
su reversa es no-op, como los bootstrap de grupos existentes.
