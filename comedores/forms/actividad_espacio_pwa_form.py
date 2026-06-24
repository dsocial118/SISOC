from django import forms
from django.core.exceptions import ValidationError

from core.models import Dia
from pwa.models import ActividadEspacioPWA, CatalogoActividadPWA


def _format_activity_schedule(start_time, end_time):
    if start_time and end_time:
        return f"{start_time:%H:%M} a {end_time:%H:%M}"
    if start_time:
        return start_time.strftime("%H:%M")
    return ""


class ActividadEspacioPWAWebForm(forms.ModelForm):
    class Meta:
        model = ActividadEspacioPWA
        fields = (
            "catalogo_actividad",
            "responsable_actividad",
            "vigencia_actividad_meses",
        )
        labels = {
            "catalogo_actividad": "Actividad",
            "responsable_actividad": "Responsable",
            "vigencia_actividad_meses": "Vigencia en meses",
        }
        widgets = {
            "catalogo_actividad": forms.Select(attrs={"class": "form-control"}),
            "responsable_actividad": forms.TextInput(attrs={"class": "form-control"}),
            "vigencia_actividad_meses": forms.NumberInput(
                attrs={"class": "form-control", "min": "1"}
            ),
        }

    def __init__(self, *args, comedor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.comedor = comedor
        self._schedule_data = []
        self.schedule_errors = []
        self.fields["catalogo_actividad"].queryset = (
            CatalogoActividadPWA.objects.filter(activo=True).order_by(
                "categoria", "actividad", "id"
            )
        )
        self.day_options = list(Dia.objects.order_by("id"))
        self.schedule_rows = self._get_initial_schedule_rows()

    def _get_initial_schedule_rows(self):
        if self.is_bound:
            return self._get_bound_schedule_rows()
        if self.instance and self.instance.pk:
            return [
                {
                    "dia_actividad": str(self.instance.dia_actividad_id or ""),
                    "hora_inicio": (
                        self.instance.hora_inicio.strftime("%H:%M")
                        if self.instance.hora_inicio
                        else ""
                    ),
                    "hora_fin": (
                        self.instance.hora_fin.strftime("%H:%M")
                        if self.instance.hora_fin
                        else ""
                    ),
                }
            ]
        return [{"dia_actividad": "", "hora_inicio": "", "hora_fin": ""}]

    def _getlist(self, field_name):
        if hasattr(self.data, "getlist"):
            return self.data.getlist(field_name)
        value = self.data.get(field_name, [])
        if isinstance(value, (list, tuple)):
            return list(value)
        return [value] if value else []

    def _get_bound_schedule_rows(self):
        dias = self._getlist("schedule_dia_actividad")
        horas_inicio = self._getlist("schedule_hora_inicio")
        horas_fin = self._getlist("schedule_hora_fin")
        row_count = max(len(dias), len(horas_inicio), len(horas_fin), 1)
        rows = []
        for index in range(row_count):
            rows.append(
                {
                    "dia_actividad": dias[index] if index < len(dias) else "",
                    "hora_inicio": (
                        horas_inicio[index] if index < len(horas_inicio) else ""
                    ),
                    "hora_fin": horas_fin[index] if index < len(horas_fin) else "",
                }
            )
        return rows

    def clean_vigencia_actividad_meses(self):
        value = self.cleaned_data.get("vigencia_actividad_meses")
        if value is not None and value < 1:
            raise forms.ValidationError("La vigencia debe ser mayor a 0 meses.")
        return value

    def clean(self):
        cleaned = super().clean()
        catalogo_actividad = cleaned.get("catalogo_actividad")
        self._schedule_data = []
        self.schedule_errors = [{} for _ in self.schedule_rows]
        parsed_rows = []

        for index, row in enumerate(self.schedule_rows):
            row_errors = self.schedule_errors[index]
            dia_actividad = self._clean_schedule_day(row.get("dia_actividad"))
            hora_inicio = self._clean_schedule_time(
                row.get("hora_inicio"),
                "Hora inicio",
            )
            hora_fin = self._clean_schedule_time(row.get("hora_fin"), "Hora fin")

            if isinstance(dia_actividad, ValidationError):
                row_errors["dia_actividad"] = dia_actividad.message
                dia_actividad = None
            if isinstance(hora_inicio, ValidationError):
                row_errors["hora_inicio"] = hora_inicio.message
                hora_inicio = None
            if isinstance(hora_fin, ValidationError):
                row_errors["hora_fin"] = hora_fin.message
                hora_fin = None

            if hora_inicio and hora_fin and hora_fin <= hora_inicio:
                row_errors["hora_fin"] = (
                    "La hora de fin debe ser posterior a la hora de inicio."
                )

            if row_errors:
                continue

            parsed_rows.append(
                {
                    "dia_actividad": dia_actividad,
                    "hora_inicio": hora_inicio,
                    "hora_fin": hora_fin,
                }
            )

        if any(self.schedule_errors):
            self.add_error(
                None,
                "Completa todos los dias y horarios con formato HH:MM.",
            )
            return cleaned

        if not parsed_rows:
            self.add_error(None, "Agrega al menos un dia y horario.")
            return cleaned

        unique_rows = []
        seen_rows = set()
        for row in parsed_rows:
            key = (
                row["dia_actividad"].id,
                row["hora_inicio"].strftime("%H:%M"),
                row["hora_fin"].strftime("%H:%M"),
            )
            if key in seen_rows:
                continue
            seen_rows.add(key)
            unique_rows.append(row)

        if self._has_schedule_overlap(unique_rows):
            self.add_error(
                None,
                "La misma actividad no puede tener horarios cruzados en el mismo dia.",
            )

        if (
            self.comedor
            and catalogo_actividad
            and self._has_existing_schedule_overlap(unique_rows, catalogo_actividad)
        ):
            self.add_error(
                None,
                "Ya existe la misma actividad con un horario que se pisa ese dia.",
            )

        self._schedule_data = unique_rows

        return cleaned

    def _clean_schedule_day(self, value):
        if not value:
            return ValidationError("Este campo es obligatorio.")
        try:
            return Dia.objects.get(pk=value)
        except (Dia.DoesNotExist, ValueError, TypeError):
            return ValidationError("Selecciona un dia valido.")

    def _clean_schedule_time(self, value, label):
        if not value:
            return ValidationError("Este campo es obligatorio.")
        field = forms.TimeField(input_formats=("%H:%M",))
        try:
            return field.clean(value)
        except ValidationError:
            return ValidationError(f"{label} debe tener formato HH:MM.")

    def _has_schedule_overlap(self, rows):
        grouped_rows = {}
        for row in rows:
            grouped_rows.setdefault(row["dia_actividad"].id, []).append(row)

        for day_rows in grouped_rows.values():
            ordered_rows = sorted(day_rows, key=lambda row: row["hora_inicio"])
            for index in range(1, len(ordered_rows)):
                if (
                    ordered_rows[index]["hora_inicio"]
                    < ordered_rows[index - 1]["hora_fin"]
                ):
                    return True
        return False

    def _has_existing_schedule_overlap(self, rows, catalogo_actividad):
        for row in rows:
            overlapping = ActividadEspacioPWA.objects.filter(
                comedor=self.comedor,
                dia_actividad=row["dia_actividad"],
                catalogo_actividad=catalogo_actividad,
                activo=True,
                hora_inicio__lt=row["hora_fin"],
                hora_fin__gt=row["hora_inicio"],
            )
            if self.instance and self.instance.pk:
                overlapping = overlapping.exclude(pk=self.instance.pk)
            if overlapping.exists():
                return True
        return False

    def get_schedule_data(self):
        return list(self._schedule_data)

    @property
    def schedule_form_rows(self):
        rows = []
        for index, row in enumerate(self.schedule_rows):
            errors = (
                self.schedule_errors[index] if index < len(self.schedule_errors) else {}
            )
            rows.append({"values": row, "errors": errors})
        return rows

    def get_service_data(self, schedule):
        data = dict(self.cleaned_data)
        data.update(schedule)
        data["horario_actividad"] = _format_activity_schedule(
            data.get("hora_inicio"),
            data.get("hora_fin"),
        )
        return data
