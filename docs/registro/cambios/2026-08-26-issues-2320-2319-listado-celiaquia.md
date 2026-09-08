# 2026-08-26 - Issues 2320 y 2319: filtros y badges del listado de Celiaquía

## Contexto

- El listado de expedientes (`/celiaquia/expedientes/`) sólo ofrecía un buscador de
  texto libre (`?q=`) que aplicaba un único criterio por vez sobre varios campos a
  la vez, obligando a consultas sucesivas para acotar resultados.
- El requerimiento pedía replicar el filtrado múltiple que ya existe en
  `/comedores/listar`.
- En la misma celda del listado, el badge de legajos "subsanados" usaba el mismo
  verde (`bg-success`) que el estado "Cruce finalizado" del expediente, lo que
  impedía distinguirlos de un vistazo (issue 2319).
- Ese filtrado no es específico de Comedores: `core.services.advanced_filters` y el
  componente `components/search_bar.html` en modo `filters_mode` ya lo proveen y son
  usados por 12 secciones del sistema. Celiaquía era una de las que faltaba.

## Cambios aplicados

- Nuevo `celiaquia/services/expediente_filter_config/` con el mapeo de campos, tipos,
  operadores y la configuración serializable para la UI, siguiendo la convención de
  services de la app (`__init__.py` + `impl.py`).
- Campos expuestos, alineados con las columnas de la grilla: ID, Número de
  expediente, Fecha de creación, Provincia, Estado y Técnico asignado.
- `ExpedienteListView` aplica `AdvancedFilterEngine` sobre el queryset **después**
  del acotamiento por rol y alcance territorial, y pasa el modo filtros al
  componente de búsqueda.
- `provincia` filtra sobre la anotación `provincia_derivada` y no sobre un join con
  los legajos: el expediente no tiene provincia propia (se deriva de sus ciudadanos,
  con respaldo en el perfil legacy del creador), así que filtrar por el join daría
  un resultado distinto del valor que muestra la grilla.
- `estado` y `provincia` se ofrecen como desplegables poblados desde
  `EstadoExpediente` y `Provincia`; `tecnico` desde los usuarios con
  `role_tecnicoceliaquia`, y sólo para quienes ven la columna de técnico
  (admin, coordinador y técnico). El backend también ignora el filtro
  `tecnico` para el resto de los roles, incluso si se envía manualmente por
  querystring.
- El listado deja de renderizar el input de texto libre, que el componente reemplaza
  por las filas de filtros. El soporte de `?q=` se conserva en el backend para no
  romper enlaces existentes.
- No se registró la sección en `favorite_filters`: el modal de filtros favoritos se
  retiró de la UI por definición de UX/UI (2026-08-04) y registrarla sería código
  muerto.
- Issue 2319: el badge de "subsanados" pasa de `bg-success` a una clase propia
  `badge-subsanado` (violeta `#6f42c1`), definida en `listModerno.css` junto al
  resto de badges de listado. "A subsanar" conserva el amarillo y "Cruce
  finalizado" conserva el verde.

## Impacto esperado

- Se pueden combinar varios filtros simultáneos; el engine aplica `OR` entre filtros
  del mismo campo y `AND` entre campos distintos.
- Los filtros no pueden ampliar el alcance de un usuario: se aplican sobre el
  queryset ya restringido por rol y territorio.
- Un filtro con un campo desconocido se ignora y el listado responde normalmente.
- Los tres estados visibles en la celda de estado quedan diferenciados por color:
  amarillo "a subsanar", violeta "subsanados", verde "Cruce finalizado".
- No cambia el modelo de datos ni hay migraciones.

## Validación

- `pytest celiaquia/tests` en Docker: 179 tests aprobados (167 previos + 10 nuevos
  en `test_expediente_list_filtros.py` y 2 en `test_expediente_list_badges.py`).
- Dos tests se verificaron como regresiones reales, comprobando que fallan al
  revertir el cambio: el de duplicados (si se quita el `distinct()`) y el del
  badge violeta (si vuelve a `bg-success`).
- `black --check`, `djlint --check` sobre el template modificado y `pylint` 10.00/10
  sobre los archivos nuevos.
- `pylint` sobre `views/expediente.py` comparado contra la baseline de `development`:
  sin hallazgos nuevos más allá de los `E0401` de resolución de imports que la
  configuración ya produce para todo import de primer nivel del repo.
- `lint-imports` (15 contratos) y `lint-imports --config .importlinter_celiaquia_config`,
  ambos KEPT.
- `git diff --check` sin observaciones.

## Riesgos y rollback

- Riesgo principal: el buscador de texto libre deja de estar visible. Quien lo usara
  para buscar "cualquier campo" ahora debe elegir el campo. Los enlaces con `?q=`
  siguen funcionando.
- Pendiente de definición de producto: en el detalle del expediente el estado
  "Subsanado" del legajo se muestra en celeste (`bg-info`), no en violeta. El
  issue 2319 pedía el cambio sólo en el listado, así que el detalle no se tocó.
- El filtro por técnico atraviesa una relación multivalor; el `distinct()` del
  queryset evita filas repetidas cuando se combinan dos técnicos.
- Rollback: revertir el commit. No hay migraciones ni datos que deshacer.
