# Contexto de feature PR #2168 - Exp imp excel

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2168
- Base: `development`
- Rama origen: `exp_imp_excel`
- Autor: `MariaNavarro90`

## Contexto funcional

- El equipo funcional necesita cargar y descargar catálogos del sistema en Excel/CSV desde el Django admin, sin depender de scripts ni de carga manual registro por registro.

## Arquitectura tocada

- No se detectó un patrón arquitectónico dominante más allá del diff observado.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: feat
- Área principal declarada: core
- Impacto usuario declarado: Los usuarios con acceso al admin ven botones de Importar y Exportar en los catálogos habilitados (nacionalidades, tipos de comedor, tipos y subtipos de intervención, destinatarios, tipos de contacto, tipos de organización y roles de firmante). Los modelos con impacto de negocio, montos, estados o datos personales solo permiten exportar o quedan sin la funcionalidad. La importación siempre muestra una vista previa antes de confirmar los cambios.
- Riesgos / rollback: Riesgo bajo. No hay migraciones ni cambios de modelo, por lo que revertir el commit deja el sistema exactamente como estaba. El riesgo residual es funcional: varios catálogos habilitados se filtran por nombre en el código (RolFirmante.objects.filter(nombre__in=...), TipoDeComedor por nombre__iexact), así que renombrarlos en lote por importación puede romper esos filtros — el mismo riesgo ya existía editando a mano, pero por importación escala. Dar de alta filas nuevas es seguro. Mitigaciones activas: preview obligatorio, importación transaccional (una fila con error revierte todo) y permiso change requerido.

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2168.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `AGENT_REPO_MAP.md`
- `admisiones/admin.py`
- `comedores/admin.py`
- `config/settings.py`
- `core/admin.py`
- `core/admin_import_export.py`
- `core/resources.py`
- `docs/registro/cambios/2026-07-27-import-export-admin.md`
- `intervenciones/admin.py`
- `intervenciones/resources.py`
- `organizaciones/admin.py`
- `tests/test_admin_import_export.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-07-27-import-export-admin.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
