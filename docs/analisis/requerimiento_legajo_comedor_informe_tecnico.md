# Requerimiento funcional: Legajo de comedor e Informe Técnico de Admisiones

**Fecha:** 31 de agosto de 2026
**Estado:** Requerimiento funcional (sin implementación)
**Alcance del documento:** define 7 requerimientos sobre el legajo de comedor (app `comedores`) y el formulario de Informe Técnico de Admisiones (app `admisiones`). No es un diseño técnico ni una guía de implementación; cada sección cita evidencia del estado actual del código (rama `development`) como punto de partida.

---

## 1. Contexto

Los 7 puntos de este requerimiento surgen de uso funcional del módulo de Admisiones, en particular del formulario de Informe Técnico (`admisiones/forms/admisiones_forms.py`, `admisiones/models/admisiones.py`, modelo `InformeTecnico`) y su relación con el legajo de comedor (`comedores/views/comedor.py:1208`, `ComedorDetailView`).

Antes de definir cada punto se relevó el estado actual del código como evidencia de partida; varios de los puntos pedidos ya tienen una implementación parcial o total, y el documento lo señala explícitamente en cada caso para no duplicar trabajo.

---

## 2. Objetivo

Definir, para cada uno de los 7 puntos pedidos:

1. Qué existe hoy (evidencia).
2. Qué cambia funcionalmente.
3. Reglas de negocio específicas, según lo definido con el usuario funcional.
4. Puntos abiertos para definición técnica, cuando corresponda.

---

## 3. Requerimiento 1 — Sección "Responsable de la Tarjeta" en el legajo (Alimentar Comunidad)

### 3.1 Estado actual

Hoy **no existe** una sección de "Responsable de la Tarjeta" en el legajo de comedor (`Comedor`, `comedores/models.py`). Sí existe un concepto equivalente, pero viven como campos sueltos del `InformeTecnico` de Admisiones, cargados **por informe** (es decir, se piden de nuevo en cada Informe Técnico), sin edición desde el legajo — `admisiones/models/admisiones.py:538-559`:

- `responsable_tarjeta_nombre` (nombre completo, un solo campo)
- `responsable_tarjeta_cuit` ("CUIL/CUIT")
- `responsable_tarjeta_dni`
- `responsable_tarjeta_domicilio`
- `responsable_tarjeta_localidad` (texto libre)
- `responsable_tarjeta_provincia` (texto libre)
- `responsable_tarjeta_telefono`
- `responsable_tarjeta_mail`

No existe campo "apellido" separado: el patrón actual usa "Nombre del Responsable de la Tarjeta" como un único campo de texto libre.

El legajo de comedor sí tiene ya un concepto de "Responsable" distinto (`Referente`, `comedores/models.py:37-98`, FK `Comedor.referente`) y un acordeón "Responsables" en el detalle (`comedor_detail.html:321`) que muestra responsables de la **Organización** (firmantes, avales) — ninguno de los dos es el "Responsable de la Tarjeta" que pide este punto.

"Alimentar Comunidad" no es un modelo propio: es un valor del catálogo `Programas` (`comedores/models.py:101-118`), vinculado por `Comedor.programa` (FK). La comparación por nombre normalizado ya existe en `comedores/services/capacitaciones_certificados_service.py:20-25` (`is_alimentar_comunidad_program`), aunque la misma lógica está duplicada en `comedores/api_serializers.py:1218-1223` y `comedores/utils.py:34-49` — sin un único punto de verdad (Enum/choice). Vale la pena unificarlo al implementar, pero no es parte de este requerimiento funcional.

El rol "técnico" mencionado por el usuario corresponde al grupo `"Tecnico Comedor"` (`core/constants.py:19`, `core.constants.Roles.TECNICO_COMEDOR`), ya usado como grupo de permisos en `core/permissions/registry.py:62` y `users/bootstrap/groups_seed.py:18,1015`.

### 3.2 Requerimiento

Agregar al legajo de comedor una sección **"Responsable de la Tarjeta"**, editable solo por usuarios del grupo `Tecnico Comedor`, con los campos:

