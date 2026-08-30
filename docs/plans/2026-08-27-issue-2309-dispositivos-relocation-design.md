# #2309 — reubicación canónica de Dispositivos

> **Supersedido el 2026-08-27.** La decisión confirmada para C1 separa el
> núcleo canónico del servicio de la compatibilidad Django del monolito. Ver
> `2026-08-27-issue-2309-c1-monorepo-boundary-design.md`.

## Objetivo del corte

Mover el código canónico de Dispositivos a `services/dispositivos/` sin
duplicarlo, conservando el app label `dispositivos`, las tablas existentes, los
IDs y las rutas públicas del monolito. Este corte no enruta tráfico al nuevo
runtime ni altera autoridad de escritura.

## Diseño aprobado

La app canónica quedará bajo
`services.dispositivos.dispositivos`, con `AppConfig.label = "dispositivos"`.
El monolito cambiará su `INSTALLED_APPS` a ese AppConfig y continuará incluyendo
las rutas por string. Así Django conserva el label de las migraciones y el
schema mientras el código tiene una única ubicación.

El proyecto independiente tendrá su propio `manage.py`, settings y URLs. Sus
ajustes sólo permiten comprobar el proyecto y preparar el runtime; no aceptan
tráfico hasta que el checkpoint de identidad firmada entregue un actor válido.

Los adaptadores que importan `core` o `users` vivirán fuera del paquete
canónico, en una zona explícita de compatibilidad del monolito. El dominio los
resolverá mediante puertos configurados. La referencia física legacy a
`core.Provincia`/`core.Municipio` se mantiene durante la Etapa A por
compatibilidad de schema; el proyecto independiente la representará como un
catálogo externo de sólo lectura, no como una importación del código de `core`.

## Alternativas descartadas

- Copiar la app en el servicio: crea dos fuentes de verdad y deriva durante el
  rollback.
- Ejecutar un proyecto nuevo que importe el paquete raíz: no transfiere la
  propiedad del código al servicio.

## Invariantes y rollback

- `label = "dispositivos"`, tabla `dispositivos_dispositivo`, IDs y las
  migraciones existentes no cambian.
- El monolito sigue siendo el único escritor y conserva las rutas actuales.
- No se crean cuentas, secretos, red, Compose, NGINX, JWS ni migración de
  datos.
- El rollback es revertir el commit de reubicación: no requiere reversa de
  datos porque el corte sólo cambia la ubicación del código y añade archivos.

## Validación

- `manage.py check` del monolito y del proyecto independiente.
- Tests focalizados de Dispositivos desde su nueva ubicación.
- `makemigrations --check`, `lint-imports`, Black, Pylint y `git diff --check`.
- Verificar que no existan dos implementaciones del dominio ni imports directos
  del paquete canónico hacia `core` o `users`.

## Condición para avanzar

Una vez que el proyecto independiente cargue el mismo dominio y el monolito
mantenga las rutas sin cambio observable, el siguiente corte será el contrato
HTTP opcional de favoritos. La autenticación firmada, routing externo y
autoridad de escritura permanecen bloqueados hasta el checkpoint 2/Etapa A.
