# 2026-07-21 - CDI: validaciones del alta de niño/a en nómina (QA 3ra tanda)

## Contexto

Tercera tanda de QA, sobre el alta de destinatario/niño en nómina
(`/centrodeinfancia/<pk>/nomina/crear/`, `NominaCentroInfanciaDestinatariosForm`).
Es la más grande de las tres: 162 casos, contra 26 del alta de CDI y 51 del legajo de
trabajador.

Mismo diagnóstico que las dos tandas anteriores: `_apply_required_flags` del form base
marcaba obligatorios solo 5 campos (`estado`, `dni`, `apellido`, `nombre`,
`fecha_nacimiento`) y no había validación de formato, así que el formulario aceptaba
prácticamente cualquier dato (TC_161).

Se reutilizan los validadores de `core/validators.py` creados en la primera tanda. Esta
rama salió de `development` y trae ese archivo por cherry-pick, así que **al mergear ambos
PRs el bloque de validadores puede aparecer duplicado en `core/validators.py`**.

## Cambios aplicados

Todo acotado a `NominaCentroInfanciaDestinatariosForm`. Los otros forms de nómina
(`NominaCentroInfanciaForm`, `...CreateForm`, `...FormEdit`) quedan intactos: QA no los
testeó y se usan en otros flujos (edición ajax, formularios embebidos).

- `CAMPOS_OBLIGATORIOS`: 38 campos requeridos, según los casos que QA marcó como
  "campo obligatorio". `_apply_required_flags` se sobrescribe en este form.
- Validación de formato:
  - **Nombres y apellidos** (niño y ambos responsables): solo letras (`validate_solo_letras`).
  - **DNI** (niño y ambos responsables): 7 u 8 dígitos.
  - **CUIT** (niño y ambos responsables): formato y dígito verificador (`validate_cuit`).
  - **Teléfonos**: entre 6 y 15 dígitos (`validate_telefono_ar`). Ver "Hallazgo".
  - **Fechas** (nacimiento del niño, de ambos responsables, y fecha de registro): no
    futuras y no anteriores a 120 años.
  - **Fechas de vacunación**: tampoco pueden ser futuras (TC_134 y siguientes).
  - **Piso**: solo números. **Altura**: hasta 5 dígitos. **Número de CUD**: solo números.
- Condicionales:
  - `recibe_apoyo_discapacidad` es obligatorio si `tiene_discapacidad == "si"` (TC_102).
  - `numero_cud` es obligatorio si `posee_cud` (TC_104).
- Exclusividad en multiselects:
  - "Ninguno de los anteriores" no se combina con otros grupos de pertenencia.
  - "No sabe" no se combina con otros tipos de discapacidad (TC_101/TS003).
- **Campos ocultos** (`CAMPOS_OCULTOS`, decisión de PM — "ocultemos los campos"):
  "Posee obra social", "Estimación del peso", "Estimación de la talla" y "Orientación
  Ministerio de Salud" se quitan del formulario (del `Meta.fields` y del `__init__`,
  porque el form base recrea `posee_obra_social`). **No se borran del modelo:** los
  datos ya cargados se conservan.
