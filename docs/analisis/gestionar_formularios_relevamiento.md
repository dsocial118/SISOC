# GESTIONAR (AppSheet): formularios de relevamiento — funcional

## Alcance

Este documento cubre el uso actual (rama `development`) de GESTIONAR/AppSheet como
frontend de campo para los formularios de relevamiento de comedores, y su
sincronización con SISOC. No cubre el corte/nativización en curso (rama
`feature/territorial-corte-appsheet`, PR #2380, aún sin mergear).

Evidencia: `relevamientos/models.py`, `relevamientos/service.py`,
`relevamientos/serializer.py`, `relevamientos/views/api_views.py`,
`comedores/models.py`, `docs/flujos/relevamiento_sync.md`.

Las secciones 1 a 9 documentan el comportamiento **actualmente implementado**
(relevamiento inicial + primer seguimiento). Las secciones 10 en adelante
documentan **requerimientos nuevos, aún no implementados**, definidos con el
usuario el 2026-09-03: instancias de seguimiento adicionales, acta
complementaria/extraordinaria, reglas de autocompletado entre instancias, rol
coordinador con ciclo de validación en SISOC web, y disponibilidad de
comedores/relevamientos por zona territorial.

## 1) Tipos de formulario

Solo existen dos tipos operativos hoy; un tercero está reservado sin implementar.
La tabla incluye también los tipos nuevos definidos con el usuario (§10-§14),
aún sin implementar.

| Tipo | Modelo SISOC | Estado |
|---|---|---|
| Relevamiento inicial | `Relevamiento` | Activo |
| Excepción (de inicial) | `Excepcion` (sub-bloque de `Relevamiento`) | Activo |
| Punto de entrega (de inicial) | `PuntoEntregas` (sub-bloque de `Relevamiento`) | Activo |
| Primer seguimiento | `PrimerSeguimiento` (OneToOne al `Relevamiento` ancla) | Activo |
| Segundo seguimiento | — | Reservado; superado por "Seguimiento posterior" (§11.2) |
| Seguimiento posterior (2º en adelante) | — a definir | Nuevo, no implementado (§11.2) |
| Acta de excepción de seguimiento | — a definir | Nuevo, no implementado (§11.3) |
| Seguimiento virtual | — a definir | Nuevo, no implementado (§11.4) |
| Acta complementaria / extraordinaria | — a definir | Nuevo, no implementado (§12) |

Ambos formularios activos del relevamiento inicial (Excepción y Punto de
Entrega) son sub-bloques `OneToOne` de `Relevamiento` — **no** son un tipo de
relevamiento aparte, sino parte de la instancia inicial (ver §2.1 y §10 para
la aclaración de alcance). Primer seguimiento es una entidad independiente
que se sincroniza con GESTIONAR por separado (altas/bajas propias, endpoints
propios) y **hereda** el territorial de su relevamiento ancla; no puede
crearse sin uno.

## 2) Independencia de formularios y sección de "datos generales"

Comportamiento actual de AppSheet (confirmado por el usuario) que además debe
preservarse como requerimiento funcional hacia adelante:

### 2.1) Los cuatro formularios funcionan de manera independiente

Relevamiento Inicial, Seguimiento, Punto de Entrega y Excepciones son flujos
de preguntas independientes en la app: iniciar un formulario de Excepción no
obliga a recorrer las preguntas del formulario de comedor, y lo mismo aplica
para Punto de Entrega. Esto es así **a nivel de experiencia de uso**,
independientemente de cómo estén modeladas las entidades en la base de datos.

Nota de reconciliación con la base de datos: en SISOC, `PuntoEntregas` y
`Excepcion` están modelados como sub-bloques `OneToOne` del `Relevamiento`
(ver §3) — esa es la estructura de persistencia, no la experiencia de carga.
Para quien completa el formulario en AppSheet, son flujos separados.

El único formulario que **siempre** viaja junto al de comedor es el
**Anexo**: no funciona como flujo independiente.

**Aclaración de alcance (definida con el usuario, 2026-09-03):** los
formularios de Excepciones y de Punto de Entrega descriptos en este documento
corresponden exclusivamente a la **instancia de relevamiento inicial**.
Mantienen la lógica actual de independencia a nivel de experiencia de carga
descripta arriba, pero pertenecen a esa instancia — no son formularios
transversales. Las instancias de seguimiento (§11) tienen su **propia** acta
de excepción (§11.3), distinta del `Excepcion` del inicial; no reutilizan el
mismo formulario ni el mismo registro.

### 2.2) Pantalla común de "Datos generales" (primera sección de todos los formularios)

Los cuatro formularios (Relevamiento Inicial, Seguimiento, Punto de Entrega,
Excepciones) exponen, como primera sección, una pantalla de **Datos
generales** con:

- Fecha y hora de visita
- Dirección: calle, número, entre calle 1, entre calle 2, provincia,
  municipio, localidad, partido, barrio, código postal, piso, departamento,
  manzana, lote
- Datos del referente

Los datos del referente ya están bien implementados (bloques de contacto
`referente_comedor` / `responsable_relevamiento`, evidencia:
relevamientos/serializer.py `CONTACT_BLOCK_FIELDS`).

### 2.3) De dónde salen estos datos y cómo vuelven a SISOC

Todos los campos de "Datos generales" **ya existen en SISOC** antes de que
arranque el relevamiento:

- Fecha y hora de visita → `Relevamiento.fecha_visita`.
- Dirección completa (los 14 campos listados arriba) → ya están en el
  `Comedor` del relevamiento, con los mismos nombres (evidencia:
  comedores/models.py:382-429).
- Referente → ya resuelto por los bloques de contacto existentes.

Flujo de información (confirmado como comportamiento actual):

1. La app expone estos datos ya cargados en SISOC y permite editarlos.
2. Se completa el resto del relevamiento (los demás bloques/formularios).
3. Cuando el relevamiento pasa a `Finalizado` o `Finalizado/Excepciones`, la
   información de esta sección vuelve a SISOC y actualiza el `Comedor` /
   `Relevamiento` según lo relevado.

Este flujo de ida y vuelta con SISOC aplica **solo** a los campos de esta
sección (fecha de visita, dirección, referente) — el resto de los bloques del
relevamiento no leen datos preexistentes de SISOC, solo escriben.

Mecanismo ya implementado en SISOC para el paso 3: el `PATCH` entrante trae
un bloque `comedor` con estos mismos campos; `RelevamientoSerializer._process_comedor`
delega en `RelevamientoService.update_comedor`, que actualiza uno a uno los
14 campos de dirección más provincia/municipio/localidad (creando
municipio/localidad si no existen) — evidencia: relevamientos/serializer.py:95-101,
relevamientos/service.py:647-715. Aclaración importante: el código de SISOC
no valida que el relevamiento esté en `Finalizado` para aplicar esta
actualización — simplemente procesa el bloque `comedor` si viene en el
payload. Que este bloque solo se envíe al finalizar es una convención del
lado de AppSheet, no una regla exigida por SISOC.

## 3) Relevamiento inicial

Formulario principal de visita a un comedor. Se completa en AppSheet por el
territorial asignado y sus datos viajan a SISOC como sub-bloques OneToOne del
`Relevamiento`:

- Funcionamiento, Espacio, Colaboradores, Fuente de recursos, Fuente de
  compras, Prestación, Anexo.
- **Punto de entregas** (`PuntoEntregas`): datos sobre si el comedor también
  opera como punto de entrega/distribución de mercadería o bolsones (tipo de
  comedor, frecuencia de entrega, si existe/funciona el punto, si retiran
  mercadería, si reciben dinero, etc.). A nivel de base de datos es un bloque
  más del relevamiento inicial (ver §2.1 para la independencia a nivel de
  experiencia de carga).

  **Selección automática del formulario (comedor vs. punto de entrega):**
  al entrar al relevamiento en AppSheet, el formulario que se muestra se
  detecta a partir del tipo de comedor ya registrado en SISOC
  (`Comedor.tipocomedor`, catálogo `TipoDeComedor`: Comedor / Merendero /
  Punto de Entrega / Comedor y Merendero — evidencia:
  comedores/fixtures/tipodecomedor.json). Si el comedor está registrado como
  "Punto de Entrega", AppSheet abre automáticamente el formulario de punto de
  entrega. Desde la app se puede cambiar manualmente al otro formulario
  (comedor ⇄ punto de entrega) para ese relevamiento puntual; ese cambio
  **no** actualiza el `tipocomedor` del comedor en SISOC — es solo un cambio
  de vista para esa carga, el dato maestro del comedor no se toca.
  Comportamiento actual, confirmado por el usuario (no evidenciado en este
  repo más allá de la existencia del catálogo `TipoDeComedor`).
- **Excepción** (`Excepcion`): motivo (catálogo `MotivoExcepcion`),
  descripción, geolocalización, adjuntos y firma. Se completa cuando la visita
  no pudo concretarse/relevarse normalmente. A nivel de base de datos es el
  bloque que se llena cuando el relevamiento termina en el estado
  `Finalizado/Excepciones` (ver §5); a nivel de experiencia de carga es un
  flujo independiente (ver §2.1).

  **Selección del formulario de excepción:** a diferencia de punto de
  entrega, acá no hay detección automática por `tipocomedor` — el usuario
  puede seleccionar manualmente el formulario de excepción desde la app para
  **cualquier tipo de comedor** (Comedor, Merendero, Punto de Entrega,
  Comedor y Merendero por igual). Comportamiento actual, confirmado por el
  usuario (no evidenciado en este repo).

  Preguntas del formulario de excepción en AppSheet (según el usuario, no
  visible en este repo salvo lo indicado):
  - Fecha y hora de visita
  - Dirección: calle, número, entre calle 1, entre calle 2, provincia,
    municipio, localidad, partido, barrio, código postal, piso, departamento,
    manzana, lote
  - Tipo de excepción (select): No existe / Revisita / Punto de entrega /
    Otros
  - Descripción de excepción
  - Datos del referente (los mismos que en el resto de los formularios)
  - Geoposición
  - Firmas
  - Fotos

  Estas primeras tres preguntas (fecha y hora de visita, dirección, datos del
  referente) son exactamente la pantalla de "Datos generales" descripta en
  §2.2 — no son exclusivas del formulario de excepción.

  De lo restante, el modelo `Excepcion` de SISOC persiste **motivo** (mapea 1
  a 1 con el select "Tipo de excepción" — el catálogo `MotivoExcepcion` tiene
  exactamente esos 4 valores: No existe, Revisita, Punto de entrega, Otros),
  **descripción**, **latitud/longitud** (geoposición, propia de la excepción,
  distinta de la dirección del comedor), **adjuntos** (fotos) y **firma** —
  evidencia: relevamientos/service.py:1251-1280, relevamientos/models.py:936-961.

## 4) Primer seguimiento

Formulario de seguimiento posterior a un relevamiento activo. Tiene su propio
set de bloques (Funcionamiento, Servicios básicos, Almacenamiento de
alimentos, Condiciones de higiene, Tareas del comedor, Recursos, Compras, Menú,
Registro de asistencia, Actividades extra, Tarjeta, Rendición de cuentas,
Asistencia técnica, Cierre) — no reutiliza los modelos del relevamiento
inicial ni tiene bloques de Punto de entregas/Excepción.

Estados propios (`PrimerSeguimiento.ESTADO_CHOICES`):

| Estado | Significado |
|---|---|
| `Asignado` | Creado, a la espera de que el territorial lo complete |
| `En Proceso` | Territorial cargando datos en AppSheet |
| `Completo` | Cerrado |

Se crea desde el modal de relevamientos (`tipo_relevamiento=primer_seguimiento`)
o vía `PATCH /api/relevamiento/primer-seguimiento`. GESTIONAR puede
identificarlo por `sisoc_id`, `gestionar_id` o `id_relevamiento` (con uno
alcanza; si vienen varios, deben apuntar al mismo registro).

## 5) Estados del Relevamiento inicial

`Relevamiento.estado` es un `CharField` libre (sin choices declarados a nivel
modelo). En SISOC (código y base de datos) solo se usan estos cuatro valores:

```
Pendiente ──(asignar territorial)──▶ Visita pendiente ──(visita + carga/revisión en AppSheet)──▶ Finalizado
                                              │
                                              └──────────────────────────────────────────────▶ Finalizado/Excepciones
```

Puertas adentro de AppSheet, mientras SISOC ve `Visita pendiente`, existe un
sub-ciclo interno de revisión (`Pendiente Revisión` ⇄ `A Subsanar`) que se
detalla en §6. Ese sub-ciclo es interno de AppSheet — no está modelado en
`Relevamiento.estado` ni en ningún otro campo de SISOC (confirmado por el
usuario, sin evidencia en este repo). SISOC recién se entera del resultado
cuando llega el `PATCH` con el estado final.

- **`Pendiente`**: relevamiento creado sin territorial asignado. Solo se
  permite la acción "Asignar" en este estado.
- **`Visita pendiente`** — *estado intermedio visible en SISOC*: territorial ya
  asignado, a la espera de que se realice la visita, se cargue el formulario y
  se revise en AppSheet (incluye todo el sub-ciclo de revisión de §6). La
  reasignación de territorial solo está permitida mientras el relevamiento
  esté en `Pendiente` o `Visita pendiente` (nunca finalizado).
- **`Finalizado`**: la visita se completó sin novedades y fue validada por el
  coordinador. GESTIONAR, al confirmar el alta con `2xx` y devolver `Rows`,
  puede además devolver `docPDF`; SISOC lo persiste y habilita el botón "Ver
  PDF" en el detalle (visible solo para `Finalizado` y
  `Finalizado/Excepciones`).
