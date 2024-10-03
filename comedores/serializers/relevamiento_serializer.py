from rest_framework import serializers

from comedores.models import (
    Relevamiento,
)
from comedores.services.relevamiento_service import RelevamientoService


class RelevamientoSerializer(serializers.ModelSerializer):
    def clean(self):
        self.initial_data["fecha_visita"] = RelevamientoService.api_format_fecha_visita(
            self.initial_data["fecha_visita"]
        )

        self.initial_data["funcionamiento"] = (
            RelevamientoService.api_create_funcionamiento(
                self.initial_data["funcionamiento"]
            ).id
        )

        self.initial_data["espacio"] = RelevamientoService.api_create_espacio(
            self.initial_data["espacio"]
        ).id

        self.initial_data["colaboradores"] = (
            RelevamientoService.api_create_colaboradores(
                self.initial_data["colaboradores"]
            ).id
        )

        self.initial_data["recursos"] = RelevamientoService.api_create_recursos(
            self.initial_data["recursos"]
        ).id

        self.initial_data["compras"] = RelevamientoService.api_create_compras(
            self.initial_data["compras"]
        ).id

        self.initial_data["prestacion"] = RelevamientoService.api_create_prestacion(
            self.initial_data["prestacion"]
        ).id

        return self

    class Meta:
        model = Relevamiento
        fields = "__all__"
