# 2026-07-16 - CDI: validaciones del legajo de Trabajador (bugs QA TC06-TC51)

## Contexto

Segunda tanda de QA, sobre el legajo de Trabajador (`/centrodeinfancia/<pk>/trabajadores/
<id>/editar/`). Mismo diagnóstico que el alta de CDI: todos los campos del modelo
`Trabajador` son `blank=True, null=True` y no había validación de formato, así que el
formulario aceptaba prácticamente cualquier cosa (TC51).

Se aplica el mismo criterio que en `2026-07-14-cdi-validaciones-alta.md`, reutilizando los
validadores de `core/validators.py` que se crearon ahí.

## Cambios aplicados

- `centrodeinfancia/forms.py` (`TrabajadorCDIForm`):
  - `CAMPOS_OBLIGATORIOS`: 21 campos requeridos, según los casos que QA marcó como
    "campo requerido". Quedan fuera los condicionales (`funcion_egp`, `funcion_cdi`,
    `sala_cdi`, `formacion_academica`, `pueblo_originario` y el bloque de discapacidad):
    el `clean()` del modelo los limpia cuando no aplican, así que exigirlos siempre
    rompería el guardado.
  - Validación de nombre y apellido (solo letras), teléfono, CUIT (con dígito
    verificador), DNI (7-8 dígitos), fecha de nacimiento y número de CUD (solo dígitos).
  - `_configurar_pais_nacionalidad()`: país de nacimiento y nacionalidad pasan de texto
    libre a desplegable, reutilizando los catálogos `NominaPais` / `NominaNacionalidad`
    que ya existían para el legajo de Nómina (199 países, 196 nacionalidades).
  - `_aplicar_campo_cuit()`: **bug que QA no reportó** — el campo tenía `max_length=11`,
    así que `MaxLengthValidator` rechazaba cualquier CUIT con guiones (13 caracteres)
    antes de poder normalizarlo. Era imposible cargar un CUIT con el formato del
    placeholder. Mismo tratamiento que en `CentroDeInfanciaForm`.
- `centrodeinfancia/models.py`: se elimina la opción "No corresponde" de `funcion_egp`
  (TC13) y de `es_interprete` (TC45). La spec funcional no las incluye.
- **TC43** (bug que confirmó QA en el retest): `grupo_pertenencia` es multiselect y dejaba
  combinar "Ninguno de los anteriores" con otras opciones. Se agrega validación de
  exclusividad en `clean_grupo_pertenencia`.
- **TC49** (bug que confirmó QA en el retest): el bloque "¿Tiene CUD?" / "Número de CUD"
  estaba fuera del `div#bloque-discapacidad`, así que se mostraba siempre. Se mueve dentro
  (`trabajador_form.html`) y el `clean()` del modelo ahora limpia `tiene_cud` cuando
  `tiene_discapacidad != "si"`.
- **RENAPER (TC22, TC20):** los datos que RENAPER precarga en el alta quedan bloqueados en
  la edición (decisión de PM: no se corrigen datos verificados por el organismo). Detalle:
  - Campo nuevo `Trabajador.campos_verificados_renaper` (JSON, lista de nombres de campo).
    Se guarda en el alta solo cuando el submit trae `origen_dato=renaper`; contiene los
    campos que RENAPER completó **con valor** (por-campo, para cubrir datos parciales:
    un campo que RENAPER no trajo nunca se bloquea).
  - `TrabajadorCDIForm._bloquear_campos_renaper`: en **edición** esos campos van `disabled`
    (robusto: en un ModelForm Django ignora el POST y toma el valor de la instancia, no se
    puede pisar). En el **alta** van `readonly` (bloqueo blando: el dato recién se trajo y
    todavía no hay instancia que respalde el valor). Ambos muestran el texto de ayuda
    "Dato verificado por RENAPER".
  - `TrabajadorCentroInfanciaCreateView`: computa la lista desde la respuesta de RENAPER,
    la transporta en un hidden `campos_renaper` y la persiste en `form_valid`, filtrando
    contra `RENAPER_FIELDS` (no se persiste lo que venga arbitrariamente por POST).
