# 2026-06-01 — Decision: el Numero de GDE vuelve a ser propiedad del Legajo de la Organizacion

Issue: #1799 (Req 3). Revierte parcialmente la decision
[2026-05-22-numero-gde-propiedad-admision](2026-05-22-numero-gde-propiedad-admision.md) (issue #1605).

## Contexto

El #1605 hizo el Numero de GDE **propiedad de la Admision** (modelo
`NumeroGdeOrganizacion`, editable desde cada admision, solo-lectura en el legajo),
con el argumento de que un mismo documento de organizacion puede repetirse en
varias admisiones con distinto GDE.

El #1799 (mismo reportante) revisa ese criterio: el GDE debe gestionarse desde el
**Legajo de la Organizacion** (unica fuente) y replicarse a las admisiones,
coherente con el principio "el flujo de informacion siempre es Legajo
Organizacion -> Admision" (req 1.5 del #1799).

## Decision (confirmada por el usuario, 2026-06-01)

**"Org unica fuente"**: el GDE se edita solo en el legajo (en documentos
`Aceptado`), se replica a TODAS las admisiones activas relacionadas, se deshabilita
la edicion desde la admision para documentos de origen organizacional, y se migran
los valores existentes de `NumeroGdeOrganizacion` a `ArchivoOrganizacion.numero_gde`.

## Implementacion

- `ArchivoOrganizacion.numero_gde` vuelve a ser el dato canonico; editable en el
  legajo via `organizacion_documento_gde` (solo `Aceptado`, permisos del legajo).
- `AdmisionService.replicar_numero_gde_desde_organizacion` propaga el valor a los
  `ArchivoAdmision` materializados (via `archivo_organizacion_origen`, Fase 0) de
  las admisiones activas, y limpia el informe tecnico afectado por cada una.
- Admision-side: el GDE de documentos de origen organizacional se muestra
  solo-lectura (`es_origen_organizacion`); `actualizar_numero_gde_ajax` rechaza
  esos documentos.
- Migracion `0062`: backfill best-effort desde `NumeroGdeOrganizacion` (valor mas
  reciente) y, en su defecto, desde `ArchivoAdmision` materializado.

## Consecuencias / riesgos

- **Perdida de divergencia por-admision**: si dos admisiones tenian GDE distinto
  para el mismo documento, el backfill conserva el mas reciente (no hay forma
  univoca de revertir un modelo 1->N). `NumeroGdeOrganizacion` no se borra (queda
  como historico; candidato a remover en una migracion futura).
- **Efecto de la replicacion**: editar el GDE en el legajo puede reiniciar el
  informe tecnico de varias admisiones (se reusa la limpieza existente). Es
  consecuencia directa de "replicar a todas".
- El endpoint admision-side `actualizar_numero_gde_organizacion_ajax`
  (NumeroGdeOrganizacion) queda sin uso desde la UI; se conserva por ahora para no
  romper datos/historico.
