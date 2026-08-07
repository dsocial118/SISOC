# 2026-07-31 - Rediseno transversal del buscador: lupa, filtro primario y CTA verde

## Resumen

Se rediseno el componente `templates/components/search_bar.html` siguiendo el
prototipo de Figma "SISOC_ Version UX" (file `yXUvxp2RKEMNDS8JHv0HdU`, frame
`13501:32237` "BUSCADOR CENTROS DE FORMACION PROFESIONAL", componente
`13503:33051` "SEARCH BAR").

El componente es punto unico de entrada de **41 listados** (14 en `filters_mode`,
5 en `ajax_search_mode`, ~22 en modo simple), asi que el cambio es transversal
por construccion: se toca un template y aplica a todos.

Cambios de interaccion:

- El boton **"Filtrar"** desaparece. Lo reemplaza una **lupa** en el margen
  derecho del input, dentro de la misma caja.
- El boton de agregar pasa de amarillo (`#e7ba61`, radio 6px, mayusculas) a
  **CTA verde** (`#2e7d33`, radio 20px, icono `+`, 18px, sin mayusculas).
- **Con filtros**: el primer filtro vive dentro de la barra
  (campo + operador + valor + lupa) y `+ Filtro` agrega filas adicionales
  debajo. **Sin filtros**: solo el buscador (input + lupa).
- **"Exportar busqueda"** (antes "Descargar CSV") se mueve arriba a la derecha,
  con icono, conservando la clase `.btn-export-csv` y el `data-url` que
  `export_helper.js` necesita.

## Archivos nuevos

- `static/custom/css/poncho.css` - **solo variables** (paleta PONCHO, radios,
  espaciados, tipografia). Al no aplicar estilos propios puede cargarse temprano
  en el `<head>` sin pelear con la cascada de los CSS por pagina.

## Archivos modificados

- `templates/includes/base.html` - carga `poncho.css`.
- `templates/components/search_bar.html` - los tres modos; barra superior de
  exportacion; fila de acciones alineada a la derecha sin "Filtrar".
- `static/custom/css/comedoresSearchBar.css` - estilos `.poncho-*` con los
  valores del prototipo.
- `static/custom/js/advanced_filters.js` - refactor (ver abajo).
- `static/custom/js/favorite_filters.js` - usa el serializador compartido.
- `VAT/templates/vat/centros/centro_list.html` - `add_text='Agregar CFP'`.
- `centrodefamilia/tests/test_beneficiarios_export.py` - el test afirmaba
  `"Descargar CSV"` y `"search-actions"`, que son justamente el texto y la
  ubicacion que este ticket cambia. Se actualizo a `"Exportar busqueda"` y
  `"poncho-topbar"`. Se mantiene la assert sobre `btn-export-csv` porque esa
  clase es el contrato real con `export_helper.js`.

## Decisiones y trade-offs

### Operadores: UX/UI definio eliminarlos (2026-08-04)

**Definicion recibida:** el selector de "tipo de coincidencia" no va mas, y los
filtros se agregan tal cual el mockup nuevo: cada filtro es una barra completa
(campo + valor + lupa), con "+ Filtro" para sumar una fila y "- Filtro" para
quitarla, visible recien desde la segunda.

Implementado asi. El operador ahora se deduce del tipo de campo
(`defaultOpByType`): texto -> `contains`, numero / fecha / choice / boolean ->
`eq`.

**Lo que se pierde con esta definicion** (se detalla porque la decision fue
tomada con la tabla de abajo a la vista, y conviene que quede el registro):

| Se pierde | Impacto |
|---|---|
| `vacio` (+ modo nulos/vacios/ambos) | no se puede listar registros con un campo sin cargar |
| `mayor a` / `menor a` | no se puede filtrar por rango en numeros ni fechas |
| `distinto de` / `no contiene` | no se puede excluir |

**AND/OR y Favoritos: tambien se retiran (definicion del 2026-08-04).**

- El selector AND/OR salio de la UI. Los filtros se combinan **siempre con
  AND** (`LOGICA_FIJA` en `advanced_filters.js`). El backend sigue aceptando el
  campo `logic`, asi que reponerlo es agregar el control.
