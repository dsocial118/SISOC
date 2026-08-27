# Contexto de feature PR #2365 - feat(dispositivos): límite ejecutable inicial (#2309)

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2365
- Base: `development`
- Rama origen: `codex/issue-2309-executable-boundary`
- Autor: `juanikitro`

## Contexto funcional

Primer corte de #2309 para preparar la extracción de Dispositivos sin cambiar
su CRUD, permisos, rutas, datos ni autoridad de escritura. El objetivo es que
la próxima reubicación física pueda sustituir los adaptadores del monolito sin
reescribir las reglas de alcance territorial.

## Arquitectura tocada

- Actor, sesión, catálogo territorial, permisos y filtros se separan mediante
  contratos/adaptadores.
- La migración aditiva `0006` incorpora la proyección territorial local y
  versionada; no migra registros existentes ni reemplaza las FKs legacy.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: boundary ejecutable, primer corte.
- Área principal declarada: Dispositivos.
- Impacto usuario declarado: no debe haber cambio observable.
- Riesgos / rollback: un error en la adaptación puede alterar permisos o el
  alcance territorial. El rollback es revertir este commit mientras el
  monolito continúa siendo el único runtime y escritor.

## Avance de Checkpoint 1

- Hecho: contratos puros de actor/alcance, adaptadores de monolito, proyección
  territorial versionada, migración aditiva y ratchet de imports.
- Pendiente: proyecto `services/dispositivos/`, rutas desde el runtime
  independiente, favoritos HTTP opcionales, imports bidireccionales y job de
  migraciones separado.
- Estado estimado: 35%. Actualizar esta sección y el body del PR en cada corte.

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2365.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.importlinter`
- `AGENT_REPO_MAP.md`
- `dispositivos/adapters/__init__.py`
- `dispositivos/adapters/monolith_filters.py`
- `dispositivos/adapters/monolith_permissions.py`
- `dispositivos/adapters/monolith_session.py`
- `dispositivos/adapters/monolith_territorial.py`
- `dispositivos/boundary.py`
- `dispositivos/favorite_filters.py`
- `dispositivos/forms.py`
- `dispositivos/migrations/0006_versionproyeccionterritorial_and_more.py`
- `dispositivos/models.py`
- `dispositivos/ports.py`
- `dispositivos/services.py`
- `dispositivos/territorial_projection.py`
- `dispositivos/tests/test_dispositivos_services.py`
- `dispositivos/tests/test_territorial_projection.py`
- `dispositivos/urls.py`
- `dispositivos/views.py`
- `docs/registro/decisiones/2026-08-21-dispositivos-actor-boundary.md`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/decisiones/2026-08-21-dispositivos-actor-boundary.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