- Nombre y apellido (un solo campo combinado, igual al patrón actual)
- Mail
- DNI
- CUIL/CUIT
- Domicilio
- Localidad
- Provincia
- Teléfono

Visible/aplicable únicamente para comedores del programa **Alimentar Comunidad** (mismo criterio que `is_alimentar_comunidad_program`).

**Autocompletado hacia el Informe Técnico:** estos mismos datos se piden hoy de nuevo en cada Informe Técnico, como los campos `responsable_tarjeta_nombre`, `responsable_tarjeta_cuit`, `responsable_tarjeta_dni`, `responsable_tarjeta_domicilio`, `responsable_tarjeta_localidad`, `responsable_tarjeta_provincia`, `responsable_tarjeta_telefono` y `responsable_tarjeta_mail` (`admisiones/models/admisiones.py:538-559`). Al crear/abrir un Informe Técnico de un comedor de Alimentar Comunidad, esos campos deben venir **precargados** con el valor cargado en la nueva sección del legajo, en lugar de quedar vacíos a la espera de que el técnico los tipee de nuevo.

### 3.3 Reglas de negocio (definidas con el usuario)

- **El legajo no es la fuente única de verdad.** El Informe Técnico sigue permitiendo editar estos mismos datos por informe. La sección del legajo solo **prellena el valor inicial** de los campos equivalentes (`responsable_tarjeta_*`) al crear/abrir un Informe Técnico; el técnico puede modificarlos en ese informe puntual sin que eso altere el dato guardado en el legajo. Puede haber divergencia histórica entre lo que dice el legajo hoy y lo que quedó firmado en un informe ya cerrado — es aceptado.
- El campo nombre se mantiene como **"Nombre y apellido"** combinado en un único campo de texto, sin separar en dos campos (consistente con `responsable_tarjeta_nombre` actual).
- Localidad y Provincia de esta sección deben quedar como desplegable, no texto libre (ver Requerimiento 2 — mismo criterio aplica acá).

### 3.4 Puntos abiertos para definición técnica

- Diseño de datos concreto: campos directos en `Comedor`, o modelo `ResponsableTarjeta` (OneToOne o FK) — a definir por el desarrollador. Dado que ya existe el precedente `Referente` (modelo aparte, FK desde `Comedor`), es razonable seguir ese mismo patrón.
- Si la sección debe ocultarse por completo del legajo cuando el comedor no es de "Alimentar Comunidad", o mostrarse deshabilitada.

---

## 4. Requerimiento 2 — Provincia y Localidad como desplegables en el Informe Técnico

### 4.1 Estado actual

Todos los campos de provincia/localidad del `InformeTecnico` son `CharField` de texto libre, sin relación a ningún catálogo — `admisiones/models/admisiones.py`:

- `localidad_organizacion` / `provincia_organizacion` (líneas 489-497)
- `localidad_espacio` / `provincia_espacio` (líneas 530-536)
- `provincia_poblacion_destinataria` (líneas 570-572; no existe `localidad_poblacion_destinataria`)
- `responsable_tarjeta_localidad` / `responsable_tarjeta_provincia` (líneas 550-555)

Se renderizan como texto libre en `admisiones/templates/admisiones/informe_tecnico_form.html:141-148,202-209`.

El sistema ya tiene un catálogo geográfico jerárquico ampliamente usado y poblado: `core.models.Provincia` (`core/models.py:127-140`) → `core.models.Municipio` (línea 184-201) → `core.models.Localidad` (línea 205-222). `Comedor` ya usa estos catálogos como FK real (`comedores/models.py:414` `provincia`, `:417-419` `localidad`) — de hecho, `admisiones_forms.py:442` ya toma `comedor.localidad` / `comedor.provincia` (objetos FK) para prellenar `localidad_espacio` / `provincia_espacio`, aunque esos campos destino siguen siendo texto libre.

