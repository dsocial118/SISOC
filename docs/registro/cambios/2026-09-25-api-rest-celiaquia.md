# 2026-09-25 - API REST de Celiaquia

## Contexto
- Celiaquia no tenia API HTTP. Lo unico que existia era `celiaquia/api.py`, que es
  el contrato **Python** que el modulo expone a otras apps del monolito (el
  resumen de un ciudadano), no una API web.
- Se decidio DRF por sobre django-ninja: la superficie es CRUD sobre modelos
  (~60 ViewSets ya en el repo, 289 modelos), hay una capa de permisos propia
  (`iam`, `core.permissions`, scope territorial) que encaja con las
  `permission_classes`, y el proyecto es 100% sincronico bajo WSGI, con lo que la
  ventaja principal de ninja (async) no aplica.

## Cambios aplicados
- `celiaquia/scope.py` (nuevo): se extrajeron las reglas de visibilidad que
  vivian como helpers privados de `celiaquia/views/expediente.py`
  (`_is_admin`, `_is_provincial`, `_apply_provincial_expediente_scope` y el
  encadenado por rol del listado). La vista ahora delega ahi. **Motivo**:
  duplicar estas reglas en la API es la forma mas facil de filtrar expedientes
  de otra provincia.
- `celiaquia/api_serializers.py` (nuevo): `ModelSerializer` por modelo, con los
  campos listados a mano. No se usa `fields = "__all__"` en ningun caso porque
  `Expediente` y `ExpedienteCiudadano` guardan FileFields con rutas internas y
  FKs a `User`.
- `celiaquia/api_views.py` (nuevo): ViewSets de **solo lectura**; cada
  transicion de estado es una `@action` que llama al service correspondiente
  (`ExpedienteService`, `LegajoService`, `AsignacionService`, `CupoService`,
  `DocumentosService`). Los `ValidationError` de Django se traducen a 400.
- `celiaquia/api_urls.py` (nuevo) + alta en `config/urls.py` bajo
  `api/celiaquia/`.
- `celiaquia/tests/test_api.py` (nuevo).

## Endpoints

| Recurso | Endpoints |
|---|---|
| Expedientes | `list`, `retrieve`, `legajos`, `historial-estados`, `asignaciones`, `fuera-de-cupo`, y las acciones `procesar`, `confirmar-envio`, `asignar-tecnico`, `desasignar-tecnico` |
| Legajos | `list`, `retrieve`, `documentos`, `subsanaciones`, accion `solicitar-subsanacion` |
| Cupos | `list`, `retrieve`, `metricas`, `ocupados`, `suspendidos` |
| Movimientos de cupo | `list`, `retrieve` |
| Pagos | `list`, `retrieve`, `nomina` |
| Catalogos | `estados-expediente`, `estados-legajo`, `organismos`, `tipos-cruce`, `tipos-documento` |

Filtros por querystring: expedientes por `estado` y `numero_expediente`;
legajos por `expediente`, `revision_tecnico` y `estado_cupo`; movimientos por
`provincia` y `expediente`; pagos por `periodo` y `estado`.

## Decisiones
- **Solo lectura + acciones.** Los expedientes tienen maquina de estados,
  historial y cupos; dejar que el serializer persista saltearia todo eso. No hay
  `create`/`update`/`destroy` en ningun ViewSet.
- **El alcance se aplica en `get_queryset()`**, no en la respuesta: un detalle
  fuera de alcance responde 404, no 403, para no confirmar que el expediente
  existe.
- Los catalogos no se paginan (`pagination_class = None`): son listas cortas que
  el front usa para llenar selects.
- No se expusieron los 34 modelos del modulo. Quedaron afuera los de historial
  interno (`HistorialCupo`, `HistorialValidacionTecnica`,
  `ExpedienteEstadoHistorial` se expone solo como sub-recurso),
  `RegistroErroneo`, `ValidacionRenaper` y `CruceResultado`, que son de proceso
  interno y no tienen consumidor definido.

## Validación
- `celiaquia/tests/test_api.py`: 17 casos, con foco en el alcance (provincial no
  ve ni lista ni detalle de otra provincia, tecnico solo lo asignado,
  coordinador todo, legajos heredan el alcance del expediente), en que la
  respuesta no filtre rutas de archivos ni datos de usuario, y en que las
  acciones deleguen en los services y traduzcan sus errores a 400.
- `celiaquia/`: 319 tests previos siguen pasando tras extraer el scope.
- `manage.py spectacular` genera el schema sin warnings de celiaquia.
- `black` sobre los archivos tocados.

## Riesgos y rollback
- Riesgo principal: el scope se movio de archivo. Si algo quedo mal, afecta
  tambien a las pantallas, no solo a la API. Los 319 tests del modulo cubren ese
  camino.
- Falta definir con el consumidor si necesita escritura (alta de expediente,
  carga de archivos): hoy esas operaciones solo existen en las pantallas.
- Rollback: revertir el commit. No hay migraciones.
