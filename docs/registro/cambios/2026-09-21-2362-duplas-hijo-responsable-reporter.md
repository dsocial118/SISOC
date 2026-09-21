# Celiaquía: duplas hijo–responsable en el reporte de provincias

Ticket 2362. Rama `CeliaquiaTk_2362`.

## Problema

En `/reporter-provincias/` el panel "Clasificación por rol" ya separaba los
legajos aprobados en cuatro categorías mutuamente excluyentes (beneficiario
únicamente, doble rol, responsable únicamente y menor de edad), pero no decía
nada sobre el vínculo entre ellos.

Producto no podía responder la pregunta operativa de fondo: **cuántas duplas
hijo–responsable hay alcanzadas**. Con sólo los subtotales por categoría, un
menor aprobado y su responsable aprobado se ven como dos legajos sueltos; contar
duplas a ojo exigía cruzar a mano el grupo familiar de cada caso.

## Solución

### Conteo de duplas

`_build_clasificacion_aprobados` ahora arma también el conjunto de duplas. La
consulta a `GrupoFamiliar` que ya existía (para detectar responsables que además
son beneficiarios) pasó a traer las dos puntas del vínculo, así que **no se
agregó ninguna consulta nueva** al cálculo del panel: se reusa el mismo batch.

Dos definiciones que conviene dejar escritas, porque el ticket no las fija y
cambian el número:

- **Una dupla se cuenta por hijo, no por par.** Si un hijo tuviera dos
  responsables vinculados, sigue siendo una sola dupla. El criterio de
  aceptación pide explícitamente no duplicar el conteo de personas.
- **Las dos puntas tienen que estar aprobadas.** Es un reporte de aprobados: si
  el responsable fue rechazado, la dupla no está conformada. El responsable se
  busca dentro del mismo queryset filtrado que el resto del panel, así que las
  duplas respetan el alcance territorial y los filtros activos.

La dupla se define por el **vínculo** (`GrupoFamiliar` con
`cuidador_principal=True`, el criterio que usa toda `FamiliaService`), no por la
edad del hijo. Atarla a "menor de 18" haría bajar el conteo de duplas cuando un
chico cumple años durante el trámite, sin que haya cambiado nada real.

### Subtotales transversales

Debajo de los chips de categoría se agregó una franja de cuatro subtotales:
legajos aprobados, personas únicas, beneficiarios alcanzados y duplas. Las
duplas se muestran separadas del total de legajos y del de beneficiarios
justamente para que no se lean como personas adicionales.

"Beneficiarios alcanzados" es el total menos los responsables únicamente: el
responsable puro valida a sus dependientes pero no es beneficiario del programa
(`ExpedienteCiudadano.es_rol_responsable_puro`, que tampoco ocupa cupo ni
padrón).

### Detalle paginado

La tabla suma una columna "Rol" con la categoría de cada legajo y un badge
"Dupla". El badge se pone **sólo del lado del hijo**, no del responsable, para
que una fila marcada equivalga siempre a una dupla del panel. El cálculo corre
sobre las 12 filas visibles y cuesta dos consultas acotadas por página.

## Archivos

- `celiaquia/views/reporter_provincias.py`: `_build_subtotales_aprobados` y
  `_anotar_clasificacion_pagina` nuevos; `_build_clasificacion_aprobados`
  devuelve `duplas`, `personas_unicas`, `beneficiarios` y `subtotales`.
- `celiaquia/templates/celiaquia/reporter_provincias.html`: franja de subtotales
  y columna "Rol" en el detalle.
- `static/custom/css/reporter_provincias.css`: `.reporter-subtotals` y el tono
  `primary` que el item "responsable" ya declaraba sin tener estilo definido.
- `celiaquia/tests/test_reporter_provincias.py`: dos tests nuevos.

## Para tener en cuenta al probar

En producción los 679 vínculos vivos de `ciudadanos_grupofamiliar` tienen
`cuidador_principal = 1`. **La base local es el caso opuesto**: los hijos de los
datos de QA cargados a mano tienen ese flag en 0, así que ahí las duplas dan
cero aunque el vínculo exista. No es un bug del reporte.
