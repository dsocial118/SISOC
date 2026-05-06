from rest_framework import serializers

from comedores.models import CursoAppMobile


class CursoAppMobilePWASerializer(serializers.ModelSerializer):
    imagen_url = serializers.SerializerMethodField()

    class Meta:
        model = CursoAppMobile
        fields = (
            "id",
            "nombre",
            "link",
            "descripcion",
            "programa_objetivo",
            "es_recomendado",
            "activo",
            "orden",
            "imagen_url",
        )

    def get_imagen_url(self, obj):
        if not obj.imagen:
            return None
        request = self.context.get("request")
        url = obj.imagen.url
        return request.build_absolute_uri(url) if request else url