- **`Finalizado/Excepciones`**: la visita terminó en excepción (no se pudo
  relevar con normalidad) y fue validada por el coordinador. En este caso se
  completa el bloque `Excepcion` (motivo, descripción, geolocalización,
  adjuntos, firma).

Reglas asociadas:
- No puede haber más de un relevamiento en `Pendiente` o `Visita pendiente`
  para el mismo comedor a la vez (bloqueado en `Relevamiento.save()`).
- Un primer seguimiento solo puede anclarse a un `Relevamiento` cuyo estado no
  sea `Finalizado` ni `Finalizado/Excepciones` (o crea uno nuevo si no hay
  relevamiento activo).
- Al pasar a cualquiera de los dos estados `Finalizado*`, se dispara la
  actualización de geolocalización del comedor desde el relevamiento.

## 6) Ciclo de validación: territorial ↔ coordinador (comportamiento actual — reemplazado a futuro)

> **Nota (2026-09-03):** este ciclo interno de AppSheet queda **reemplazado**
> por el ciclo descripto en §14 (Rol coordinador), que traslada la validación
> a SISOC web para toda instancia y todo formulario. Se conserva esta sección
> como registro del comportamiento actual hasta que se implemente §14.

Detalle del sub-ciclo interno de AppSheet mencionado en §5 (confirmado por el
usuario, sin evidencia en este repo — no está modelado en SISOC):

