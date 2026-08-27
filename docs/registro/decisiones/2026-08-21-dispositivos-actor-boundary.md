# 2026-08-21 - Dispositivos: contrato de actor territorial

## Contexto

La extracción de Dispositivos definida en #2309 no puede depender de sesión
Django ni de los modelos de `users`. El comportamiento actual debe conservar
los permisos Django y el alcance territorial provincial/municipal, incluso
para un usuario territorial sin alcances.

## Decisión

El dominio consume `DispositivosActor` y `TerritorialScope`, contratos puros
que contienen únicamente el identificador del actor, estado de autenticación,
privilegio de superusuario, permisos y alcances territoriales.
`dispositivos.services` no conoce `User`, `Profile` ni
`users.territorial_scope`.

Mientras el monolito continúe atendiendo las rutas, el único adaptador permitido
es `dispositivos.adapters.monolith_session.actor_from_session_user`. En la
extracción, el gateway que valide la sesión y el JWS deberá producir el mismo
contrato; no se trasladará ese adaptador al servicio.

`DispositivoForm(user=...)` sigue aceptándose como compatibilidad del monolito,
pero internamente se traduce al mismo actor. Las vistas ya entregan el actor de
forma explícita.

## Catálogo y límites de esta etapa

La migración `0006` incorpora una proyección territorial versionada, inmutable
y aditiva, con un único puntero a la versión vigente. El contrato de publicación
recibe DTOs puros; por eso puede ser alimentado por una fuente autorizada sin
que el dominio consulte el ORM de `core`. El puntero evita depender de un índice
único parcial, que no es portable a MySQL.

Las FKs legacy hacia `core_provincia` y `core_municipio` se conservan por
compatibilidad y no se escriben desde la proyección. Formularios, filtros y
rutas acceden al monolito mediante adaptadores explícitos; el reemplazo de esas
FKs exige una migración de datos y una ventana de corte aprobada. Tampoco se
crea una API pública Python: no hay consumidores de negocio externos de
Dispositivos.

## Validación

Se agrega un contrato `import-linter` que prohíbe a los módulos de dominio de
Dispositivos importar `core` o `users` directamente. Las pruebas focalizadas
cubren la conversión de alcances, la publicación e idempotencia de la
proyección, y las regresiones de vista/formulario existentes cubren los
adaptadores del monolito.
