# Merge de migraciones de Comedores

## Motivo

El despliegue de Homologacion del 7 de septiembre de 2026 se detuvo porque
`comedores` tenia dos migraciones terminales que dependian de la misma
migracion `0056`.

## Cambio

Se agrego `0058_merge_20260908_0000`, una migracion vacia que unifica
`0057_huecos_seguimiento_n19` y `0057_issue_2403_responsable_tarjeta`.

No ejecuta operaciones SQL ni modifica datos: solo vuelve lineal el grafo de
migraciones para que Django pueda validar y aplicar las migraciones pendientes.
