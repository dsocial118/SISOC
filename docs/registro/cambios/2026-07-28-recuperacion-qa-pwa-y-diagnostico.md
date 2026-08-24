# Recuperación de QA: fixtures PWA y diagnóstico de despliegue

## Contexto

La validación `pytest` de `development` quedó bloqueada después de incorporar
la regla que oculta en PWA los comedores que no tienen programa. Dos fixtures
todavía creaban comedores sin programa, y la suite de nómina refería
`Programas` sin importarlo.

El despliegue de QA llega a reconstruir el stack, pero el chequeo posterior de
migraciones agotó sus reintentos sin dejar el estado del contenedor que lo
impedía.

## Cambio

- Los fixtures de las pruebas PWA crean comedores con el programa
  `Abordaje Comunitario`, que representa un comedor visible en PWA.
- La suite de nómina importa explícitamente `Programas`.
- Los jobs de QA y homologación muestran `docker compose ps` y las últimas 200
  líneas del servicio `django` sólo cuando `migrate --check` no se vuelve
  disponible. Esto permite diferenciar un arranque lento de un contenedor
  detenido sin exponer información durante un deploy sano.

## Validación esperada

- Ejecutar las suites PWA afectadas con pytest.
- Confirmar en CI que `pytest` vuelve a pasar y que el job de QA informa el
  estado real del servicio si la disponibilidad sigue fallando.
