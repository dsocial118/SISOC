# INET · Buscador por Ciudadano (trayectoria formativa por DNI/CUIL)

**Módulo**: `VAT` (INET) · **Labels sugeridos**: `modulo:vat`, `backend`, `frontend`, `docs`
**Milestone sugerido**: `INET-Buscador-Ciudadano`

Convenciones transversales (no repetir en cada sub-issue): lógica en `VAT/services/`,
views CBV sin lógica (`VAT/views/`), tests en `/tests/` o `VAT/test_*.py` siguiendo el
patrón de `VAT/test_reporte_inscripciones_asistencia.py`, registro del cambio en
`docs/registro/cambios/`, respetar `docs/ia/MODULAR_BOUNDARIES.md` y `docs/ia/STYLE_GUIDE.md`.

---

## 1. Contexto

Hoy el menú **INET** del sidebar ([templates/includes/sidebar/opciones.html:538](templates/includes/sidebar/opciones.html:538))
expone tres entradas:

1. **Centros de Formación Profesional** → `vat_centro_list`
2. **Reporte Inscriptos y Asistencias** → `vat_reporte_inscripciones_asistencias`
3. **Catálogos** (subgrupo)

Ambas vistas están orientadas a la **oferta**: se entra por centro, curso o comisión y se
llega a los inscriptos. El reporte general permite un detalle nominal, pero es un listado
agregado que se filtra por territorio/oferta y se pagina de a 50 —
[VAT/services/reportes_inscripciones_asistencia.py:373](VAT/services/reportes_inscripciones_asistencia.py:373).

No existe la entrada inversa: **dado un ciudadano, ver toda su trayectoria formativa en INET**.

## 2. Problema

Consultas frecuentes de mesa de ayuda, referentes de centro y equipos provinciales del tipo
*"esta persona dice que hizo un curso, ¿en cuáles se anotó, cuáles terminó, cuáles abandonó?"*
se resuelven hoy **corriendo SQL a mano contra la base** (query de referencia en §5). Eso
implica:

- Acceso directo a la base para tareas de consulta operativa.
- Sin control de alcance territorial: la query devuelve el país entero sin importar quién la corre.
- Sin trazabilidad ni auditoría de la consulta.
- Resultado incompleto: la query cubre solo una de las dos rutas de inscripción del modelo (§5.2).

## 3. Objetivo

Agregar en el menú **INET** una cuarta entrada, **"Buscador por Ciudadano"**, que dado un
**DNI o CUIL/CUIT** muestre en una sola pantalla la trayectoria formativa completa del
ciudadano en INET: a qué cursos se anotó, en qué comisión y centro, en qué estado quedó
cada inscripción (cursando / completada / abandonada / rechazada), el resultado final
(aprobado / desaprobado / sin calificar) y su asistencia.

Equivalente funcional de la query de referencia, pero **dentro del sistema**, con permisos,
alcance territorial y exportación.

## 4. Alcance

**Incluye**

- Nueva ruta, vista, service y template en la app `VAT`.
- Nueva entrada en el sidebar INET.
- Búsqueda por documento y por CUIL/CUIT.
- Ficha del ciudadano + resumen agregado + tabla de inscripciones.
- Exportación CSV/XLSX del resultado.
- Respeto estricto del alcance de acceso del usuario (`VAT/services/access_scope.py`).

**No incluye**

- Edición de inscripciones desde esta pantalla (es solo lectura; se enlaza a las vistas existentes).
- Alta de ciudadanos ni consulta RENAPER (ya existe `VAT/services/consulta_renaper/`).
- Datos de otros módulos (comedores, celiaquía, ATM): esta vista es exclusivamente INET/VAT.
- Endpoint público o de API. Si se necesita, va en un issue aparte sobre `VAT/api_views.py`.

## 5. Query de referencia y su traducción

### 5.1 SQL provista por negocio

