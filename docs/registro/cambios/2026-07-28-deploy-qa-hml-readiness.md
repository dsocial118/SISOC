# Espera de disponibilidad en deploy de QA y HML

Fecha: 2026-07-28

## Cambio

El workflow de despliegue espera de forma acotada que terminen las migraciones
del entrypoint y que responda el healthcheck de QA y homologación antes de
declarar el deploy fallido.

En homologación incorpora además un bootstrap seguro: si el helper local no
reconoce `--expected-revision`, actualiza solo el checkout de la branch
`homologacion` mediante `merge --ff-only` después de validar el SHA remoto.

## Motivo

El workflow verificaba migraciones inmediatamente después de levantar los
contenedores. Eso podía observar el estado intermedio del entrypoint y fallar
aunque el proceso siguiera aplicándolas. HML tampoco podía actualizar su
helper local porque invocaba una opción nueva antes de refrescar el checkout.

## Alcance y resguardo

No se cambia el comportamiento de producción. Los reintentos tienen un límite
de 30 intentos con dos segundos entre ellos y muestran la última salida si no
se alcanza disponibilidad.
