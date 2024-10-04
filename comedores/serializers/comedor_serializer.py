from rest_framework import serializers

from comedores.models import Comedor
from comedores.services.comedor_service import ComedorService


class ComedorSerializer(serializers.ModelSerializer):
    def clean(self):
        try:
            self.initial_data["comienzo"] = self.initial_data.get(
                "comienzo", ""
            ).replace(".", "")

            self.initial_data["referente"] = ComedorService.create_referente(
                self.initial_data
            ).id

            ComedorService.get_ubicaciones_ids(self.initial_data)

        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})

        return self

    class Meta:
        model = Comedor
        fields = "__all__"
