# Ciudadanos - estados de revision de identidad

## Contexto

La pantalla `/ciudadanos/revision/` mostraba la cola de registros con revision manual pendiente y permitia solo editar o marcar como revisado.

El booleano `requiere_revision_manual` alcanzaba para saber si un registro seguia pendiente, pero no permitia distinguir historicamente entre una definicion positiva y una negativa una vez cerrada la revision.

## Cambio

Se agrego un estado persistente de revision manual en `Ciudadano`:

- `PENDIENTE`
- `APROBADA`
- `DESCARTADA`

La grilla de revision ahora:

- muestra por defecto solo solicitudes pendientes,
- permite filtrar automaticamente entre pendientes, descartadas y aprobadas,
- conserva visibles los registros aprobados y descartados,
- reemplaza las acciones por un indicador final cuando la solicitud ya fue
  aprobada o descartada,
- agrega la accion de descarte como contracara de la aprobacion.

Tambien se actualizaron textos visibles:

- Sidebar: `Revision de Identidad`.
- Titulo de pagina: `Revision de Identidades No Validadas`.
- Encabezado interno: `Revision manual`.

## Decision principal

Se mantuvo `requiere_revision_manual` como indicador operativo de pendiente y se agrego `estado_revision_manual` como fuente de verdad del resultado de la revision.

Esto evita inferir estados cerrados desde un booleano ambiguo y permite filtrar aprobados y descartados sin ocultarlos del registro historico.

## Compatibilidad

La migracion inicializa:

- registros pendientes como `PENDIENTE`,
- registros no estandar ya cerrados como `APROBADA`.

No se modifican permisos: se reutiliza `ciudadanos.revision_identidad`.

## Validacion esperada

- `manage.py check`
- `makemigrations ciudadanos --check --dry-run`
- tests puntuales de ciudadanos para filtro y acciones de revision
- `djlint` sobre `ciudadanos/templates/ciudadanos/cola_revision.html`