1. El territorial recibe el relevamiento asignado y lo completa en AppSheet.
2. Al enviarlo, un **coordinador** lo revisa (estado interno de AppSheet
   `Pendiente Revisión`).
3. Resultado de la revisión:
   - **Valida** → el relevamiento pasa a `Finalizado` o
     `Finalizado/Excepciones` (según corresponda). Este es el momento en que
     SISOC recibe el `PATCH` final (ver §5 y §8).
   - **Pide modificaciones** → el relevamiento pasa al estado interno
     `A Subsanar` y vuelve al territorial para que corrija.
4. El territorial corrige y reenvía → vuelve a quedar `Pendiente Revisión`
   para el coordinador.
5. Los pasos 2-4 (`Pendiente Revisión` ⇄ `A Subsanar`) pueden repetirse **N
   veces** hasta que el coordinador valida el relevamiento.

```
                (AppSheet, interno — SISOC solo ve "Visita pendiente")
                ┌─────────────────────────────────────────────────┐
                │                                                 │
                │   Pendiente Revisión ──(pide cambios)──▶ A Subsanar
                │        ▲                                    │   │
                │        └────────────(territorial corrige)───┘   │
                │                                                 │
                └─────────────────────┬───────────────────────────┘
                                      │ (coordinador valida)
                                      ▼
                    SISOC: Finalizado / Finalizado con Excepciones
                              (llega por PATCH entrante)
```

