# 2026-06-01 — Issue #1799 (Req 2): el Acta de Solicitud de Subsidio vuelve a la Admision

Rama: `claude/issue-1799-req2-acta-admision` (apilada sobre Req 4)
Plan: [docs/plans/2026-06-01-issue-1799-documentacion-organizacion-admisiones.md](../../plans/2026-06-01-issue-1799-documentacion-organizacion-admisiones.md)

## Resumen

El documento "Acta de solicitud de subsidio al programa" deja de estar en el
legajo de la Organizacion y vuelve a gestionarse como documento nativo de la
Admision (solo personeria juridica / convenio 3, sin ampliar alcance — decision
confirmada).

## Cambios

- Migracion de datos [0015_quitar_acta_solicitud_subsidio.py](../../../organizaciones/migrations/0015_quitar_acta_solicitud_subsidio.py):
  quita el "Acta de solicitud de subsidio al programa" del catalogo
  `DocumentacionOrganizacion` y soft-deletea los `ArchivoOrganizacion` cargados
  para ese documento (se preservan como historico). Reverse no-op.
- Servicio: se elimina el alias del acta en
  `AdmisionService.ALIAS_DOCUMENTACION_ORGANIZACIONAL[CATEGORIA_PERSONERIA]`
  (admisiones/services/admisiones_service/impl.py), para que
  `congelar_documentacion_organizacional` deje de materializar el acta desde el
  legajo.

## Comportamiento resultante

- En el legajo de la Organizacion ya no aparece el acta.
- En la Admision (convenio 3) el acta sigue disponible como `Documentacion`
  (pk 9 "Acta de Solicitud de Subsidio" del fixture `documentacion_tipoconvenio.json`)
  y se gestiona con la logica de Admision (adjuntar/estado/GDE/rectificacion),
  cumpliendo el req 2.1.
- Admisiones existentes que ya habian materializado el acta conservan su
  `ArchivoAdmision` (queda como documento nativo). No se rompe nada.

## Dependencias / supuestos

- El catalogo de `Documentacion` de admisiones se siembra por el fixture
  `documentacion_tipoconvenio.json` (no por migracion). El acta (pk 9, convenio 3)
  ya esta ahi; por eso Req 2 NO crea Documentacion de admision (evita divergencia
  con el fixture).
- Requiere la migracion 0014 (Req 4) aplicada antes: el borrado del catalogo se
  apoya en `ArchivoOrganizacion.documentacion` ya nullable (`SET_NULL`).

## Validacion

Entorno local Windows (venv Django 4.2.27, sqlite; Docker apagado):

- `pytest organizaciones/test_quitar_acta_solicitud_subsidio.py admisiones/tests/ organizaciones/test_update_view_tipo_entidad.py` → 50 passed.
- `manage.py makemigrations --check --dry-run organizaciones admisiones` → sin cambios.
- `manage.py migrate organizaciones` (sqlite) → aplica 0015 OK.
- `black` sobre los archivos tocados → limpio.
