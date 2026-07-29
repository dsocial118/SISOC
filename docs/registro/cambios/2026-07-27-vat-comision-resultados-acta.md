# VAT/INET: pestaña "Resultados" en el detalle de comisión de curso

## Contexto

El detalle de comisión sólo permitía gestionar inscriptos, clases y horarios. No
había forma de registrar el resultado final del curso (aprobado/desaprobado) por
alumno ni los datos del acta de cierre.

`Evaluacion` / `ResultadoEvaluacion` ya existían, pero:

- están FK-eados **sólo a `Comision`** (camino legacy de oferta institucional),
  no a `ComisionCurso` — la asimetría conocida del módulo;
- modelan notas numéricas por instancia de evaluación (`calificacion`,
  `ponderacion`), no un pass/fail de curso más un acta.

Reusarlos habría implicado sumar otra FK dual nullable a la deuda existente. Se
optó por modelos nuevos, acotados al camino `Curso → ComisionCurso` (el activo).

## Cambio

### Modelos (`VAT/models.py`, migración `0050_resultados_comision_curso`)

- **`ProfesorCentro`** (nuevo, soft delete): `centro`, `apellido`, `nombre`,
  `documento`, `email`. `unique_together (centro, documento)`.
  Deliberadamente **independiente de `ciudadanos.Ciudadano`**: un profesor no es
  beneficiario del programa y no debe entrar al padrón que alimenta validación
  RENAPER, cola de revisión de duplicados ni vouchers. El alta es directa, sin
  validación de identidad externa (pedido explícito del ticket).
- **`ActaCierreComision`** (nuevo, soft delete): `OneToOne` con `ComisionCurso`,
  `profesor`, `fecha_fin`, `numero_acta` (opcional), `registrado_por`.
- **`Inscripcion`**: se agregan `resultado_final`
  (`aprobado` / `desaprobado`, **NULL = "Sin calificar"**),
  `resultado_registrado_por` y `resultado_fecha`. Los dos últimos son
  necesarios porque `audittrail/` no cubre VAT ni `Inscripcion`.

### Service (`VAT/services/resultados_comision_service.py`, nuevo)

- `alumnos_calificables(comision_curso)` → filtro del listado.
- `resumen(inscripciones)` → contadores de las cards.
- `guardar_resultados(...)` → atómico; valida acta, hace upsert y aplica
  calificaciones.

### Views / URLs

- `ComisionCursoDetailView`: contexto de la pestaña (`puede_gestionar_resultados`,
  `alumnos_resultados`, `resumen_resultados`, `acta_cierre`, urls y form).
- `ComisionCursoResultadosView` (POST) — guardado único de acta + calificaciones.
- `ProfesorCentroBuscarView` (GET) / `ProfesorCentroCrearView` (POST).
- `ProfesorCentroForm` en `VAT/forms.py`.

### Template (`vat/oferta_institucional/comision_detail.html`)

Solapa "Resultados" a la derecha de "Horarios" (chip rail + ambos juegos de
side-tabs), panel con 4 cards de resumen, bloque "Datos del acta" y tabla
"Calificación de alumnos" con botones Aprobar / Desaprobar. CSS nuevo:
`.sisoc-metric-grid--quad`, `.sisoc-btn--gold`, `.sisoc-btn--light` y los
estilos `ci-acta-*` / `ci-prof-*` / `ci-filtro-*`.

## Decisiones y trade-offs

**Quién aparece en el listado.** "Inscripción confirmada" = `estado="inscripta"`.
Pero el filtro real es `estado__in=("inscripta", "completada")`: como calificar
mueve la inscripción a `completada`, filtrar sólo por `inscripta` haría
desaparecer del listado a los ya calificados al recargar, rompiendo la
corrección posterior de resultados y la aritmética de las cards
(aprobados + desaprobados + sin calificar = inscriptos).

