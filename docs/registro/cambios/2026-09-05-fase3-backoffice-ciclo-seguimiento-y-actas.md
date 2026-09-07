# 2026-09-05 — Fase 3 territoriales/app: paridad del backoffice con lo que carga la app

Rama `pwanueva-v3` (apilada sobre `pwanueva-v2`, PR #2432).

## Contexto

La fase 2 (N14–N19) dejó el modelo y la API para que la app cargue N instancias
del ciclo de seguimiento (primer, posterior, virtual, acta de excepción), la
revisión del coordinador y las actas complementarias extraordinarias. El
backoffice, en cambio, seguía pensado para "un primer seguimiento por
relevamiento": no se podían crear ni editar las instancias nuevas, no se podía
revisar un seguimiento, las actas complementarias no se veían, y las pantallas
de detalle/borrado del seguimiento resolvían por relevamiento (con dos
instancias daban `MultipleObjectsReturned` → 500).

## Qué cambia (visible)

- **Popup "Agregar" del listado de relevamientos:** además de "Primer
  seguimiento" ahora ofrece "Seguimiento posterior", "Seguimiento virtual" y
  "Acta de excepción". El primer seguimiento sigue siendo único por ciclo
  (`numero_orden=1`); las demás instancias toman el siguiente número libre. El
  botón queda disponible aunque el relevamiento ya tenga instancias.
- **El ancla creada desde el popup queda asignada al territorial**
  (`territorial_user`), que es lo que la API usa para mostrarle el trabajo en
  la app. Antes solo se guardaba el uid.
- **Rutas por instancia:** `…/relevamiento/<rel>/seguimiento/<pk>/` (detalle,
  `editar`, `eliminar`, `revision`). Las rutas históricas
  `…/primer-seguimiento/` siguen funcionando y resuelven a la primera instancia
  del ciclo.
- **Detalle del relevamiento:** tabla "Ciclo de seguimiento" con todas las
  instancias (tipo, número, estado, validación, origen, GESTIONAR) y acciones
  Ver / Editar / Eliminar por fila.
- **Detalle de la instancia:** navegación entre instancias del ciclo, badges de
  validación y origen, botón **Revisar** (Validado / A subsanar con
  observaciones obligatorias, mismo criterio que el relevamiento) y botón
  **Editar** habilitado.
- **Edición completa de la instancia:** datos raíz, los 17 bloques de
  `BLOQUES_SEGUIMIENTO` (un `ModelForm` por bloque; los bloques inexistentes se
  crean solo si se cargó algo) y la tabla de prestaciones (formset inline).
- **Actas complementarias extraordinarias:** card propia en el listado de
  relevamientos del comedor, con alta, detalle, edición (con formset de
  prestaciones día × tipo) y borrado. Si no se elige técnico, queda el usuario
  que carga.
- **Origen:** badge "App" en listados y detalles para lo que cargó el
  territorial desde la app; lo creado en el backoffice queda `origen=sisoc`.

## Permisos

- Rutas nuevas: `relevamientos.change_primerseguimiento` (editar),
  `relevamientos.delete_primerseguimiento` (eliminar),
  `relevamientos.review_relevamiento` (revisar, mismo permiso que el
  relevamiento), `relevamientos.add/change/delete_actacomplementaria`.
- Semilla de grupos: los grupos que ya tenían `change_relevamiento`
  ("Comedores total" y el grupo administrador de comedores) reciben además
  `change/delete_primerseguimiento` y `add/change/delete_actacomplementaria`.
  "Revisor Relevamientos" no cambia (ver + revisar).

## Decisiones

- **La API de la app no cambia.** Todo es backoffice; el contrato documentado
  en `SISOC-CONTRATO-CAMPOS.md` sigue vigente.
- Los formularios por bloque se generan con `modelform_factory` sobre los
  mismos modelos que consume la API, para no mantener dos definiciones de los
  ~150 campos. `referente` se excluye del formulario raíz (FK a todos los
  referentes: un `<select>` inviable en prod).
- La edición desde el backoffice **no reenvía a GESTIONAR** (la integración
  está apagada tras el corte de AppSheet).
- El helper de revisión del coordinador se unificó (`aplicar_revision_coordinador`)
  y lo usan tanto el relevamiento como las instancias.

## Tests

- `tests/test_seguimiento_instancias_backoffice.py` (servicio `create_instancia`).
- `tests/test_backoffice_seguimientos_actas.py` (detalle por instancia, ruta
  histórica con N instancias, edición, revisión, ABM de actas, listado).
- Ajustados: `comedores/tests.py` (el popup ya no rechaza el segundo
  seguimiento), `tests/test_relevamientos_web_views_unit.py` (stubs con
  `seguimientos`/`origen`).