Ninguno de los dos estados internos (`Pendiente Revisión`, `A Subsanar`) es
visible en SISOC ni tiene contraparte en `Relevamiento.estado`: todo el ciclo
ocurre "adentro" de `Visita pendiente` desde la perspectiva de SISOC.

## 7) Observaciones y hallazgos sobre el formulario de Relevamiento Inicial

Relevado por el usuario sobre el formulario actual en AppSheet (numeración de
pasos propia de AppSheet, no de este repo). Todos corresponden al
Relevamiento Inicial:

- **Paso 4 (Espacio/Cocina)**: falta la pregunta condicional "¿Dónde
  almacenan los alimentos secos?", que debería activarse si se responde que
  no hay lugar para almacenarlos. SISOC ya tiene un campo preparado para esa
  respuesta — `EspacioCocina.almacenamiento_alimentos_secos_otro`, cuyo
  `verbose_name` es literalmente *"2.2.2.1 Si respondió 'No', especificar
  dónde almacenan"* (evidencia: relevamientos/models.py:206-214) — el campo
  existe en SISOC pero la pregunta condicional no está implementada en el
  formulario de AppSheet.
- **Paso 5 (Espacio)**: falta la pregunta condicional "Otra frecuencia de
  limpieza", que debería activarse si se elige "Otra" en la pregunta de
  frecuencia de limpieza de las instalaciones. El campo
  `Espacio.frecuencia_limpieza_otro` ya existe en el modelo (evidencia:
  relevamientos/models.py:399-402), listo para recibir esa respuesta; falta
  la pregunta condicional en AppSheet.
- **Paso 10 (Anexo)**: falta una pregunta gate "¿Recibió o no insumos?"
  previa al detalle de insumos. El modelo `Anexo` solo tiene
  `veces_recibio_insumos_2024` (cantidad de veces en el año), sin un campo
  booleano dedicado a esa pregunta sí/no (evidencia:
  relevamientos/models.py:905-910) — a definir si conviene inferir la
  respuesta de la cantidad (0 = no recibió) o si hace falta agregar un campo
  nuevo.
- **Paso 10 (Anexo)**: la etiqueta "Espacio para Huerta" debería decir
  "Espacio para actividades". El campo subyacente es `Anexo.espacio_huerta`
  (evidencia: relevamientos/models.py:903) — es un cambio de etiqueta/copy en
  AppSheet, no de modelo.
- **Paso 12 (cierre del Relevamiento Inicial)**: falta la firma del
  responsable del comedor; hoy solo se pide la firma del relevador/técnico
  territorial. A diferencia del Primer Seguimiento, que en su bloque
  `CierreSeguimiento` ya tiene dos firmas (`firma_entrevistado` y
  `firma_tecnico`, evidencia: relevamientos/models.py:1543-1544), el
  Relevamiento Inicial no tiene un bloque de cierre equivalente: la única
  firma modelada en SISOC para el relevamiento inicial es `Excepcion.firma`
  (evidencia: relevamientos/models.py:954), y esa solo aplica al camino de
  excepción, no al cierre normal en `Finalizado`. Si se agrega la firma del
  responsable en el paso 12, probablemente haga falta un campo nuevo en el
  modelo — hoy no hay dónde persistirla para el flujo normal de `Finalizado`.