```sql
SELECT c.nombre, c.apellido, c.documento AS dni, c.email,
       i.estado, cu.nombre AS curso, cc.codigo_comision, cc.nombre AS nombre_comision,
       cen.nombre AS centro, p.nombre AS provincia, l.nombre AS localidad,
       ubi.domicilio AS direccion, ide.valor_identificador AS cue
FROM VAT_inscripcion i
JOIN ciudadanos_ciudadano c ON c.id = i.ciudadano_id
LEFT JOIN VAT_comisioncurso cc ON cc.id = i.comision_curso_id
LEFT JOIN VAT_curso cu ON cu.id = cc.curso_id
LEFT JOIN VAT_centro cen ON cen.id = cu.centro_id
LEFT JOIN core_provincia p ON p.id = cen.provincia_id
LEFT JOIN core_localidad l ON l.id = cen.localidad_id
LEFT JOIN VAT_institucionubicacion ubi ON ubi.id = cc.ubicacion_id
LEFT JOIN VAT_institucionidentificadorhist ide
    ON ide.centro_id = cen.id AND ide.tipo_identificador = 'cue' AND ide.es_actual = 1
WHERE c.documento = 46272601
ORDER BY i.fecha_inscripcion DESC;
```

### 5.2 Diferencias detectadas — ajustes obligatorios en la implementación

La query es correcta como diagnóstico manual, pero **no debe portarse literal**. Siete
correcciones, todas verificables en el repo:

| # | Problema en la SQL | Corrección |
|---|---|---|
| 1 | Solo recorre `comision_curso_id`. `Inscripcion` tiene **dos** FK de comisión: `comision_curso` (ComisionCurso→Curso→Centro) y `comision` (Comision→OfertaInstitucional→Centro) — [VAT/models.py:1689](VAT/models.py:1689). Una inscripción por la ruta `comision` sale con curso/centro/CUE en NULL. | Resolver ambas rutas con `Coalesce`, exactamente como `_base_queryset_for_user` — [VAT/services/reportes_inscripciones_asistencia.py:85](VAT/services/reportes_inscripciones_asistencia.py:85). |
| 2 | No filtra `deleted_at`. `Inscripcion`, `ComisionCurso`, `Curso` y `Centro` usan `SoftDeleteModelMixin` — [core/soft_delete/base.py:74](core/soft_delete/base.py:74). La SQL cruda incluye registros dados de baja lógica. | Usar el manager `objects` del ORM (excluye borrados). |
| 3 | Busca solo por `c.documento`. El requerimiento es **CUIT/DNI**. | Buscar también por `Ciudadano.cuil_cuit` ([ciudadanos/models.py:174](ciudadanos/models.py:174)), normalizando guiones y puntos. |
| 4 | Sin filtro de alcance: devuelve el país entero. | Aplicar `filter_centros_queryset_for_user` — [VAT/services/access_scope.py:189](VAT/services/access_scope.py:189). Ver §8. |
| 5 | `direccion` sale de `ubi` (ubicación de la comisión) pero `localidad` sale de `cen` (localidad del centro): pueden no coincidir. `InstitucionUbicacion` tiene su propia `localidad` — [VAT/models.py:847](VAT/models.py:847). | Tomar domicilio **y** localidad de la misma fuente: la ubicación de la comisión, con fallback al centro. |
| 6 | El join de CUE puede duplicar filas: `unique_together` de `InstitucionIdentificadorHist` es `(centro, tipo_identificador, valor_identificador)` — [VAT/models.py:810](VAT/models.py:810) —, o sea que un centro puede tener más de un CUE con `es_actual=1`. | Traer el CUE con `Subquery(...[:1])` ordenado por `-vigencia_desde`, nunca con `LEFT JOIN` directo. |
| 7 | No devuelve lo que el requerimiento pide sobre "cumplió / abandonó": faltan `resultado_final`, fechas de la comisión, estado de curso/comisión y asistencia. | Ver §7. |

### 5.3 Mapa tabla → modelo

