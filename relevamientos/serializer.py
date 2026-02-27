import logging
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError

from core.validators import validate_unicode_email
from core.utils import format_fecha_django

from relevamientos.models import Relevamiento

from relevamientos.service import RelevamientoService

logger = logging.getLogger("django")


class RelevamientoSerializer(serializers.ModelSerializer):
    CONTACT_BLOCK_FIELDS = ("referente_comedor", "responsable_relevamiento")

    def _run_steps(self, steps):
        for step in steps:
            step()

    def _run_clean_normalization_steps(self):
        self._run_steps(
            (
                lambda: self._convert_yn_to_boolean(self.initial_data),
                self._normalize_fecha_visita,
                self._process_comedor,
                self._process_territorial,
                self._normalize_responsable_es_referente,
                self._normalize_contact_blocks,
                self._validate_contact_blocks_emails,
                self._normalize_imagenes,
            )
        )

    def _run_clean_related_entity_steps(self):
        self._run_steps(
            (
                self._process_related_blocks,
                self._process_responsable_y_referente,
            )
        )

    def _run_clean_pipeline(self):
        self._run_clean_normalization_steps()
        self._run_clean_related_entity_steps()

    def clean(  # pylint: disable=too-many-statements,too-many-branches, too-many-locals
        self,
    ):
        self._run_clean_pipeline()

        return self

    def _get_related_instance(self, field_name):
        if not self.instance:
            return None
        return getattr(self.instance, field_name, None)

    def _normalize_fecha_visita(self):
        if "fecha_visita" in self.initial_data:
            self.initial_data["fecha_visita"] = format_fecha_django(
                self.initial_data["fecha_visita"]
            )

    def _process_comedor(self):
        if "comedor" not in self.initial_data:
            return
        self.initial_data["comedor"] = RelevamientoService.update_comedor(
            self.initial_data["comedor"],
            self._get_related_instance("comedor"),
        )

    def _process_territorial(self):
        if "territorial" not in self.initial_data:
            return
        territorial_data = self.initial_data["territorial"]
        self.initial_data["territorial_nombre"] = territorial_data["nombre"]
        self.initial_data["territorial_uid"] = territorial_data["gestionar_uid"]
        # Evitar que quede un campo no modelado que rompa la validación
        self.initial_data.pop("territorial", None)

    def _replace_related_block_with_id(self, field_name, service_method):
        if field_name not in self.initial_data:
            return
        related_instance = self._get_related_instance(field_name)
        self.initial_data[field_name] = service_method(
            self.initial_data[field_name], related_instance
        ).id

    def _get_related_block_handlers(self):
        return {
            "funcionamiento": RelevamientoService.create_or_update_funcionamiento,
            "espacio": RelevamientoService.create_or_update_espacio,
            "colaboradores": RelevamientoService.create_or_update_colaboradores,
            "recursos": RelevamientoService.create_or_update_recursos,
            "compras": RelevamientoService.create_or_update_compras,
            "anexo": RelevamientoService.create_or_update_anexo,
            "punto_entregas": RelevamientoService.create_or_update_punto_entregas,
            "prestacion": RelevamientoService.create_or_update_prestacion,
            "excepcion": RelevamientoService.create_or_update_excepcion,
        }

    def _process_related_blocks(self):
        for field_name, service_method in self._get_related_block_handlers().items():
            self._replace_related_block_with_id(field_name, service_method)

    def _normalize_responsable_es_referente(self):
        if "responsable_es_referente" not in self.initial_data:
            return
        responsable_es_referente = self.initial_data["responsable_es_referente"]
        if isinstance(responsable_es_referente, str):
            self.initial_data["responsable_es_referente"] = (
                responsable_es_referente.upper() == "Y"
            )

    def _normalize_phone_or_document(self, value):
        if value == "":
            return None
        if isinstance(value, str):
            return value.strip().replace(" ", "").replace("-", "").replace(".", "")
        return value

    def _normalize_contact_block(self, field_name):
        data = self.initial_data.get(field_name)
        if not isinstance(data, dict):
            return

        if "celular" in data:
            data["celular"] = self._normalize_phone_or_document(data["celular"])
        if "documento" in data:
            data["documento"] = self._normalize_phone_or_document(data["documento"])

    def _normalize_contact_blocks(self):
        for field_name in self.CONTACT_BLOCK_FIELDS:
            self._normalize_contact_block(field_name)

    def _validate_contact_blocks_emails(self):
        email_errors = {}
        for field_name in self.CONTACT_BLOCK_FIELDS:
            self._validate_nested_email(
                self.initial_data.get(field_name),
                field_name,
                email_errors,
            )
        if email_errors:
            raise serializers.ValidationError(email_errors)

    def _process_responsable_y_referente(self):
        if (
            "referente_comedor" not in self.initial_data
            and "responsable_relevamiento" not in self.initial_data
        ):
            return

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

    def _normalize_imagenes(self):
        if "imagenes" not in self.initial_data:
            return
        imagenes = self.initial_data["imagenes"]
        if isinstance(imagenes, str):
            self.initial_data["imagenes"] = [
                img.strip() for img in imagenes.split(",") if img.strip()
            ]
        elif isinstance(imagenes, list):
            self.initial_data["imagenes"] = imagenes
        else:
            self.initial_data["imagenes"] = []

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
