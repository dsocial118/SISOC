# Control mensual de supervivencia PAS

## Objetivo funcional

El control consulta RENAPER para identificar fallecimientos entre los titulares
del padrón PAS. Se inicia el último día del mes a las 02:00, hora argentina,
cuando la programación está habilitada en el ambiente. Las 02:00 son la hora
de inicio, no un plazo de finalización.

## Qué ve el operador

En `/pas/cruces`, Supervivencia muestra la última corrida, fecha de corte,
estado y cantidad procesada sobre el total. El avance se consulta recargando
la página. El botón solicita una corrida mensual y responde inmediatamente.
Si ya existe una corrida para ese mes, devuelve la misma: no fuerza otra.
Solicitarla manualmente antes del cierre consume la corrida de ese mes; por
eso el botón debe usarse para recuperación del cierre, no como control diario.

Los valores internos de estado son `pending` (pendiente), `running` (en proceso), `paused`
(requiere intervención), `completed` y `completed_with_errors`.

Cada fallecimiento confirmado crea una incompatibilidad de Supervivencia
pendiente, visible en la bandeja existente. No cambia automáticamente el
estado administrativo del titular. El impacto es el primer día del mes
siguiente a la fecha de corte, aunque la ejecución termine otro mes.
Errores técnicos y ausencia de coincidencia no se interpretan como muerte.
La bandeja conserva su límite existente de 100 incompatibilidades recientes.

## Volumen y recuperación

Al comenzar se fija la lista de identificadores del padrón, dividida en lotes
de 2.000 por defecto. Sigue existiendo un solo lote activo global, protegido
por el `GET_LOCK` de MySQL. Dentro del lote, dos hilos consultan en paralelo;
cada uno conserva su propia sesión y token RENAPER.

Las personas se procesan en ventanas del tamaño de la concurrencia. Celery
espera que termine toda la ventana y después guarda sus resultados y avanza
el punto de control en una única transacción. Si el proceso muere antes de confirmar,
la entrega siguiente puede repetir como máximo esa ventana; las escrituras son
idempotentes. El lote cede ejecución aproximadamente a los 240 segundos y
continúa en otra entrega.

El máximo inicial es 16 solicitudes HTTP por segundo entre todos los hilos. Es
una tasa agregada: aumentar `PAS_CONCURRENCY` no multiplica ese límite. Un
segundo intento por sexo y un reintento posterior a un 401 también consumen
una ranura. Por eso 16 solicitudes/s no equivale necesariamente a 16 personas/s.

Para 250.000 titulares, el piso matemático es unas 4 h 20 min si cada persona
requiere una solicitud, y unas 8 h 41 min si todas requieren dos. No es un tiempo
prometido: la latencia, los reintentos, pausas y la proporción de segundos
intentos pueden extenderlo.

Los errores internos `timeout` y `remote_error` reintentan la persona hasta tres veces,
siempre bajo el mismo limitador. Al agotarse se registra error y continúa el
padrón. Un error de autenticación pausa la corrida después de drenar la ventana
activa. También se abre el interruptor de circuito si una ventana no tiene ninguna respuesta
operativamente exitosa o se alcanza el umbral de timeouts consecutivos. En ese
caso no se encolan más personas, no se avanza la ventana y un humano debe
revisar el servicio antes de reanudar. Los resultados ya confirmados se conservan.

## Infraestructura y activación

`docker-compose.celery.yml` agrega Redis persistente, un worker Celery exclusivo
de PAS y una única instancia de Beat. El deploy versionado incorpora este
archivo para todos los ambientes. MySQL conserva corridas, lotes y resultados;
Redis transporta identificadores. No se guardan DNI ni tokens en mensajes.

Configuración en `.env`:

- `PAS_MONTHLY_ENABLED=false`: habilitar expresamente en producción tras retirar cron.
- `PAS_BATCH_SIZE=2000`: titulares por lote.
- `PAS_BATCH_SECONDS=240`: presupuesto por ejecución del lote.
- `PAS_REQUESTS_PER_SECOND=16`: tasa agregada objetivo de solicitudes RENAPER.
- `PAS_CONCURRENCY=2`: hilos de consulta dentro del único lote activo.
- `PAS_CIRCUIT_BREAKER_TIMEOUTS=8`: timeouts consecutivos que pausan la corrida.
- `CELERY_BROKER_URL=redis://redis:6379/0`.

El scheduler comprueba días 28–31 a las 02:00 y valida fin de mes. Un mensaje
demorado fuera de esa hora no inicia una corrida nueva. Si el servidor estuvo caído
durante la ventana, Operaciones debe solicitar el cierre con `--fecha`.
Las corridas existentes se recuperan automáticamente al volver los servicios.

## Instalación, cron y rollback

Responsable operativo: equipo de despliegue o referente técnico. Aplicar migraciones antes
de activar la programación. Verificar MySQL, broker, worker, Beat y permisos
de RENAPER en el ambiente objetivo.

1. Ejecutar `sudo bash scripts/infra/remove_pas_cron.sh` (inspección).
2. Revisar envoltorios y temporizadores adicionales, y comprobar que no haya
   un proceso PAS antiguo activo.
3. Ejecutar el mismo script con `--apply`: respalda y elimina solo las entradas
   directas de `manage.py sincronizar_supervivencia_pas` de usuarios y cron del sistema.
4. Repetir inspección y revisar crontabs efectivos. El script no detecta comandos
   ocultos en envoltorios; éstos requieren revisión del servidor.
5. Levantar el Compose del ambiente con `-f docker-compose.celery.yml` y habilitar
   la programación solo después de la validación.

La línea PAS se retira de `scripts/crontab`; los cron ajenos permanecen.
Los respaldos efectivos viven en `/var/backups/sisoc/pas-cron/`.

Comandos de operador:

```bash
python manage.py sincronizar_supervivencia_pas --fecha 2026-09-30
python manage.py sincronizar_supervivencia_pas --reanudar 123
celery -A config.celery:app inspect ping
```

La versión nueva del comando ya no admite `--forzar` ni `--limite`; toda
ejecución usa la cola y la exclusión. Para rollback: deshabilitar programación,
detener Beat y worker con espera, conservar volúmenes y tablas/checkpoints.
No restaurar automáticamente el cron diario antiguo. Revertir código no debe
borrar datos ni reactivar consultas sobre una corrida ya procesada.

## Verificación pendiente en cada servidor

Comprobar retiro de cron, única instancia de Beat, ping del worker, logs,
progreso/última actividad de una corrida controlada y resultados. Antes de
habilitar `PAS_MONTHLY_ENABLED`, ejecutar `logs/bench_pas/bench_renaper.py` con
16 solicitudes/s y concurrencia 2 durante al menos 15–20 minutos, preferentemente
fuera de horario, y confirmar que no aparece un corte total. El valor 16 es una
decisión conservadora pendiente de esa validación, no una cuota confirmada por
RENAPER.
