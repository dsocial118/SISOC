# Plan — Issue #1793 "Fixes Celiaquia - Provincia"

Rama propuesta: `codex/issue-1793-celiaquia-provincia`
Fecha: 2026-06-01
Estado: pendiente de aprobacion.
Autor del issue: jcamiloparra. Asignado: juanikitro.

## Contexto

El issue [#1793](https://github.com/dsocial118/SISOC/issues/1793) reporta 5 sintomas
en el modulo `celiaquia`, todos derivados de **una unica causa raiz**: el codigo
asume "una provincia por usuario", pero se introdujo la capacidad de asignar
**multiples provincias (y municipios) por usuario** via `ProfileTerritorialScope`
(migracion `users/0030`). El campo legacy `Profile.provincia` dejo de poblarse en
esos casos y toda la cadena `expediente.usuario_provincia.profile.provincia`
devuelve `None`.

## Causa raiz

`Expediente` no tiene provincia propia: la expone como property derivada del
perfil del usuario creador.

```python
# celiaquia/models.py:148-153
@property
def provincia(self):
    try:
        return self.usuario_provincia.profile.provincia  # FK legacy
    except Exception:
        return None
```

El legacy `Profile.provincia` solo se rellena cuando el usuario tiene
**exactamente 1 scope territorial sin municipio**:

```python
# users/territorial_scope.py:261-266
legacy_provincia_id = None
if len(scopes_data) == 1 and not scopes_data[0]["municipio_id"]:
    legacy_provincia_id = scopes_data[0]["provincia_id"]
...
profile.provincia_id = legacy_provincia_id
```

Por lo tanto, con 2+ provincias **o** con 1 provincia + municipio especifico,
`Profile.provincia = None` -> `expediente.provincia = None`. Ese `None` se propaga
a la grilla, el detalle, el cruce SINTYS y los filtros de cupo/pago.

**La fuente de verdad correcta ya existe**: cada `Ciudadano` guarda `provincia`,
`municipio` y `localidad` propios cargados desde el Excel del expediente
([ciudadano_service/impl.py:193-195](../../celiaquia/services/ciudadano_service/impl.py)),
y el codigo **ya tiene el patron** para derivar territorio desde el ciudadano en
`_apply_provincial_expediente_scope`
([expediente.py:533-546](../../celiaquia/views/expediente.py)), que filtra por
`expediente_ciudadanos__ciudadano__provincia_id` / `municipio_id` / `localidad_id`.
Los lugares rotos simplemente nunca se migraron a ese patron.

## Hallazgos previos clave

- `Expediente.usuario_provincia` -> FK a `User` (creador). No hay FK a provincia
  ([models.py:87-89](../../celiaquia/models.py)).
- Property rota: [models.py:148-153](../../celiaquia/models.py).
- `Ciudadano.provincia/municipio/localidad` -> FK directas
  (ciudadanos/models.py). Cadena: `Localidad.municipio.provincia`.
- `ExpedienteCiudadano.ciudadano` -> FK; related_name del expediente:
  `expediente_ciudadanos` ([models.py:204-208](../../celiaquia/models.py)).
- Patron correcto ya existente: `apply_territorial_scope` y
  `_apply_provincial_expediente_scope`
  ([expediente.py:533-546](../../celiaquia/views/expediente.py),
  [users/territorial_scope.py:318-346](../../users/territorial_scope.py)).
- Codigo muerto que anticipa la solucion denormalizada:
  `if hasattr(Expediente, "provincia_id")` en
  [expediente_service/impl.py:170-175](../../celiaquia/services/expediente_service/impl.py)
  (hoy nunca entra: `Expediente` no tiene campo `provincia_id`).

### Mapa sintoma -> codigo

| # | Sintoma | Ubicacion |
|---|---|---|
| 1 | Provincia "none" en grilla y detalle | property [models.py:148](../../celiaquia/models.py); queryset [expediente.py:648-685](../../celiaquia/views/expediente.py); [expediente_list.html:80](../../celiaquia/templates/celiaquia/expediente_list.html); [expediente_detail.html:87,184](../../celiaquia/templates/celiaquia/expediente_detail.html) |
| 2 | Modal "Buscar Localidades": municipio del usuario no se ve bien | `LocalidadesLookupView` [expediente.py:588-635](../../celiaquia/views/expediente.py); resolucion fragil `_user_provincia` [expediente.py:509-523](../../celiaquia/views/expediente.py); modal [expediente_form.html:68-140](../../celiaquia/templates/celiaquia/expediente_form.html) |
| 3 | SINTYS bloquea el cruce | [cruce_service/impl.py:624-629](../../celiaquia/services/cruce_service/impl.py) (usa `expediente.provincia`); `metrics_por_provincia` [cupo_service/impl.py:37-44](../../celiaquia/services/cupo_service/impl.py) |
| 4 | "Error al cargar expediente" sin accion | [expediente.py:1238-1246](../../celiaquia/views/expediente.py) (`cupo_error` espurio) |
| 5 | Otras referencias a `profile.provincia` | cupo_service 49,70,87,178,205,295,358,447; cupo.py 90,99,112,193; pago_service 67; expediente.py 340,511; pdf_prd_cruce.html 267 |

## Decision de diseno

Hay dos caminos. Este plan **recomienda el Enfoque A** y deja el B documentado
como evolucion futura.

- **Enfoque A (recomendado): derivar del ciudadano, sin migracion.**
  La provincia del expediente y los filtros se calculan desde el territorio de los
  ciudadanos importados. Es lo que pide literalmente el issue ("derivar del
  Municipio y/o Localidad del Excel"), es consistente con
  `_apply_provincial_expediente_scope`, y respeta AGENTS.md (cambios chicos,
  locales, sin migracion ni backfill).

- **Enfoque B (alternativa): denormalizar `Expediente.provincia` como FK real**,
  poblada en import desde el territorio de los ciudadanos, con migracion +
  backfill, y repuntar todos los filtros a `expediente__provincia`. Resuelve el
  N+1 de la grilla de forma natural y el codigo muerto de
  [expediente_service:170](../../celiaquia/services/expediente_service/impl.py)
  ya lo anticipaba. Mayor alcance; recomendado solo si se necesita performance o
  consistencia fuerte mas adelante.

**Regla multi-provincia (supuesto a confirmar):** un expediente puede, en teoria,
tener ciudadanos de mas de una provincia. Para mostrar/validar se usa la
**provincia dominante** (la mas frecuente entre sus ciudadanos). Alternativa mas
estricta: validar homogeneidad al importar y rechazar mezclas. Ver Supuestos.

## Seccion 0 — Helper de derivacion (nucleo compartido)

Nuevo helper, idealmente en `celiaquia/services/expediente_service/impl.py` (o
`celiaquia/utils.py`):

- `provincias_de_expediente(expediente) -> set[int]`: ids distintos de
  `expediente.expediente_ciudadanos.values_list("ciudadano__provincia_id", flat=True)`
  (excluyendo `None`).
- `provincia_principal_de_expediente(expediente) -> Provincia | None`: la dominante
  (o la unica). `None` si el expediente no tiene ciudadanos con provincia.

Todos los puntos siguientes consumen este helper, para que la regla viva en un
solo lugar.

## Seccion 1 — Grilla y detalle (puntos 1 y 4)

### Property

Reescribir `Expediente.provincia` ([models.py:148](../../celiaquia/models.py)) para
delegar en `provincia_principal_de_expediente(self)` con fallback al legacy
`usuario_provincia.profile.provincia` (compatibilidad hacia atras). Quitar el
`except Exception` mudo (acotar a las excepciones reales).

### Grilla (evitar N+1)

En `ExpedienteListView.get_queryset`
([expediente.py:647-685](../../celiaquia/views/expediente.py)) **no** depender de la
property por fila. Anotar la provincia derivada con un `Subquery` sobre
`ExpedienteCiudadano` (primer/maximo `ciudadano__provincia__nombre`) y exponerla al
template. Actualizar [expediente_list.html:80](../../celiaquia/templates/celiaquia/expediente_list.html)
para leer la anotacion en vez de `exp.provincia`.

### Detalle / cupo_error espurio

En el detalle ([expediente.py:1234-1246](../../celiaquia/views/expediente.py)),
resolver `prov` con el helper. Si sigue siendo `None` por falta de ciudadanos
cargados, **no** mostrar "No se pudo determinar la provincia del expediente" como
error visible en la carga inicial: degradar a estado neutro (sin cupo aun) y
mostrar el aviso solo cuando corresponda. Corregir
[expediente_detail.html:87,184](../../celiaquia/templates/celiaquia/expediente_detail.html)
y [pdf_prd_cruce.html:267](../../celiaquia/templates/celiaquia/pdf_prd_cruce.html)
para usar la provincia derivada.

## Seccion 2 — Modal "Buscar Localidades" (punto 2)

El modal sirve para que el usuario vea los **codigos** (ids) de
provincia/municipio/localidad y los cargue en el Excel
([expediente_form.html:68-140](../../celiaquia/templates/celiaquia/expediente_form.html)).
Lo alimenta `LocalidadesLookupView`
([expediente.py:588-635](../../celiaquia/views/expediente.py)).

Problema: para un usuario provincial con municipio configurado,
`_user_provincia(user)` ([expediente.py:509-523](../../celiaquia/views/expediente.py))
es fragil. Devuelve la provincia solo si hay `Profile.provincia` o un unico scope
de provincia **completa**; con municipio especifico devuelve `None` y cae al
fallback `apply_territorial_scope`, y en escenarios mixtos (un scope full-province
+ otro con municipio) puede cortocircuitar y filtrar por una sola provincia,
perdiendo el resto. El resultado es que el municipio del usuario no se refleja bien
en el listado.

Cambios:

1. Reemplazar la rama `if prov: ... else: ...`
   ([expediente.py:600-611](../../celiaquia/views/expediente.py)) por **siempre**
   `apply_territorial_scope` con los lookups del propio modelo `Localidad`
   (`municipio__provincia_id`, `municipio_id`, `id`). Asi un usuario con municipio
   ve exactamente las localidades de su(s) municipio(s) y uno con provincia
   completa ve toda la provincia; coordinador/admin siguen sin restriccion.
2. Verificar el JS del modal (en `static/`, buscar el fetch a
   `expediente_localidades_lookup`) para confirmar que la columna/selector de
   municipio se renderiza desde `municipio_nombre`/`municipio_id` del JSON.
3. Confirmar el comportamiento esperado contra las capturas del issue (si el
   municipio debe pre-seleccionarse o solo filtrarse).

## Seccion 3 — Cupo y Pago (filtros)

Repuntar los filtros que cuelgan del perfil del usuario hacia el territorio del
ciudadano (consistente con `_apply_provincial_expediente_scope`):

- `cupo_service/impl.py` lineas 49, 70, 87:
  `expediente__usuario_provincia__profile__provincia=provincia`
  -> `ciudadano__provincia=provincia` (el queryset ya es sobre
  `ExpedienteCiudadano`, que tiene FK directa a `ciudadano`).
- `cupo.py` lineas 90, 99, 112: idem.
- `pago_service/impl.py` linea 67: idem.
- Revisar los `getattr(legajo.expediente.usuario_provincia.profile, "provincia", None)`
  (cupo_service 178, 295, 358, 447) y `_get_legajo_validado`
  ([cupo.py:192-196](../../celiaquia/views/cupo.py)): la validacion "el legajo
  pertenece a la provincia" debe compararse contra `legajo.ciudadano.provincia_id`,
  no contra el perfil del creador.

Nota: el cupo es por provincia de **residencia del beneficiario**, por lo que
filtrar por `ciudadano.provincia` es ademas semanticamente mas correcto que por la
provincia del usuario creador.

## Seccion 4 — Cruce SINTYS (punto 3, el mas critico: bloquea el resto del flujo)

En `procesar_cruce_por_cuit`
([cruce_service/impl.py:624-629](../../celiaquia/services/cruce_service/impl.py)):

- Resolver la provincia con `provincia_principal_de_expediente(expediente)` (helper
  Seccion 0) en vez de `expediente.provincia` legacy.
- Si el expediente abarca varias provincias, validar cupo por cada provincia
  involucrada (o por la dominante, segun la regla confirmada).
- Mejorar el mensaje: distinguir "no se pudo determinar la provincia del
  expediente" (no hay ciudadanos con territorio) de "la provincia X no tiene cupo
  configurado". El mensaje actual ("No hay cupo configurado...") es enganoso cuando
  el problema real es la provincia `None`.
- Aplicar el mismo criterio a la segunda llamada
  ([cruce_service/impl.py:~832](../../celiaquia/services/cruce_service/impl.py)).

## Seccion 5 — Barrido de referencias (punto 5)

Punto 5 del issue: corregir toda referencia a la provincia derivada del usuario.
Ademas de lo anterior:

- `expediente.py:340` (`_resolver_provincia_id_registro_erroneo`) y `expediente.py:511`
  (`_user_provincia`): unificar con el helper / scopes.
- Limpiar el codigo muerto `hasattr(Expediente, "provincia_id")` en
  [expediente_service/impl.py:170-175](../../celiaquia/services/expediente_service/impl.py)
  (eliminar si se va por Enfoque A; convertir en asignacion real si se va por B).
- `grep` de cierre por `profile__provincia` y `profile.provincia` en `celiaquia/`
  para no dejar rutas sin migrar.

## Orden de implementacion

1. **Seccion 0** (helper) — base sin breaking changes.
2. **Seccion 4** (SINTYS) — desbloquea el flujo completo, habilita pruebas E2E.
3. **Seccion 3** (cupo/pago) — repunte de filtros.
4. **Seccion 1** (grilla/detalle) — UI + anotacion anti N+1.
5. **Seccion 2** (modal localidades) — independiente; cerrar al final.
6. **Seccion 5** (barrido) — limpieza y verificacion de que no queden referencias.

Cada seccion = 1 commit revisable. Si el alcance crece (p. ej. si se elige
Enfoque B), separar la migracion + backfill en su propio commit.

## Archivos clave

| Archivo | Cambio |
|---|---|
| `celiaquia/services/expediente_service/impl.py` | + helper de derivacion; limpiar codigo muerto |
| `celiaquia/models.py` | reescribir property `Expediente.provincia` |
| `celiaquia/views/expediente.py` | queryset grilla (anotacion), `LocalidadesLookupView`, detalle/cupo_error, `_user_provincia`, `_resolver_provincia_id_registro_erroneo` |
| `celiaquia/services/cruce_service/impl.py` | derivar provincia para SINTYS + mensajes |
| `celiaquia/services/cupo_service/impl.py` | repuntar filtros a `ciudadano__provincia` |
| `celiaquia/views/cupo.py` | repuntar filtros + `_get_legajo_validado` |
| `celiaquia/services/pago_service/impl.py` | repuntar filtro de nomina |
| `celiaquia/templates/celiaquia/expediente_list.html` | leer provincia anotada |
| `celiaquia/templates/celiaquia/expediente_detail.html` | provincia derivada |
| `celiaquia/templates/celiaquia/pdf_prd_cruce.html` | provincia derivada |
| `static/.../*localidades*.js` (a ubicar) | render municipio en el modal |

## Validacion

Manual (post-cambio), idealmente con un usuario provincial multi-provincia y otro
con municipio especifico:

1. **Punto 1**: grilla `/celiaquia/expedientes/` muestra la provincia derivada del
   Excel (no "none"); el detalle muestra la misma provincia.
2. **Punto 3/4**: abrir un expediente como `/celiaquia/expedientes/<id>/` no muestra
   el cartel de provincia espurio; el cruce SINTYS procede (no se bloquea con "no
   hay cupo").
3. **Punto 2**: con usuario de municipio especifico, el modal "Buscar Localidades"
   lista las localidades del municipio correcto y muestra el municipio.
4. **Cupo/Pago**: el detalle de cupo por provincia y la nomina muestran los legajos
   esperados para usuarios multi-provincia.

Automatizada (extender, hoy asumen `profile.provincia` unico):
- `celiaquia/tests/test_expediente_list.py`, `test_expediente_detail.py`,
  `test_cruce_service.py`, `test_pago_expediente_list.py`,
  `test_localidades_lookup.py` — agregar casos multi-provincia y municipio.
- `powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 validate`

## Registro

Al cerrar la PR:
- `docs/registro/cambios/2026-06-01-issue-1793-celiaquia-provincia.md`
- Si se adopta el Enfoque B (FK + migracion):
  `docs/registro/decisiones/2026-06-01-expediente-provincia-denormalizada.md`

## Supuestos

1. **Provincia dominante** para expedientes con ciudadanos de varias provincias.
   Si el negocio exige que un expediente sea de una sola provincia, cambiar a
   validacion de homogeneidad en import (rechazar mezclas) — decision a confirmar
   con el equipo funcional.
2. `Ciudadano.provincia_id` esta poblado en la importacion (lo setea
   `ciudadano_service`). Si hubiera ciudadanos sin provincia, usar
   `ciudadano__municipio__provincia` como fuente secundaria.
3. El sintoma exacto del punto 2 (municipio "no se visualiza correctamente") se
   confirma contra las capturas del issue; la correccion propuesta (filtrar el
   lookup por scopes territoriales completos) cubre las variantes conocidas.
4. Se prioriza el Enfoque A (sin migracion). El Enfoque B queda como evolucion si
   se requiere performance/consistencia fuerte.
