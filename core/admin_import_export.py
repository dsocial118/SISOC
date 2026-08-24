"""Bases reutilizables para habilitar import/export en el Django admin.

Se apoyan en django-import-export. La política del repo es:

- ``BaseImportExportAdmin``: catálogos simples que el equipo funcional necesita
  cargar en lote (import + export).
- ``BaseExportAdmin``: modelos donde exportar aporta valor pero importar puede
  romper reglas de negocio, montos, estados o sincronizaciones externas.

El detalle de qué modelo quedó en cada grupo vive en
``docs/registro/cambios/2026-07-27-import-export-admin.md``.
"""

from django.contrib import admin
from import_export.admin import ExportMixin, ImportExportModelAdmin
from import_export.forms import ExportForm
from import_export.formats import base_formats

# Solo Excel y CSV: evita exponer JSON/YAML/HTML, que no aportan al caso de uso
# y amplían la superficie de parseo de archivos subidos.
FORMATOS_HABILITADOS = [base_formats.XLSX, base_formats.CSV]


class BaseImportExportAdmin(ImportExportModelAdmin):
    """Admin con acciones de importación y exportación en XLSX/CSV."""

    # Mantiene el flujo previo a django-import-export 4.x: el usuario elige el
    # formato, pero no una selección parcial de columnas.
    export_form_class = ExportForm
    formats = FORMATOS_HABILITADOS
    # django-import-export 4.x reemplaza `formats` por estos dos atributos.
    # Se declaran los tres para que la restricción siga vigente si se sube el
    # pin de 3.2.0.
    import_formats = FORMATOS_HABILITADOS
    export_formats = FORMATOS_HABILITADOS


class BaseExportAdmin(ExportMixin, admin.ModelAdmin):
    """Admin que solo exporta: no habilita la carga de archivos."""

    export_form_class = ExportForm
    formats = FORMATOS_HABILITADOS
    export_formats = FORMATOS_HABILITADOS