Además ya existe un componente reutilizable de selects en cascada Provincia → Municipio → Localidad, con caché y Select2 opcional: `static/custom/js/ubicacionSelects.js`, usado hoy en `comedor_form.html`, `ciudadano_form.html`, `organizacion_form.html`, formularios de VAT, Centro de Infancia y Centro de Familia, entre otros.

### 4.2 Requerimiento

Convertir todos los campos de provincia/localidad del Informe Técnico listados arriba de `CharField` a desplegables sobre los catálogos existentes (`core.models.Provincia` / `core.models.Localidad`), reutilizando el mismo patrón de selects en cascada ya usado en el resto del sistema (`ubicacionSelects.js`), en vez de crear un mecanismo nuevo.

### 4.3 Puntos abiertos para definición técnica

- Confirmar si conviene exponer también el nivel intermedio "Municipio" (como en `Comedor`) o si Localidad puede filtrarse directamente por Provincia ocultando Municipio en la UI del Informe Técnico — a resolver siguiendo el patrón ya usado en `comedor_form.html`.
- Migración de datos existentes: los `InformeTecnico` ya guardados tienen provincia/localidad como texto libre; no hay garantía de que ese texto matchee exactamente contra `Provincia.nombre` / `Localidad.nombre`. Definir si se migran (con matcheo aproximado) o si el cambio aplica solo hacia adelante, dejando el dato histórico como estaba.

---

## 5. Requerimiento 3 — Autocompletar el cuadro de prestaciones del último convenio

### 5.1 Estado actual

El Informe Técnico de **renovación** tiene un bloque de 28 campos "aprobadas en el último convenio" (`aprobadas_ultimo_convenio_<tipo>_<día>`, 4 tipos de prestación × 7 días — `admisiones/models/admisiones.py:778-862`), que hoy se cargan **manualmente**: se confirmó (`admisiones/forms/admisiones_forms.py:408-428`) que estos campos solo se vuelven obligatorios cuando `require_full` y `tipo == "renovacion"`, pero **no tienen ningún `.initial` asignado** — no se autocompletan desde ningún lado hoy.

Separado de esto, el legajo de comedor **sí** tiene ya resuelto el problema de "cuál es el cuadro de prestaciones vigente, considerando que un informe complementario puede haberlo modificado" — mecanismo ya implementado y usado tanto en la vista web como en la API PWA:

- `comedores/services/comedor_service/impl.py:972-1011` — `aplicar_complementario_validado(informe_tecnico)`: busca el `InformeComplementario` con `estado="validado"` asociado a ese informe y sobrescribe en memoria los campos que ese complementario modificó (vía `InformeComplementarioCampos`, par campo/valor).
- `comedores/services/comedor_service/impl.py:1014-1040` — `get_informe_tecnico_finalizado_efectivo(admision)`: retorna el `InformeTecnico` finalizado de esa admisión, con el complementario validado ya aplicado si existe.
- Consumido en el legajo: `comedores/views/comedor.py:1480-1483` → acordeón "Prestaciones" / "Prestaciones mensuales" en `comedor_detail.html:381,422`.

Es decir: **el mecanismo para obtener "el cuadro de prestaciones correcto, contemplando complementarios" ya existe**, pero hoy solo se usa para mostrarlo en el legajo — no está conectado al formulario de Informe Técnico para autocompletar `aprobadas_ultimo_convenio_*`.

**La visualización de este cuadro dentro del Informe Técnico ya existe** — no es parte de lo que falta. Los 28 campos `aprobadas_ultimo_convenio_*` ya se renderizan hoy en:

- El formulario web: `admisiones/templates/admisiones/informe_tecnico_form.html`.
- El PDF de previsualización de renovación: `renovacion_pdf_informe_tecnico_base.html` / `renovacion_pdf_informe_tecnico_juridico.html`.
- El DOCX de renovación (base y jurídico): `renovacion_docx_informe_tecnico_base.docx` / `renovacion_docx_informe_tecnico_juridico.docx` (placeholders `aprobadas_ultimo_convenio_*` confirmados dentro de cada `.docx`).

Es decir: el bloque ya se pide, ya se muestra y ya se imprime — lo único que falta es que su **valor inicial** venga autocompletado en vez de cargarse a mano.

