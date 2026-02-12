from rest_framework import serializers

from comedores.models import Comedor, Nomina
from core.models import Localidad, Municipio, Provincia
from duplas.models import Dupla
from organizaciones.models import Organizacion
from admisiones.models.admisiones import InformeTecnico
from relevamientos.models import ClasificacionComedor, Relevamiento
from rendicioncuentasmensual.models import RendicionCuentaMensual


class SimpleUbicacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Provincia
        fields = ("id", "nombre")


class SimpleMunicipioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Municipio
        fields = ("id", "nombre")


class SimpleLocalidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Localidad
        fields = ("id", "nombre")


class OrganizacionDetalleSerializer(serializers.ModelSerializer):
    provincia = SimpleUbicacionSerializer(read_only=True)
    municipio = SimpleMunicipioSerializer(read_only=True)
    localidad = SimpleLocalidadSerializer(read_only=True)

    class Meta:
        model = Organizacion
        fields = (
            "id",
            "nombre",
            "cuit",
            "telefono",
            "email",
            "domicilio",
            "provincia",
            "municipio",
            "localidad",
            "partido",
        )


class DuplaDetalleSerializer(serializers.ModelSerializer):
    abogado = serializers.SerializerMethodField()
    coordinador = serializers.SerializerMethodField()
    tecnicos = serializers.SerializerMethodField()

    class Meta:
        model = Dupla
        fields = ("id", "nombre", "estado", "abogado", "coordinador", "tecnicos")

    def _serialize_user(self, user):
        if not user:
            return None
        full_name = f"{user.last_name} {user.first_name}".strip()
        return {
            "id": user.id,
            "username": user.username,
            "full_name": full_name or user.username,
        }

    def get_abogado(self, obj):
        return self._serialize_user(obj.abogado)

    def get_coordinador(self, obj):
        return self._serialize_user(obj.coordinador)

    def get_tecnicos(self, obj):
        return [self._serialize_user(user) for user in obj.tecnico.all()]


