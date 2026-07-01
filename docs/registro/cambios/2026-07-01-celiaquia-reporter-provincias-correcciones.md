# Correcciones de correctitud de datos en reporter-provincias (celiaquia)

## Fecha
2026-07-01

## Objetivo
Corregir 12 defectos de correctitud de datos detectados en el reporte
`/reporter-provincias/` y en flujos que alimentan sus conteos, a partir de una
auditoría motivada por diferencias reportadas en el padrón de Tucumán (645 vs
624 aprobados). Los conteos, porcentajes y el listado del reporte deben reflejar
fielmente el estado real de los legajos.

## Alcance
- `celiaquia/views/reporter_provincias.py`
- `celiaquia/templates/celiaquia/reporter_provincias.html`
- `celiaquia/views/validacion_renaper.py`
- `celiaquia/services/familia_service/impl.py`
- `celiaquia/services/padron_final_service/impl.py`
- `celiaquia/services/cruce_service/impl.py`
- `celiaquia/tests/test_reporter_provincias_fixes.py` (nuevo)
- `celiaquia/tests/test_padron_final_export.py`
- `celiaquia/tests/test_cruce_service.py`

## Cambios realizados

### Reporte (`reporter_provincias.py` + template)
1. **Rango de fechas inclusivo del último día** (`_apply_report_filters`): las
   fechas `Desde/Hasta` (input `date`, sin hora) ahora se convierten a datetimes
   aware; `Hasta` incluye el día completo (`creado_en < día+1`). Antes
   `creado_en__lte='YYYY-MM-DD'` cortaba en medianoche local y excluía todo el
   último día (y devolvía 0 casos cuando `Desde=Hasta`).
2. **Paginación con orden estable** (`_build_pagination`): se ordena por
   `(-creado_en, -pk)`. Sin el desempate `pk`, las importaciones masivas (muchos
   legajos con igual `creado_en`) producían orden no determinista entre páginas
   (filas repetidas/salteadas).
3. **Desglose por provincia consistente** (`_build_expedientes_por_provincia`):
   se agrega directamente sobre el queryset de legajos (mismo universo que
   `total_casos`) en lugar de re-derivar desde `Expediente.objects`. Ahora la
   suma de `casos` coincide con `total_casos`, los `share` suman 100 % y no se
   pierden legajos vivos cuyo expediente padre esté soft-deleted.
4. **Columna "Provincia" del detalle** (template): muestra
   `caso.ciudadano.provincia` (la provincia usada para contar/agrupar/filtrar) en
   vez de `caso.expediente.provincia` (derivada del primer ciudadano del
   expediente). Se agregó `ciudadano__provincia` a `select_related` para evitar
   N+1.
5. **Etiqueta correcta**: el soporte de las tarjetas de documentación dice
   "legajos" en lugar de "expedientes" (cuentan `ExpedienteCiudadano`).
6. **`?provincia=` validado contra el scope** (`_get_provincia_actual`): un
   usuario provincial ya no puede fijar como "Alcance" el nombre de una provincia
   fuera de sus scopes vía URL.
7. **Provincias disponibles según nivel de scope** (`_get_provincias_disponibles`):
   a usuarios provinciales solo se les ofrecen provincias con alcance completo
   (`get_full_province_scope_ids`), no una provincia entera cuando su scope es
   municipal.
8. **Clasificación de aprobados con doble rol familiar**
   (`_build_clasificacion_aprobados`): un responsable que además es beneficiario
   en su grupo familiar se clasifica como doble rol, igual que el detalle del
   expediente. Consulta batch a `GrupoFamiliar`.
9. **Documentación completa siempre vigente**: ver cambio en `familia_service`.

### Validación RENAPER (`validacion_renaper.py`) — CAMBIO DE COMPORTAMIENTO
- Al marcar **Rechazado (estado 2)** en la validación RENAPER, el legajo ahora
  degrada `revision_tecnico` a **RECHAZADO** (antes solo guardaba
  `estado_validacion_renaper=2` y el legajo seguía contando como APROBADO en el
  reporte, el padrón final y el pago).
- Si el legajo tenía cupo ocupado (`estado_cupo=DENTRO`), se libera con
  `CupoService.liberar_slot` (BAJA, devuelve el cupo a la provincia). Un
  rechazado no debe retener titularidad.

### Nómina Aprobados / Padrón final (`padron_final_service/impl.py`)
- **Emparejamiento CUIL↔DNI** al generar el Excel de "Descargar Nómina
  Aprobados". Antes se comparaba el documento de la base contra el del Excel
  original con el número completo normalizado; los titulares aprobados cuyo
  `ciudadano.documento` está como CUIL (11 díg.) mientras el Excel los tiene como
  DNI (8 díg.) —o viceversa— **no matcheaban y se descartaban en silencio** de la
  nómina. Se agregó `_documento_match_key`, que reduce el CUIL/CUIT de persona
  física a su núcleo DNI (`prefijo(2) + DNI(8) + verificador(1)`) y se aplica
  simétricamente a ambos lados. Caso real Tucumán: la nómina bajaba 624 de 645
  titulares aprobados+MATCH; los 21 faltantes eran esta discrepancia de formato.
- **Observabilidad**: si algún aprobado no encuentra su fila en el Excel original
  (p. ej. no está cargado en la nómina), se registra `logger.warning`
  `padron_final.aprobados_sin_fila_excel` con los conteos (aprobados / en nómina /
  faltan), para no perder titulares en silencio.