- **Mensaje de municipios** (`destinatarioForm.js`, decisión de PM — "avancemos con el
  mensaje"): cuando el desplegable queda vacío por scope territorial, se muestra
  "No hay municipios disponibles para su jurisdicción" (ver TC_061 más abajo).

## Hallazgo (no reportado por QA)

Los teléfonos de los responsables (`responsable_legal_1_telefono`,
`responsable_legal_2_telefono`) son `PositiveBigIntegerField` en el modelo, no texto.
Eso significa que **no admiten guiones y pierden el cero inicial del código de área**
(`011-4774-2015` se guarda como `1147742015`). Conecta directo con la observación de QA
de que "no está diferenciado el código de área" (TC_034, crítico). No se tocó: arreglarlo
implica cambiar el tipo de campo en el modelo y migrar datos. Queda junto a la
antropometría, que el PM está averiguando.

## Verificado como NO-bug

**TC_061 ("Municipio funciona solo para Buenos Aires", crítico):** no es un bug. El
endpoint `core.views.load_municipios` filtra los municipios por el **scope territorial del
usuario**; si la provincia elegida no está en su alcance devuelve lista vacía. Es control
de acceso funcionando. Se descartaron las otras causas posibles: la lógica del encadenado
es genérica, los datos están completos (24 provincias, 2264 municipios — Córdoba tiene más
que Buenos Aires) y el AJAX está conectado en `destinatarioForm.js`.

El desplegable quedaba vacío sin explicar por qué; se agregó el aviso (ver "Cambios
aplicados"). Para retestear municipios de otras provincias hace falta un usuario con
alcance nacional.

## Decisiones de producto (PM, 2026-07-21)

- **BAHRA**: descartado definitivamente ("rompe con todo el sistema nuestro"). Nota: la
  *bajada de datos* territoriales desde georef/IGN (PR #2103, ya en development) es otra
  cosa distinta de la codificación BAHRA que se rechazó; completa municipios/localidades
  faltantes sin cambiar la estructura.
- **Campos a eliminar** (TC_112, TC_119, TC_120, TC_121): se **ocultan** (no se borran),
  ver "Cambios aplicados".
- **Teléfonos** (TC_034, TC_048): rango único de 6 a 15 dígitos para todo el sistema, para
  no dejar ninguno afuera. Cambió `validate_telefono_ar` de 6-11 a 6-15.
- **CUIT vinculado al DNI** (TC_022, TC_033, TC_047): descartado ("no le demos bola"). Se
  valida solo formato y dígito verificador.
- **Mensaje de municipios** (TC_061): se agrega el aviso.

## Pendiente de definición de producto

- **Antropometría** (TC_113 a TC_116): QA pide que talla, peso, longitud y perímetro
  cefálico pasen de desplegable a ingreso manual, con validación de rango. Es cambio de
  tipo de campo + migración de datos, y faltan los rangos válidos. El PM lo está averiguando
  (junto con el teléfono numérico de los responsables, ver "Hallazgo").
- **Dosis de vacunación obligatorias** (TC_133 y siguientes): QA las marca como requeridas
  (severidad media). Hacer obligatorias las 14 vacunas es una decisión de UX que conviene
  confirmar; por ahora solo se valida que la fecha no sea futura.

## Contradicciones de la planilla (a corregir por QA)

- **TC_058 (Departamento del domicilio):** el resultado esperado dice "debe permitir vacío"
  pero la observación dice "campo obligatorio".
- **TC_129 a TC_132 (asignaciones ANSES):** el esperado dice "debe permitir vacío" pero los
  casos figuran como rechazados.

## Validación

- `pytest centrodeinfancia/` → **341 passed**.
- `centrodeinfancia/tests/test_destinatario_form.py`: 35 funciones de test (más las
  parametrizadas), con una clase nueva (`TestValidacionesQA`) que cubre cada caso
  implementado de la planilla, incluidos teléfono y campos ocultos.
- Se actualizaron los tests de nómina que posteaban payloads mínimos, ahora rechazados por
  las validaciones. Se centralizó el payload completo en `datos_validos(centro, ...)`,
  reutilizado por `test_destinatario_views.py`, `test_nomina_edit_view.py` y
  `test_nomina_integridad.py`.
- `black`, `pylint` (10.00/10) OK.

## Riesgos y rollback

- Igual que en las tandas anteriores: los legajos ya cargados que no tengan todos los
  campos obligatorios **quedan ineditables** hasta completarlos. Aplica el criterio del PM
  (los datos actuales son de prueba y se borran antes de producción).
- El cambio está acotado al form de destinatarios; los otros forms de nómina no se tocaron.
- **Rollback:** revertir el commit. No hay migraciones ni cambios de datos.
