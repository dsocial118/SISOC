import logging
from rest_framework import serializers

from comedores.models.relevamiento import Relevamiento

from comedores.services.relevamiento_service import RelevamientoService
from comedores.utils import format_fecha_django


logger = logging.getLogger(__name__)

class RelevamientoSerializer(serializers.ModelSerializer):

    def to_internal_value(self, data):
        data = data.copy()
        try:
            if "fecha_visita" in data:
                data["fecha_visita"] = format_fecha_django(data["fecha_visita"])

            if "territorial" in data:
                territorial_data = data["territorial"]
                data["territorial_nombre"] = territorial_data["nombre"]
                data["territorial_uid"] = territorial_data["gestionar_uid"]

            if "funcionamiento" in data:
                funcionamiento_instance = (
                    self.instance.funcionamiento
                    if self.instance and self.instance.funcionamiento
                    else None
                )
                data["funcionamiento"] = (
                    RelevamientoService.create_or_update_funcionamiento(
                        data["funcionamiento"], funcionamiento_instance
                    ).id
                )

            if "espacio" in data:
                espacio_instance = (
                    self.instance.espacio
                    if self.instance and self.instance.espacio
                    else None
                )
                data["espacio"] = RelevamientoService.create_or_update_espacio(
                    data["espacio"], espacio_instance
                ).id

            if "colaboradores" in data:
                colaboradores_instance = (
                    self.instance.colaboradores
                    if self.instance and self.instance.colaboradores
                    else None
                )
                data["colaboradores"] = (
                    RelevamientoService.create_or_update_colaboradores(
                        data["colaboradores"], colaboradores_instance
                    ).id
                )

            if "recursos" in data:
                recursos_instance = (
                    self.instance.recursos
                    if self.instance and self.instance.recursos
                    else None
                )
                data["recursos"] = RelevamientoService.create_or_update_recursos(
                    data["recursos"], recursos_instance
                ).id

            if "compras" in data:
                compras_instance = (
                    self.instance.compras
                    if self.instance and self.instance.compras
                    else None
                )
                data["compras"] = RelevamientoService.create_or_update_compras(
                    data["compras"], compras_instance
                ).id

            if "anexo" in data:
                anexo_instance = (
                    self.instance.anexo
                    if self.instance and self.instance.anexo
                    else None
                )
                data["anexo"] = RelevamientoService.create_or_update_anexo(
                    data["anexo"], anexo_instance
                ).id
            if "punto_entregas" in data:
                punto_entregas_instance = (
                    self.instance.punto_entregas
                    if self.instance and self.instance.punto_entregas
                    else None
                )
                data["punto_entregas"] = (
                    RelevamientoService.create_or_update_punto_entregas(
                        data["punto_entregas"], punto_entregas_instance
                    ).id
                )

            if "prestacion" in data:
                prestacion_instance = (
                    self.instance.prestacion
                    if self.instance and self.instance.prestacion
                    else None
                )
                data["prestacion"] = RelevamientoService.create_or_update_prestacion(
                    data["prestacion"], prestacion_instance
                ).id

            if "excepcion" in data:
                excepcion_instance = (
                    self.instance.excepcion
                    if self.instance and self.instance.excepcion
                    else None
                )
                data["excepcion"] = RelevamientoService.create_or_update_excepcion(
                    data["excepcion"], excepcion_instance
                ).id

            # Referente / Responsable
            if "responsable_es_referente" in data:
                data["responsable_es_referente"] = (
                    data["responsable_es_referente"] == "Y"
                )
            if "referente_comedor" in data:
                if "celular" in data["referente_comedor"]:
                    data["referente_comedor"]["celular"] = self.limpiar_string_para_int(
                        data["referente_comedor"]["celular"]
                    )
                if "documento" in data["referente_comedor"]:
                    data["referente_comedor"]["documento"] = (
                        self.limpiar_string_para_int(
                            data["referente_comedor"]["documento"]
                        )
                    )
            if "responsable_relevamiento" in data:
                if "celular" in data["responsable_relevamiento"]:
                    data["referente_comedor"]["celular"] = self.limpiar_string_para_int(
                        data["referente_comedor"]["celular"]
                    )
                if "documento" in data["responsable_relevamiento"]:
                    data["responsable_relevamiento"]["documento"] = (
                        self.limpiar_string_para_int(
                            data["responsable_relevamiento"]["documento"]
                        )
                    )
            if "referente_comedor" in data or "responsable_relevamiento" in data:
                responsable_relevamiento_id, referente_comedor_id = (
                    RelevamientoService.create_or_update_responsable_y_referente(
                        data.get("responsable_es_referente", False),
                        data.get("responsable_relevamiento", {}),
                        data.get("referente_comedor", {}),
                        data.get("sisoc_id"),
                    )
                )
                data["responsable_relevamiento"] = responsable_relevamiento_id
                data["referente_comedor"] = referente_comedor_id

            # Imágenes
            if "imagenes" in data:
                imagenes = data["imagenes"]
                if isinstance(imagenes, str):
                    data["imagenes"] = [
                        img.strip() for img in imagenes.split(",") if img.strip()
                    ]
                else:
                    data["imagenes"] = []
        except Exception as e:
            logger.exception(
                "Error al procesar los datos del relevamiento enviado por GESCOM: %s",
                str(e),
            )
            raise serializers.ValidationError(
                {"RelevamientoSerializer.to_internal_value()": [str(e)]}
            )

        return super().to_internal_value(data)

    def limpiar_string_para_int(self, string):
        if string == "":
            return None
        else:
            return string.strip().replace("-", "").replace(".", "").replace("+", "")

    class Meta:
        model = Relevamiento
        fields = "__all__"
