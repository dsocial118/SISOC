# VAT/INET: estado visual del checkbox de lista de espera (#2006)

## Hallazgo previo: el ticket pide dos cosas y una ya estaba

El requerimiento planteaba dos problemas. Al revisar el codigo, sólo uno estaba
abierto.

### 1. "Falta configuracion de limite" — ya implementado

`ComisionCurso.cupo_lista_espera` existe desde la migracion
`0049_comisioncurso_cupo_lista_espera` (05-jun-2026, presente en `development` y
en `main`). La cadena completa ya estaba:

- Modelo: `cupo_lista_espera` + `ComisionCurso.clean()` que exige el cupo cuando
  `acepta_lista_espera` esta activo y lo limpia cuando no.
- Form: `ComisionCursoForm.cupo_lista_espera` en `Meta.fields`.
- Modal (`centro_cursos_panel.html`): el campo con
  `[data-waitlist-capacity-wrapper]` y `d-none` inicial.
- Trigger del boton Editar: `data-cupo-lista-espera`.
- JS (`centro_detail.html` → `syncWaitlistCapacity`): muestra/oculta el campo y
  lo marca `required` segun el toggle.
- Ya existia un test: `test_cursos_panel_boton_editar_emite_estado_lista_espera`.

**No se agrego funcionalidad para este punto.** El campo aparece al tildar el
checkbox, que es el comportamiento pedido. Es plausible que el ticket se haya
escrito antes de que `0049` estuviera desplegado, o que no se haya notado que el
campo aparece recien al activar el toggle.

### 2. "El boton no se muestra tildado" — bug real, corregido

**Causa raiz.** Los modales de esta pagina llevan la clase `vat-ui-modal`, pero
las reglas que estilan checkboxes en `static/custom/css/vat_design.css` estaban
scopeadas a `.vat-ui`:

```css
.vat-ui input[type="checkbox"] { accent-color: var(--cteal); }
.vat-ui .form-check-input:checked { background-color: var(--cteal); ... }
```

`centro_detail.html` usa `.sisoc-centro-page` como raiz, **no** `.vat-ui` (se
verifico: la clase no aparece en el template). El CSS se carga, pero esos dos
selectores nunca matchean. Resultado: sobre el fondo navy del modal el checkbox
queda con el estilo de Bootstrap — fondo blanco, borde gris claro — y su estado
marcado es practicamente ilegible. Exactamente lo reportado.

El modal equivalente de `comision_detail.html` no tenia el problema porque usa la
clase `ci-modal`, que si define `accent-color` en su propio `<style>`.

## Cambio

### `static/custom/css/vat_design.css`

- Los selectores de `input[type=checkbox]` / `input[type=radio]` y de
  `.form-check-input:checked` pasan a cubrir **tambien** `.vat-ui-modal`, que es
  la clase que estos modales si tienen.
- Se agrega estilo base de `.vat-ui-modal .form-check-input` para superficie
  oscura: fondo translucido, borde claro, 1.15em (antes heredaba el blanco de
  Bootstrap) y un `:focus` coherente con el teal del modal.

El fix es deliberadamente en el scope del modal y no agregando `.vat-ui` a la
raiz de la pagina: `centro_detail.html` tiene su propio sistema visual
(`.sisoc-centro-page`) y meterle `.vat-ui` arrastraria todo el design system
sobre una pagina ya estilada, con riesgo de regresiones visuales amplias. Alcanza
a todos los `.vat-ui-modal` de VAT, que es justamente para lo que existe esa
clase.

### Asterisco de requerido coherente (`centro_cursos_panel.html` + `centro_detail.html`)

`cupo_lista_espera` es `required=False` en el form, asi que el label no mostraba
`*` — pero el JS lo marca `required` al tildar el toggle y `ComisionCurso.clean()`
lo exige. El usuario veia un campo sin asterisco que igual bloqueaba el guardado.

Se agrego `[data-waitlist-required-mark]` en el label, que `syncWaitlistCapacity`
enciende y apaga junto con la visibilidad del campo. Va en la linea de lo que
pide el ticket ("reflejar visualmente su estado de forma clara") y son tres
lineas.

## Validacion

- 5 tests nuevos en `VAT/tests.py`: el trigger expone `data-cupo-lista-espera`
  con el valor configurado; con la espera apagada el atributo viaja vacio (no
  `"None"`); el modal renderiza el campo con su wrapper y la marca de requerido;
  y dos de la regla de negocio del form (activar la espera obliga a dar cupo /
  desactivarla lo limpia).
- Usan `RequestFactory` sobre `CentroCursosPanelView` en vez del test client, asi
  que **los 5 corren en el venv local** pese al problema de Python 3.14 +
  Django 4.2 documentado en `2026-07-27-vat-comision-resultados-acta.md`.
- Suite VAT completa: 68F/175P antes → 68F/180P despues. **Cero regresiones.**
- `black` y `manage.py check` limpios. `djlint` sobre el partial: 8 hunks antes y
  8 despues, sin violaciones nuevas.

### Pendiente de verificacion visual

El fix de CSS **no es testeable automaticamente**. Hay que confirmarlo en el
navegador: abrir el detalle de un centro → solapa Cursos → Editar en una comision
con lista de espera activa, y comprobar que el checkbox se ve tildado en teal y
que aparece "Cupo Lista de Espera" con el valor cargado. Si el entorno sirve
static con cache, puede necesitar `collectstatic` y/o hard-refresh.
