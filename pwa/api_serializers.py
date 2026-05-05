import re
from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import OperationalError, ProgrammingError
from rest_framework import serializers

from comunicados.models import Comunicado, ComunicadoAdjunto, SubtipoComunicado
from comedores.models import CursoAppMobile, Nomina
from comedores.models import ActividadColaboradorEspacio, ColaboradorEspacio
from core.models import Dia, Sexo

from pwa.models import (
    ActividadEspacioPWA,
    CatalogoActividadPWA,
    ColaboradorEspacioPWA,
    InscriptoActividadEspacioPWA,
    PushSubscriptionPWA,
    RegistroAsistenciaNominaPWA,
)

DNI_REGEX = re.compile(r"^\d{7,8}$")
PHONE_REGEX = re.compile(r"^[\d+\-() ]{6,30}$")
TIME_RANGE_REGEX = re.compile(
    r"^(?P<start>\d{1,2}:\d{2})(?:\s*(?:a|-)\s*(?P<end>\d{1,2}:\d{2}))?$"
)


def _format_activity_schedule(start_time, end_time):
    if start_time and end_time:
        return f"{start_time:%H:%M} a {end_time:%H:%M}"
    if start_time:
        return start_time.strftime("%H:%M")
    return ""


def _parse_legacy_schedule(value):
    raw_value = (value or "").strip()
    if not raw_value:
        return None, None

    match = TIME_RANGE_REGEX.fullmatch(raw_value)
    if not match:
        return None, None

    start_time = datetime.strptime(match.group("start"), "%H:%M").time()
    end_raw = match.group("end")
    if not end_raw:
        return start_time, None
    end_time = datetime.strptime(end_raw, "%H:%M").time()
    return start_time, end_time