- `centrodeinfancia/migrations/0037_...`: `AlterField` por el cambio de `choices`.
  `0038_...`: agrega `campos_verificados_renaper`. Ninguna toca datos.

## Criterios adoptados (PM, 2026-07-16)

- **Edad**: se rechaza fecha futura y se acota el máximo en 100 años. El mínimo pasó a 0
  ("la mayoría van a ser nenes", punto 4). **Nota**: hay una tensión entre respuestas —
  el punto 4 pide rango 0-100, pero en el punto 3 el equipo dijo "sin restricción de edad
  si se carga manualmente". Se tomó 0-100 (respuesta directa a la pregunta) + rechazo de
  fecha futura (lo único en que coinciden las dos respuestas y el objetivo real de
  TC20/TS03). Si se decide sacar el tope, es una constante (`EDAD_MAXIMA`).
- **DNI**: se valida 7-8 dígitos (TC22/TS02 reporta que acepta 10).

## Verificado en el retest de QA

La lógica condicional ya funcionaba en la mayoría de los casos (`trabajadorForm.js` +
`clean()` del modelo): **TC15** (Sala CDI), **TC47/48** (tipo y apoyo de discapacidad),
**TC50** (Número de CUD). QA lo confirmó.

Dos que el retest sí marcó como reales, y se corrigieron (ver "Cambios aplicados"):
**TC43** ("Ninguno" combinable con otros grupos) y **TC49** ("¿Tiene CUD?" no era
condicional).

## Pendiente / definido en esta iteración

- **Sección "Institución" (TC06-TC10):** ya existía. El template renderiza los datos del
  CDI (jurisdicción, departamento, municipio, localidad, nombre y código) como tarjeta de
  solo lectura al inicio del form. Lo único que faltaba era la codificación BAHRA, que el
  PM descartó. No requiere trabajo.
- **RENAPER, política de corrección:** se implementó bloqueo puro (`disabled`), sin escape
  para corregir un dato de RENAPER que esté mal. Si en algún momento hace falta permitir la
  corrección (con justificación), es una feature aparte.

## Fuera de alcance de este cambio

- **BAHRA** (TC08, TC09, TC10 y la codificación de TC39/40/41): descartado por PM.
  Nota: TC39 pide además "agregar campo Departamento", que **ya existe**
  (`departamento_contacto`, migración 0034).
- **Campos que no existen y la spec pide**: `funcion_pfpi` (TC12), `registro_tipo` (TC17),
  y dos que QA no reportó: **`funcion_uaf`** y **`fecha_actualizacion`**. `Subcomponente`
  ofrece PFPI y UAF pero no hay campo de función para ninguno de los dos.
## Validación

- `pytest centrodeinfancia/` → 333 passed.
- `centrodeinfancia/tests/test_trabajador_form.py` (nuevo) + `test_trabajadores_views.py`:
  63 tests, cubren obligatorios, formatos, TC43, TC49 y el flujo RENAPER (alta persiste la
  lista; edición bloquea e ignora intentos de sobrescribir).
- `tests/` → 2035 passed, 4 failed. **Las 4 fallas son preexistentes** (scripts de deploy,
  `set: pipefail`), llegaron con el merge de `development` `2496e804a` y se reproducen sin
  estos cambios.
- `black`, `pylint` OK.

## Riesgos y rollback

- Igual que en el alta de CDI: los legajos de Trabajador ya cargados que no tengan todos
  los campos obligatorios **quedan ineditables** hasta completarlos. Aplica el mismo
  criterio del PM: son datos de prueba y se van a borrar.
- Quitar "No corresponde" de `funcion_egp` y `es_interprete` deja inválidos los registros
  que hoy tengan ese valor. Mismo criterio.
- **Rollback:** revertir el commit y la migración 0037 (`AlterField` de choices, sin
  cambio de esquema).
