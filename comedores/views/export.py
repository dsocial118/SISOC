from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Case, When, Value, IntegerField
from core.mixins import CSVExportMixin
from comedores.services.comedor_service import ComedorService

class ComedorExportView(LoginRequiredMixin, CSVExportMixin, View):
    export_filename = "listado_comedores.csv"
    
    def get_export_columns(self):
        # Tuplas (Encabezado CSV, Key en el diccionario/objeto)
        return [
            ("Nombre", "nombre"),
            ("Tipo", "tipocomedor__nombre"),
            ("Provincia", "provincia__nombre"),
            ("Municipio", "municipio__nombre"),
            ("Localidad", "localidad__nombre"),
            ("Barrio", "barrio"),
            ("Calle", "calle"),
            ("Número", "numero"),
            ("Referente Nombre", "referente__nombre"),
            ("Referente Apellido", "referente__apellido"),
            ("Estado Validación", "estado_validacion"),
            ("Fecha Validación", "fecha_validado"),
        ]

    def get_queryset(self):
        # 1. Obtener queryset filtrado (reutilizando lógica del listado)
        queryset = ComedorService.get_filtered_comedores(self.request, user=self.request.user)
        
        # 2. Aplicar ordenamiento desde parámetros GET
        sort_col = self.request.GET.get('sort')
        direction = self.request.GET.get('direction', 'asc')
        
        if sort_col:
            order_prefix = '-' if direction == 'desc' else ''
            
            if sort_col == 'nombre':
                queryset = queryset.order_by(f'{order_prefix}nombre')
                
            elif sort_col == 'validacion':
                # Replicar logica de peso visual: Validado(3) > Pendiente(2) > No Validado(1) > Otro(0)
                # Nota: En JS, ASC es 0->3.
                
                # Definir pesos
                w_validado = 3
                w_pendiente = 2
                w_novalidado = 1
                w_default = 0
                
                queryset = queryset.annotate(
                    val_weight=Case(
                        When(estado_validacion="Validado", then=Value(w_validado)),
                        When(estado_validacion="Pendiente", then=Value(w_pendiente)),
                        When(estado_validacion="No Validado", then=Value(w_novalidado)),
                        default=Value(w_default),
                        output_field=IntegerField(),
                    )
                ).order_by(f'{order_prefix}val_weight')

        return queryset

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        return self.export_csv(queryset)
