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
  - `CAMPOS_OBLIGATORIOS`: 22 campos requeridos, según los casos que QA marcó como
    "campo requerido". Quedan fuera los condicionales (`funcion_pfpi`, `funcion_egp`,
    `funcion_cdi`, `sala_cdi`, `funcion_uaf`, `formacion_academica`,
    `pueblo_originario` y el bloque de discapacidad), además de
    `fecha_actualizacion`: el `clean()` del modelo los limpia cuando no aplican, así
    que exigirlos siempre rompería el guardado.
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
    Se guarda en el alta solo desde un token firmado, de vida corta y ligado al usuario y
    al CDI que contiene la respuesta RENAPER. Incluye únicamente los campos que RENAPER
    completó **con valor** (por-campo, para cubrir datos parciales: un campo que RENAPER
    no trajo nunca no se bloquea).
  - `TrabajadorCDIForm._bloquear_campos_renaper`: en alta y edición esos campos van
    `disabled` (Django ignora el POST y toma el valor inicial firmado o el de la instancia,
    por lo que no se pueden pisar). Ambos muestran el texto de ayuda
    "Dato verificado por RENAPER".
  - `TrabajadorCentroInfanciaCreateView`: crea el token desde la respuesta RENAPER y lo
    verifica antes de construir el form y de persistir `campos_verificados_renaper`; no se
    acepta la procedencia desde campos hidden manipulables.
  - `centrodeinfancia/migrations/0039_...`: `AlterField` por el cambio de `choices`;
    `0040_...`: agrega `campos_verificados_renaper`; `0041_...`: agrega los campos
    funcionales nuevos. Ninguna hace una migración de datos.

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

## Campos nuevos de la spec (agregados 2026-07-20, post-merge de development)

La spec funcional pedía cuatro campos que no existían. Se agregaron (migración 0041,
opciones tomadas de la planilla de requerimientos):

- **`funcion_pfpi`** (TC12) y **`funcion_uaf`** (no reportado por QA): condicionales, se
  muestran/limpian según el subcomponente, igual que `funcion_egp`/`funcion_cdi`. No son
  obligatorios (el modelo los limpia si no aplican).
- **`registro_tipo`** (TC17, "Tipo de registro": Alta/Baja/Edición): **obligatorio**.
- **`fecha_actualizacion`** ("Fecha de actualización del personal", no reportado por QA):
  **optativo** — ni QA ni la spec lo marcan como requerido. Si producto lo quiere
  obligatorio, va a `CAMPOS_OBLIGATORIOS`.

De paso, el `clean()` del modelo ahora también limpia `sala_cdi` cuando el subcomponente
no es CDI (antes solo lo hacía el JS).

## Fuera de alcance de este cambio

- **BAHRA** (TC08, TC09, TC10 y la codificación de TC39/40/41): descartado por PM.
  Nota: TC39 pide además "agregar campo Departamento", que **ya existe**
  (`departamento_contacto`, migración 0034).
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
- **Rollback:** las migraciones del cambio son `0039`, `0040` y `0041`; no revertir
  `0037` ni `0038`, que son ajenas. Revertir `0040` o `0041` después de usar el flujo
  elimina sus columnas y los datos cargados en ellas. En un entorno con datos, respaldar
  antes y preferir un fix hacia adelante salvo que Operaciones apruebe el rollback.
