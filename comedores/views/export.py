from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Case, When, Value, IntegerField
from core.mixins import CSVExportMixin
from core.services.column_preferences import build_columns_context_from_fields
from comedores.services.comedor_service import ComedorService


class ComedorExportView(LoginRequiredMixin, CSVExportMixin, View):
    export_filename = "listado_comedores.csv"

    def get_export_columns(self):
        headers = [
            {"title": "ID"},
            {"title": "Nombre"},
            {"title": "Tipo"},
            {"title": "Organización"},
            {"title": "Programa"},
            {"title": "Dupla"},
            {"title": "Estado general"},
            {"title": "Estado actividad"},
            {"title": "Estado proceso"},
            {"title": "Estado detalle"},
            {"title": "Provincia"},
            {"title": "Municipio"},
            {"title": "Localidad"},
            {"title": "Barrio"},
            {"title": "Partido"},
            {"title": "Calle"},
            {"title": "Número"},
            {"title": "Ubicación"},
            {"title": "Dirección"},
            {"title": "Referente"},
            {"title": "Referente celular"},
            {"title": "Validación"},
            {"title": "Fecha validación"},
        ]
        fields = [
            {"name": "id"},
            {"name": "nombre"},
            {"name": "tipo"},
            {"name": "organizacion"},
            {"name": "programa"},
            {"name": "dupla"},
            {"name": "estado_general"},
            {"name": "estado_actividad"},
            {"name": "estado_proceso"},
            {"name": "estado_detalle"},
            {"name": "provincia"},
            {"name": "municipio"},
            {"name": "localidad"},
            {"name": "barrio"},
            {"name": "partido"},
            {"name": "calle"},
            {"name": "numero"},
            {"name": "ubicacion"},
            {"name": "direccion"},
            {"name": "referente"},
            {"name": "referente_celular"},
            {"name": "validacion"},
            {"name": "fecha_validado"},
        ]
        columns_context = build_columns_context_from_fields(
            self.request,
            "comedores_list",
            headers,
            fields,
            required_keys=["nombre"],
        )
        columns_map = {
            "id": ("ID", "id"),
            "nombre": ("Nombre", "nombre"),
            "tipo": ("Tipo", "tipocomedor__nombre"),
            "organizacion": ("Organización", "organizacion__nombre"),
            "programa": ("Programa", "programa__nombre"),
            "dupla": ("Dupla", "dupla__nombre"),
            "estado_general": ("Estado general", "estado_general"),
            "estado_actividad": (
                "Estado actividad",
                "ultimo_estado__estado_general__estado_actividad__estado",
            ),
            "estado_proceso": (
                "Estado proceso",
                "ultimo_estado__estado_general__estado_proceso",
            ),
            "estado_detalle": (
                "Estado detalle",
                "ultimo_estado__estado_general__estado_detalle",
            ),
            "provincia": ("Provincia", "provincia__nombre"),
            "municipio": ("Municipio", "municipio__nombre"),
            "localidad": ("Localidad", "localidad__nombre"),
            "barrio": ("Barrio", "barrio"),
            "partido": ("Partido", "partido"),
            "calle": ("Calle", "calle"),
            "numero": ("Número", "numero"),
            "ubicacion": ("Ubicación", "custom_ubicacion"),
            "direccion": ("Dirección", "custom_direccion"),
            "referente": ("Referente", "custom_referente"),
            "referente_celular": ("Referente celular", "referente__celular"),
            "validacion": ("Validación", "custom_validacion"),
            "fecha_validado": ("Fecha validación", "fecha_validado"),
        }
        active_keys = columns_context.get("column_active_keys", [])
        if not active_keys:
            return list(columns_map.values())
        return [columns_map[key] for key in active_keys if key in columns_map]

    def get_queryset(self):
        # 1. Obtener queryset filtrado (reutilizando lógica del listado)
        queryset = ComedorService.get_filtered_comedores(
            self.request, user=self.request.user
        )

        # 2. Aplicar ordenamiento desde parámetros GET
        sort_col = self.request.GET.get("sort")
        direction = self.request.GET.get("direction", "asc")

        if sort_col:
            order_prefix = "-" if direction == "desc" else ""

            if sort_col == "nombre":
                queryset = queryset.order_by(f"{order_prefix}nombre")

            elif sort_col == "validacion":
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
                ).order_by(f"{order_prefix}val_weight")

        return queryset

    def resolve_field(self, obj, field_path):
        if field_path == "custom_ubicacion":
            provincia = obj.get("provincia__nombre") if isinstance(obj, dict) else None
            municipio = obj.get("municipio__nombre") if isinstance(obj, dict) else None
            localidad = obj.get("localidad__nombre") if isinstance(obj, dict) else None
            barrio = obj.get("barrio") if isinstance(obj, dict) else None
            partes = [p for p in [provincia, municipio, localidad] if p]
            if barrio:
                partes.append(barrio)
            return " / ".join(partes) if partes else "-"

        if field_path == "custom_direccion":
            calle = obj.get("calle") if isinstance(obj, dict) else None
            numero = obj.get("numero") if isinstance(obj, dict) else None
            calle = calle or "Sin calle"
            numero = numero or "S/N"
            return f"{calle} {numero}".strip()

        if field_path == "custom_referente":
            nombre = obj.get("referente__nombre") if isinstance(obj, dict) else None
            apellido = obj.get("referente__apellido") if isinstance(obj, dict) else None
            nombre = nombre or ""
            apellido = apellido or ""
            full = f"{nombre} {apellido}".strip()
            return full if full else "Sin información"

        if field_path == "custom_validacion":
            estado = obj.get("estado_validacion") if isinstance(obj, dict) else None
            fecha = obj.get("fecha_validado") if isinstance(obj, dict) else None
            if fecha and hasattr(fecha, "strftime"):
                # Format dates as YYYY-MM-DD HH:MM:SS
                if hasattr(fecha, 'hour'):  # datetime
                    fecha = fecha.strftime("%Y-%m-%d %H:%M:%S")
                else:  # date
                    fecha = fecha.strftime("%Y-%m-%d 00:00:00")
            if fecha:
                return f"{estado or 'Pendiente'} ({fecha})"
            return estado or "Pendiente"

        return super().resolve_field(obj, field_path)

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        return self.export_csv(queryset)
