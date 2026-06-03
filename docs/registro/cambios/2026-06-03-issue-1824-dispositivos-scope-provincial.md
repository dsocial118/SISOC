# 2026-06-03 - Dispositivos (Data Calle): alcance territorial provincial

## Contexto

HOTFIX del issue [#1824](https://github.com/dsocial118/SISOC/issues/1824). El módulo
`dispositivos/` (rutas `/dispositivos/` y `/dispositivos/crear`) **no** aplicaba el
alcance territorial del usuario: las cuatro vistas CRUD usaban
`get_dispositivos_queryset()` sin filtrar, y el formulario ofrecía todas las
provincias/municipios. Un usuario provincial podía listar, ver, editar y crear
dispositivos de cualquier provincia.

Regla pedida:

1. Usuario con provincia asignada: solo lista/ve/edita/crea dispositivos dentro de su
   provincia.
2. Si además tiene municipio (y/o localidad) configurado, se restringe a esa selección.
3. Usuario sin provincia asignada y/o admin: interactúa con todos los registros.

## Cambios aplicados

### Lógica de alcance (nueva, centralizada en `services.py`)

- **`apply_dispositivos_scope(queryset, user)`**
  ([dispositivos/services.py](../../../dispositivos/services.py)): acota el queryset al
  alcance del usuario. No autenticado → vacío; superusuario o usuario no provincial →
  sin restricción; usuario provincial → `provincia` (+ `municipio` cuando el alcance lo
  precisa). Un usuario provincial sin alcances configurados no ve nada.
- **`get_dispositivos_geography_scope(user)`** (nueva): devuelve el mapa
  `provincia_id -> set(municipio_id) | None` que usa el formulario para limitar los
  desplegables. `None` = sin restricción.

### Vistas (control de acceso de lectura y escritura)

- **`DispositivoListView`**: aplica `apply_dispositivos_scope` antes de los filtros
  avanzados y la búsqueda libre.
- **`DispositivoDetailView` / `DispositivoUpdateView` / `DispositivoDeleteView`**:
  `get_queryset()` devuelve el queryset acotado, por lo que un pk fuera de alcance
  responde **404** (también vía POST directo).
- **`DispositivoCreateView` / `DispositivoUpdateView`**: `get_form_kwargs()` pasa el
  usuario al formulario.

### Formulario (control de acceso en alta/edición)

- **`DispositivoForm`** ([dispositivos/forms.py](../../../dispositivos/forms.py)): toma
  `user` por kwarg; `_configure_geography_fields()` restringe el `queryset` de
  `provincia` y `municipio` al alcance. Como `ModelChoiceField` valida contra su
  `queryset`, un POST con una provincia/municipio fuera de alcance es rechazado por la
  propia validación del form (defensa server-side, no solo UI). Si en el `data` llega una
  provincia fuera del alcance, el `queryset` de `municipio` queda vacío (no ofrece
  municipios de esa provincia), además del rechazo del campo `provincia`.

### Limpieza

- Se elimina `get_dispositivo_or_404` de `services.py`: estaba **sin uso** y devolvía un
  objeto sin acotar por alcance (footgun si se cableaba a una vista). Las vistas resuelven
  el objeto vía `get_queryset()` acotado.

## Decisiones / supuestos

- **Localidad → municipio**: el modelo `Dispositivo` tiene `provincia` y `municipio`,
  **no** `localidad`. Un alcance a nivel localidad se respeta hasta su **municipio** (la
  granularidad más fina que admite el modelo). Por eso no se reutiliza directamente
  `apply_territorial_scope` con `localidad_lookup`, que descartaría esos alcances
  (`build_territorial_scope_q` hace `continue`) y dejaría sin acceso al usuario; se
  construye el `Q` a medida.
- **Delete acotado**: el issue menciona listar/ver/editar/crear; se incluye también
  `DispositivoDeleteView` para no dejar un hueco (borrado fuera de provincia por POST
  directo).
- **Usuarios provinciales = territoriales**: se asume el modelo documentado
  (`Profile.es_usuario_provincial` + `ProfileTerritorialScope`), consistente con
  celiaquía y centrodeinfancia. Un usuario provincial sin alcances no ve ni puede crear
  dispositivos.
- **Sin migración**: no se tocan modelos; el cambio es de vistas/servicios/formulario.
- **Compatibilidad**: `DispositivoForm` sin `user` (instanciación directa, p. ej. tests
  legacy) conserva el comportamiento previo sin restricción.

## Validación

- `black --check`: OK sobre los archivos tocados.
- `pylint` (archivos cambiados): 10.00/10.
- `manage.py check`: sin issues (wiring/imports, sin import circular).
- `pytest dispositivos/tests/`: **43 passed** (Docker one-off, SQLite). 14 tests nuevos
  en [test_dispositivos_views.py](../../../dispositivos/tests/test_dispositivos_views.py):
  listado por provincia y por municipio, alcance localidad → municipio, multi-provincia,
  admin/superusuario y usuario sin provincia ven todo, usuario provincial sin alcance no
  ve nada, detalle 200 dentro / 404 fuera, editar y eliminar 404 fuera, el form de alta
  restringe provincias, rechaza el POST fuera de alcance y deja vacío el municipio de una
  provincia fuera de alcance.
- `makemigrations --check` / `djlint`: N/A (sin cambios de modelo/migración ni
  templates).

## Cómo probar manualmente

1. Usuario provincial con alcance en provincia A.
2. `/dispositivos/` muestra solo dispositivos de A; los de otra provincia no aparecen.
3. Abrir el detalle/editar de un dispositivo de otra provincia por URL directa → 404.
4. `/dispositivos/crear`: el desplegable de provincia solo ofrece A (y municipio, los de
   A o el municipio configurado). Forzar por POST otra provincia → el form no valida.
5. Usuario con municipio configurado: solo ve/crea dentro de ese municipio.
6. Admin / usuario sin provincia: ve y opera sobre todos los dispositivos.