class ComedorDetailSerializer(serializers.ModelSerializer):
    provincia = SimpleUbicacionSerializer(read_only=True)
    municipio = SimpleMunicipioSerializer(read_only=True)
    localidad = SimpleLocalidadSerializer(read_only=True)
    organizacion = OrganizacionDetalleSerializer(read_only=True)
    programa = serializers.SerializerMethodField()
    tipocomedor = serializers.SerializerMethodField()
    referente = serializers.SerializerMethodField()
    dupla = DuplaDetalleSerializer(read_only=True)
    imagenes = serializers.SerializerMethodField()
    foto_legajo_url = serializers.SerializerMethodField()
    ultimo_estado = serializers.SerializerMethodField()
    relevamientos = serializers.SerializerMethodField()
    observaciones = serializers.SerializerMethodField()
    clasificaciones = serializers.SerializerMethodField()
    rendiciones_mensuales = serializers.SerializerMethodField()
    programa_changes = serializers.SerializerMethodField()

    class Meta:
        model = Comedor
        fields = (
            "id",
            "nombre",
            "id_externo",
            "codigo_de_proyecto",
            "comienzo",
            "estado",
            "estado_validacion",
            "fecha_validado",
            "fecha_creacion",
            "calle",
            "numero",
            "piso",
            "departamento",
            "manzana",
            "lote",
            "entre_calle_1",
            "entre_calle_2",
            "latitud",
            "longitud",
            "provincia",
            "municipio",
            "localidad",
            "partido",
            "barrio",
            "codigo_postal",
            "organizacion",
            "programa",
            "tipocomedor",
            "dupla",
            "referente",
            "foto_legajo_url",
            "imagenes",
            "ultimo_estado",
            "relevamientos",
            "observaciones",
            "clasificaciones",
            "rendiciones_mensuales",
            "programa_changes",
        )

    def _absolute_url(self, file_field):
        if not file_field:
            return None
        request = self.context.get("request")
        url = file_field.url
        return request.build_absolute_uri(url) if request else url

    def get_programa(self, obj):
        if not obj.programa:
            return None
        return {"id": obj.programa.id, "nombre": obj.programa.nombre}

    def get_tipocomedor(self, obj):
        if not obj.tipocomedor:
            return None
        return {"id": obj.tipocomedor.id, "nombre": obj.tipocomedor.nombre}

    def get_referente(self, obj):
        referente = obj.referente
        if not referente:
            return None
        return {
            "id": referente.id,
            "nombre": referente.nombre,
            "apellido": referente.apellido,
            "mail": referente.mail,
            "celular": referente.celular,
            "documento": referente.documento,
            "funcion": referente.funcion,
        }

    def get_imagenes(self, obj):
        imagenes = getattr(obj, "imagenes_optimized", None) or obj.imagenes.all()
        return [
            {"id": imagen.id, "url": self._absolute_url(imagen.imagen)}
            for imagen in imagenes
        ]

    def get_foto_legajo_url(self, obj):
        return self._absolute_url(obj.foto_legajo)

    def get_ultimo_estado(self, obj):
        ultimo_estado = obj.ultimo_estado
        if not ultimo_estado or not ultimo_estado.estado_general:
            return None
        estado_general = ultimo_estado.estado_general
        return {
            "estado_actividad": (
                estado_general.estado_actividad.estado
                if estado_general.estado_actividad
                else None
            ),
            "estado_proceso": (
                estado_general.estado_proceso.estado
                if estado_general.estado_proceso
                else None
            ),
            "estado_detalle": (
                estado_general.estado_detalle.estado
                if estado_general.estado_detalle
                else None
            ),
            "fecha_cambio": ultimo_estado.fecha_cambio,
            "usuario_id": ultimo_estado.usuario_id,
        }

    def get_relevamientos(self, obj):
        relevamientos = getattr(obj, "relevamientos_optimized", None)
        if relevamientos is None:
            relevamientos = (
                Relevamiento.objects.filter(comedor=obj)
                .order_by("-fecha_visita", "-id")
                .only("id", "fecha_visita", "estado", "prestacion")
            )
        return [
            {
                "id": relevamiento.id,
                "fecha_visita": relevamiento.fecha_visita,
                "estado": getattr(relevamiento, "estado", None),
                "prestacion_id": getattr(relevamiento, "prestacion_id", None),
            }
            for relevamiento in relevamientos
        ]

    def get_observaciones(self, obj):
        observaciones = getattr(obj, "observaciones_optimized", None)
        if observaciones is None:
            observaciones = obj.observacion_set.order_by("-fecha_visita")[:3]
        return [
            {
                "id": obs.id,
                "observador": obs.observador,
                "fecha_visita": obs.fecha_visita,
                "observacion": obs.observacion,
            }
            for obs in observaciones
        ]

    def get_clasificaciones(self, obj):
        clasificaciones = getattr(obj, "clasificaciones_optimized", None)
        if clasificaciones is None:
            clasificaciones = (
                ClasificacionComedor.objects.filter(comedor=obj)
                .select_related("categoria")
                .order_by("-fecha")
            )
        return [
            {
                "id": clasificacion.id,
                "puntuacion_total": clasificacion.puntuacion_total,
                "categoria": (
                    {
                        "id": clasificacion.categoria_id,
                        "nombre": clasificacion.categoria.nombre,
                    }
                    if clasificacion.categoria
                    else None
                ),
                "fecha": clasificacion.fecha,
                "relevamiento_id": clasificacion.relevamiento_id,
            }
            for clasificacion in clasificaciones
        ]

    def get_rendiciones_mensuales(self, obj):
        rendiciones = getattr(obj, "rendiciones_optimized", None)
        if rendiciones is None:
            rendiciones = (
                RendicionCuentaMensual.objects.filter(comedor=obj)
                .order_by("-anio", "-mes")
                .only(
                    "id",
                    "mes",
                    "anio",
                    "observaciones",
                    "documento_adjunto",
                    "ultima_modificacion",
                    "fecha_creacion",
                )
            )
        return [
            {
                "id": rendicion.id,
                "mes": rendicion.mes,
                "anio": rendicion.anio,
                "documento_adjunto": rendicion.documento_adjunto,
                "observaciones": rendicion.observaciones,
                "ultima_modificacion": rendicion.ultima_modificacion,
                "fecha_creacion": rendicion.fecha_creacion,
            }
            for rendicion in rendiciones
        ]

    def get_programa_changes(self, obj):
        cambios = getattr(obj, "programa_changes_optimized", None)
        if cambios is None:
            cambios = obj.programa_changes.select_related(
                "from_programa", "to_programa", "changed_by"
            ).order_by("-changed_at", "-id")
        return [
            {
                "id": cambio.id,
                "from_programa": (
                    cambio.from_programa.nombre if cambio.from_programa else None
                ),
                "to_programa": (
                    cambio.to_programa.nombre if cambio.to_programa else None
                ),
                "changed_at": cambio.changed_at,
                "changed_by": (
                    {
                        "id": cambio.changed_by_id,
                        "username": cambio.changed_by.username,
                        "full_name": (
                            f"{cambio.changed_by.last_name} {cambio.changed_by.first_name}".strip()
                            or cambio.changed_by.username
                        ),
                    }
                    if cambio.changed_by
                    else None
                ),
            }
            for cambio in cambios
        ]


