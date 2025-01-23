from rest_framework import serializers

from comedores.models.relevamiento import Relevamiento
from comedores.models.relevamiento import (
    Territorial,
)
from comedores.services.relevamiento_service import RelevamientoService
from comedores.utils import format_fecha_django


class RelevamientoSerializer(serializers.ModelSerializer):
    def clean(self):
        if "fecha_visita" in self.initial_data:
            self.initial_data["fecha_visita"] = format_fecha_django(
                self.initial_data["fecha_visita"]
            )

        if "territorial" in self.initial_data:
            territorial_data = self.initial_data["territorial"]
            territorial, _ = Territorial.objects.get_or_create(
                gestionar_uid=territorial_data["gestionar_uid"],
                defaults={"nombre": territorial_data["nombre"]},
            )
            self.initial_data["territorial"] = territorial.id

        if "funcionamiento" in self.initial_data:
            funcionamiento_instance = (
                self.instance.funcionamiento
                if self.instance and self.instance.funcionamiento
                else None
            )
            self.initial_data["funcionamiento"] = (
                RelevamientoService.create_or_update_funcionamiento(
                    self.initial_data["funcionamiento"], funcionamiento_instance
                ).id
            )

        if "espacio" in self.initial_data:
            espacio_instance = (
                self.instance.espacio
                if self.instance and self.instance.espacio
                else None
            )
            self.initial_data["espacio"] = RelevamientoService.create_or_update_espacio(
                self.initial_data["espacio"], espacio_instance
            ).id

        if "colaboradores" in self.initial_data:
            colaboradores_instance = (
                self.instance.colaboradores
                if self.instance and self.instance.colaboradores
                else None
            )
            self.initial_data["colaboradores"] = (
                RelevamientoService.create_or_update_colaboradores(
                    self.initial_data["colaboradores"], colaboradores_instance
                ).id
            )

        if "recursos" in self.initial_data:
            recursos_instance = (
                self.instance.recursos
                if self.instance and self.instance.recursos
                else None
            )
            self.initial_data["recursos"] = (
                RelevamientoService.create_or_update_recursos(
                    self.initial_data["recursos"], recursos_instance
                ).id
            )

        if "compras" in self.initial_data:
            compras_instance = (
                self.instance.compras
                if self.instance and self.instance.compras
                else None
            )
            self.initial_data["compras"] = RelevamientoService.create_or_update_compras(
                self.initial_data["compras"], compras_instance
            ).id

        if "prestacion" in self.initial_data:
            prestacion_instance = (
                self.instance.prestacion
                if self.instance and self.instance.prestacion
                else None
            )
            self.initial_data["prestacion"] = (
                RelevamientoService.create_or_update_prestacion(
                    self.initial_data["prestacion"], prestacion_instance
                ).id
            )

        if "gestionar_uid" in self.initial_data:
            if (
                Relevamiento.objects.filter(
                    gestionar_uid=self.initial_data["gestionar_uid"]
                )
                .exclude(id=self.initial_data["sisoc_id"])
                .exists()
            ):
                raise serializers.ValidationError(
                    {"error": "gestionar_uid debe ser único si no es nulo."}
                )
        return self

    class Meta:
        model = Relevamiento
        fields = "__all__"
