import csv
import logging
from datetime import datetime
from django.http import StreamingHttpResponse
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet

logger = logging.getLogger(__name__)


class CSVExportMixin:
    """
    Mixin para exportar QuerySets a CSV de manera genérica.
    Requiere que la vista implemente `get_export_columns()`.
    """

    export_filename = "export.csv"
    permission_group_export = "Exportar a csv"

    def check_export_permission(self, request):
        if not request.user.is_authenticated:
            raise PermissionDenied

        if request.user.is_superuser:
            return True

        # Verificar grupo específico
        if not request.user.groups.filter(name=self.permission_group_export).exists():
            raise PermissionDenied

        return True

    def get_export_filename(self):
        """Devuelve el nombre del archivo con timestamp."""
        # Extract module name from export_filename (e.g., "listado_comedores.csv" -> "comedores")
        base_name = self.export_filename.replace("listado_", "").replace(".csv", "")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        return f"exportacion_{base_name}_{timestamp}.csv"

    def get_export_columns(self):
        """
        Debe devolver una lista de tuplas: [('Encabezado', 'path.al.campo')]
        Ejemplo: [('Nombre', 'nombre'), ('Provincia', 'provincia.nombre')]
        """
        raise NotImplementedError("Debe implementar get_export_columns()")

    def resolve_field(self, obj, field_path):
        """Resuelve paths tipo 'provincia.nombre' o metodos."""
        try:
            parts = field_path.split(".")
            value = obj
            for part in parts:
                if value is None:
                    break
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    value = getattr(value, part, None)
                    if callable(value):
                        value = value()

            # Formateo básico de tipos
            if value is None:
                return ""
            if isinstance(value, bool):
                return "Si" if value else "No"
            if hasattr(value, "strftime"):  # Fechas
                # Format dates as YYYY-MM-DD HH:mm:ss
                if hasattr(value, "hour"):  # datetime
                    return value.strftime("%Y-%m-%d %H:%M:%S")
                else:  # date
                    return value.strftime("%Y-%m-%d 00:00:00")

            return str(value)
        except Exception:
            return ""

    class Echo:
        """
        Una clase 'file-like' requerida por el writer de CSV de Python.
        En lugar de escribir a un buffer en memoria (como StringIO), simplemente devuelve
        la cadena que se le pasa. Esto permite que el generator (stream_rows) ceda
        el control inmediatamente con el string de la fila, facilitando el streaming
        HTTP eficiente sin cargar todo el archivo en memoria.
        """

        def write(self, value):
            return value

    def export_csv(self, queryset):
        """Genera el response CSV streaming."""
        self.check_export_permission(self.request)

        if not isinstance(queryset, QuerySet) and not isinstance(queryset, list):
            # Si no es un queryset o lista, intentar forzar lista
            queryset = list(queryset)

        filename = self.get_export_filename()
        columns = self.get_export_columns()
        headers = [col[0] for col in columns]
        fields = [col[1] for col in columns]

        pseudo_buffer = self.Echo()
        # Use semicolon as delimiter
        writer = csv.writer(pseudo_buffer, delimiter=";")

        def stream_rows():
            yield writer.writerow(headers)
            for obj in queryset:
                row_data = [self.resolve_field(obj, field) for field in fields]
                yield writer.writerow(row_data)

        response = StreamingHttpResponse(stream_rows(), content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
