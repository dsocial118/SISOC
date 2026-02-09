import logging
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError

from core.validators import validate_unicode_email
from core.utils import format_fecha_django

from relevamientos.models import Relevamiento

from relevamientos.service import RelevamientoService

logger = logging.getLogger("django")


class RelevamientoSerializer(serializers.ModelSerializer):

    # TODO: Refactorizar
    def clean(  # pylint: disable=too-many-statements,too-many-branches, too-many-locals
        self,
    ):
        # Convertir valores Y/N a booleanos automáticamente
        self._convert_yn_to_boolean(self.initial_data)

        if "fecha_visita" in self.initial_data:
            self.initial_data["fecha_visita"] = format_fecha_django(
                self.initial_data["fecha_visita"]
            )

        if "comedor" in self.initial_data:
            self.initial_data["comedor"] = RelevamientoService.update_comedor(
                self.initial_data["comedor"],
                (
                    self.instance.comedor
                    if self.instance and self.instance.comedor
                    else None
                ),
            )

        if "territorial" in self.initial_data:
            territorial_data = self.initial_data["territorial"]
            self.initial_data["territorial_nombre"] = territorial_data["nombre"]
            self.initial_data["territorial_uid"] = territorial_data["gestionar_uid"]
            # Evitar que quede un campo no modelado que rompa la validación
            self.initial_data.pop("territorial", None)

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

        if "anexo" in self.initial_data:
            anexo_instance = (
                self.instance.anexo if self.instance and self.instance.anexo else None
            )
            self.initial_data["anexo"] = RelevamientoService.create_or_update_anexo(
                self.initial_data["anexo"], anexo_instance
            ).id
        if "punto_entregas" in self.initial_data:
            punto_entregas_instance = (
                self.instance.punto_entregas
                if self.instance and self.instance.punto_entregas
                else None
            )
            self.initial_data["punto_entregas"] = (
                RelevamientoService.create_or_update_punto_entregas(
                    self.initial_data["punto_entregas"], punto_entregas_instance
                ).id
            )

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

        if "excepcion" in self.initial_data:
            excepcion_instance = (
                self.instance.excepcion
                if self.instance and self.instance.excepcion
                else None
            )
            self.initial_data["excepcion"] = (
                RelevamientoService.create_or_update_excepcion(
                    self.initial_data["excepcion"], excepcion_instance
                ).id
            )

        if "responsable_es_referente" in self.initial_data:
            responsable_es_referente = self.initial_data["responsable_es_referente"]
            if isinstance(responsable_es_referente, str):
                self.initial_data["responsable_es_referente"] = (
                    responsable_es_referente.upper() == "Y"
                )
        if "referente_comedor" in self.initial_data:
            if "celular" in self.initial_data["referente_comedor"]:
                # TODO: Crear una funcion que limpie todo
                if self.initial_data["referente_comedor"]["celular"] == "":
                    self.initial_data["referente_comedor"]["celular"] = None
                else:
                    self.initial_data["referente_comedor"]["celular"] = (
                        self.initial_data["referente_comedor"]["celular"]
                        .strip()
                        .replace(" ", "")
                        .replace("-", "")
                        .replace(".", "")
                    )
            if "documento" in self.initial_data["referente_comedor"]:
                if self.initial_data["referente_comedor"]["documento"] == "":
                    self.initial_data["referente_comedor"]["documento"] = None
                else:
                    self.initial_data["referente_comedor"]["documento"] = (
                        self.initial_data["referente_comedor"]["documento"]
                        .strip()
                        .replace(" ", "")
                        .replace("-", "")
                        .replace(".", "")
                    )

        if "responsable_relevamiento" in self.initial_data:
            if "celular" in self.initial_data["responsable_relevamiento"]:
                if self.initial_data["responsable_relevamiento"]["celular"] == "":
                    self.initial_data["responsable_relevamiento"]["celular"] = None
                else:
                    self.initial_data["responsable_relevamiento"]["celular"] = (
                        self.initial_data["responsable_relevamiento"]["celular"]
                        .strip()
                        .replace(" ", "")
                        .replace("-", "")
                        .replace(".", "")
                    )
            if "documento" in self.initial_data["responsable_relevamiento"]:
                if self.initial_data["responsable_relevamiento"]["documento"] == "":
                    self.initial_data["responsable_relevamiento"]["documento"] = None
                else:
                    self.initial_data["responsable_relevamiento"]["documento"] = (
                        self.initial_data["responsable_relevamiento"]["documento"]
                        .strip()
                        .replace(" ", "")
                        .replace("-", "")
                        .replace(".", "")
                    )

        email_errors = {}
        self._validate_nested_email(
            self.initial_data.get("referente_comedor"),
            "referente_comedor",
            email_errors,
        )
        self._validate_nested_email(
            self.initial_data.get("responsable_relevamiento"),
            "responsable_relevamiento",
            email_errors,
        )
        if email_errors:
            raise serializers.ValidationError(email_errors)

        if (
            "referente_comedor" in self.initial_data
            or "responsable_relevamiento" in self.initial_data
        ):
            responsable_relevamiento_id, referente_comedor_id = (
                RelevamientoService.create_or_update_responsable_y_referente(
                    self.initial_data.get("responsable_es_referente", False),
                    self.initial_data.get("responsable_relevamiento", {}),
                    self.initial_data.get("referente_comedor", {}),
                    self.initial_data.get("sisoc_id"),
                )
            )
            self.initial_data["responsable_relevamiento"] = responsable_relevamiento_id
            self.initial_data["referente_comedor"] = referente_comedor_id

        if "imagenes" in self.initial_data:
            imagenes = self.initial_data["imagenes"]
            if isinstance(imagenes, str):
                self.initial_data["imagenes"] = [
                    img.strip() for img in imagenes.split(",") if img.strip()
                ]
            elif isinstance(imagenes, list):
                self.initial_data["imagenes"] = imagenes
            else:
                self.initial_data["imagenes"] = []

        return self

    def validate(self, attrs):
        """Validación personalizada con mejor logging de errores."""
        try:
            logger.info(f"Validando relevamiento con datos: {list(attrs.keys())}")
            return super().validate(attrs)
        except Exception as e:
            logger.exception(f"Error en validación de relevamiento: {str(e)}")
            # Intentar identificar el campo problemático
            for field_name, field_value in attrs.items():
                if isinstance(field_value, bool):
                    logger.exception(
                        f"Campo booleano encontrado: {field_name} = {field_value}"
                    )
            raise

    def _convert_yn_to_boolean(self, data):
        """
        Convierte selectivamente valores 'Y'/'N' a booleanos true/false.
        Solo convierte campos que sabemos que son booleanos en Django.
        """
        # Campos que deben ser booleanos (lista blanca)
        boolean_fields = {
            # Nivel raíz
            "responsable_es_referente",
            "servicio_por_turnos",
            # Campos de cocina
            "espacio_elaboracion_alimentos",
            "almacenamiento_alimentos_secos",
            "heladera",
            "freezer",
            "recipiente_residuos_organicos",
            "recipiente_residuos_reciclables",
            "otros_residuos",
            "instalacion_electrica",
            # Campos de prestacion (temporalmente deshabilitados para debug)
            # 'espacio_equipado', 'tiene_ventilacion', 'tiene_salida_emergencia',
            # 'salida_emergencia_senializada', 'tiene_equipacion_incendio',
            # 'tiene_botiquin', 'tiene_buena_iluminacion', 'tiene_sanitarios',
            # Campos de colaboradores
            "colaboradores_capacitados_alimentos",
            "colaboradores_recibieron_capacitacion_alimentos",
            "colaboradores_capacitados_salud_seguridad",
            "colaboradores_recibieron_capacitacion_emergencias",
            "colaboradores_recibieron_capacitacion_violencia",
            # Campos de recursos
            "recibe_donaciones_particulares",
            "recibe_estado_nacional",
            "recibe_estado_provincial",
            "recibe_estado_municipal",
            "recibe_otros",
            # Campos de compras
            "almacen_cercano",
            "verduleria",
            "granja",
            "carniceria",
            "pescaderia",
            "supermercado",
            "mercado_central",
            "ferias_comunales",
            "mayoristas",
            "otro",
            # Campos de anexo
            "comedor_merendero",
            "insumos_organizacion",
            "servicio_internet",
            "zona_inundable",
            "actividades_jardin_maternal",
            "actividades_jardin_infantes",
            "apoyo_escolar",
            "alfabetizacion_terminalidad",
            "capacitaciones_talleres",
            "promocion_salud",
            "actividades_discapacidad",
            "necesidades_alimentarias",
            "actividades_recreativas",
            "actividades_culturales",
            "emprendimientos_productivos",
            "actividades_religiosas",
            "actividades_huerta",
            "espacio_huerta",
            "otras_actividades",
        }

        self._convert_yn_recursive(data, boolean_fields)

    def _convert_yn_recursive(self, data, boolean_fields):
        """Función recursiva para la conversión."""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and key in boolean_fields:
                    if value.upper() == "Y":
                        data[key] = True
                    elif value.upper() == "N":
                        data[key] = False
                elif isinstance(value, (dict, list)):
                    self._convert_yn_recursive(value, boolean_fields)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    self._convert_yn_recursive(item, boolean_fields)

    def _normalize_email(self, value):
        if value is None:
            return None
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    def _validate_nested_email(self, data, field_name, errors):
        if not isinstance(data, dict):
            return

        if "mail" not in data:
            return

        data["mail"] = self._normalize_email(data.get("mail"))
        mail = data["mail"]
        if mail is None:
            return

        if not isinstance(mail, str):
            errors.setdefault(field_name, {})["mail"] = [
                "El correo electrónico debe ser una cadena válida."
            ]
            return

        try:
            validate_unicode_email(mail)
        except DjangoValidationError as exc:
            errors.setdefault(field_name, {})["mail"] = exc.messages

    class Meta:
        model = Relevamiento
        fields = "__all__"
