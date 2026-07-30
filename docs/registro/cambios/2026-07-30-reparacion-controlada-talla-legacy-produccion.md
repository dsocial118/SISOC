# Recuperacion controlada de talla legacy bloqueante en produccion

## Causa confirmada

El deploy productivo del SHA `19ce61617bf5e6c320dc5064564f976724e6d0b9` llego
a ejecutar `centrodeinfancia.0042_alter_nominacentroinfancia_talla`. La
migracion se detuvo de forma intencional porque `NominaCentroInfancia.talla`
conserva los ids 7 y 242 no numericos, y el id 237 fuera de la capacidad de
`Decimal(5, 1)`. La advertencia MySQL `models.W036` no fue la causa.

## Decision

No se cambia la migracion ni se interpreta el dato historico. Se incorpora al
workflow de deploy, que es el unico autorizado para el runner productivo, una
accion manual para inspeccionar categorias sin exponer valores y otra para
limpiar unicamente esos tres valores como `NULL`.

La accion mutante exige la confirmacion exacta, verifica otra vez las categorias
esperadas, bloquea cada fila con `FOR UPDATE` y actualiza las tres dentro de una
misma transaccion. Cualquier fila ausente, categoria distinta o conteo de update
inesperado revierte todo.

## Compatibilidad, riesgo y rollback

No cambia APIs, permisos, UI ni el schema planificado por la migracion. Cambia
datos historicos invalidos solo tras una aprobacion del Environment
`production`; no imprime valores ni PII. No existe rollback automatico: el
valor invalido no es una altura confiable para restaurar. Si luego se dispone de
una fuente autorizada, una persona habilitada debe cargar el valor valido de
forma auditable.

El deploy se reintenta solo despues de la reparacion confirmada y contra el SHA
actual de `main`.
