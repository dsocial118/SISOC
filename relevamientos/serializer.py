import logging
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models

from comedores.models import Referente
from core.validators import validate_unicode_email
from core.utils import format_fecha_django

from relevamientos.models import (
    ActividadesExtrasSeguimiento,
    AlmacenamientoAlimentosSeguimiento,
    AsistenciaTecnicaSeguimiento,
    CantidadColaboradores,
    CierreSeguimiento,
    ComprasSeguimiento,
    CondicionesHigieneSeguimiento,
    FrecuenciaAlimentosSeguimiento,
    FrecuenciaCompraAlimentosSeguimiento,
    FuncionamientoSeguimiento,
    ItemRecetaSeguimiento,
    MenuSeguimiento,
    PrestacionSeguimiento,
    PrimerSeguimiento,
    Relevamiento,
    RegistroAsistenciaSeguimiento,
    RendicionCuentasSeguimiento,
    RecursosSeguimiento,
    ServiciosBasicosSeguimiento,
    TareasComedorSeguimiento,
    TarjetaSeguimiento,
    TipoModalidadPrestacion,
)

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


class PrimerSeguimientoSerializer(serializers.ModelSerializer):
    BOOLEAN_TRUE_VALUES = {"Y", "S", "SI", "TRUE", "1", "YES"}
    BOOLEAN_FALSE_VALUES = {"N", "NO", "FALSE", "0"}

    SERVICIOS_BASICOS_FIELDS = (
        "agua_potable",
        "gas_red",
        "gas_envasado",
        "electricidad",
        "lenia_carbon",
        "otros_cocina",
        "banio",
        "recipiente",
        "otro_recipiente",
        "observan_animales",
        "elementos_guardados",
    )
    ALMACENAMIENTO_FIELDS = (
        "alimentos_secos_cerrados",
        "alimentos_secos_cerrados_adecuados",
        "alimentos_secos_desparramados",
        "alimentos_secos_noseobservan",
        "otros_alimentos_secos",
        "heladera_existe",
        "freezer_existe",
        "almacenado_cerrados_heladera",
        "almacenado_cerrados_freezer",
        "almacenado_cerradoscondiciones_heladera",
        "almacenado_cerradoscondiciones_freezer",
        "almacenado_desparramados_heladera",
        "almacenado_desparramados_freezer",
        "almacenado_etiquetados_heladera",
        "almacenado_etiquetados_freezer",
        "almacenado_noseobservan_heladera",
        "almacenado_noseobservan_freezer",
        "almacenado_otro",
    )
    HIGIENE_FIELDS = (
        "condiciones_piso_limpieza",
        "condiciones_piso_orden",
        "condiciones_mesada_limpieza",
        "condiciones_mesada_orden",
        "condiciones_mesas_limpieza",
        "condiciones_mesas_orden",
        "condiciones_bacha_limpieza",
        "condiciones_bachas_orden",
        "condiciones_equipamiento_limpieza",
        "condiciones_equipamiento_orden",
        "condiciones_utensillos_limpieza",
        "condiciones_utensillos_orden",
        "entregan_viandas",
    )
    TAREAS_FIELDS = (
        "tareas_comedor_cant_personas",
        "tareas_capacitacion",
        "tareas_capacitacion_especificar",
    )
    RECURSOS_FIELDS = (
        "recursos_comedor_estado_nacional",
        "recursos_comedor_estado_nacional_frecuencia",
        "recursos_comedor_estado_nacional_recibe",
        "recursos_comedor_estado_provincial",
        "recursos_comedor_estado_provincial_frecuencia",
        "recursos_comedor_estado_provincial_recibe",
        "recursos_comedor_estado_municipal",
        "recursos_comedor_estado_municipal_frecuencia",
        "recursos_comedor_estado_municipal_recibe",
        "recursos_comedor_donaciones",
        "recursos_comedor_donaciones_frecuencia",
        "recursos_comedor_donaciones_recibe",
        "financiamiento_principal",
        "financiamiento_principal_otros",
        "financiaminento_otras_necesidades",
        "financiaminento_otras_necesidades_paraque",
        "financiaminento_otras_necesidades_frecuencia",
    )
    COMPRAS_FIELDS = (
        "lugares_compra",
        "lugares_compra_otros",
        "frecuencia_compras",
        "otra_frecuencia_compras",
        "quien_realiza_compras",
        "quien_realiza_compras_otro",
        "elije_alimentos_compra",
    )
    FRECUENCIA_COMPRA_FIELDS = (
        "frecuencia_compra_hortalizas_frutas",
        "frecuencia_compra_leche_yogur_queso",
        "frecuencia_compra_carnes",
        "frecuencia_compra_legumbres",
        "frecuencia_compra_alimentos_secos",
        "frecuencia_compra_pan",
        "frecuencia_compra_huevos",
        "frecuencia_compra_otros",
    )
    MENU_FIELDS = (
        "id_menu",
        "tipo_prestacion",
        "cantidad_personas_menu",
        "cambios_menu",
        "cambios_cuales",
        "cambios_porque",
        "menu_semana_pasada_lunes",
        "menu_semana_pasada_martes",
        "menu_semana_pasada_miercoles",
        "menu_semana_pasada_jueves",
        "menu_semana_pasada_viernes",
        "menu_semana_pasada_sabado",
        "menu_semana_pasada_domingo",
        "menu_preestablecido",
        "menu_preestablecido_porquien",
        "frecuencia_menu_preestablecido",
        "menu_preestablecido_porque",
        "modalidad_prestacion_del_dia",
        "considera_menu_variado",
        "considera_menu_saludable",
        "considera_menu_porque",
        "considera_menu_tamanio_porciones",
        "considera_personas_conformes",
        "considera_personas_conformes_porque",
        "mejora_alimentacion_ofrecida",
    )
    REGISTRO_ASISTENCIA_FIELDS = (
        "registro_asistencia",
        "registro_asistencia_quien",
        "registro_asistencia_metodo",
        "asisten_personas_calle",
        "asisten_personas_calle_cantidad",
        "cantidad_asistencia_total",
    )
    FRECUENCIA_ALIMENTOS_FIELDS = (
        "frecuencia_alimentos_alm_cena_frutas",
        "frecuencia_alimentos_alm_cena_verduras",
        "frecuencia_alimentos_alm_cena_carne",
        "frecuencia_alimentos_alm_cena_pollo",
        "frecuencia_alimentos_alm_cena_pescado",
        "frecuencia_alimentos_alm_cena_fideos",
        "frecuencia_alimentos_alm_cena_legumbres",
        "frecuencia_alimentos_alm_cena_ultraprocesados",
        "frecuencia_alimentos_alm_cena_huevos",
        "frecuencia_alimentos_des_merienda_leche",
        "frecuencia_alimentos_des_merienda_te",
        "frecuencia_alimentos_des_merienda_mate_cocido",
        "frecuencia_alimentos_des_merienda_yogurt",
        "frecuencia_alimentos_des_merienda_queso",
        "frecuencia_alimentos_des_merienda_fruta",
        "frecuencia_alimentos_des_merienda_pan",
        "frecuencia_alimentos_des_merienda_galletitas",
        "frecuencia_alimentos_des_merienda_mermelada_dulce",
    )
    ACTIVIDADES_FIELDS = (
        "id_actividad",
        "talleres_recreativos",
        "talleres_recreativos_donde",
        "talleres_recreativos_frecuencia",
        "apoyo_educativo",
        "apoyo_educativo_donde",
        "apoyo_educativo_frecuencia",
        "grupos_contencion",
        "grupos_contencion_donde",
        "grupos_contencion_frecuencia",
        "actividades_deportivas",
        "actividades_deportivas_donde",
        "actividades_deportivas_frecuencia",
        "talleres_oficio",
        "talleres_oficio_donde",
        "talleres_oficio_frecuencia",
        "huerta",
        "huerta_donde",
        "huerta_frecuencia",
        "actividades_culturales",
        "actividades_culturales_donde",
        "actividades_culturales_frecuencia",
        "actividades_religiosas",
        "actividades_religiosas_donde",
        "actividades_religiosas_frecuencia",
        "actividades_discapacidad",
        "actividades_discapacidad_donde",
        "actividades_discapacidad_frecuencia",
        "ayuda_tramites",
        "ayuda_tramites_donde",
        "ayuda_tramites_frecuencia",
        "servicios_legales",
        "servicios_legales_donde",
        "servicios_legales_frecuencia",
        "terminalidad_educativa",
        "terminalidad_educativa_donde",
        "terminalidad_educativa_frecuencia",
        "emprendimientos_productivos",
        "emprendimientos_productivos_donde",
        "emprendimientos_productivos_frecuencia",
        "promocion_salud",
        "promocion_salud_donde",
        "promocion_salud_frecuencia",
        "otro",
        "otro_donde",
        "otro_frecuencia",
    )
    TARJETA_FIELDS = (
        "id_tarjeta",
        "persona_responsable",
        "llegada_tarjeta",
        "mes_notificado",
        "conforme_tarjeta",
        "conforme_porque",
    )
    RENDICION_FIELDS = (
        "id_rendicion",
        "persona_encargada",
        "recibio_capacitacion",
        "norecibio_porque",
        "sencilla_plataforma",
        "nosencilla_porque",
        "inconvenientes_carga",
        "incovenientes_porque",
    )
    ASISTENCIA_FIELDS = (
        "id_asistencia",
        "socio_organizativo",
        "alimentario_nutricion",
        "seguridad_higiene",
        "administrativo_rendicion",
        "otro",
    )
    CIERRE_FIELDS = (
        "info_adicional",
        "realizo_forma",
        "comentarios_finales",
        "firma_entrevistado",
        "firma_tecnico",
    )

    NESTED_BLOCKS = {
        "frecuencia_compra_alimentos": FRECUENCIA_COMPRA_FIELDS,
        "actividades_extras": ACTIVIDADES_FIELDS,
        "tarjeta": TARJETA_FIELDS,
        "rendicion_cuentas": RENDICION_FIELDS,
        "asistencia_tecnica": ASISTENCIA_FIELDS,
    }
    FIELD_ALIASES = {
        "actividades_depostivas_frecuencia": "actividades_deportivas_frecuencia",
    }

    def clean(self):
        if hasattr(self.initial_data, "copy"):
            self.initial_data = self.initial_data.copy()
        self._normalize_aliases()
        self._normalize_fecha_hora()
        self._process_referente()
        self._process_simple_block(
            "funcionamiento",
            FuncionamientoSeguimiento,
            ("funcionamiento",),
            {"funcionamiento": self.initial_data.get("funcionamiento")},
        )
        self._process_simple_block(
            "servicios_basicos",
            ServiciosBasicosSeguimiento,
            self.SERVICIOS_BASICOS_FIELDS,
        )
        self._process_simple_block(
            "almacenamiento_alimentos",
            AlmacenamientoAlimentosSeguimiento,
            self.ALMACENAMIENTO_FIELDS,
        )
        self._process_simple_block(
            "condiciones_higiene",
            CondicionesHigieneSeguimiento,
            self.HIGIENE_FIELDS,
        )
        self._process_tareas_comedor()
        self._process_simple_block(
            "recursos",
            RecursosSeguimiento,
            self.RECURSOS_FIELDS,
        )
        self._process_simple_block(
            "compras",
            ComprasSeguimiento,
            self.COMPRAS_FIELDS,
        )
        self._process_nested_block(
            "frecuencia_compra_alimentos",
            FrecuenciaCompraAlimentosSeguimiento,
            self.FRECUENCIA_COMPRA_FIELDS,
        )
        self._process_menu()
        self._process_simple_block(
            "registro_asistencia",
            RegistroAsistenciaSeguimiento,
            self.REGISTRO_ASISTENCIA_FIELDS,
        )
        self._process_simple_block(
            "frecuencia_alimentos",
            FrecuenciaAlimentosSeguimiento,
            self.FRECUENCIA_ALIMENTOS_FIELDS,
        )
        self._process_nested_block(
            "actividades_extras",
            ActividadesExtrasSeguimiento,
            self.ACTIVIDADES_FIELDS,
        )
        self._process_nested_block("tarjeta", TarjetaSeguimiento, self.TARJETA_FIELDS)
        self._process_nested_block(
            "rendicion_cuentas",
            RendicionCuentasSeguimiento,
            self.RENDICION_FIELDS,
        )
        self._process_nested_block(
            "asistencia_tecnica",
            AsistenciaTecnicaSeguimiento,
            self.ASISTENCIA_FIELDS,
        )
        self._process_simple_block("cierre", CierreSeguimiento, self.CIERRE_FIELDS)
        self._process_prestaciones()
        self._drop_external_fields()
        return self

    def _normalize_aliases(self):
        for old_key, new_key in self.FIELD_ALIASES.items():
            if old_key in self.initial_data and new_key not in self.initial_data:
                self.initial_data[new_key] = self.initial_data[old_key]
            self.initial_data.pop(old_key, None)

    def _normalize_fecha_hora(self):
        if not self.initial_data.get("fecha_hora"):
            self.initial_data.pop("fecha_hora", None)

    def _drop_external_fields(self):
        for field_name in (
            "sisoc_id",
            "id_seguimiento1",
            "cod_pnud",
            "prestaciones_seguimientos",
            "menu",
        ):
            self.initial_data.pop(field_name, None)

    def _has_values(self, data):
        return any(value not in (None, "", [], {}) for value in data.values())

    def _clean_scalar(self, value, model_field):
        if value == "":
            return None
        if value is None:
            return None
        if isinstance(model_field, models.BooleanField):
            return self._to_bool(value)
        if isinstance(
            model_field,
            (
                models.IntegerField,
                models.PositiveIntegerField,
                models.PositiveSmallIntegerField,
            ),
        ):
            return self._to_int(value)
        if isinstance(model_field, models.ForeignKey):
            return value
        return value

    def _to_bool(self, value):
        if isinstance(value, bool) or value is None:
            return value
        if isinstance(value, str):
            normalized = value.strip().upper()
            if normalized == "":
                return None
            if normalized in self.BOOLEAN_TRUE_VALUES:
                return True
            if normalized in self.BOOLEAN_FALSE_VALUES:
                return False
        return value

    def _to_int(self, value):
        if value in (None, ""):
            return None
        return int(value)

    def _field(self, model, field_name):
        return model._meta.get_field(field_name)

    def _normalize_block_data(self, model, data):
        normalized = {}
        for field_name, value in data.items():
            field = self._field(model, field_name)
            normalized[field_name] = self._clean_scalar(value, field)
        return normalized

    def _extract_flat_fields(self, fields):
        data = {
            field_name: self.initial_data.get(field_name)
            for field_name in fields
            if field_name in self.initial_data
        }
        for field_name in fields:
            self.initial_data.pop(field_name, None)
        return data

    def _upsert_block(self, model, data, current_instance=None, lookup_field=None):
        if not self._has_values(data):
            return None

        normalized = self._normalize_block_data(model, data)
        lookup_value = normalized.get(lookup_field) if lookup_field else None
        instance = current_instance
        if lookup_field and lookup_value:
            instance = model.objects.filter(**{lookup_field: lookup_value}).first()

        if instance is None:
            instance = model(**normalized)
        else:
            for field_name, value in normalized.items():
                setattr(instance, field_name, value)

        instance.full_clean()
        instance.save()
        return instance

    def _process_simple_block(self, relation_name, model, fields, extra_data=None):
        data = extra_data or self._extract_flat_fields(fields)
        if extra_data:
            for field_name in fields:
                self.initial_data.pop(field_name, None)
        current = getattr(self.instance, relation_name, None) if self.instance else None
        instance = self._upsert_block(model, data, current)
        if instance is not None:
            self.initial_data[relation_name] = instance.id

    def _process_nested_block(self, relation_name, model, fields):
        nested_data = self.initial_data.pop(relation_name, None)
        if not isinstance(nested_data, dict):
            data = self._extract_flat_fields(fields)
        else:
            data = {field_name: nested_data.get(field_name) for field_name in fields}
        lookup_field = fields[0] if fields and fields[0].startswith("id_") else None
        current = getattr(self.instance, relation_name, None) if self.instance else None
        instance = self._upsert_block(model, data, current, lookup_field)
        if instance is not None:
            self.initial_data[relation_name] = instance.id

    def _process_tareas_comedor(self):
        data = self._extract_flat_fields(self.TAREAS_FIELDS)
        if not self._has_values(data):
            return
        cantidad = data.get("tareas_comedor_cant_personas")
        if cantidad not in (None, ""):
            data["tareas_comedor_cant_personas"] = self._resolve_named_catalog(
                CantidadColaboradores,
                cantidad,
            )
        current = (
            getattr(self.instance, "tareas_comedor", None) if self.instance else None
        )
        instance = self._upsert_block(TareasComedorSeguimiento, data, current)
        if instance is not None:
            self.initial_data["tareas_comedor"] = instance.id

    def _process_menu(self):
        nested_menu = self.initial_data.pop("menu", None)
        data = self._extract_flat_fields(self.MENU_FIELDS)
        receta_data = None
        if isinstance(nested_menu, dict):
            receta_data = nested_menu.get("receta")
            for field_name in (
                "id_menu",
                "tipo_prestacion",
                "cantidad_personas_menu",
            ):
                if nested_menu.get(field_name) not in (None, ""):
                    data[field_name] = nested_menu[field_name]

        modalidad = data.get("modalidad_prestacion_del_dia")
        if modalidad not in (None, ""):
            data["modalidad_prestacion_del_dia"] = self._resolve_named_catalog(
                TipoModalidadPrestacion,
                modalidad,
            )

        current = getattr(self.instance, "menu", None) if self.instance else None
        menu = self._upsert_block(MenuSeguimiento, data, current, "id_menu")
        if menu is not None:
            self.initial_data["menu"] = menu.id
            self._process_receta(menu, receta_data)

    def _process_receta(self, menu, receta_data):
        if not isinstance(receta_data, dict):
            return
        fields = ("id_item_receta", "ingrediente", "unidad_medida", "cantidad_medida")
        data = {field_name: receta_data.get(field_name) for field_name in fields}
        self._upsert_child(
            ItemRecetaSeguimiento,
            data,
            {
                "parent_field": "menu",
                "parent": menu,
                "lookup_field": "id_item_receta",
            },
        )

    def _process_prestaciones(self):
        prestaciones_data = self.initial_data.get("prestaciones_seguimientos")
        if prestaciones_data is None:
            return
        if isinstance(prestaciones_data, dict):
            prestaciones_data = [prestaciones_data]
        if not isinstance(prestaciones_data, list):
            raise serializers.ValidationError(
                {"prestaciones_seguimientos": "Formato invalido."}
            )
        fields = (
            "id_prestacion_seg",
            "dias_prestacion",
            "tipo_prestacion",
            "ap_presencial",
            "ap_vianda",
            "de_presencial",
            "de_vianda",
        )
        for prestacion_data in prestaciones_data:
            if not isinstance(prestacion_data, dict):
                raise serializers.ValidationError(
                    {"prestaciones_seguimientos": "Formato invalido."}
                )
            data = {
                field_name: prestacion_data.get(field_name) for field_name in fields
            }
            self._upsert_child(
                PrestacionSeguimiento,
                data,
                {
                    "parent_field": "seguimiento",
                    "parent": self.instance,
                    "lookup_field": "id_prestacion_seg",
                },
            )

    def _upsert_child(self, model, data, relation):
        if not self._has_values(data):
            return None
        normalized = self._normalize_block_data(model, data)
        parent_field = relation["parent_field"]
        parent = relation["parent"]
        lookup_field = relation["lookup_field"]
        normalized[parent_field] = parent
        lookup_value = normalized.get(lookup_field)
        instance = None
        if lookup_value:
            instance = model.objects.filter(**{lookup_field: lookup_value}).first()
        if instance is None:
            instance = model(**normalized)
        else:
            for field_name, value in normalized.items():
                setattr(instance, field_name, value)
        instance.full_clean()
        instance.save()
        return instance

    def _resolve_named_catalog(self, model, value):
        if value in (None, ""):
            return None
        if isinstance(value, model):
            return value
        if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
            found = model.objects.filter(pk=int(value)).first()
            if found:
                return found
        return model.objects.get_or_create(nombre=str(value).strip())[0]

    def _process_referente(self):
        data = self.initial_data.get("referente")
        if not isinstance(data, dict):
            return
        referente_data = {
            "nombre": data.get("nombre_apellido"),
            "mail": self._normalize_string(data.get("mail_referente")),
            "celular": self._to_int_or_none(data.get("celular_referente")),
            "funcion": data.get("funcion_cumple"),
        }
        if not self._has_values(referente_data):
            self.initial_data.pop("referente", None)
            return
        external_id = self._normalize_string(data.get("id_referente"))
        referente = None
        if external_id:
            referente = (
                Referente.objects.filter(documento__isnull=True)
                .filter(nombre=referente_data["nombre"])
                .last()
            )
        if referente is None:
            referente = Referente(**referente_data)
        else:
            for field_name, value in referente_data.items():
                setattr(referente, field_name, value)
        referente.save()
        self.initial_data["referente"] = referente.id

    def _normalize_string(self, value):
        if value is None:
            return None
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    def _to_int_or_none(self, value):
        if value in (None, ""):
            return None
        return int(
            str(value).strip().replace(" ", "").replace("-", "").replace(".", "")
        )

    class Meta:
        model = PrimerSeguimiento
        fields = "__all__"