### 5.2 Requerimiento

Al abrir/crear un Informe Técnico de **renovación**, el bloque "aprobadas en el último convenio" debe autocompletarse a partir del cuadro de prestaciones **efectivo** (considerando informes complementarios validados) de la admisión anterior del mismo comedor, reutilizando `get_informe_tecnico_finalizado_efectivo` (o su lógica equivalente) en lugar de construir un mecanismo nuevo.

### 5.3 Reglas de negocio

- Debe tomar el cuadro **`aprobadas_*`** (no `solicitudes_*`) del informe técnico finalizado efectivo de la admisión anterior, y prellenar los 28 campos `aprobadas_ultimo_convenio_*` correspondientes.
- Si hubo un Informe Complementario validado que modificó prestaciones sobre esa admisión anterior, el autocompletado debe reflejar el valor **ya corregido** por el complementario, no el original del informe técnico base — este es el escenario que el usuario pidió cuidar explícitamente, y el mecanismo (`aplicar_complementario_validado`) ya está resuelto en el código existente para ese propósito.
- Como en el resto de los campos autocompletados (expediente/convenio de incorporación, antecedentes — ver Requerimientos 5 y 6), sigue siendo editable: el autocompletado da el valor inicial, no bloquea el campo.

### 5.4 Puntos abiertos para definición técnica

- Definir cuál es "la última admisión" de referencia cuando no hay un campo explícito que vincule una renovación con la admisión que renueva (no existe hoy un FK `admision_anterior` en `Admision`, `admisiones/models/admisiones.py:36+`). El patrón ya usado para antecedentes y expediente/convenio de incorporación (`admisiones_forms.py:100-166`) resuelve esto ordenando por `creado`/`pk` y excluyendo la admisión actual; se recomienda seguir el mismo criterio acá (comedor igual, la más reciente antes de la actual).

---

## 6. Requerimiento 4 — Agregar criterio "D. Equivalencias"

### 6.1 Estado actual

`InformeTecnico.CRITERIOS` tiene exactamente 3 opciones (`admisiones/models/admisiones.py:451-456`):

```python
CRITERIOS = [
    ("A", "A - Coincidencia"),
    ("B", "B - Solicitud Menor"),
    ("C", "C - Solicitud Mayor"),
]
```

Campo `criterio_seleccionado` (línea 611-617), usado en `admisiones_forms.py:97-98` (obligatorio según `require_full` para informes de renovación tipo "2233") y en `_guardar_antecedentes_informe_2233` (líneas 169-171) para completar el texto de `conclusiones` a partir del diccionario `dict(InformeTecnico.CRITERIOS)`.

### 6.2 Requerimiento

Agregar una cuarta opción:

```python
("D", "D - Equivalencias"),
```

Aplica a **todos los casos de renovación** que usan este campo (no es exclusivo de un sub-flujo).

### 6.3 Puntos abiertos para definición técnica

- Confirmar el texto exacto de la etiqueta ("D - Equivalencias" vs. otra redacción) con el área funcional antes de publicarlo en producción, dado que `conclusiones` se arma con este texto y probablemente impacta el DOCX/PDF generado.
- Verificar si el template DOCX/PDF de informe técnico de renovación tiene texto fijo que enumera "3 criterios" y necesita actualizarse para mencionar 4.

---

## 7. Requerimiento 5 — Autocompletar "Expediente de Incorporación" y "Convenio de Incorporación"

### 7.1 Estado actual: **ya implementado**

Este punto **ya está resuelto en el código actual**, no requiere desarrollo nuevo:

- Campos en el Informe Técnico de renovación: `expediente_incorporacion`, `convenio_incorporacion` (`admisiones/models/admisiones.py:641-646`), solo aplican cuando `es_renovacion` (`admisiones_forms.py:76-88`).
- Autocompletado ya implementado en `admisiones/forms/admisiones_forms.py:100-113`: busca la `Admision` de tipo `"incorporacion"` del mismo comedor (excluyendo la actual, ordenada por `creado`/`pk`) y prellena:
  - `expediente_incorporacion.initial = incorporacion.num_expediente`
  - `convenio_incorporacion.initial = incorporacion.numero_convenio`