## 8) Sincronización con GESTIONAR (resumen)

- **Saliente (SISOC → GESTIONAR)**: alta/baja de `Relevamiento` y
  `PrimerSeguimiento` vía tareas asíncronas (`ThreadPoolExecutor` +
  `requests`), usando `GESTIONAR_API_*`. Se marca `sincronizado_gestionar=True`
  solo si GESTIONAR responde `2xx` **y** devuelve `Rows` (un `200` con `Rows`
  vacío se trata como rechazo silencioso y queda logueado).
- **Entrante (GESTIONAR → SISOC)**: `PATCH /api/relevamiento` y
  `PATCH /api/relevamiento/primer-seguimiento`, autenticados con
  `HasAPIKeyOrToken`. Cada PATCH exitoso también marca
  `sincronizado_gestionar=True`. Este es el mecanismo por el cual AppSheet
  entrega el formulario completado (incluye el paso a `Finalizado` /
  `Finalizado/Excepciones`, la actualización de "Datos generales" descripta
  en §2.3, y para el primer seguimiento, todos sus bloques).

Evidencia detallada del flujo: [docs/flujos/relevamiento_sync.md](../flujos/relevamiento_sync.md).

## 9) Nota operativa: enlace al PDF roto (404)

Cada relevamiento finalizado implica volcar la información relevada en un
template de PDF; ese proceso ya está implementado (SISOC solo persiste y
expone el link que GESTIONAR devuelve en `docPDF` — ver §5 y §8 —, y muestra
el botón "Ver PDF" cuando el relevamiento está `Finalizado` o
`Finalizado/Excepciones`).

**Advertencia reportada por el usuario (no evidenciada en este repo, a
verificar/corregir):** con la aplicación nueva, el enlace de cada PDF no
apunta a ningún lado y devuelve error 404. Estos PDF deben existir y ser
accesibles — es un problema operativo a resolver, no una decisión de diseño.

---

# Parte II — Requerimientos nuevos (definidos con el usuario, 2026-09-03)

Todo lo que sigue es **diseño funcional a implementar**, no comportamiento
actual. Se referencia evidencia del repo donde existe una base parcial sobre
la que construir (asignación territorial, permisos), y se marca explícitamente
como "no encontrado" lo que hay que crear desde cero.

## 10) Instancia inicial: alcance confirmado

Ver aclaración agregada en §2.1. Los formularios de Excepción y Punto de
Entrega **no cambian** con este trabajo: siguen siendo sub-bloques de la
instancia de relevamiento inicial, con la misma independencia de carga a
nivel de experiencia de usuario. Este punto se deja escrito explícitamente
porque las instancias de seguimiento (§11) introducen su propia acta de
excepción, y no debe confundirse una con otra.

## 11) Instancias de seguimiento

El seguimiento deja de ser un único formulario (§4, `PrimerSeguimiento`) y
pasa a componerse de varios tipos, todos anclados a un `Relevamiento` inicial
ya existente (mismo patrón de herencia de territorial que el primer
seguimiento actual):

1. **Primer seguimiento** — el realizado inmediatamente después del inicial.
    Se mantiene igual salvo por quedar sujeto al nuevo
   ciclo de validación del coordinador (§14) y a las reglas de autocompletado
   de §13.
2. **Seguimiento posterior** — del segundo seguimiento en adelante. Se repite
   para cada seguimiento sucesivo sobre el mismo comedor/relevamiento ancla.
3. **Acta de excepción de seguimiento** — funciona igual que `Excepcion` del
   inicial (§3), pero aplicada a una instancia de seguimiento.
4. **Seguimiento virtual** — formulario que reemplaza al formulario normal de
   seguimiento cuando la modalidad de la visita es virtual.

(El acta complementaria/extraordinaria, si bien puede usarse durante un
seguimiento, no es exclusiva de esta sección — ver §12.)

### 11.1) Numeración de seguimientos posteriores

Los seguimientos posteriores llevan **número de orden explícito** (2º, 3º,
4º...), a diferencia del primer seguimiento que no necesita numerarse por ser
único. Este número:

- Reemplaza al reservado "Segundo seguimiento" de §1 (que quedaba
  deshabilitado en UI y rechazado en el servicio).
- Es la clave para la cadena de autocompletado (§13.2): cada seguimiento
  posterior hereda de "el seguimiento con el número inmediato anterior", no
  necesariamente del inicial ni del primer seguimiento.

