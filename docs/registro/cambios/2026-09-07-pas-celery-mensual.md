# PAS: control mensual con Celery

Se reemplaza el disparo diario/manual sincrónico por corridas mensuales
persistidas, lotes con punto de control y Celery/Redis administrados desde Compose.
La lógica pertenece a PAS; el cliente técnico RENAPER admite reutilización
opcional de sesión/token sin cambiar el comportamiento de otros consumidores.

Decisiones: MySQL GET_LOCK serializa la ejecución global, incluso entre
mensajes duplicados. Dentro de ese único lote activo se usan dos hilos, cada
uno con su propia sesión y token, y un limitador compartido de 16 solicitudes/s.
Las ventanas se drenan antes de guardar; una transacción acopla todos sus
resultados con el avance del punto de control. La membresía del padrón se materializa
al comenzar y el lote por defecto sube de 500 a 2.000 personas. El progreso es
durable; no se depende de un backend Celery de resultados.

Un interruptor de circuito pausa la corrida después de drenar la ventana activa si
ésta tiene 0% de éxito operativo o si se acumulan ocho timeouts consecutivos.
No quedan hilos escribiendo después de marcar la pausa ni se llena una cola
interna de personas que continúe enviando tráfico.

Contrapartida inicial: un solo lote activo, paralelismo acotado y cuota conservadora,
sin promesa de terminar en el día. Incorporar Celery es una dependencia
explícitamente solicitada y no migra los workers de otros dominios.

## Evidencia de capacidad del 7 de septiembre de 2026

Las corridas productivas de 3.000, 9.000 y 260.913 personas sostuvieron hasta
aproximadamente 143 solicitudes/s durante pruebas breves sin degradación. En la
corrida larga, a unas 32 solicitudes/s, `/consultarenaper` dejó de responder tras
aproximadamente 107.700 consultas exitosas y 73 minutos. El login continuó
respondiendo y el endpoint de consulta no se recuperó en las verificaciones de
los 10–15 minutos siguientes. No hay confirmación de RENAPER sobre la causa.

Por esa incertidumbre se adopta 16 solicitudes/s agregadas y concurrencia 2 como
configuración inicial ajustable. Estos valores todavía deben validarse durante
15–20 minutos sostenidos antes de activar la programación mensual. Ser menores
que el punto observado de falla no demuestra que sean seguros.

Contrato funcional y guía operativa: `docs/implementaciones/pas_control_mensual_celery.md`.
La decisión de control diario 2026-07-29 queda sustituida por esta decisión.

## Validación local

- 76 tests PAS aprobados después del ajuste de capacidad, incluyendo partición
  de 250.000 IDs en 125 lotes de 2.000, límite agregado, aislamiento de clientes,
  reversión de ventana, reintentos e interruptor de circuito.
- 19 tests del cliente/fachada RENAPER aprobados.
- 5 tests de deploy aprobados tras incorporar el fixture de Compose Celery.
- Django check sin errores; makemigrations PAS sin cambios pendientes.
  No se pudo verificar el historial contra MySQL del servidor, que no era
  accesible desde el contenedor descartable.
- Pylint focalizado: 10/10. Black y djlint aplicados.
- Compose productivo válido, scripts Bash comprobados, diff sin errores de whitespace.
- Smoke real de Celery y Redis aislados: tarea recibida y completada.

La prueba larga posterior aporta evidencia de RENAPER, pero no valida todavía
la configuración nueva de 16 solicitudes/s y concurrencia 2. Tampoco se certificó
GET_LOCK con dos procesos Celery contra MySQL productivo. La activación
productiva y la retirada efectiva de cron quedan para la guía operativa del servidor.