### 7.2 Acción recomendada

No es un requerimiento funcional nuevo. Si el pedido del usuario responde a un caso puntual donde el autocompletado no funcionó (por ejemplo, comedor sin admisión de incorporación cargada en SISOC, o con más de una admisión de tipo `"incorporacion"`), conviene reportarlo como bug con el caso concreto (comedor/admisión) en vez de tratarlo como funcionalidad a construir. Este documento no encontró evidencia de que el mecanismo esté roto — solo confirma que existe.

---

## 8. Requerimiento 6 — Antecedentes de renovaciones: listar y poder excluir filas

### 8.1 Estado actual

Ya está vinculado a las admisiones de renovación anteriores del comedor (no es texto libre desconectado), aunque se persiste como `JSONField`, no como relación real. Evidencia en `admisiones/forms/admisiones_forms.py:115-166`:

- Se activa cuando `tipo_renovacion == "segunda_o_posterior"` y hay comedor.
- Busca todas las `Admision` anteriores de tipo `"renovacion"` del mismo comedor (`.exclude(pk=admision.pk).order_by("creado", "pk")`).
- Por cada una, genera 3 campos de formulario (`resolucion`, `convenio`, `expediente`), precargados desde `numero_disposicion`, `numero_convenio`, `num_expediente` de esa admisión anterior, editables.
- Al guardar, se serializa a `InformeTecnico.antecedentes_renovaciones` (`JSONField(default=list)`, línea 618) como lista de `{"admision_id", "resolucion", "convenio", "expediente"}`.

Es decir: hoy genera automáticamente **una fila por cada renovación anterior encontrada**, sin posibilidad de excluir ninguna del listado que se imprime.

### 8.2 Requerimiento y regla de negocio (definida con el usuario)

El formulario debe permitir **ocultar/excluir** del Informe Técnico alguna de las filas de antecedentes detectadas automáticamente (por ejemplo, una renovación anterior que no corresponde citar en ese informe puntual), sin necesidad de borrar la `Admision` de renovación original.

**Fuera de alcance de este punto:** no se pide poder cargar antecedentes "a mano" que no correspondan a ninguna `Admision` cargada en SISOC. El listado sigue estando 100% vinculado a admisiones reales del comedor; solo se agrega la posibilidad de excluir filas del subconjunto detectado automáticamente.

### 8.3 Puntos abiertos para definición técnica

- Cómo se persiste la exclusión: un flag `incluido: bool` por fila dentro del mismo `antecedentes_renovaciones` JSON (recomendado, dado que ya es una lista de diccionarios), vs. otro mecanismo.
- Si la exclusión es por informe (cada Informe Técnico decide qué filas mostrar) o si debería afectar a futuros informes del mismo comedor — se asume que es por informe, consistente con que hoy los 3 campos por fila (`resolucion`/`convenio`/`expediente`) ya son editables por informe sin afectar la `Admision` de origen.

---

## 9. Requerimiento 7 — Eliminar la sección "Resolución de pago" de todos los Informes Técnicos

### 9.1 Estado actual

`InformeTecnico` tiene 6 pares `resolucion_de_pago_N` / `monto_N` (`admisiones/models/admisiones.py:963-1027`), exclusivos de **renovación** (comentario explícito: "Campos exclusivos de Renovación", línea 962).

Aparece en:

- **Modelo**: campos `resolucion_de_pago_1..6`, `monto_1..6`.
- **Formulario**: `resolucion_de_pago_1..4` y sus montos se vuelven obligatorios cuando `require_full` y `tipo == "renovacion"` (`admisiones_forms.py:400-406`).
- **DOCX**: `renovacion_docx_informe_tecnico_base.docx` y `renovacion_docx_informe_tecnico_juridico.docx` (6 ocurrencias cada uno). **No** aparece en ningún DOCX de incorporación ni en `informe_tecnico_complementario.docx`.
- **PDF de previsualización**: `admisiones/templates/admisiones/pdf/renovacion_pdf_informe_tecnico_base.html:305-330` y `renovacion_pdf_informe_tecnico_juridico.html:305-330`.
- **Agrupador de campos para visualización**: `admisiones/services/informes_service/impl.py:377,398,400-401,416-417` — grupo `"Resolución de pago"`, incluido solo si `es_renovacion`.