- **Identidad consistente con el cruce**: `_aprobados_con_estado` empareja por
  `documento` **y** `cuil_cuit`. El cruce identifica a la persona por su
  CUIL/CUIT (`resolver_cuit_ciudadano`) y recién después por `documento`; si el
  export mirara solo `documento`, un aprobado matcheado por `cuil_cuit` (con
  `documento` vacío o en otro formato) quedaba fuera de la nómina en silencio.
- **Columna "Estado de cupo"**: el padrón incluye a **todos** los aprobados+MATCH
  (no responsables) y agrega una columna final que distingue **"Con cupo
  asignado"** (estado_cupo DENTRO) de **"Lista de espera"** (FUERA) — decisión
  operativa confirmada. Así un operador ve el universo completo de titulares
  elegibles y a la vez quiénes tienen cupo efectivo (subconjunto que va al pago).

### Cruce SINTYS — doble rol ocupa su propio cupo (`cruce_service/impl.py`)
- Antes, el cruce decidía "responsable" por la **relación familiar**
  (`cuidador_principal`) y salteaba a **todo** cuidador, sin consumir cupo. Eso
  dejaba afuera a los **doble rol** (`beneficiario_y_responsable`) y a los
  beneficiarios que además son cuidadores: son celíacos y deben ocupar su propio
  cupo y estar en el padrón, pero quedaban `SIN_CRUCE`.
- Ahora el cruce saltea al **responsable puro** (`rol=responsable`) al inicio del
  loop, según el `rol` y **sin importar la relación familiar**, usando la misma
  regla por `rol` que ya aplican cupo (`reservar_slot`) y padrón. Con esto un
  responsable puro nunca queda marcado `MATCH` (queda `SIN_CRUCE`), aunque no sea
  cuidador de nadie —antes, un `rol=responsable` sin hijo vinculado se validaba
  por su documento y quedaba `MATCH`, inflando el panel "Match" del reporte
  (no afectaba cupo ni padrón). Un doble rol (o beneficiario cuidador) se valida
  por su **propio documento** y ocupa su cupo, **además** de seguir sirviendo de
  ancla para validar a sus hijos. Se centralizó la regla en
  `CruceService._es_responsable_puro`.
- Caso real Tucumán: 2 legajos doble rol (y 2 beneficiarios cuidadores) estaban
  `SIN_CRUCE` por este motivo; con el cambio pasan a cruzarse como beneficiarios
  (si matchean en SINTYS, suman al padrón).

### Documentación cacheada (`familia_service/impl.py`)
- `crear_relacion_responsable_hijo` recalcula `archivos_ok` de los legajos del
  responsable y del hijo tras crear/actualizar la relación (`_refrescar_archivos_ok`).
  El conjunto de documentos requeridos depende del rol/relación familiar; sin
  esto, la métrica "Documentación completa" del reporte quedaba desactualizada
  respecto al detalle del legajo.

## Saneo de datos existentes (management command)
Las correcciones de RENAPER y del cruce solo aplican **hacia adelante**; los
expedientes ya procesados no se corrigen solos. Para repararlos se agregó
`python manage.py sanear_celiaquia` (`celiaquia/management/commands/`):

- **Seguro por defecto**: sin `--apply` es *dry-run* (solo reporta, no escribe).
- Alcance: `--provincia <id>`, `--expedientes <ids...>` o `--todas`.
- Correcciones (todas por defecto, o seleccionables con `--renaper` /
  `--responsable-match` / `--doble-rol`):
  1. RENAPER estado 2 + APROBADO → RECHAZADO + libera cupo.
  2. Responsable puro con MATCH → SIN_CRUCE (+ libera cupo si tuviera).
  3. Doble rol / beneficiario cuidador `SIN_CRUCE` → re-evalúa contra el
     `cruce_excel` del expediente (por su propio documento, reusando
     `CruceService`) y reserva cupo si matchea.
- Idempotente (re-ejecutable). Ejemplo: `sanear_celiaquia --provincia 23 --apply`.
- Preview en Tucumán (dry-run): RENAPER=0, responsable-match=0, doble-rol=4
  candidatos (2 doble rol + 2 beneficiarios cuidadores) a re-evaluar.

## Riesgo / Impacto (IMPORTANTE)
- **RENAPER rechazado degrada a RECHAZADO y libera cupo**: es un cambio de
  comportamiento en producción. Legajos ya rechazados en RENAPER en el pasado
  **no** se recalculan retroactivamente (el cambio aplica desde el próximo
  rechazo). Si se quiere sanear el histórico, correr un saneo puntual sobre
  `estado_validacion_renaper=2 AND revision_tecnico=APROBADO`.
- El resto de los cambios son de solo lectura/consistencia del reporte, sin
  efectos fuera de él.

## Validación
- `pytest celiaquia/tests/test_reporter_provincias_fixes.py` (8 tests nuevos) y
  `pytest tests/test_familia_service_unit.py` (5 tests) en verde.
- `black` sin cambios; `djlint` sin errores en el template.
- Nota: los tests preexistentes de `test_reporter_provincias.py` usan
  `client.get(reverse(...))` y requieren el ROOT_URLCONF completo (dependencias
  nativas no disponibles en el venv local Python 3.14); se validan en CI. Los
  tests nuevos usan `RequestFactory` + `get_context_data` para ejercitar la
  lógica sin cargar todo el URLconf.

## Rollback
Revertir los cambios en los 4 archivos listados. El cambio de RENAPER es el único
con efecto de datos hacia adelante; revertirlo restaura el comportamiento previo
(el legajo rechazado en RENAPER vuelve a conservar `revision_tecnico=APROBADO`).
