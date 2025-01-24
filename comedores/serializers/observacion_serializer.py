import datetime

from rest_framework import serializers
from django.utils import timezone

from comedores.models.comedor import Observacion


class ObservacionSerializer(serializers.ModelSerializer):
    def clean(self):
        self.initial_data["fecha_visita"] = self.format_fecha(
            self.initial_data["fecha_visita"]
        )

        return self

    def format_fecha(self, fecha):
        fecha_formateada = datetime.datetime.strptime(fecha, "%d/%m/%Y %H:%M")
        return timezone.make_aware(fecha_formateada, timezone.get_default_timezone())

    class Meta:
        model = Observacion
        fields = "__all__"