Confirmado: es exclusivo del flujo de renovación (base y jurídico); no existe en incorporación ni en el informe complementario, así que "todos los informes técnicos" en la práctica equivale a "ambas variantes del informe técnico de renovación".

### 9.2 Requerimiento y regla de negocio (definida con el usuario)

Sacar la sección "Resolución de pago" de todo lo que el usuario ve y de todo lo que se genera de ahora en adelante:

- Formulario del Informe Técnico (dejar de pedirla / dejar de exigirla como obligatoria).
- DOCX de renovación (base y jurídico).
- PDF de previsualización de renovación (base y jurídico).
- Agrupador de campos usado para mostrar el informe (`informes_service`).

**Los datos históricos ya cargados se conservan** en el modelo (no se elimina la columna ni se corre una migración destructiva); solo se deja de mostrar y de pedir hacia adelante.

### 9.3 Puntos abiertos para definición técnica

- Si además de sacarla de la vista, conviene marcar los campos como `editable=False` a nivel de formulario (para que no puedan volver a cargarse aunque quede el dato viejo) o alcanza con quitarlos del `Form`/template.
- Revisar si algún reporte o export adicional (fuera de los 5 puntos listados en 9.1) también referencia `resolucion_de_pago_*` o `monto_*` antes de dar por completa la limpieza.

---

## 10. Fuera de alcance (explícito, para todo el documento)

- Unificar la lógica duplicada de detección de "Alimentar Comunidad" (`is_alimentar_comunidad_program` vs. las 2 copias inline) — mencionado como hallazgo, no como parte del pedido.
- Cambios al modelo de datos de `Admision` para vincular explícitamente una renovación con "la admisión que renueva" (hoy se infiere por comedor + orden de creación) — se señala como punto abierto en el Requerimiento 3, pero rediseñar esa relación no es parte de este pedido.
- Migración retroactiva de provincia/localidad de texto libre a FK en informes técnicos ya cerrados (Requerimiento 2) — a decidir por el equipo técnico, no bloquea el requerimiento funcional.
- Requerimiento 5 (expediente/convenio de incorporación): no se abre como desarrollo, solo se documenta que ya existe.

---

## 11. Referencias

- `comedores/models.py` — `Comedor`, `Referente`, `Programas`.
- `comedores/views/comedor.py:1208` — `ComedorDetailView` (legajo).
- `comedores/services/comedor_service/impl.py:972-1115` — prestaciones efectivas, complementarios validados.
- `comedores/services/capacitaciones_certificados_service.py:20-25` — `is_alimentar_comunidad_program`.
- `admisiones/models/admisiones.py` — `InformeTecnico`, `Admision`, `InformeComplementario`, `InformeComplementarioCampos`.
- `admisiones/forms/admisiones_forms.py` — lógica condicional del formulario, autocompletados existentes.
- `admisiones/services/informes_service/impl.py:377-417` — agrupador de campos para visualización.
- `admisiones/templates/admisiones/informe_tecnico_form.html`, `admisiones/templates/admisiones/pdf/renovacion_pdf_informe_tecnico_*.html`, `admisiones/templates/admisiones/docx/renovacion_docx_informe_tecnico_*.docx`.
- `core/models.py:127-222` — `Provincia`, `Municipio`, `Localidad`.
- `static/custom/js/ubicacionSelects.js` — componente reutilizable de selects en cascada.
- `core/constants.py:19`, `core/permissions/registry.py:62` — rol `Tecnico Comedor`.
- `docs/implementaciones/admisiones_informes_tecnicos.md` — contrato general de Informes Técnicos, templates dinámicos.