**Pendiente de definir:** si el set de preguntas/bloques de un seguimiento
posterior es idéntico al del primer seguimiento (mismo modelo de datos,
distinto número de instancia) o si difiere en contenido. No se relevó
evidencia ni definición del usuario sobre esto — a confirmar antes de
modelar.

### 11.2) Acta de excepción de seguimiento

- Se completa cuando la visita de una instancia de seguimiento (primer o
  posterior) no pudo concretarse/relevarse normalmente — mismo criterio que
  la excepción del inicial (§3).
- Es un **registro separado** del `Excepcion` del inicial (ver aclaración de
  §10): una excepción de seguimiento no debe persistirse en el mismo modelo
  que la excepción del relevamiento inicial.
- Al completarse, la instancia de seguimiento correspondiente queda en un
  estado **análogo a `Finalizado/Excepciones`** del inicial (mismo patrón:
  motivo, descripción, geolocalización, adjuntos, firma), sujeto igual que
  cualquier otro cierre a la validación del coordinador (§14).

### 11.3) Seguimiento virtual

- Cuando la modalidad de la visita es virtual, el formulario de seguimiento
  virtual **reemplaza completamente** al formulario normal de esa instancia
  (son excluyentes) — aplica indistintamente a que sea primer seguimiento o
  un seguimiento posterior.
- **Pendiente de definir:** en qué momento y de qué manera se determina que
  una instancia es "virtual" (¿selección explícita antes de iniciar la carga,
  igual que la selección de tipo comedor/punto de entrega en §3, o una
  pregunta dentro del propio flujo que deriva a otro set de preguntas?). No
  hay definición del usuario sobre este punto todavía.

## 12) Acta complementaria - extraordinaria

Formulario transversal, distinto de la excepción de inicial (§3) y de la
excepción de seguimiento (§11.2):

- **Siempre disponible, sin depender de una instancia de relevamiento
  activa**: a diferencia de todos los formularios anteriores (que cuelgan de
  un `Relevamiento` o de un seguimiento), el acta complementaria/
  extraordinaria se liga directamente al **comedor**, y puede completarse en
  cualquier momento, exista o no un relevamiento/seguimiento en curso.
- **Disparador**: registrar novedades o situaciones puntuales del comedor que
  no están atadas a ninguna visita de relevamiento en curso — a diferencia de
  la excepción, que específicamente documenta que una visita programada no
  pudo concretarse con normalidad.
- Funciona de forma similar a Excepciones en cuanto a estructura de datos
  (motivo/descripción, geolocalización, adjuntos, firma), pero **no** hereda
  su ciclo de vida de ningún `Relevamiento.estado`.
- Al ser un dato que impacta sobre el comedor, también queda sujeta a la
  regla general de validación del coordinador antes de impactar en SISOC
  (§14) — no es una excepción a esa regla por ser standalone.
- Implica un modelo nuevo en SISOC, con FK directa a `Comedor` (no a
  `Relevamiento`). No se encontró ningún modelo existente en el repo que
  cubra este caso (`Excepcion` requiere `Relevamiento`).

## 13) Reglas de autocompletado y persistencia de datos entre instancias

### 13.1) Formularios iniciales (comportamiento ya implementado, ver §2.3)

Los datos de localización del comedor y datos del referente se muestran tal
como están cargados en SISOC al iniciar el formulario, son editables, y al
finalizar (ahora: al ser **validado por el coordinador**, ver §14) la
información vuelve a SISOC y actualiza `Comedor`/`Relevamiento`.

### 13.2) Formularios de seguimiento

- **Localización y referente**: siguen la misma lógica que el inicial — se
  muestran tal como están en SISOC (`Comedor`) al momento de iniciar el
  seguimiento, son editables, y al validarse por el coordinador la
  información **también actualiza el maestro `Comedor`** en SISOC, igual que
  hoy hace la validación del inicial. No hay tratamiento especial para
  seguimiento en este punto: el seguimiento tiene el mismo privilegio de
  actualizar el dato maestro que el inicial.
- **Preguntas que se repiten entre inicial y primer seguimiento**: el primer
  seguimiento trae precargada la información cargada en el relevamiento
  inicial para esas preguntas puntuales, permitiendo editarla.
- **Preguntas que se repiten entre seguimientos posteriores**: siguen una
  **cadena**, no vuelven siempre al inicial — cada seguimiento posterior trae
  precargado lo cargado en el seguimiento con el número de orden inmediato
  anterior (ver numeración en §11.1). Ejemplo: el 3er seguimiento hereda del
  2do, no del inicial ni del 1er seguimiento.
- **Persistencia por instancia**: cada instancia de seguimiento persiste su
  propia snapshot de estos datos de forma independiente. Editar un valor en
  un seguimiento **no modifica** el registro de la instancia anterior ya
  finalizada/validada — ni el inicial, ni un seguimiento posterior previo.

## 14) Rol coordinador y ciclo de validación en SISOC web