**Calificar cierra la inscripción.** Aprobar y desaprobar dejan la inscripción en
`completada` vía `InscripcionService.actualizar_estado_inscripcion` (no se
duplican las reglas de transición). Con esto `completada` pasa a ser alcanzable
desde la UI por primera vez. Consecuencia: `completada` **no** está en
`ESTADOS_INSCRIPCION_OCUPAN_CUPO`, así que guardar resultados **libera cupo**. En
la práctica no habilita altas indebidas porque `_comision_vencida` y
`CierreComisionService` ya bloquean comisiones vencidas/cerradas.

`abandonada` queda fuera de esta pestaña: desaprobado ≠ abandonado. Sigue sin ser
alcanzable desde la UI.

**`fecha_fin` del acta es propia del acta.** Se precarga con la de la comisión y
es editable, pero **no** escribe sobre `ComisionCurso.fecha_fin`: eso alteraría
el cierre automático de `CierreComisionService` y el bloqueo de altas de
`InscripcionService._comision_vencida`.

**Permisos: se gatea con `VAT.change_inscripcion`**, el mismo permiso que ya
habilita Admitir/Rechazar en la lista de espera. No se toca
`users/bootstrap/groups_seed.py` ni se agrega data migration de reconciliación.
Motivo: `create_groups` es aditivo y no actualiza entornos existentes, y este
repo ya se comió el costo de olvidarlo — ver la nota final de
`2026-07-06-vat-perfiles-permisos-bootstrap.md`, donde `VAT.view_curso` quedó
fuera de los 4 perfiles y dejó el detalle de curso inalcanzable. Así la feature
es usable por CFP e INET Admin General desde el día uno. Si más adelante se
quieren permisos granulares (`VAT.add_actacierrecomision`, etc.), es un cambio
de seeds aparte con su migración de reconciliación.

**Alcance: sólo `ComisionCurso`.** El template es compartido con el camino legacy
`OfertaInstitucional → Comision`, que no define `puede_gestionar_resultados` y
por lo tanto no renderiza la solapa. Extenderlo después es agregar contexto en
`ComisionDetailView` y FKs duales en el acta.

**Sub-filtro en vez de solapa extra.** Se evaluó separar "a calificar" y
"finalizados" en dos solapas; se implementó como filtro cliente (Todos / A
calificar / Finalizados) sobre la misma tabla: mismo resultado, sin un segundo
query ni una segunda tabla, y las cards siguen sumando el total.

**Hash en el controlador de tabs.** Se agregó soporte de `location.hash` para que
el redirect posterior al POST vuelva a "Resultados" en lugar de caer siempre en
"Información". Beneficia a todas las solapas.

## Validación

- `VAT/tests.py`: 14 tests nuevos (listado confirmadas, render de la solapa,
  ocultamiento sin permiso, persistencia de acta y calificaciones, `fecha_fin` de
  la comisión intacta, N° de acta opcional, bloqueo sin profesor y sin fecha,
  corrección posterior, aislamiento entre comisiones, profesor de otro centro,
  búsqueda por nombre/DNI con email, alta y duplicado).
- `black` y `manage.py check`: limpios.
- `pylint`: 9.99/10 en los archivos tocados. `curso.py` mantiene
  `too-many-lines` y `too-many-locals`, ambos **preexistentes** (1011/1000 y
  25/15 en baseline).
- `djlint`: se ajustó el markup propio. El archivo ya fallaba `--check` antes del
  cambio (29 hunks en baseline); no se reformateó en masa para no mezclar
  formateo con feature.

### Nota sobre el entorno local

Los 5 tests que renderizan template no se pudieron correr en el `.venv` local:
tiene **Python 3.14 con Django 4.2.27**, combinación no soportada, y
`django/template/context.py` revienta en la instrumentación del test client
(`AttributeError: 'super' object has no attribute 'dicts'`). Afecta por igual a
63 tests preexistentes. Se validó el render con `RequestFactory` (que no pasa por
esa instrumentación) y se comparó la suite completa contra baseline:
63F/143P → 68F/152P, es decir **cero regresiones**. Falta correrlos en Docker
(`docker compose exec django pytest VAT/tests.py -k resultados`).
