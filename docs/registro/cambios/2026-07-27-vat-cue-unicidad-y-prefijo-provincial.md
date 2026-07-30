# VAT/INET: validaciones de unicidad y prefijo provincial para el CUE (#2146)

## Contexto

El CUE del centro es `Centro.codigo`. En el formulario de alta/edición
(`CentroAltaForm`, usado por `CentroCreateView` **y** `CentroUpdateView`) sólo se
validaba que fuera numérico de 9 dígitos (`clean_codigo` →
`_clean_numeric_text`).

Dos observaciones sobre el estado previo:

- **La unicidad ya existía a nivel modelo** (`Centro.codigo` es `unique=True`),
  pero el usuario veía el mensaje default de Django ("Centro con este Codigo ya
  existe."), no uno del dominio.
- **Y estaba incompleta.** `Centro` usa `SoftDeleteModelMixin`, cuyo
  `objects` (que excluye borrados) es el `_default_manager`. El
  `validate_unique` de Django consulta ese manager, así que **no veía centros
  dados de baja**, mientras el índice único de la DB sí los tiene. Reusar el CUE
  de un centro soft-deleted terminaba en `IntegrityError` → 500, no en un error
  de formulario.

## Cambio

Todo en `VAT/forms.py`.

### Mapeo de prefijos

`CUE_PREFIJOS_POR_PROVINCIA`: nombre de provincia → prefijo de 2 dígitos. Son los
códigos INDEC de jurisdicción. Las claves son los nombres canónicos de
`core/fixtures/localidad_municipio_provincia.json`.

`core.Provincia` **no tiene campo de código** (sólo `nombre`), por eso el mapeo es
por nombre. La solución durable sería un `codigo_indec` en `core.Provincia`, pero
es un cambio de `core/` que impacta otros módulos (ver
`docs/ia/MODULAR_BOUNDARIES.md`); quedó fuera de alcance.

### Validaciones

- `_validar_cue_duplicado(codigo, instance)` — consulta **`Centro.all_objects`**
  (incluye borrados, ver arriba) y excluye `instance.pk` para que la edición sin
  cambiar el CUE propio siga funcionando.
- `_validar_prefijo_cue(codigo, provincia)` — compara `codigo[:2]` contra el
  prefijo de la provincia.

### Cableado

- Unicidad en `clean_codigo()` (base `CentroForm` y `CentroAltaForm`). Va ahí, y
  no en `clean()`, por dos razones: el error queda sobre el campo, y al fallar
  `clean_codigo` Django excluye `codigo` de su propio `validate_unique`, así que
  **no se muestran dos mensajes** por lo mismo (hay test que lo cubre).
- Prefijo en `CentroForm.clean()`, vía `add_error("codigo", ...)`: es cross-field
  (necesita `provincia`, que se limpia después de `codigo`). `CentroAltaForm` no
  redefine `clean()`, así que lo hereda.
- `CentroAltaForm.clean_codigo` mantiene la validación numérica primero.

El template no se tocó: `{{ form.codigo|as_crispy_field }}` ya renderiza los
errores del campo debajo.

### Mensajes

| Caso | Mensaje |
|---|---|
| Duplicado con centro activo | `El CUE ingresado ya se encuentra registrado en otro centro.` |
| Duplicado con centro dado de baja | `El CUE ingresado ya se encuentra registrado en otro centro dado de baja.` |
| Prefijo inválido | `Los primeros 2 dígitos del CUE no corresponden a la provincia seleccionada.` |

Los dos primeros salen de dividir el caso único del ticket: sin la variante de
"dado de baja", el usuario recibiría un mensaje que le dice que busque un centro
que no puede encontrar en el listado.

## Desvío respecto del requerimiento: La Pampa

**La tabla de equivalencias del ticket omite La Pampa.** Lista 23 de las 24
jurisdicciones y salta de `38` (Jujuy) a `46` (La Rioja), sin el `42` que le
corresponde por INDEC — el mismo esquema que siguen todas las demás filas.

La Pampa existe en el sistema (`pk 11` del fixture canónico), así que
implementar la tabla literal habría dejado **todos los centros de La Pampa
imposibles de guardar**. Se incluyó `"La Pampa": "42"`.

Hay un test (`test_cue_prefijos_cubren_todas_las_provincias_del_sistema`) que
carga el fixture y falla si alguna provincia del sistema queda sin prefijo: es la
red que hubiera cazado esta omisión.

**Pendiente de confirmación funcional**: si La Pampa realmente no debe tener
CFP, hay que quitarla del mapeo y el test lo va a marcar.

## Otras decisiones

**Provincia fuera del mapeo → no se valida el prefijo.** Si el nombre de la
provincia no está en el mapeo (nomenclatura no canónica), se omite la validación
en lugar de bloquear. Es preferible no rechazar un alta legítima por un desajuste
de nombres. Contrapartida: si alguien renombra una provincia, el prefijo deja de
validarse en silencio — otro argumento para el `codigo_indec` en `core`.

**Alcance: sólo el formulario.** Es lo que pide el ticket. Quedan **sin cubrir**
otras dos vías de alta/edición de centro:

- `CentroViewSet` / `CentroSerializer` (API con API Key) — es un ModelViewSet
  completo.
- `manage.py import_vat_centros_excel` (alta masiva).

Moverlo a `Centro.clean()` cubriría el form pero **no** la API (DRF no llama
`full_clean`), así que no resolvía el problema por sí solo. Si se quiere paridad,
hay que replicar las validaciones en el serializer.

## Datos de test alineados

`_build_centro_payload` usaba `codigo="500144900"` (prefijo `50` = Mendoza) con la
fixture `vat_geo_data`, que crea provincia "Buenos Aires" (`06`). Los pares
codigo/provincia de los tests eran incoherentes y ahora la validación los
rechaza. Se hizo:

- `_build_centro_payload` deriva el prefijo de la provincia recibida.
- Los 33 literales `"50XXXXXXX"` de `VAT/tests.py` pasaron a `"06XXXXXXX"`
  (todos eran valores de CUE: `codigo`, `valor_identificador` y asserts; ninguno
  era teléfono ni DNI).

## Validación

- 11 tests nuevos en `VAT/tests.py`: duplicado en alta, duplicado en edición,
  edición sin cambiar el CUE propio, prefijo inválido, prefijo correcto de otra
  provincia, La Pampa con `42`, provincia fuera del mapeo, validación numérica
  intacta, duplicado contra centro dado de baja (el caso del `IntegrityError`),
  no duplicación del mensaje default de Django, y cobertura de las 24 provincias.
- Son tests de formulario (no renderizan template), así que **corren en el venv
  local**: los 11 pasan.
- Suite VAT completa: 68F/152P antes → 68F/163P después. **Cero regresiones**
  (las 68 fallas son las preexistentes por el venv con Python 3.14 + Django 4.2,
  documentado en `2026-07-27-vat-comision-resultados-acta.md`).
- `black` y `manage.py check` limpios. `pylint VAT/forms.py`: 10.00/10.