class ColaboradorEspacioPWASerializer(serializers.ModelSerializer):
    class Meta:
        model = ColaboradorEspacioPWA
        fields = (
            "id",
            "comedor",
            "nombre",
            "apellido",
            "dni",
            "telefono",
            "email",
            "rol_funcion",
            "activo",
            "fecha_creacion",
            "fecha_actualizacion",
            "fecha_baja",
        )
        read_only_fields = (
            "id",
            "comedor",
            "activo",
            "fecha_creacion",
            "fecha_actualizacion",
            "fecha_baja",
        )

    def validate_nombre(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Este campo es obligatorio.")
        return value

    def validate_apellido(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Este campo es obligatorio.")
        return value

    def validate_rol_funcion(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Este campo es obligatorio.")
        return value

    def validate_dni(self, value):
        dni = (value or "").strip()
        if not DNI_REGEX.fullmatch(dni):
            raise serializers.ValidationError(
                "Formato de DNI inválido. Debe contener 7 u 8 dígitos."
            )
        return dni

    def validate_telefono(self, value):
        phone = (value or "").strip()
        if not PHONE_REGEX.fullmatch(phone):
            raise serializers.ValidationError(
                "Formato de teléfono inválido. Solo números y + - ( ) espacios."
            )
        return phone

    def validate_email(self, value):
        return (value or "").strip().lower()

    def validate(self, attrs):
        attrs = super().validate(attrs)
        comedor_id = self.context.get("comedor_id")
        dni = attrs.get("dni")
        if not comedor_id or not dni:
            return attrs

        queryset = ColaboradorEspacioPWA.objects.filter(
            comedor_id=comedor_id,
            dni=dni,
            activo=True,
        )
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError(
                {"dni": "Ya existe un colaborador activo con ese DNI en este espacio."}
            )
        return attrs


class ColaboradorEspacioPWAListSerializer(serializers.ModelSerializer):
    ciudadano_id = serializers.IntegerField(read_only=True)
    nombre = serializers.CharField(source="ciudadano.nombre", read_only=True)
    apellido = serializers.CharField(source="ciudadano.apellido", read_only=True)
    dni = serializers.SerializerMethodField()
    prefijo_cuil = serializers.CharField(read_only=True)
    cuil_cuit = serializers.CharField(read_only=True)
    sufijo_cuil = serializers.CharField(read_only=True)
    sexo = serializers.CharField(source="sexo_display", read_only=True)
    fecha_nacimiento = serializers.DateField(read_only=True)
    edad = serializers.IntegerField(read_only=True)
    actividades = serializers.SerializerMethodField()
    activo = serializers.SerializerMethodField()

    class Meta:
        model = ColaboradorEspacio
        fields = (
            "id",
            "comedor",
            "ciudadano_id",
            "nombre",
            "apellido",
            "dni",
            "prefijo_cuil",
            "cuil_cuit",
            "sufijo_cuil",
            "sexo",
            "genero",
            "fecha_nacimiento",
            "edad",
            "codigo_telefono",
            "numero_telefono",
            "fecha_alta",
            "fecha_baja",
            "activo",
            "actividades",
            "fecha_creado",
            "fecha_modificado",
        )
        read_only_fields = fields

    def get_dni(self, obj):
        return str(obj.dni or "")

    def get_actividades(self, obj):
        actividades = getattr(obj, "actividades", None)
        if actividades is None:
            actividades = obj.actividades.all()
        return [
            {
                "id": actividad.id,
                "alias": actividad.alias,
                "nombre": actividad.nombre,
            }
            for actividad in actividades.order_by("orden", "id")
        ]

    def get_activo(self, obj):
        return obj.fecha_baja is None


class ColaboradorEspacioPWACreateUpdateSerializer(serializers.Serializer):
    ciudadano_id = serializers.IntegerField(required=False)
    dni = serializers.CharField(required=False, allow_blank=False)
    genero = serializers.ChoiceField(
        choices=ColaboradorEspacio.GeneroChoices.choices, required=False
    )
    codigo_telefono = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    numero_telefono = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    fecha_alta = serializers.DateField(required=False)
    fecha_baja = serializers.DateField(required=False, allow_null=True)
    actividad_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=False,
    )

    def validate_dni(self, value):
        dni = (value or "").strip()
        if not DNI_REGEX.fullmatch(dni):
            raise serializers.ValidationError(
                "Formato de DNI inválido. Debe contener 7 u 8 dígitos."
            )
        return dni

    def validate_codigo_telefono(self, value):
        phone = str(value or "").strip()
        if phone and not phone.isdigit():
            raise serializers.ValidationError(
                "El código de teléfono debe contener solo números."
            )
        return phone or None

    def validate_numero_telefono(self, value):
        phone = str(value or "").strip()
        if phone and not phone.isdigit():
            raise serializers.ValidationError(
                "El número de teléfono debe contener solo números."
            )
        return phone or None

    def validate_actividad_ids(self, value):
        actividad_ids = list(dict.fromkeys(value or []))
        actividades_validas = set(
            ActividadColaboradorEspacio.objects.filter(
                id__in=actividad_ids,
                activo=True,
            ).values_list("id", flat=True)
        )
        if len(actividades_validas) != len(actividad_ids):
            raise serializers.ValidationError(
                "Hay actividades inválidas o inactivas en la selección."
            )
        return actividad_ids

    def validate(self, attrs):
        attrs = super().validate(attrs)
        is_create = self.instance is None

        if is_create and not attrs.get("ciudadano_id") and not attrs.get("dni"):
            raise serializers.ValidationError(
                {
                    "dni": (
                        "Debe informar un DNI para buscar en SISOC/RENAPER o enviar "
                        "un ciudadano existente."
                    )
                }
            )

        if is_create and "fecha_alta" not in attrs:
            raise serializers.ValidationError(
                {"fecha_alta": "Este campo es obligatorio."}
            )

        if is_create and not attrs.get("actividad_ids"):
            raise serializers.ValidationError(
                {"actividad_ids": "Debe seleccionar al menos una actividad."}
            )

        fecha_alta = attrs.get("fecha_alta")
        fecha_baja = attrs.get("fecha_baja")
        instance_fecha_alta = getattr(self.instance, "fecha_alta", None)
        effective_fecha_alta = fecha_alta or instance_fecha_alta
        if effective_fecha_alta and fecha_baja and fecha_baja < effective_fecha_alta:
            raise serializers.ValidationError(
                {
                    "fecha_baja": (
                        "La fecha de baja no puede ser anterior a la fecha de alta."
                    )
                }
            )

        return attrs

    def create(self, validated_data):
        raise NotImplementedError(
            "ColaboradorEspacioPWACreateUpdateSerializer no implementa create()."
        )

    def update(self, instance, validated_data):
        raise NotImplementedError(
            "ColaboradorEspacioPWACreateUpdateSerializer no implementa update()."
        )


class ColaboradorActividadCatalogoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActividadColaboradorEspacio
        fields = ("id", "alias", "nombre", "orden")
        read_only_fields = fields


class ColaboradorGeneroPWAListSerializer(serializers.Serializer):
    id = serializers.CharField()
    label = serializers.CharField()

    def create(self, validated_data):
        raise NotImplementedError(
            "ColaboradorGeneroPWAListSerializer no implementa create()."
        )

    def update(self, instance, validated_data):
        raise NotImplementedError(
            "ColaboradorGeneroPWAListSerializer no implementa update()."
        )


class CatalogoActividadPWASerializer(serializers.ModelSerializer):
    class Meta:
        model = CatalogoActividadPWA
        fields = (
            "id",
            "categoria",
            "actividad",
        )


class ActividadEspacioPWAListSerializer(serializers.ModelSerializer):
    categoria = serializers.CharField(
        source="catalogo_actividad.categoria", read_only=True
    )
    actividad = serializers.CharField(
        source="catalogo_actividad.actividad", read_only=True
    )
    dia_actividad_nombre = serializers.CharField(
        source="dia_actividad.nombre", read_only=True
    )
    cantidad_inscriptos = serializers.IntegerField(read_only=True)
    horario_actividad = serializers.SerializerMethodField()

    class Meta:
        model = ActividadEspacioPWA
        fields = (
            "id",
            "comedor",
            "catalogo_actividad",
            "categoria",
            "actividad",
            "dia_actividad",
            "dia_actividad_nombre",
            "hora_inicio",
            "hora_fin",
            "horario_actividad",
            "cantidad_inscriptos",
            "activo",
            "fecha_alta",
            "fecha_actualizacion",
            "fecha_baja",
        )
        read_only_fields = fields

    def get_horario_actividad(self, obj):
        return _format_activity_schedule(obj.hora_inicio, obj.hora_fin) or (
            obj.horario_actividad or ""
        )


class ActividadEspacioPWACreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActividadEspacioPWA
        fields = (
            "id",
            "comedor",
            "catalogo_actividad",
            "dia_actividad",
            "hora_inicio",
            "hora_fin",
            "horario_actividad",
            "activo",
            "fecha_alta",
            "fecha_actualizacion",
            "fecha_baja",
        )
        read_only_fields = (
            "id",
            "comedor",
            "activo",
            "fecha_alta",
            "fecha_actualizacion",
            "fecha_baja",
        )
        extra_kwargs = {
            "horario_actividad": {"required": False, "allow_blank": True},
            "hora_inicio": {"required": False},
            "hora_fin": {"required": False},
        }

    def validate_catalogo_actividad(self, value):
        if value and not value.activo:
            raise serializers.ValidationError(
                "La actividad seleccionada no esta disponible."
            )
        return value

    def validate_horario_actividad(self, value):
        value = (value or "").strip()
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        hora_inicio = attrs.get(
            "hora_inicio",
            getattr(self.instance, "hora_inicio", None),
        )
        hora_fin = attrs.get(
            "hora_fin",
            getattr(self.instance, "hora_fin", None),
        )
        horario_actividad = attrs.get("horario_actividad")

        if (hora_inicio is None or hora_fin is None) and horario_actividad:
            parsed_start, parsed_end = _parse_legacy_schedule(horario_actividad)
            hora_inicio = hora_inicio or parsed_start
            hora_fin = hora_fin or parsed_end

        if hora_inicio is None:
            raise serializers.ValidationError(
                {"hora_inicio": "Este campo es obligatorio."}
            )

        if hora_fin is None:
            raise serializers.ValidationError(
                {"hora_fin": "Este campo es obligatorio."}
            )

        if hora_fin <= hora_inicio:
            raise serializers.ValidationError(
                {"hora_fin": ("La hora de fin debe ser posterior a la hora de inicio.")}
            )

        dia_actividad = attrs.get(
            "dia_actividad",
            getattr(self.instance, "dia_actividad", None),
        )
        catalogo_actividad = attrs.get(
            "catalogo_actividad",
            getattr(self.instance, "catalogo_actividad", None),
        )
        comedor_id = self.context.get("comedor_id") or getattr(
            self.instance, "comedor_id", None
        )
        if dia_actividad and comedor_id and catalogo_actividad:
            overlapping = ActividadEspacioPWA.objects.filter(
                comedor_id=comedor_id,
                dia_actividad=dia_actividad,
                catalogo_actividad=catalogo_actividad,
                activo=True,
                hora_inicio__lt=hora_fin,
                hora_fin__gt=hora_inicio,
            )
            if self.instance:
                overlapping = overlapping.exclude(pk=self.instance.pk)
            if overlapping.exists():
                raise serializers.ValidationError(
                    {
                        "hora_inicio": (
                            "Ya existe la misma actividad con un horario que se pisa ese día."
                        )
                    }
                )

        attrs["hora_inicio"] = hora_inicio
        attrs["hora_fin"] = hora_fin
        attrs["horario_actividad"] = _format_activity_schedule(hora_inicio, hora_fin)
        return attrs


class InscriptoActividadPWAListSerializer(serializers.ModelSerializer):
    nombre = serializers.SerializerMethodField()
    apellido = serializers.SerializerMethodField()
    dni = serializers.SerializerMethodField()
    genero = serializers.SerializerMethodField()
    fecha_nacimiento = serializers.SerializerMethodField()

    class Meta:
        model = InscriptoActividadEspacioPWA
        fields = (
            "id",
            "nomina",
            "nombre",
            "apellido",
            "dni",
            "genero",
            "fecha_nacimiento",
        )

    def _get_ciudadano(self, obj):
        nomina = getattr(obj, "nomina", None)
        return getattr(nomina, "ciudadano", None)

    def get_nombre(self, obj):
        ciudadano = self._get_ciudadano(obj)
        return ciudadano.nombre if ciudadano else ""

    def get_apellido(self, obj):
        ciudadano = self._get_ciudadano(obj)
        return ciudadano.apellido if ciudadano else ""

    def get_dni(self, obj):
        ciudadano = self._get_ciudadano(obj)
        return str(ciudadano.documento) if ciudadano and ciudadano.documento else ""

    def get_genero(self, obj):
        ciudadano = self._get_ciudadano(obj)
        sexo = getattr(ciudadano, "sexo", None) if ciudadano else None
        return sexo.sexo if sexo else ""

    def get_fecha_nacimiento(self, obj):
        ciudadano = self._get_ciudadano(obj)
        return ciudadano.fecha_nacimiento if ciudadano else None


class DiaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dia
        fields = (
            "id",
            "nombre",
        )


class SexoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sexo
        fields = ("id", "sexo")


class NominaEspacioPWAListSerializer(serializers.ModelSerializer):
    nombre = serializers.SerializerMethodField()
    apellido = serializers.SerializerMethodField()
    dni = serializers.SerializerMethodField()
    genero = serializers.SerializerMethodField()
    fecha_nacimiento = serializers.SerializerMethodField()
    badges = serializers.SerializerMethodField()
    actividades = serializers.SerializerMethodField()
    cantidad_actividades = serializers.SerializerMethodField()
    es_indocumentado = serializers.SerializerMethodField()
    identificador_interno = serializers.SerializerMethodField()
    asistencia_mes_actual = serializers.SerializerMethodField()
    historial_asistencias = serializers.SerializerMethodField()
    observaciones = serializers.CharField(read_only=True, allow_null=True)
    observaciones_historial = serializers.SerializerMethodField()

    class Meta:
        model = Nomina
        fields = (
            "id",
            "nombre",
            "apellido",
            "dni",
            "genero",
            "fecha_nacimiento",
            "estado",
            "badges",
            "actividades",
            "cantidad_actividades",
            "es_indocumentado",
            "identificador_interno",
            "asistencia_mes_actual",
            "historial_asistencias",
            "observaciones",
            "observaciones_historial",
        )

    def _get_ciudadano(self, obj):
        return getattr(obj, "ciudadano", None)

    def _get_profile(self, obj):
        try:
            return obj.perfil_pwa
        except ObjectDoesNotExist:
            return None

    def get_nombre(self, obj):
        ciudadano = self._get_ciudadano(obj)
        return ciudadano.nombre if ciudadano else ""

    def get_apellido(self, obj):
        ciudadano = self._get_ciudadano(obj)
        return ciudadano.apellido if ciudadano else ""

    def get_dni(self, obj):
        ciudadano = self._get_ciudadano(obj)
        return str(ciudadano.documento) if ciudadano and ciudadano.documento else ""

    def get_genero(self, obj):
        ciudadano = self._get_ciudadano(obj)
        sexo = getattr(ciudadano, "sexo", None) if ciudadano else None
        return sexo.sexo if sexo else ""

    def get_fecha_nacimiento(self, obj):
        ciudadano = self._get_ciudadano(obj)
        return ciudadano.fecha_nacimiento if ciudadano else None

    def get_badges(self, obj):
        profile = self._get_profile(obj)
        badges = []
        asistencia_alimentaria = (
            True if profile is None else bool(profile.asistencia_alimentaria)
        )
        asistencia_actividades = (
            False if profile is None else bool(profile.asistencia_actividades)
        )
        if asistencia_alimentaria:
            badges.append("Alimentación")
        if asistencia_actividades:
            badges.append("Actividades")
        return badges

    def get_actividades(self, obj):
        include_details = self.context.get("include_details", False)
        if not include_details:
            return []
        items = []
        inscripciones_activas = getattr(
            obj, "inscripciones_actividad_pwa_activas", None
        )
        if inscripciones_activas is None:
            inscripciones_activas = obj.inscripciones_actividad_pwa.filter(activo=True)
        for inscripto in inscripciones_activas:
            actividad_espacio = getattr(inscripto, "actividad_espacio", None)
            if not actividad_espacio:
                continue
            catalogo = getattr(actividad_espacio, "catalogo_actividad", None)
            if not catalogo:
                continue
            items.append(
                {
                    "actividad_id": actividad_espacio.id,
                    "categoria": catalogo.categoria,
                    "actividad": catalogo.actividad,
                    "dia": getattr(actividad_espacio.dia_actividad, "nombre", ""),
                    "horario": _format_activity_schedule(
                        actividad_espacio.hora_inicio,
                        actividad_espacio.hora_fin,
                    )
                    or actividad_espacio.horario_actividad,
                }
            )
        return items

    def get_cantidad_actividades(self, obj):
        include_details = self.context.get("include_details", False)
        if include_details:
            actividades = self.get_actividades(obj)
            return len({item["actividad"] for item in actividades})

        actividades_count = getattr(obj, "cantidad_actividades_pwa", None)
        if actividades_count is not None:
            return actividades_count

        return (
            obj.inscripciones_actividad_pwa.filter(activo=True)
            .values("actividad_espacio__catalogo_actividad_id")
            .distinct()
            .count()
        )

    def get_es_indocumentado(self, obj):
        profile = self._get_profile(obj)
        return bool(profile.es_indocumentado) if profile else False

    def get_identificador_interno(self, obj):
        profile = self._get_profile(obj)
        return profile.identificador_interno if profile else None

    def _serialize_registro_asistencia(self, registro):
        if not registro:
            return None
        tomado_por = getattr(registro, "tomado_por", None)
        return {
            "id": registro.id,
            "periodicidad": registro.periodicidad,
            "periodo_referencia": registro.periodo_referencia,
            "periodo_label": registro.periodo_referencia.strftime("%m/%Y"),
            "fecha_toma_asistencia": registro.fecha_toma_asistencia,
            "tomado_por": tomado_por.username if tomado_por else None,
        }

    def get_asistencia_mes_actual(self, obj):
        registro = getattr(obj, "asistencia_mes_actual_pwa", None)
        if isinstance(registro, list):
            registro = registro[0] if registro else None
        return self._serialize_registro_asistencia(registro)

    def get_historial_asistencias(self, obj):
        registros = getattr(obj, "historial_asistencias_pwa", None)
        if registros is None:
            return []
        return [self._serialize_registro_asistencia(registro) for registro in registros]

    def get_observaciones_historial(self, obj):
        observaciones = getattr(obj, "observaciones_pwa", None)
        if observaciones is None:
            return []
        if hasattr(observaciones, "all"):
            try:
                observaciones = list(observaciones.all())
            except (OperationalError, ProgrammingError):
                return []
        else:
            observaciones = list(observaciones)
        return [
            {
                "id": observacion.id,
                "texto": observacion.texto,
                "fecha_creacion": observacion.fecha_creacion,
                "creada_por": (
                    observacion.creada_por.username if observacion.creada_por else None
                ),
            }
            for observacion in observaciones
        ]


class RegistroAsistenciaNominaPWAListSerializer(serializers.ModelSerializer):
    tomado_por = serializers.CharField(source="tomado_por.username", read_only=True)
    periodo_label = serializers.SerializerMethodField()

    class Meta:
        model = RegistroAsistenciaNominaPWA
        fields = (
            "id",
            "periodicidad",
            "periodo_referencia",
            "periodo_label",
            "fecha_toma_asistencia",
            "tomado_por",
        )
        read_only_fields = fields

    def get_periodo_label(self, obj):
        return obj.periodo_referencia.strftime("%m/%Y")


class NominaEspacioPWACreateUpdateSerializer(serializers.Serializer):
    ciudadano_id = serializers.IntegerField(required=False)
    nombre = serializers.CharField(required=False, allow_blank=False)
    apellido = serializers.CharField(required=False, allow_blank=False)
    dni = serializers.CharField(required=False, allow_blank=False)
    sexo_id = serializers.IntegerField(required=False, allow_null=True)
    fecha_nacimiento = serializers.DateField(required=False)
    es_indocumentado = serializers.BooleanField(required=False, default=False)
    identificador_interno = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    asistencia_alimentaria = serializers.BooleanField(required=False, default=False)
    asistencia_actividades = serializers.BooleanField(required=False, default=False)
    actividad_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=True,
    )
    observaciones = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    estado = serializers.ChoiceField(choices=Nomina.ESTADO_CHOICES, required=False)

    def validate_dni(self, value):
        dni = (value or "").strip()
        if not DNI_REGEX.fullmatch(dni):
            raise serializers.ValidationError(
                "Formato de DNI inválido. Debe contener 7 u 8 dígitos."
            )
        return dni

    def validate(self, attrs):
        attrs = super().validate(attrs)
        es_indocumentado = bool(attrs.get("es_indocumentado"))
        if es_indocumentado:
            for field in ("nombre", "apellido", "fecha_nacimiento", "sexo_id"):
                if field not in attrs:
                    raise serializers.ValidationError(
                        {field: "Este campo es obligatorio para indocumentados."}
                    )
        return attrs

    def create(self, validated_data):
        raise NotImplementedError(
            "NominaEspacioPWACreateUpdateSerializer no implementa create()."
        )

    def update(self, instance, validated_data):
        raise NotImplementedError(
            "NominaEspacioPWACreateUpdateSerializer no implementa update()."
        )


class NominaRenaperPreviewSerializer(serializers.Serializer):
    dni = serializers.CharField(required=True, allow_blank=False)

    def validate_dni(self, value):
        dni = (value or "").strip()
        if not DNI_REGEX.fullmatch(dni):
            raise serializers.ValidationError(
                "Formato de DNI inválido. Debe contener 7 u 8 dígitos."
            )
        return dni

    def create(self, validated_data):
        raise NotImplementedError(
            "NominaRenaperPreviewSerializer no implementa create()."
        )

    def update(self, instance, validated_data):
        raise NotImplementedError(
            "NominaRenaperPreviewSerializer no implementa update()."
        )


class NominaAsistenciaAlimentariaBulkSerializer(serializers.Serializer):
    nomina_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=True,
        allow_empty=True,
    )

    def validate_nomina_ids(self, value):
        return list(dict.fromkeys(value or []))

    def create(self, validated_data):
        raise NotImplementedError(
            "NominaAsistenciaAlimentariaBulkSerializer no implementa create()."
        )

    def update(self, instance, validated_data):
        raise NotImplementedError(
            "NominaAsistenciaAlimentariaBulkSerializer no implementa update()."
        )


class MensajeAdjuntoPWASerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = ComunicadoAdjunto
        fields = ("id", "nombre_original", "fecha_subida", "url")

    def get_url(self, obj):
        if not obj.archivo:
            return None
        request = self.context.get("request")
        url = obj.archivo.url
        return request.build_absolute_uri(url) if request else url


class MensajeEspacioPWASerializer(serializers.ModelSerializer):
    adjuntos = MensajeAdjuntoPWASerializer(many=True, read_only=True)
    cuerpo = serializers.SerializerMethodField()
    visto = serializers.SerializerMethodField()
    fecha_visto = serializers.SerializerMethodField()
    seccion = serializers.SerializerMethodField()
    accion = serializers.SerializerMethodField()

    ACTION_MARKER_RE = re.compile(
        r"\[SISOC_ACCION\](?P<action>[^\[]+)\[/SISOC_ACCION\]",
        re.MULTILINE,
    )

    class Meta:
        model = Comunicado
        fields = (
            "id",
            "titulo",
            "cuerpo",
            "accion",
            "destacado",
            "subtipo",
            "seccion",
            "fecha_creacion",
            "fecha_publicacion",
            "fecha_vencimiento",
            "visto",
            "fecha_visto",
            "adjuntos",
        )

    def _extract_action_payload(self, obj):
        cuerpo = str(getattr(obj, "cuerpo", "") or "")
        match = self.ACTION_MARKER_RE.search(cuerpo)
        if not match:
            return None
        return match.group("action").strip()

    def get_cuerpo(self, obj):
        cuerpo = str(getattr(obj, "cuerpo", "") or "")
        cleaned = self.ACTION_MARKER_RE.sub("", cuerpo).strip()
        return cleaned

    def get_accion(self, obj):
        payload = self._extract_action_payload(obj)
        if not payload:
            return None
        action_type, separator, value = payload.partition(":")
        if action_type != "rendicion_detalle" or not separator:
            return None
        try:
            rendicion_id = int(value)
        except (TypeError, ValueError):
            return None
        return {
            "tipo": "rendicion_detalle",
            "rendicion_id": rendicion_id,
        }

    def _get_lectura(self, obj):
        lecturas = getattr(obj, "lecturas_pwa_usuario_espacio", None)
        if lecturas is not None:
            comedor_id = self.context.get("comedor_id")
            if obj.subtipo == SubtipoComunicado.INSTITUCIONAL:
                return lecturas[0] if lecturas else None
            for lectura in lecturas:
                if getattr(lectura, "comedor_id", None) == comedor_id:
                    return lectura
            return None

        comedor_id = self.context.get("comedor_id")
        user = self.context.get("user")
        if not comedor_id or not user:
            return None
        lecturas = obj.lecturas_pwa.filter(user=user)
        if obj.subtipo == SubtipoComunicado.INSTITUCIONAL:
            return lecturas.order_by("-fecha_visto", "-id").first()
        return (
            lecturas.filter(comedor_id=comedor_id)
            .order_by("-fecha_visto", "-id")
            .first()
        )

    def get_visto(self, obj):
        lectura = self._get_lectura(obj)
        return bool(lectura and lectura.visto)

    def get_fecha_visto(self, obj):
        lectura = self._get_lectura(obj)
        return lectura.fecha_visto if lectura and lectura.visto else None

    def get_seccion(self, obj):
        if obj.subtipo == SubtipoComunicado.INSTITUCIONAL:
            return "general"
        return "espacio"


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


class PushSubscriptionPWAConfigSerializer(serializers.Serializer):
    enabled = serializers.BooleanField()
    public_key = serializers.CharField(allow_blank=True)

    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        return instance


class PushSubscriptionPWASerializer(serializers.ModelSerializer):
    endpoint = serializers.URLField(max_length=500)
    p256dh = serializers.CharField(max_length=255)
    auth = serializers.CharField(max_length=255)
    content_encoding = serializers.CharField(
        max_length=30,
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = PushSubscriptionPWA
        fields = ("endpoint", "p256dh", "auth", "content_encoding")
