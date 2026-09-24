# 2026-09-23 — Token y tasa RENAPER para importación masiva

## Contexto

El issue #2561 identifica un login antes de cada consulta RENAPER. El usuario informó un cupo aproximado de 35 consultas por segundo, global y aplicable sólo a consultas, no a logins. La decisión del 2026-08-10 había establecido un token efímero por consulta para evitar estado compartido.

## Decisión

Reutilizar el token únicamente en memoria del cliente de cada lote de importación de ciudadanos. El cliente existente renueva el token al recibir un 401. No se persisten tokens ni se comparten entre procesos o hilos.

Reservar cada consulta, incluidos los reintentos, mediante un turno global en la base de datos existente. Configurar inicialmente 30 consultas/s como margen respecto del cupo aproximado. El login no usa un turno. Si la base de datos no permite reservar, se omite la consulta y se devuelve un error clasificado.

Esta decisión cambia sólo la duración del token en el importador respecto de la decisión del 2026-08-10. Los demás consumidores mantienen su ciclo de token por consulta.

## Alternativas y consecuencias

- Un límite por proceso no controla la suma de réplicas y otros consumidores SISOC.
- Una caché local no coordina procesos; Redis agregaría una dependencia operativa para este flujo.
- La fila única de MySQL agrega una escritura breve por consulta y exige migrar antes de desplegar código. Si MySQL cae, RENAPER queda temporalmente no disponible, de manera controlada.
- El cupo informado es aproximado. QA debe comprobar la ventana de medición, respuestas de rechazo y convivencia con los otros consumidores antes de subir concurrencia. Una integración externa a SISOC que use el mismo cupo no queda cubierta por este límite.
- Una caída después de consultar RENAPER y antes de confirmar el checkpoint puede repetir esa consulta al reanudar. La transacción y la clave única evitan duplicar el ciudadano; no es posible prometer una única llamada externa sin un contrato idempotente del proveedor.

Revisar la estrategia si el bloqueo de la fila limita el caudal medido o si RENAPER define otro mecanismo formal de cuotas.