- Favoritos salio de la UI: se quitaron el boton, el modal y la carga de
  `favorite_filters.js`. **El backend y el archivo JS siguen existiendo**, solo
  se dejaron de renderizar. Los favoritos ya guardados no se borran.

### El borde dorado del buscador: causa y solucion

En revision se vio que el selector "Buscar por" y la caja del buscador salian
con borde dorado en vez del blanco del prototipo. La causa concreta:
`listModerno.css` tiene reglas del diseño anterior

    #filters-rows select, #filters-rows input { border: 2px solid #e7ba61 !important }

Mientras el filtro primario vivia fuera del contenedor no las tocaba, pero al
pasar **todas** las filas a `#filters-rows` quedaron alcanzadas.

Solucion: se renombro el contenedor a **`#poncho-filters-rows`**. Es mas limpio
que competir con `!important` y deja las reglas viejas intactas para quien
todavia use ese marcado. Se aprovecho para borrar de `comedoresSearchBar.css`
las reglas muertas del modelo anterior (`.filters-row`, `.filters-header-row`,
`.filters-toolbar`, `.filters-logic-select` y el bloque select2 dorado).

### Medidas del buscador tomadas del componente

Se alinearon contra el nodo `13503:33051` ("SEARCH BAR"):

- caja: `padding-left: 20px` y `gap: 45px` entre el texto y la lupa;
- input: `padding: 10px` en los cuatro lados (sumado al `pl` de la caja da los
  30px de sangria del prototipo) y `line-height: 40px`;
- selector de campo: `padding-right: 40px` (el ancho de la caja del chevron),
  `max-width: 193px` y chevron centrado en esa caja (`right 12px`);
- el placeholder de cada fila es "Buscar por filtro N", como el mockup: no se
  usa el `placeholder` que pasa cada listado.

El `border-radius: 5px` del selector y el fondo `rgba(255,255,255,.2)` de su
hover salen de los estados del prototipo.

Unica diferencia conocida que queda: el chevron del prototipo mide `18x10` y el
implementado es un SVG de `16x16`. Igualarlo requiere redibujar el path, porque
escalar el viewBox cuadrado lo deforma.

### select2: se probo y se descarto

Se llego a montar select2 sobre el selector de campo con un tema propio, pero
el equipo pidio sacarlo. El selector quedo como **`<select>` nativo estilado**
(`appearance: none` + chevron propio en SVG), que es lo que ya replicaba el
prototipo.

Con eso se removieron tambien el wrapper `.poncho-search__fieldwrap` (existia
solo porque select2 inserta su `<span>` como hermano del `<select>` y hubiera
sido una cuarta columna del grid) y todo el bloque de estilos `.poncho-select2`.

Consecuencia a tener en cuenta: en listados con muchos campos, el combo no
tiene buscador interno.

Nota tecnica: al desaparecer el operador tambien se removieron el selector de
"modo de vacio" y el panel avanzado plegable. Las filas ya no usan select2 (el
campo es un `select` nativo estilado, como pide el diseño); en listados con
muchas opciones eso cambia la experiencia de busqueda dentro del combo.

### Version anterior de esta decision (reemplazada)

Antes de la definicion de UX/UI se habia optado por conservar los operadores
plegados en un panel avanzado. Ese enfoque quedo sin efecto.

El prototipo muestra unicamente `Buscar por` + valor + lupa + `+ Filtro`. No
muestra el selector de **"Tipo de coincidencia"**, ni **AND/OR**, ni
**Favoritos**.

Eliminarlos degrada la busqueda de forma concreta y verificable:

| Se perderia | Impacto |
|---|---|
| `vacio` (+ modo nulos/vacios/ambos) | no se puede listar registros con un campo sin cargar |
| `mayor a` / `menor a` | no se puede filtrar por rango en numeros ni fechas |
| `distinto de` / `no contiene` | no se puede excluir |
| logica `OR` | solo se podria pedir que se cumplan todos los filtros a la vez |
| Favoritos | se pierden los filtros guardados que ya usan los equipos |

