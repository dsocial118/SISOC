# Import/Export Excel-CSV en el Django admin

Fecha: 2026-07-27
Rama: `exp_imp_excel`

## Qué se hizo

Se integró `django-import-export` (ya pineado en `requirements/base.txt` como
`django-import-export==3.2.0` y declarado en `INSTALLED_APPS`) al Django admin,
con dos bases reutilizables en `core/admin_import_export.py`:

- `BaseImportExportAdmin`: agrega los botones **Importar** y **Exportar**.
- `BaseExportAdmin`: agrega solo **Exportar**; la URL de import ni siquiera se
  registra.

Formatos habilitados: **XLSX** y **CSV** únicamente. Se descartan JSON, YAML,
TSV, ODS y HTML para no ampliar la superficie de parseo de archivos subidos.

## Configuración (`config/settings.py`)

| Setting | Valor | Motivo |
| --- | --- | --- |
| `IMPORT_EXPORT_USE_TRANSACTIONS` | `True` | Una fila con error revierte toda la importación. |
| `IMPORT_EXPORT_SKIP_ADMIN_CONFIRM` | `False` | Preview obligatorio antes de confirmar. |
| `IMPORT_EXPORT_IMPORT_PERMISSION_CODE` | `"change"` | Importar exige permiso de cambio sobre el modelo. |
| `IMPORT_EXPORT_EXPORT_PERMISSION_CODE` | `"view"` | Exportar exige permiso de lectura. |
| `IMPORT_EXPORT_ESCAPE_FORMULAE_ON_EXPORT` | `True` | Neutraliza fórmulas en las celdas exportadas (formula injection). |

## Modelos habilitados

### Importación + exportación

| Modelo | Resource | Nota |
| --- | --- | --- |
| `core.Nacionalidad` | por defecto | Catálogo de un campo. |
| `comedores.TipoDeComedor` | por defecto | Catálogo de un campo. |
| `organizaciones.TipoOrganizacion` | por defecto | Catálogo de un campo. |
| `organizaciones.RolFirmante` | por defecto | Ver advertencia abajo. |
| `intervenciones.TipoIntervencion` | `TipoIntervencionResource` | Acota a `id`, `nombre`, `programa`. |
| `intervenciones.SubIntervencion` | `SubIntervencionResource` | La FK se importa por id; el nombre del tipo va como columna de solo lectura. |
| `intervenciones.TipoDestinatario` | por defecto | Catálogo de un campo. |
| `intervenciones.TipoContacto` | por defecto | Catálogo de un campo. |

En todos los casos `import_id_fields` queda en el default (`id`): una fila con
id existente actualiza, una fila sin id crea.

### Solo exportación

| Modelo | Motivo |
| --- | --- |
| `core.Provincia`, `core.Municipio`, `core.Localidad` | La fuente autoritativa del territorio es la bajada BAHRA (`core/services/territorio_sync.py`). Una carga manual competiría con esa sincronización. |
| `core.Sexo` | Sus valores se comparan por string en el código (`ciudadano__sexo__sexo="Masculino"` en las métricas de comedores). |
| `core.Mes`, `core.Dia`, `core.Turno` | Catálogos cerrados y ordenados por id, referenciados por pk desde formularios (PWA). Importar no aporta valor. |
| `core.Programa` | Sus ids están referenciados desde `settings` (`PROG_MILD`, `PROG_CDIF`, `PROG_CDLE`, `PROG_PDV`, `PROG_MA`, `PROG_SL`). |
| `core.MontoPrestacionPrograma` | Impacto económico directo. El resource excluye `usuario_creador`. |
| `comedores.Programas` | `usa_admision_para_nomina` cambia el flujo de nómina del comedor. |
| `comedores.ValorComida` | Impacto económico directo. |
| `admisiones.EstadoAdmision`, `admisiones.TipoConvenio` | Los servicios de admisiones los resuelven por nombre (`EstadoAdmision.objects.get(nombre=...)`); renombrarlos en lote rompería la máquina de estados. |

### No habilitados (ni import ni export)

| Modelo / grupo | Motivo |
| --- | --- |
| `ciudadanos.*` | Datos personales (documento, CUIL, domicilio). Además ya existe un pipeline propio de importación masiva con job y trazabilidad (`CiudadanosImportJob`). |
| `comedores.Comedor` y su cadena transaccional (`Nomina`, `NominaDerivacion`, `HistorialValidacion`, convenios, certificados) | Estados, validaciones y sincronización con GESTIONAR. |
| `admisiones.Admision` y sus documentos/informes | Máquina de estados, archivos y permisos por rol. |
| `intervenciones.Intervencion` | Soft delete y signal `post_save` que crea hitos. |
| `users.Profile`, `users.AuditAccesoComedorPWA`, jobs y auditoría | Credenciales y trazas: no deben poder alterarse ni volcarse en lote. |
| `dispositivos`, `insumos`, `celiaquia`, `centrodefamilia`, `centrodeinfancia`, `VAT`, resto | Fuera de alcance de esta primera etapa. |

## Advertencias

- Varios catálogos habilitados se filtran por nombre en el código
  (`RolFirmante.objects.filter(nombre__in=allowed)` en
  `organizaciones/views.py`, `TipoDeComedor.objects.filter(nombre__iexact=...)`
  en el comando de importación de comedores). Renombrar filas por import puede
  romper esos filtros — el mismo riesgo ya existía editando a mano, pero por
  import escala. Importar altas nuevas es seguro; renombrar existentes requiere
  criterio.
- Importar exige permiso `change` sobre el modelo: si un grupo hoy solo tiene
  `view`, no verá el botón Importar.

## Próximos candidatos

`insumos.InsumoCategoria` y los catálogos de `centrodefamilia` /
`centrodeinfancia`, una vez validado el uso real de esta primera tanda.

## Validación

`tests/test_admin_import_export.py` cubre formatos habilitados, export CSV y
XLSX, el ciclo preview → confirmación de una importación, y que un modelo
export-only no exponga la URL de import.
