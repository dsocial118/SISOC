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

**La franja mezcla dos unidades y eso hay que leerlo con cuidado.** Sólo
"Legajos aprobados" cuenta legajos; "Personas únicas", "Beneficiarios
alcanzados" y "Duplas" cuentan **personas**. La distinción no es teórica:
`ExpedienteCiudadano` es único por `(expediente, ciudadano)` y el reporte agrega
sobre todos los expedientes del alcance, así que un ciudadano con legajos
aprobados en dos expedientes suma 2 al primer número y 1 a los otros tres. Que
el caso existe lo confirma `CupoService`, que usa `es_titular_activo`
justamente para elegir cuál de los legajos de un ciudadano está vivo.

"Beneficiarios alcanzados" son entonces las **personas distintas** que no son
responsable puro: el responsable puro valida a sus dependientes pero no es
beneficiario del programa (`ExpedienteCiudadano.es_rol_responsable_puro`, que
tampoco ocupa cupo ni padrón). Se cuenta en personas y no en legajos para que
las tres cifras de la derecha de la franja sean comparables entre sí; contarlo
en legajos podía dar un número **mayor** que el de personas únicas que tiene al
lado. Un ciudadano que es responsable puro en un expediente y beneficiario en
otro cuenta como beneficiario.

### Lo que el conteo de duplas no filtra

La dupla se arma con `cuidador_principal=True` y **no** se filtra por `vinculo`.
`FamiliaService` siempre escribe `PADRE/MADRE` junto con esa marca, pero la
ficha del ciudadano (`ciudadanos/forms.py`) deja cargar cualquier vínculo con
`cuidador_principal` tildado. Si hubiera vínculos no parentales marcados así,
se contarían como duplas hijo–responsable. Para verificarlo:

```sql
SELECT vinculo, COUNT(*)
FROM ciudadanos_grupofamiliar
WHERE cuidador_principal = 1 AND deleted_at IS NULL
GROUP BY vinculo;
```

Si aparecen vínculos distintos de `PADRE/MADRE`, hay que acotar por `vinculo` en
`_build_clasificacion_aprobados` y en `_anotar_clasificacion_pagina` — y tener
en cuenta que eso también cambia la clasificación `doble_rol`, que ya usaba este
mismo criterio desde antes de este cambio.

### Detalle paginado

La tabla suma una columna "Rol" con la categoría de cada legajo y un badge
"Dupla". El cálculo corre sobre las 12 filas visibles y cuesta dos consultas
acotadas por página.

La columna "Rol" se completa para **todos** los legajos de la página, aprobados
o no: la categoría es una propiedad de la persona y su rol, no del resultado de
la revisión. Por eso la columna no es sumable contra el panel, que cuenta
únicamente aprobados. Está aclarado en el `title` de la cabecera.

El badge "Dupla" sí exige legajo aprobado y se pone **sólo del lado del hijo**,
no del responsable, porque esa es la punta que el panel cuenta. Con el matiz de
la unidad: el panel cuenta duplas por persona, así que un hijo con legajos
aprobados en dos expedientes marcaría dos filas para una sola dupla.

## Archivos

- `celiaquia/views/reporter_provincias.py`: `_build_subtotales_aprobados` y
  `_anotar_clasificacion_pagina` nuevos; `_build_clasificacion_aprobados`
  devuelve `duplas`, `personas_unicas`, `beneficiarios` y `subtotales`.
- `celiaquia/templates/celiaquia/reporter_provincias.html`: franja de subtotales
  y columna "Rol" en el detalle.
- `static/custom/css/reporter_provincias.css`: `.reporter-subtotals` y el tono
  `primary` que el item "responsable" ya declaraba sin tener estilo definido.
  La tarjeta de duplas va resaltada en `accent`, el mismo tono que el badge
  "Dupla" del detalle, para que las dos lecturas del dato se reconozcan como la
  misma.
- `celiaquia/tests/test_reporter_provincias.py`: cinco tests nuevos.

## Para tener en cuenta al probar

En producción los 679 vínculos vivos de `ciudadanos_grupofamiliar` tienen
`cuidador_principal = 1`. **La base local es el caso opuesto**: los hijos de los
datos de QA cargados a mano tienen ese flag en 0, así que ahí las duplas dan
cero aunque el vínculo exista. No es un bug del reporte.

## Cobertura

- `test_reporter_provincias_cuenta_duplas_hijo_responsable`: dupla completa,
  responsable rechazado (no cuenta) y hijo con dos responsables (cuenta una).
- `test_reporter_provincias_marca_dupla_en_el_detalle`: la marca está del lado
  del hijo y no del responsable.
- `test_reporter_provincias_cuenta_beneficiarios_en_personas_no_en_legajos`:
  mismo ciudadano aprobado en dos expedientes, y un ciudadano que es responsable
  puro en uno y beneficiario en otro. Es el test que distingue personas de
  legajos: con el conteo en legajos, "Beneficiarios alcanzados" daba 3 contra 3
  personas únicas.
- `test_reporter_provincias_subtotales_respetan_el_filtro_activo`: los
  subtotales y las duplas se recalculan sobre la lectura filtrada.
- `test_reporter_provincias_clasificacion_no_agrega_consultas`: fija en 2 + 2 el
  costo declarado y protege del N+1 en `caso.ciudadano` si alguien sacara el
  `select_related` de la vista.