Este ciclo **reemplaza** al descripto en §6 (ciclo interno de AppSheet,
invisible para SISOC). Aplica a **toda instancia y todo formulario**: inicial,
primer seguimiento, seguimientos posteriores, actas de excepción (de inicial
y de seguimiento), seguimiento virtual y acta complementaria/extraordinaria.
Ningún dato relevado en territorio impacta en SISOC antes de ser revisado y
validado por este rol.

### 14.1) Rol nuevo

Se define un rol **Coordinador** en SISOC web, distinto de los roles
existentes en el repo. Aclaración por evidencia encontrada al investigar (no
es parte de la decisión, es una observación para tener en cuenta al
implementar): ya existe declarado — pero **no aplicado en ningún lugar del
código** — un permiso `relevamientos.review_relevamiento` ("Puede revisar y
finalizar relevamientos"), asignado al grupo `Revisor Relevamientos`
(evidencia: `relevamientos/models.py:1128-1129`,
`users/bootstrap/groups_seed.py:106-110`). Se definió con el usuario que el
rol Coordinador es un concepto **nuevo**, no una reutilización de ese
permiso — queda como nota para quien implemente, para decidir si conviene
reemplazar/eliminar ese permiso sin uso o dejarlo en desuso junto al nuevo rol.

### 14.2) Estados nuevos

- **Estado intermedio genérico** (nombre tentativo: `Pendiente validación
  coordinador`): cuando el territorial "finaliza" cualquier formulario en la
  app, la instancia correspondiente queda en este estado — visible en SISOC,
  sin impactar todavía ningún dato maestro. Es un único estado genérico,
  válido para cualquier tipo de instancia/formulario (no uno distinto por
  cada tipo).
- **Estado de rechazo** (nombre tentativo: `A subsanar`): si el coordinador,
  desde SISOC web, no valida la instancia y pide correcciones, pasa a este
  estado. El territorial lo ve reflejado en la app, corrige y reenvía —
  puede repetirse **N veces** hasta que el coordinador valide.
- **Validación positiva**: el coordinador valida → la instancia pasa a
  `Finalizado` / `Finalizado con Excepciones` (según corresponda) y **recién
  en ese momento** se disparan los efectos de impacto (actualización de
  `Comedor`, geolocalización, datos de "Datos generales" — ver §2.3 y §13).

### 14.3) Diagrama actualizado (reemplaza el ciclo de §6)

```
Territorial completa y "finaliza" en la app
                │
                ▼
      Pendiente validación coordinador  ◀────────────┐
                │                                     │
                │ (coordinador revisa en SISOC web)   │
                ▼                                     │
        ┌───────┴────────┐                            │
        │                │                            │
     valida           pide correcciones                │
        │                │                            │
        ▼                ▼                            │
  Finalizado /       A subsanar ──(territorial corrige)┘
  Finalizado con
  Excepciones
   (impacta en SISOC:
   Comedor, geolocalización,
   datos generales)
```

El nombre definitivo de los dos estados nuevos queda pendiente de definición
(los usados arriba son tentativos, para dejar clara la mecánica).

### 14.4) Nota de compatibilidad con §5

`Relevamiento.estado` (§5) tendrá que incorporar el nuevo estado intermedio y
el de rechazo (hoy es un `CharField` libre sin choices, por lo que técnicamente
no requiere migración de esquema, solo de valores usados y de la lógica que
los interpreta). Las reglas de §5 sobre unicidad de relevamiento
`Pendiente`/`Visita pendiente` por comedor y sobre reasignación de territorial
deberán revisarse para contemplar estos nuevos estados.

## 15) Disponibilidad de comedores y relevamientos por zona territorial

### 15.1) Comportamiento actual (evidencia del repo)

Ya existe una asignación territorial↔zona, pero a nivel **solo provincia**:
`TerritorialComedorProvincia` (evidencia: `users/models.py:308-323`). El
filtrado de qué relevamientos ve un territorial ya combina, con `OR`, esta
asignación por zona con la asignación puntual directa
(`Relevamiento.territorial_user`): evidencia,
`_scope_relevamientos_for_authenticated_user` en
`relevamientos/views/api_views.py:20-44`. Es decir, la convivencia entre
"acceso por zona" y "asignación puntual" **ya está resuelta a nivel de
filtrado de datos** — lo que falta es la granularidad y las acciones
disponibles sobre esos comedores.

### 15.2) Requerimiento nuevo

- Extender la granularidad de la asignación territorial de **provincia** a
  **provincia + municipio + localidad**. Pendiente de definir el modelo
  concreto (extensión de `TerritorialComedorProvincia` o modelo nuevo) y si
  un mismo territorial puede tener múltiples combinaciones asignadas.
- Dentro de esa zona asignada, el territorial debe poder:
  - **Ver** todos los comedores de la zona, no solo los que ya tienen un
    relevamiento activo.
  - **Activar autónomamente** un relevamiento (inicial o, si corresponde,
    una instancia de seguimiento) sobre cualquiera de esos comedores.
- La activación autónoma **arranca directo**: mismo flujo que un relevamiento
  asignado puntualmente desde SISOC (queda en estado inicial habilitado para
  carga), sin pasos de aprobación previos.
- La asignación puntual de relevamientos desde SISOC (mecanismo actual)
  **se mantiene** y convive con el acceso por zona — no la reemplaza.
- Los relevamientos asignados puntualmente desde SISOC deben **destacarse/
  priorizarse** frente a los que el territorial activó de forma autónoma
  dentro de su zona. Pendiente de definir si esto es solo un tratamiento
  visual/de orden en el listado, o si implica lógica adicional (plazos,
  notificaciones, reportes).

## 16) Pendientes abiertos (a confirmar antes de modelar)

- Set de preguntas/bloques de "seguimiento posterior": ¿idéntico al primer
  seguimiento o distinto? (§11.1)
- Momento y mecanismo de determinación de "seguimiento virtual": ¿selección
  previa o pregunta derivadora dentro del flujo? (§11.3)
- Nombres definitivos de los estados nuevos `Pendiente validación
  coordinador` y `A subsanar` (§14.2), y si aplican tal cual a
  `Relevamiento.estado` o requieren un campo/modelo nuevo.
- Modelo concreto para la asignación territorial a nivel municipio/localidad
  y si admite múltiples zonas por usuario (§15.2).
- Tratamiento de "destacado/priorizado" para relevamientos asignados desde
  SISOC: ¿solo visual o con lógica de negocio adicional? (§15.2)
- Qué ocurre con el permiso `relevamientos.review_relevamiento` /grupo
  `Revisor Relevamientos` ya declarado y sin uso, frente al rol Coordinador
  nuevo (§14.1): mantener sin uso, deprecar, o consolidar.
## 17) Observaciones y hallazgos sobre el formulario de Relevamiento Inicial

Relevado por el usuario sobre el formulario actual en AppSheet (numeración de
pasos propia de AppSheet, no de este repo). Todos corresponden al
Relevamiento Inicial:

- **Paso 4 (Espacio/Cocina)**: falta la pregunta condicional "¿Dónde
  almacenan los alimentos secos?", que debería activarse si se responde que
  no hay lugar para almacenarlos. SISOC ya tiene un campo preparado para esa
  respuesta — `EspacioCocina.almacenamiento_alimentos_secos_otro`, cuyo
  `verbose_name` es literalmente *"2.2.2.1 Si respondió 'No', especificar
  dónde almacenan"* (evidencia: relevamientos/models.py:206-214) — el campo
  existe en SISOC pero la pregunta condicional no está implementada en el
  formulario de AppSheet.
- **Paso 5 (Espacio)**: falta la pregunta condicional "Otra frecuencia de
  limpieza", que debería activarse si se elige "Otra" en la pregunta de
  frecuencia de limpieza de las instalaciones. El campo
  `Espacio.frecuencia_limpieza_otro` ya existe en el modelo (evidencia:
  relevamientos/models.py:399-402), listo para recibir esa respuesta; falta
  la pregunta condicional en AppSheet.
- **Paso 10 (Anexo)**: falta una pregunta gate "¿Recibió o no insumos?"
  previa al detalle de insumos. El modelo `Anexo` solo tiene
  `veces_recibio_insumos_2024` (cantidad de veces en el año), sin un campo
  booleano dedicado a esa pregunta sí/no (evidencia:
  relevamientos/models.py:905-910) — a definir si conviene inferir la
  respuesta de la cantidad (0 = no recibió) o si hace falta agregar un campo
  nuevo.
- **Paso 10 (Anexo)**: la etiqueta "Espacio para Huerta" debería decir
  "Espacio para actividades". El campo subyacente es `Anexo.espacio_huerta`
  (evidencia: relevamientos/models.py:903) — es un cambio de etiqueta/copy en
  AppSheet, no de modelo.
- **Paso 12 (cierre del Relevamiento Inicial)**: falta la firma del
  responsable del comedor; hoy solo se pide la firma del relevador/técnico
  territorial. A diferencia del Primer Seguimiento, que en su bloque
  `CierreSeguimiento` ya tiene dos firmas (`firma_entrevistado` y
  `firma_tecnico`, evidencia: relevamientos/models.py:1543-1544), el
  Relevamiento Inicial no tiene un bloque de cierre equivalente: la única
  firma modelada en SISOC para el relevamiento inicial es `Excepcion.firma`
  (evidencia: relevamientos/models.py:954), y esa solo aplica al camino de
  excepción, no al cierre normal en `Finalizado`. Si se agrega la firma del
  responsable en el paso 12, probablemente haga falta un campo nuevo en el
  modelo — hoy no hay dónde persistirla para el flujo normal de `Finalizado`.