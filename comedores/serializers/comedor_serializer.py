from rest_framework import serializers

from comedores.models import Comedor, Referente
from comedores.services.comedor_service import ComedorService
from legajos.models import LegajoLocalidad, LegajoMunicipio, LegajoProvincias


class ComedorSerializer(serializers.ModelSerializer):
    def clean(self):
        try:
            self.initial_data["comienzo"] = self.initial_data.get(
                "comienzo", ""
            ).replace(".", "")

            self.obtener_ubicacion_ids(self.initial_data)
            self.crear_referente(self.initial_data)
        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})

        return self

    def crear_referente(self, data):
        referente = Referente.objects.create(
            nombre=data["referente"]["nombre"],
            apellido=data["referente"]["apellido"],
            celular=data["referente"]["celular"].replace("-", ""),
            mail=data["referente"]["mail"],
            documento=data["referente"]["documento"].replace(".", ""),
        )
        data["referente"] = referente.id

    def obtener_ubicacion_ids(self, data):
        # TODO: Refactorizar cuando nehui termine lo de las provincias

        provincia_obj = LegajoProvincias.objects.filter(
            nombre__iexact=data["provincia"]
        ).first()
        data["provincia"] = provincia_obj.id if provincia_obj else None

        municipio_obj = LegajoMunicipio.objects.filter(
            nombre__iexact=data["municipio"]
        ).first()
        data["municipio"] = municipio_obj.id if municipio_obj else None

        localidad_obj = LegajoLocalidad.objects.filter(
            nombre__iexact=data["localidad"]
        ).first()
        data["localidad"] = localidad_obj.id if localidad_obj else None

    class Meta:
        model = Comedor
        fields = "__all__"
