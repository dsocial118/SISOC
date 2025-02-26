from rest_framework import serializers


from comedores.models.comedor import Comedor, ImagenComedor
from comedores.services.comedor_service import ComedorService


class ComedorImagenSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagenComedor
        fields = "__all__"


class ComedorSerializer(serializers.ModelSerializer):
    imagenes = ComedorImagenSerializer(many=True, read_only=True)

    def clean(self):
        try:
            if "comienzo" in self.initial_data:
                self.initial_data["comienzo"] = self.initial_data.get(
                    "comienzo", ""
                ).replace(".", "")

            if "referente" in self.initial_data:
                if self.instance and self.instance.referente:
                    self.initial_data["referente"] = (
                        ComedorService.create_or_update_referente(
                            self.initial_data, self.instance.referente
                        ).id
                    )
                else:
                    self.initial_data["referente"] = (
                        ComedorService.create_or_update_referente(self.initial_data).id
                    )

            if (
                "provincia" in self.initial_data
                or "municipio" in self.initial_data
                or "localidad" in self.initial_data
            ):
                ComedorService.get_ubicaciones_ids(self.initial_data)

        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})

        return self

    class Meta:
        model = Comedor
        fields = "__all__"
