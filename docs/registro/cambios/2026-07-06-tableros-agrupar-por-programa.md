# 2026-07-06 - Tableros: agrupar por programa y quitar el "Ver"

## Contexto
- En el menú lateral (`templates/includes/sidebar/opciones.html`) cada tablero se
  renderizaba como un submenú colapsable con un único hijo "Ver" que llevaba al
  tablero. Resultaba redundante y desalineado con el prototipo.
- El prototipo agrupa los tableros por programa (ej. Aduana, DataCalle) y el nombre
  del tablero es el enlace directo (sin el paso intermedio "Ver").

## Qué se hizo
- **Modelo:** se agregó `Tablero.grupo_menu` (`CharField`, opcional). Vacío = enlace
  directo; con valor = se agrupa bajo un submenú con ese nombre. No confundir con los
  `Group` de permisos (ver `2026-03-18-tableros-grupos-por-tablero.md`).
- **Migración:** `dashboard/0002_tablero_grupo_menu.py` agrega el campo y hace
  backfill de las filas existentes por prefijo de nombre (`DataCalle*` → "DataCalle",
  `Aduana`/`Aduana Ejecutivo` → "Aduana"), sin pisar valores ya seteados.
- **Admin:** `grupo_menu` es editable y aparece en list_display / list_filter /
  search_fields.
- **Template tag:** `tableros_para_sidebar` ahora devuelve una estructura agrupada
  (`tipo: single | grupo`) preservando el orden y marcando el ítem activo según el
  path. Un grupo con un solo tablero visible se colapsa a enlace directo.
- **Template:** la sección Tableros quedó sin el "Ver": los tableros sueltos son
  enlaces directos y los agrupados abren un submenú cuyos hijos también son enlaces
  directos. "Centros de Familia" (dashboard CF) también pasó a enlace directo.
- **Fixture:** `dashboard/fixtures/tableros.json` incluye `grupo_menu` en las entradas
  agrupadas.

## Seguimiento (mismo día): grupo "Espacios Comunitarios"
- A pedido de negocio se sumó un grupo más, **"Espacios Comunitarios"**, que reúne
  Perfilamiento de Espacios Comunitarios, Seguimiento Espacios Comunitatios,
  Coordinadores Alimentar Comunidad y Comedores Interno.
- `dashboard/0003_tablero_grupo_espacios_comunitarios.py` hace el backfill por `slug`
  (solo filas con `grupo_menu` vacío) y el fixture agrega `grupo_menu` en esas 4
  entradas. Queda "Prestación Alimentar" como único enlace suelto.
- Se recalcularon otra vez los fingerprints de `.gitleaksignore` por el corrimiento de
  líneas del fixture.

## Riesgos / seguimiento
- Al insertar líneas en el fixture se recalcularon los fingerprints de gitleaks en
  `.gitleaksignore` (regla `grafana-api-key`, URLs de Power BI). Si se vuelve a editar
  el fixture, hay que recomputar esos números de línea.
- Tableros nuevos que deban agruparse solo necesitan setear `grupo_menu` (por admin o
  fixture); no requiere tocar el template.
