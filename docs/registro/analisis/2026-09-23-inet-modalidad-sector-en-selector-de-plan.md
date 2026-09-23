# REQ — Modalidad y Sector siguen visibles en el selector de Plan Curricular

| | |
|---|---|
| **Tipo** | Corrección / depuración funcional |
| **Sistema / Módulo** | SISOC — INET/VAT, alta y detalle de Curso |
| **Estado** | Implementado |
| **Relacionado** | Complementa el REQ #2457 (PR #2512, ya mergeado) |

## Situación actual

El PR #2512 quitó las columnas y el filtro de Modalidad/Sector de la tabla del
modal "Seleccionar Plan Curricular". Pero los valores **siguen apareciendo** en
el desplegable "Plan curricular" del modal *Nuevo Curso* y en otras pantallas,
porque no vienen del template sino de la representación en texto del modelo.

`VAT/models.py` → `PlanVersionCurricular.__str__()` arma la etiqueta así:

- con nombre: `"{nombre} - {modalidad_cursada}"`
- sin nombre, con título: `"{titulo_referencia} - {modalidad_cursada}"`
- sin ninguno de los dos: `"{sector} - {modalidad_cursada}"`

Es decir, **siempre** agrega la modalidad y, en el tercer caso, también el
sector. Como es el `__str__` del modelo, se propaga a todo lugar donde el plan
se renderiza como texto.

## Objetivo

Que ni Modalidad ni Sector se muestren al usuario en el alta de curso ni en las
vistas asociadas, sin eliminar los campos ni los datos.

## Alcance

**Incluye** la etiqueta del modelo y las pantallas donde se propaga:

| Ubicación | Detalle |
|---|---|
| `VAT/models.py` | `PlanVersionCurricular.__str__()` (origen del problema) |
| Modal *Nuevo Curso* | Opciones del desplegable `plan_estudio` (`ModelChoiceField`) |
| `curso/curso_detail.html:251,273` | Subtítulo y dato "Plan de estudio" |
| `oferta_institucional/oferta_detail.html:41` | Plan de la oferta |
| `oferta_institucional/oferta_list.html:42` | Columna y `data-plan` del listado |
| `comision_curso_wizard/step3_confirmacion.html:30` | Resumen de confirmación |

**No incluye:** los catálogos de gestión (Sector, Subsector, Modalidad de
Cursado y Plan Curricular), donde esos campos son atributos obligatorios para
definir un plan. Tampoco se toca la base de datos.

## Requerimiento funcional

1. Quitar Modalidad y Sector de la etiqueta visible del plan curricular.
2. La etiqueta pasa a identificar el plan por su **normativa** en lugar de la
   modalidad. Es el criterio que ya usa el área para diferenciarlos: en el
   listado conviven varios planes con el mismo nombre (p. ej. tres "Artesanías
   y Manualidades") que sólo se distinguen por la normativa.
3. No modificar el modelo de datos: `sector`, `subsector` y `modalidad_cursada`
   siguen existiendo y se siguen cargando.
4. El desplegable se ordena por nombre y normativa, que es lo que muestra la
   etiqueta. Antes se ordenaba por sector y modalidad: al dejar de verse, la
   lista habría quedado en un orden que parece aleatorio.

## Criterios de aceptación

- [ ] El desplegable "Plan curricular" del modal *Nuevo Curso* no muestra
      Modalidad ni Sector.
- [ ] Tampoco aparecen en el detalle de curso, el detalle y listado de oferta,
      ni el paso de confirmación del wizard de comisión.
- [ ] Los planes se distinguen entre sí por su normativa en el desplegable.
- [ ] Se puede crear y editar un curso normalmente, eligiendo el plan correcto.
- [ ] Los catálogos de gestión siguen permitiendo definir un plan con sector,
      subsector y modalidad.

## Riesgos

- `__str__` se usa también en el admin de Django y en mensajes/logs. Cambiarlo
  altera esas representaciones; hay que confirmar que ninguna lógica compare o
  parsee ese texto.
- Planes sin normativa cargada quedarían con etiquetas idénticas entre sí. Hay
  que verificar en el relevamiento cuántos hay y definir un respaldo (por
  ejemplo, mostrar el título de referencia).