APROBADAS_FIELDS = tuple(
    f"aprobadas_{tipo}_{dia}"
    for tipo in ("desayuno", "almuerzo", "merienda", "cena")
    for dia in (
        "lunes",
        "martes",
        "miercoles",
        "jueves",
        "viernes",
        "sabado",
        "domingo",
    )
)


class InformeTecnicoPrestacionSerializer(serializers.ModelSerializer):
    informe_id = serializers.IntegerField(source="id", read_only=True)
    admision_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = InformeTecnico
        fields = (
            "informe_id",
            "admision_id",
            "tipo",
            "estado_formulario",
            "creado",
            "modificado",
            *APROBADAS_FIELDS,
        )


class DocumentoComedorSerializer(serializers.Serializer):
    id = serializers.CharField()
    origen = serializers.CharField()
    tipo = serializers.CharField()
    nombre = serializers.CharField(allow_null=True)
    fecha = serializers.DateTimeField(allow_null=True)
    url = serializers.CharField(allow_null=True)
    path = serializers.CharField(allow_null=True, write_only=True)


class NominaCiudadanoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nombre = serializers.CharField(allow_null=True)
    apellido = serializers.CharField(allow_null=True)
    documento = serializers.CharField(allow_null=True)
    sexo = serializers.CharField(allow_null=True)


class NominaSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    fecha = serializers.DateTimeField()
    estado = serializers.CharField()
    observaciones = serializers.CharField(allow_null=True)
    ciudadano = NominaCiudadanoSerializer(allow_null=True)

    def to_representation(self, instance):
        if isinstance(instance, dict):
            return super().to_representation(instance)
        ciudadano = getattr(instance, "ciudadano", None)
        return {
            "id": instance.id,
            "fecha": instance.fecha,
            "estado": instance.estado,
            "observaciones": instance.observaciones,
            "ciudadano": (
                {
                    "id": ciudadano.id,
                    "nombre": ciudadano.nombre,
                    "apellido": ciudadano.apellido,
                    "documento": ciudadano.documento,
                    "sexo": ciudadano.sexo.sexo if ciudadano.sexo else None,
                }
                if ciudadano
                else None
            ),
        }


class NominaCreateSerializer(serializers.Serializer):
    ciudadano_id = serializers.IntegerField(required=False)
    ciudadano = serializers.DictField(required=False)
    estado = serializers.CharField(required=False)
    observaciones = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        ciudadano_id = attrs.get("ciudadano_id")
        ciudadano = attrs.get("ciudadano")
        estado = attrs.get("estado")
        if not ciudadano_id and not ciudadano:
            raise serializers.ValidationError("Debe enviar ciudadano_id o ciudadano.")
        if ciudadano_id and ciudadano:
            raise serializers.ValidationError(
                "Enviar solo ciudadano_id o ciudadano, no ambos."
            )
        if estado and estado not in dict(Nomina.ESTADO_CHOICES):
            raise serializers.ValidationError("Estado inválido.")
        return attrs


class NominaUpdateSerializer(serializers.Serializer):
    estado = serializers.CharField(required=False)
    observaciones = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        estado = attrs.get("estado")
        if estado and estado not in dict(Nomina.ESTADO_CHOICES):
            raise serializers.ValidationError("Estado inválido.")
        if not attrs:
            raise serializers.ValidationError("Debe enviar al menos un campo.")
        return attrs
