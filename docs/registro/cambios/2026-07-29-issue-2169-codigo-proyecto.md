# Issue 2169 - Código de Proyecto según programa

## Cambio funcional

En alta y edición de comedores, el campo `Código de Proyecto` solo se muestra
para los programas Abordaje Comunitario - Línea Secos y Línea Tradicional.

La misma regla se aplica en el servidor: si se envía un código para Alimentar
Comunidad u otro programa no habilitado, se descarta antes de persistirlo.

## Limpieza histórica

La migración `comedores/0052_issue_2169_codigo_proyecto.py` deja en `NULL` el
código de proyecto de los comedores de Alimentar Comunidad. Es idempotente,
pero su reversa es `noop`: los valores eliminados no pueden reconstruirse sin
un respaldo previo.

Antes de aplicarla sobre datos reales se debe registrar el conjunto afectado y
contar con aprobación explícita para la limpieza.