Solucion adoptada: **no se eliminan y tampoco ensucian la barra**. El estado en
reposo es identico al mockup; todo lo avanzado vive en un panel plegado que
abre `+ Filtro` (`#filters-advanced`). El panel se abre solo cuando la URL trae
un estado que la barra no puede representar (mas de un filtro, u operador
distinto del default del campo), para que el usuario nunca vea resultados
filtrados por algo que no esta a la vista.

Si UX/UI decide igualmente darlos de baja, el cambio es acotado: quitar el
bloque `#filters-advanced` del template y las funciones `openAdvanced()` /
`necesitaPanelAbierto()` de `advanced_filters.js`. Conviene que quede escrito
que implica perder lo de la tabla de arriba.

### Alcance del rediseno visual (fondo, tabla, tipografia)

La primera version de este PR cubria solo la barra de busqueda, y al verlo en
pantalla no se parecia al prototipo: el frame de Figma es una **pagina entera**
y la barra es una franja. El grueso de lo que define ese look es el fondo, la
tabla y la tipografia del titulo.

Se incorporo entonces `static/custom/css/poncho_listados.css`:

- **Fondo** de la zona de contenido a `--poncho-azul-secundario`. Esto ademas
  corrige que el buscador se leyera violeta: `#232d4f` ahora queda mas oscuro
  que la pagina, como en el prototipo, en vez de mas claro.
- **Tabla**: encabezado teal `#3b8681` con texto blanco en mixto (antes
  `#34495e` con dorado en MAYUSCULAS), esquinas 15px, separadores claros, sin
  cebra, celdas 56px.
- **Botones de accion** de tabla con radio 12px y la paleta del prototipo.
- **Paginacion** con el borde y radio del design system.
- **Titulo** en mixto y bold (`.poncho-titulo`), ya no `display-4` en MAYUSCULAS.

**El alcance esta acotado con `:has(.poncho-search)`**: aplica solo en las
paginas que renderizan el buscador nuevo. Repintar toda la app (formularios,
detalles, dashboards) es un cambio de tema con otro riesgo y otra validacion.
`:has()` ya se usaba en `listModerno.css`, asi que no agrega una dependencia
nueva.

Consecuencia a tener presente: al navegar de un listado a un detalle el fondo
cambia. Unificarlo es el paso siguiente y deberia decidirse con diseno.

### La forma transversal a todos los botones queda para un PR aparte

El pedido incluia aplicar la forma del boton a **todos** los botones de la app.
No se hizo en este PR porque **no existe una capa central de botones**: `.btn` y
`.btn-primary` estan redefinidos en ~20 hojas de estilo (`listModerno.css`,
`nuevoColorPrimary.css`, `login.css`, `cdf.css`, `ciudadano.css`,
`comedorFormModerno.css`, ...), varias con `!important`. El amarillo actual sale
de `listModerno.css:52` (`.search-actions .btn-primary`), no del `btn-primary`
global — de hecho `nuevoColorPrimary.css` esta comentado en el `<head>`.

Desarmar esos overrides es un refactor propio y mezclarlo aca contradice la
regla de "cambios pequenos y revisables". `poncho.css` deja los tokens listos
para ese segundo PR.

### Refactor de `advanced_filters.js`

La logica de una fila (campo -> operadores -> valor) estaba encerrada en
closures dentro de `addRow()`. Se extrajo a `wireRow(refs, options)`, que ahora
usan tanto la fila primaria de la barra como las filas dinamicas.

- `initPrimaryRow(prefill)` conecta los elementos que el template ya renderiza.
- `addRow(prefill)` crea y conecta las filas de `+ Filtro`.
- La fila primaria usa **selects nativos** (`useSelect2: false`): select2 rompe
  el estilo de la barra. Las filas dinamicas siguen usando select2.
- `setVisible()` unifica el ocultado, porque la fila primaria usa el atributo
  `hidden` (es hija flex de la barra) y las dinamicas `style.display`.

### Bug evitado en Favoritos

