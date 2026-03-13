# Diseño: automatización de documentación de PR y changelog en CI

## Resumen

Se implementará una automatización en GitHub Actions disparada por `pull_request` para reforzar la disciplina spec-as-source sin depender de asistentes interactivos ni de LLMs en CI.

La automatización tendrá tres salidas principales:

- documentación por PR en `docs/registro/prs/`
- contexto de feature para agentes en `docs/contexto/features/`
- release notes preliminares + regeneración de `CHANGELOG.md` solo en PRs hacia `main`

## Objetivos

- Construir contexto reutilizable para futuros agentes a partir del diff real del PR y sus metadatos.
- Dejar trazabilidad documental automática por PR sin depender de disciplina manual.
- Mantener `CHANGELOG.md` actualizado únicamente en el flujo de release a producción.
- Evitar introducir una capa paralela de tooling fuera del stack actual del repo.

## Alcance

- Nuevo workflow de GitHub Actions para eventos `pull_request`.
- Scripts Python propios del repo para generar Markdown determinista.
- Commit automático a la rama origen del PR cuando se detecten cambios generados.
- Ajuste de la plantilla de PR para facilitar el parseo de metadata útil para docs y changelog.

## Artefactos generados

### 1. Documento por PR

Ruta:

- `docs/registro/prs/PR-<numero>.md`

Contenido esperado:

- metadata del PR
- resumen del cambio
- módulos y archivos tocados
- docs relacionadas
- riesgos y testing reportado
- notas operativas útiles para revisión y continuidad

### 2. Contexto de feature para agentes

Ruta:

- `docs/contexto/features/pr-<numero>-<slug>.md`

Contenido esperado:

- contexto funcional observado
- impacto arquitectónico
- decisiones y supuestos visibles
- notas de design system o UI cuando apliquen
- memoria operativa para agentes futuros

Este documento no reemplaza la documentación manual del dominio, pero sirve como capa de contexto incremental y trazable.

### 3. Release note preliminar

Ruta:

- `docs/registro/releases/pending/<fecha-release>-pr-<numero>.md`

Se generará solo cuando el PR tenga base `main`.

### 4. Regeneración de `CHANGELOG.md`

`CHANGELOG.md` se regenerará solo en PRs hacia `main`, tomando como fuente los archivos en `docs/registro/releases/pending/` de la release objetivo.

## Regla de release objetivo

Para PRs a `main`, la release objetivo se calculará como el próximo miércoles respecto de la fecha de ejecución del workflow.

Formato de versión visible:

- `DD.MM.YYYY`

Formato de nombre de archivo:

- `YYYY-MM-DD`

## Diseño técnico

## Workflow

- Evento: `pull_request`
- Permisos: `contents: write`, `pull-requests: read`
- Checkout de la rama origen del PR
- Ejecución de script Python con contexto del evento
- Commit automático si hay cambios

## Script generador

Se implementará un script Python sin dependencias externas de terceros.

Responsabilidades:

- leer `GITHUB_EVENT_PATH`
- extraer metadata del PR
- consultar la API de GitHub para obtener archivos modificados
- detectar módulos afectados
- parsear metadata estructurada del body del PR
- escribir los artefactos Markdown
- regenerar `CHANGELOG.md` cuando corresponda

## Estructura de metadata del PR

Se agregará a la plantilla del PR una sección explícita para:

- contexto funcional
- tipo de cambio
- área o módulo principal
- resumen para changelog
- impacto para usuario
- riesgos y rollback

Si faltan esos datos, el generador usará fallbacks a partir del título del PR, el cuerpo libre y los archivos modificados.

## Enfoque sobre arquitectura, decisiones y design system

No se actualizarán automáticamente los documentos base de arquitectura del proyecto ni ADRs globales.

En su lugar, el contexto generado por feature consolidará:

- arquitectura tocada por el PR
- decisiones visibles en el alcance del cambio
- notas de UI/design system si se modifican templates, static o componentes

Esto reduce riesgo de sobreescritura indebida en documentos canónicos y mantiene el contexto acoplado al PR que lo originó.

## Testing

Se agregarán tests unitarios para cubrir:

- parseo de metadata del body del PR
- detección de módulos afectados
- cálculo del próximo miércoles
- generación del changelog desde pending notes
- escritura de artefactos Markdown principales

## Riesgos y mitigaciones

- Conflictos de commit automático:
  se minimizan escribiendo archivos derivados por PR y regeneración determinista.
- PRs desde forks:
  el workflow debe evitar el commit automático cuando no tenga permisos sobre la rama origen.
- Metadata incompleta en el body:
  se resuelve con fallbacks y plantilla de PR reforzada.
- Ruido documental:
  se separan documentos por PR y por release para evitar mezclar contexto operativo con documentación manual canónica.

## Criterios de aceptación

- Cada PR a `development` o `main` actualiza su archivo en `docs/registro/prs/`.
- Cada PR a `development` o `main` actualiza su contexto en `docs/contexto/features/`.
- Cada PR a `main` genera o actualiza su pending release note.
- Cada PR a `main` regenera `CHANGELOG.md`.
- El workflow commitea automáticamente los cambios generados a la rama del PR.
- Existen tests unitarios para la lógica principal del generador.