| Tabla SQL | Modelo | Ubicación |
|---|---|---|
| `VAT_inscripcion` | `Inscripcion` | [VAT/models.py:1651](VAT/models.py:1651) |
| `ciudadanos_ciudadano` | `Ciudadano` | [ciudadanos/models.py:128](ciudadanos/models.py:128) |
| `VAT_comisioncurso` | `ComisionCurso` | [VAT/models.py:1098](VAT/models.py:1098) |
| `VAT_curso` | `Curso` | [VAT/models.py:918](VAT/models.py:918) |
| `VAT_centro` | `Centro` | [VAT/models.py:11](VAT/models.py:11) |
| `VAT_institucionubicacion` | `InstitucionUbicacion` | [VAT/models.py:847](VAT/models.py:847) |
| `VAT_institucionidentificadorhist` | `InstitucionIdentificadorHist` | [VAT/models.py:767](VAT/models.py:767) |
| — (no está en la SQL) | `AsistenciaSesion` | [VAT/models.py:1905](VAT/models.py:1905) |

## 6. Ubicación en la UI

Cuarta entrada del bloque INET, después de *Reporte Inscriptos y Asistencias*, en
[templates/includes/sidebar/opciones.html:555](templates/includes/sidebar/opciones.html:555):

```
INET
 ├─ Centros de Formación Profesional
 ├─ Reporte Inscriptos y Asistencias
 ├─ Buscador por Ciudadano        ← NUEVO
 └─ Catálogos
```

Marcado activo por `'vat/buscador-ciudadano/' in pagina_actual`, mismo patrón que las
entradas hermanas.

## 7. Contenido de la pantalla

### 7.1 Formulario de búsqueda

Un solo campo, `q`, que acepta DNI (`46272601`) o CUIL/CUIT (`20-46272601-5`, `20462726015`).
Normalización: quitar puntos, guiones y espacios; si quedan 11 dígitos se busca por
`cuil_cuit` **y** por el documento contenido; si quedan 7–8 dígitos, por `documento`.
El submit es `GET` (URL compartible/marcable), sin datos personales más allá de `q`.

Casos a contemplar:
- Sin resultados de ciudadano → estado vacío con el texto de "no se encontró un ciudadano con ese documento".
- Ciudadano existente sin inscripciones INET → se muestra la ficha con la tabla vacía.
- Más de un ciudadano coincidente (mismo número, distinto `tipo_documento` — la unicidad es
  `documento_unico_key` = tipo+número, [ciudadanos/models.py:263](ciudadanos/models.py:263)) →
  listar candidatos para que el usuario elija.

### 7.2 Ficha del ciudadano

`apellido`, `nombre`, `tipo_documento` + `documento`, `cuil_cuit`, `email`, `telefono`.
Enlace al legajo del ciudadano si el usuario tiene permiso de ciudadanos.

### 7.3 Resumen

Contadores sobre las inscripciones visibles: total, en curso (`inscripta` +
`validada_presencial`), completadas, abandonadas, rechazadas, pre-inscriptas/en espera,
aprobadas, desaprobadas, sin calificar, y % de asistencia global.

### 7.4 Tabla de inscripciones (una fila por inscripción, orden `-fecha_inscripcion`)

