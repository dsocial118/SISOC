# Altas de comedores desde Gestionar con idempotencia

## Alcance

El contrato objetivo de Gestionar para crear y editar comedores usa la API
territorial de SISOC:

- `POST /api/territorial/comedores/`
- `PATCH /api/territorial/comedores/{id}/`

Ambas rutas requieren `Authorization: Token <token>` y un usuario marcado como
territorial de comedores. El alta solo admite la provincia incluida en
`TerritorialComedorProvincia`; la edición recupera el objeto desde el queryset
scopeado y responde `404` fuera de alcance.

## Contrato de alta

`POST` recibe el formulario de Gestionar en nombres legibles (`tipo`, `programa`,
`organizacion`, `provincia`, `municipio`, `localidad`) y un `client_uuid` de hasta
100 caracteres. Las relaciones deben existir y respetar la jerarquía
provincia → municipio → localidad. SISOC responde el shape territorial usado por
la PWA, con `id` remoto numérico y los campos de formulario normalizados.

La clave es estable por `usuario + client_uuid`. La tabla
`ComedorPwaCreateOperation` reserva esa combinación dentro de una transacción
antes de crear el comedor y la restricción única de MySQL evita duplicados entre
procesos. Un reintento equivalente devuelve `200` y el mismo comedor; una clave
reutilizada con otro payload devuelve `409` con
`code=idempotency_payload_conflict`. El reintento vuelve a validar el alcance
actual del usuario. La huella se calcula sobre el request del cliente y queda
persistida antes de responder; así un reintento idéntico no vuelve a depender de
que los catálogos con nombres legibles sigan teniendo el mismo nombre.

En una edición que cambie `provincia` debe enviarse también `municipio`; si el
municipio cambia o se limpia, debe enviarse `localidad` (con un valor válido o
vacío). SISOC rechaza las actualizaciones incompletas para no conservar una
jerarquía provincia → municipio → localidad inconsistente.

## Migración y entrega

Aplicar primero la migración `comedores.0059_comedorpwacreateoperation` junto con
el backend. Después publicar el frontend que envía `client_uuid`, usa las rutas
territoriales y hace `PATCH` para edición. El backend nuevo acepta clientes
anteriores para lectura, pero un frontend nuevo no debe publicarse antes de la
migración porque su alta requiere la tabla de operaciones.

La reversión del frontend es independiente. Para revertir backend después de que
hubo altas, conservar la migración aplicada y restaurar el código anterior solo
si se deshabilita el alta de la PWA; deshacer la migración eliminaría el historial
de idempotencia y haría inseguros los reintentos pendientes. No borrar ni editar
filas de operaciones para resolver conflictos.

## Verificación requerida

Ejecutar las pruebas de `tests/test_territorial_api.py`, incluidas las marcadas
`mysql_compat`, contra una base MySQL aislada. La concurrencia no se considera
validada por SQLite ni por mocks HTTP. Antes de publicar, verificar en un entorno
autorizado el alta, pérdida de respuesta y reintento, reemplazo del ID `loc_...`,
edición, logout y cambio de cuenta.
