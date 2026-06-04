# 2026-06-04 — Decision: la tendencia mensual del Reporter de Provincias se agrupa en Python, no con TruncMonth

Contexto: error 500 en `/reporter-provincias/` reportado por el usuario.

## Sintoma

`GET /reporter-provincias/` levantaba `ValueError: Database returned an invalid
datetime value. Are time zone definitions for your database installed?`, con el
traceback terminando en `_build_tendencia_mensual`
(`celiaquia/views/reporter_provincias.py`).

## Causa raiz

`_build_tendencia_mensual` agrupaba los casos por mes con
`annotate(periodo=TruncMonth("creado_en"))`. En MySQL, cualquier `Trunc*`/`Extract*`
sobre un `DateTimeField` con `USE_TZ=True` y `TIME_ZONE` distinto de UTC se traduce
a `CONVERT_TZ(creado_en, 'UTC', 'America/Argentina/Buenos_Aires')`. Esa funcion
devuelve `NULL` cuando la base **no tiene cargadas/activas** las tablas
`mysql.time_zone*`, y Django convierte ese `NULL` en el `ValueError` de arriba.

La base de produccion (`Produccion-vieja`, `10.80.5.46:3306`) no las tiene activas.

## Alternativas evaluadas

1. **Cargar `mysql.time_zone*` en produccion** (`mysql_tzinfo_to_sql`): es la
   solucion "de plataforma", pero requiere permisos de escritura sobre el schema
   `mysql` y, sobre todo, un **restart de `mysqld`** para que el server active las
   zonas nombradas (es un flag que MySQL fija al arrancar; no hay `FLUSH` que lo
   fuerce). No tenemos acceso a reiniciar el servicio productivo.
2. **Usar offset fijo `-03:00`** en vez de la zona nombrada: valido (Argentina es
   UTC-3 constante desde 2009, sin horario de verano) y no necesita las tablas,
   pero obliga a tocar la config de conexion de Django y deja una convencion
   implicita facil de romper.
3. **Agrupar en Python** (elegida): se traen las fechas ya filtradas y se bucketea
   por `(anio, mes)` en memoria, sin delegar la truncacion temporal a la base.

## Decision

Se adopta la opcion 3. `_build_tendencia_mensual` deja de usar `TruncMonth` y agrupa
en Python usando `timezone.localtime` para respetar `settings.TIME_ZONE`. Asi el
reporte funciona en cualquier entorno (produccion sin tz tables, CI con SQLite,
local) sin depender del estado de `mysql.time_zone*` ni de un restart del server.

## Implementacion

- `celiaquia/views/reporter_provincias.py`: se elimina el import y el uso de
  `django.db.models.functions.TruncMonth`; el conteo mensual se hace con un
  `collections.Counter` sobre `creado_en` (ya acotado a 180 dias). Se conserva el
  contrato de salida (`label` `MM/AAAA`, `count`, `size`) que consume
  `celiaquia/templates/celiaquia/reporter_provincias.html`.

## Consecuencias

- **El reporte deja de depender de las tz tables de la base**: red de seguridad
  permanente, no solo para produccion.
- **Costo**: el agrupado pasa de la base a la app. El volumen esta acotado por el
  filtro `creado_en >= hoy - 180 dias` y por el scope territorial del usuario, asi
  que el set materializado es chico; el impacto es despreciable.
- **Carga de `mysql.time_zone*` en produccion**: queda como tarea de plataforma de
  baja prioridad (requiere restart de `mysqld`, coordinable por Infra). No es
  bloqueante. Mientras tanto, cualquier consulta futura que necesite conversion de
  zona del lado de la base deberia usar el offset fijo `-03:00` en vez de la zona
  nombrada, o resolver el agrupado en Python como aca.