| Columna | Origen |
|---|---|
| Fecha de inscripción | `Inscripcion.fecha_inscripcion` |
| Curso | `comision_curso__curso__nombre` ‖ `comision__oferta__nombre_local` ‖ `comision__oferta__plan_curricular__nombre` |
| Comisión (código y nombre) | `comision_curso__codigo_comision` / `__nombre` ‖ `comision__codigo_comision` |
| Período | `ComisionCurso.fecha_inicio` – `fecha_fin` |
| Centro | `...curso__centro__nombre` ‖ `...oferta__centro__nombre` |
| CUE | `InstitucionIdentificadorHist` (`tipo_identificador='cue'`, `es_actual=True`), vía Subquery |
| Provincia / Localidad | centro + ubicación de la comisión (§5.2 #5) |
| Dirección | `InstitucionUbicacion.domicilio` |
| Estado de la inscripción | `Inscripcion.estado` (§7.5) |
| Resultado final | `Inscripcion.resultado_final` (§7.5) |
| Asistencia | presentes / total registrado + % (§7.6) |
| Estado de curso / comisión | `Curso.estado`, `ComisionCurso.estado` |
| Origen | `Inscripcion.origen_canal` |

Cada fila enlaza al detalle de comisión existente.

### 7.5 Semántica de "cumplió / abandonó"

Son **dos ejes distintos** y la pantalla debe mostrarlos por separado; colapsarlos en una
sola columna es un error de lectura frecuente.

Eje 1 — `Inscripcion.estado`, [VAT/models.py:1657](VAT/models.py:1657):

| Valor | Etiqueta | Lectura de negocio |
|---|---|---|
| `pre_inscripta` | Pre-inscripta | Se anotó, sin confirmar |
| `en_espera` | En Espera | Sin cupo |
| `inscripta` | Inscripta | Cursando |
| `validada_presencial` | Validada Presencial | Cursando, presencia validada |
| `completada` | Completada | **Cumplió el cursado** |
| `abandonada` | Abandonada | **Abandonó** |
| `rechazada` | Rechazada | No se efectivizó |

Eje 2 — `Inscripcion.resultado_final`, [VAT/models.py:1678](VAT/models.py:1678):
`aprobado` / `desaprobado` / `NULL` = **sin calificar** (estado inicial, distingue al alumno
pendiente de carga del ya calificado). Renderizar `NULL` como "Sin calificar", nunca vacío.

### 7.6 Asistencia

Por inscripción, contra `AsistenciaSesion` ([VAT/models.py:1905](VAT/models.py:1905)):
`presentes = Count(asistencias, filter=presente=True)`, `ausentes = ... presente=False`,
`% = presentes / (presentes + ausentes)`. Si no hay registros, mostrar "Sin registros",
no `0%`. Mismo criterio que el reporte existente —
[VAT/services/reportes_inscripciones_asistencia.py:247](VAT/services/reportes_inscripciones_asistencia.py:247).

## 8. Alcance de datos y seguridad

**Decisión**: la vista respeta el alcance del usuario. Las inscripciones se filtran por los
centros visibles según `filter_centros_queryset_for_user`
([VAT/services/access_scope.py:189](VAT/services/access_scope.py:189)):

- **SSE / INET Admin Visualizador / superusuario** → trayectoria completa del país.
- **Provincial** → solo inscripciones en centros de su alcance territorial.
- **Referente / revisor de centro** → solo inscripciones en sus centros.

Un referente que busca a un ciudadano ve la ficha y **solo las inscripciones de sus centros**.
No se revela el conteo de inscripciones fuera de alcance (evita inferencia de trayectoria por
diferencia). Sí se muestra una leyenda fija indicando que el resultado está limitado al
alcance del usuario, para que no se lea como "no hizo ningún otro curso".

**Permisos de ruta**: `permissions_any_required(["VAT.view_inscripcion", "VAT.view_centro"])`,
mismo criterio que la ruta del reporte — [VAT/urls.py:165](VAT/urls.py:165).

**Datos personales**: el parámetro `q` viaja en querystring (es el criterio de búsqueda, no
un dato derivado); nombre, email y teléfono nunca deben ir a la URL. Ver `docs/ia/SECURITY_AI.md`.

## 9. Diseño técnico

```
VAT/services/buscador_ciudadano_service.py   ← nuevo: normalización, lookup, queryset, export
VAT/views/buscador_ciudadano.py              ← nuevo: CBV (TemplateView + LoginRequiredMixin), sin lógica
VAT/templates/vat/buscador/ciudadano.html    ← nuevo
VAT/urls.py                                  ← nueva ruta 'vat/buscador-ciudadano/'
templates/includes/sidebar/opciones.html     ← nueva entrada de menú
```

- **Service**: `normalizar_identificador(q)`, `buscar_ciudadanos(q)`,
  `build_trayectoria_queryset(user, ciudadano)`, `build_resumen(qs)`,
  `export_trayectoria_to_csv/_to_excel(user, ciudadano)`. Reusar los `Coalesce` de
  `_base_queryset_for_user` en vez de duplicarlos: si hace falta, extraer esa función a un
  helper compartido — es la única pieza con riesgo real de divergencia entre las dos vistas.
- **View**: espeja `ReporteInscriptosAsistenciasView`
  ([VAT/views/reporte.py:21](VAT/views/reporte.py:21)), incluido el manejo de `?export=`.
- **Template**: extiende `includes/main.html`, estética consistente con
  `vat/reportes/inscripciones_asistencia.html`.
- **Export**: cabeceras y formato alineados con `VAT/services/nomina_export.py`.

## 10. Criterios de aceptación

- [ ] La entrada **"Buscador por Ciudadano"** aparece en el menú INET, entre *Reporte Inscriptos y Asistencias* y *Catálogos*, y solo para usuarios con permiso.
- [ ] Buscar por DNI (`46272601`) y por CUIL con y sin guiones (`20-46272601-5`, `20462726015`) devuelve el mismo ciudadano.
- [ ] El resultado incluye inscripciones creadas por **ambas** rutas (`comision_curso` y `comision`); un caso de cada una en los tests.
- [ ] Las inscripciones y comisiones con borrado lógico **no** aparecen.
- [ ] Un centro con dos CUE marcados `es_actual` **no** duplica filas.
- [ ] Estado de inscripción y resultado final se muestran en columnas separadas; `resultado_final` nulo se lee "Sin calificar".
- [ ] Una inscripción sin registros de asistencia muestra "Sin registros", no `0%`.
- [ ] Referente de centro A no ve la inscripción del mismo ciudadano en centro B; SSE ve ambas.
- [ ] Ciudadano inexistente y ciudadano sin inscripciones muestran estados vacíos distintos y explícitos.
- [ ] Documento presente con dos `tipo_documento` distintos ofrece elegir entre candidatos.
- [ ] Export CSV y XLSX respetan el alcance y contienen las mismas filas que la pantalla.
- [ ] La consulta completa se resuelve en un número acotado de queries (sin N+1 al recorrer filas en el template).

## 11. Tests

Archivo `VAT/test_buscador_ciudadano.py`, siguiendo el armado de fixtures de
[VAT/test_reporte_inscripciones_asistencia.py](VAT/test_reporte_inscripciones_asistencia.py)
(`_build_comision_curso`, `_grant_referente_role`).

1. `test_normaliza_cuil_y_dni` — variantes con guiones/puntos/espacios.
2. `test_incluye_ambas_rutas_de_inscripcion` — `comision_curso` y `comision`.
3. `test_excluye_soft_deleted`.
4. `test_no_duplica_por_cue_multiple`.
5. `test_scope_referente_no_ve_otros_centros`.
6. `test_scope_sse_ve_todo`.
7. `test_resumen_cuenta_estados_y_resultados`.
8. `test_asistencia_sin_registros_no_es_cero`.
9. `test_export_csv_respeta_scope`.
10. `test_ciudadano_inexistente_devuelve_estado_vacio`.
11. Smoke de ruta y permisos (`403` sin permiso, `200` con permiso).

## 12. Performance

- `ciudadanos_ciudadano.documento` ya tiene índice ([ciudadanos/models.py:274](ciudadanos/models.py:274)); `cuil_cuit` **no** — si el volumen de búsquedas por CUIL lo justifica, evaluar índice en un issue aparte (implica migración).
- Un ciudadano tiene decenas de inscripciones como máximo: no se necesita paginación en la tabla; sí `select_related` completo para evitar N+1.
- CUE por `Subquery`, no por join (§5.2 #6).

## 13. Documentación y registro

- Nota en `docs/registro/cambios/2026-XX-XX-inet-buscador-por-ciudadano.md`.
- Actualizar `docs/vat/manual_usuario.md` con la nueva pantalla y la aclaración de alcance de §8.
- Si se extrae el queryset base a un helper compartido, dejar la decisión en `docs/registro/decisiones/`.

## 14. División sugerida en sub-issues

| # | Título | Labels |
|---|---|---|
| 1 | Service de búsqueda y trayectoria (`buscador_ciudadano_service`) + tests | `backend` |
| 2 | Vista, ruta, permisos y entrada de sidebar | `backend`, `frontend` |
| 3 | Template: ficha, resumen y tabla de inscripciones | `frontend` |
| 4 | Exportación CSV/XLSX | `backend` |
| 5 | Manual de usuario y registro de cambios | `docs` |