`favorite_filters.js` serializaba recorriendo `#filters-rows`. Como la fila
primaria ya **no vive ahi**, guardar un favorito habria perdido silenciosamente
el primer filtro. Se expone `window.AdvancedFilters.collectPayload()` desde
`advanced_filters.js` y `favorite_filters.js` lo usa, con su bucle previo como
fallback. Aplicar un favorito no se toco: navega con `?filters=...` y
`loadFromQuerystring()` reconstruye.

## Correcciones tras la primera revision visual

- **`+ Filtro` se dibujaba como pildora verde en mayusculas.** Sobrevivian las
  reglas viejas `#add-filter { background:#10b981; text-transform:uppercase }`
  en `comedoresSearchBar.css`. Al ser selector de **ID** le ganaban a
  `.poncho-addfilter` (clase). Se eliminaron.
- **El selector de campo se veia distinto segun el listado** (con caja de borde
  dorado en CFP, sin borde en otros). No se logro identificar la hoja exacta que
  lo pisa. Se endurecio el componente: selectores compuestos (`.poncho-search
  .poncho-search__field`, 0-2-0) y `appearance:none` con chevron propio en SVG,
  para que el control se dibuje igual en los 41 listados sin depender de que
  ninguna hoja por pagina lo redefina.

## Pendiente de diseno: el buscador lee violeta sobre el tema actual

En el prototipo el fondo detras de la barra es `#3e5a7e` (PONCHO/azul
secundario), asi que la caja `#232d4f` (PONCHO/azul principal) se ve **mas
oscura** que la pagina. En la app el fondo real es el dark theme de AdminLTE,
bastante mas oscuro que `#3e5a7e`, con lo cual `#232d4f` queda **mas claro** que
la pagina y se lee violeta.

El componente es fiel al token; lo que difiere es el contexto. Hay que definir
con diseno una de dos: o el fondo de pagina migra a la paleta PONCHO, o la caja
del buscador necesita otro tratamiento sobre el tema oscuro actual. No se
cambio por cuenta propia porque implica tocar el tema global.

## El buscador y las filas se veian violeta: colision de variables

Sintoma: la caja del buscador y las filas de la tabla se veian violeta en vez
del azul del prototipo.

Causa: **`hitos.css` declaraba la misma variable** `--poncho-azul-principal`
con valor `#230D4F` —que es violeta— y en `templates/includes/base.html` se
carga **despues** de `poncho.css`, asi que pisaba el `#232d4f` correcto. Los dos
valores difieren en un solo caracter (`230d4f` vs `232d4f`), asi que muy
probablemente el de `hitos.css` era un typo o un valor viejo. El valor bueno
esta verificado contra las variables reales del archivo de Figma:
`Poncho/ Azul Principar = #232d4f`.

Solucion: se quito la declaracion de `hitos.css` y se dejo un comentario en su
lugar advirtiendo que la variable vive en `poncho.css` y que no hay que volver
a declararla ahi. Las tres reglas de `hitos.css` que la usan (lineas 166, 419 y
607) pasan a tomar `#232d4f`; el cambio de tono es imperceptible.

Se revisaron las demas colisiones entre ambos archivos: `--poncho-verde`,
`--poncho-rojo` y `--poncho-blanco` estan declaradas en los dos pero con el
**mismo valor**, asi que son inocuas.

Nota: en una primera revision se concluyo, equivocadamente, que el violeta era
el token correcto y que se trataba de contraste con el teal del encabezado. No
lo era; queda asentado para que no se repita el diagnostico.

## Pendientes / deuda

- **"Exportar busqueda" en CFP**: `VAT/templates/vat/centros/centro_list.html`
  pasa `export_url=''` y no existe endpoint de exportacion de centros en
  `VAT/urls.py`. El boton no se muestra ahi hasta que se construya la vista.
- **`H025` en `search_bar.html`**: djlint reporta un `</div>` huerfano. Es
  **preexistente** (linea 181 en HEAD antes de este cambio). No se corrigio
  porque tocarlo puede desplazar el layout de los 41 listados; conviene
  resolverlo aislado.
- La forma de boton transversal (PR 2).
