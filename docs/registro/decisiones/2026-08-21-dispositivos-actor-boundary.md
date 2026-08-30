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
`services.dispositivos.application` no conoce `User`, `Profile` ni
`users.territorial_scope`.

El núcleo canónico vive en `services/dispositivos/application/contracts/v1/`.
El paquete Django legacy —label `dispositivos`, tablas, IDs, migraciones,
formularios, vistas y rutas— vive temporalmente en
`services.dispositivos.monolith_compat.app`. Sus adaptadores a `core` y `users`
viven en `services.dispositivos.monolith_compat.adapters`. En la extracción, el
gateway que valide la sesión y el JWS deberá producir el mismo contrato; no se
trasladará ese adaptador al servicio.

`DispositivoForm(user=...)` sigue aceptándose como compatibilidad del monolito,
pero internamente se traduce al mismo actor. Las vistas ya entregan el actor de
forma explícita.

## Catálogo y límites de esta etapa

La migración `0006` incorpora una proyección territorial versionada, inmutable
y aditiva, con un único puntero a la versión vigente. El contrato de publicación
recibe DTOs puros; por eso puede ser alimentado por una fuente autorizada sin
que el dominio consulte el ORM de `core`. El puntero evita depender de un índice
único parcial, que no es portable a MySQL.

Las FKs legacy hacia `core_provincia` y `core_municipio` se conservan sólo en
la compatibilidad monolítica y no se escriben desde la proyección. El núcleo
recibe snapshots de catálogo como DTOs versionados; no declara modelos espejo ni
consulta tablas `core_*`. Formularios, filtros y rutas acceden al monolito
mediante adaptadores explícitos; el reemplazo de esas FKs exige una migración de
datos y una ventana de corte aprobada. Tampoco se crea una API pública Python:
no hay consumidores de negocio externos de Dispositivos.

## Validación

Se agrega un contrato `import-linter` que prohíbe al núcleo de Dispositivos
importar `core`, `users` o su capa de compatibilidad. Las pruebas unitarias de
contratos v1 no requieren settings Django; las regresiones de vista/formulario
continúan cubriendo la compatibilidad monolítica.
