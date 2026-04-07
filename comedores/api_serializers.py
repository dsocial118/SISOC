"""Serializers de API para comedores y flujos mobile/PWA."""

# pylint: disable=too-many-lines

from rest_framework import serializers

from comedores.models import Comedor, Nomina
from core.models import Localidad, Municipio, Provincia
from duplas.models import Dupla
from organizaciones.models import Organizacion
from admisiones.models.admisiones import InformeTecnico
from relevamientos.models import ClasificacionComedor, Relevamiento
from rendicioncuentasmensual.models import DocumentacionAdjunta
from rendicioncuentasmensual.models import RendicionCuentaMensual
from rendicioncuentasmensual.services import RendicionCuentaMensualService


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
    relevamiento_actual_mobile = serializers.SerializerMethodField()

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
            "relevamiento_actual_mobile",
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

    def _format_bool_answer(self, value):
        if value is None:
            return "Sin dato"
        return "Sí" if value else "No"

    def _join_names(self, items):
        values = [item.nombre for item in items if getattr(item, "nombre", None)]
        return ", ".join(values) if values else "Sin dato"

    def _join_truthy_labels(self, pairs):
        values = [label for label, enabled in pairs if enabled]
        return ", ".join(values) if values else "Sin dato"

    def _build_relevamiento_mobile_items(  # pylint: disable=too-many-locals
        self, relevamiento
    ):
        if not relevamiento:
            return []

        funcionamiento = getattr(relevamiento, "funcionamiento", None)
        espacio = getattr(relevamiento, "espacio", None)
        cocina = getattr(espacio, "cocina", None) if espacio else None
        espacio_prestacion = getattr(espacio, "prestacion", None) if espacio else None
        colaboradores = getattr(relevamiento, "colaboradores", None)
        recursos = getattr(relevamiento, "recursos", None)
        compras = getattr(relevamiento, "compras", None)
        anexo = getattr(relevamiento, "anexo", None)

        tipos_actividad = self._join_truthy_labels(
            [
                (
                    "Jardín maternal",
                    getattr(anexo, "actividades_jardin_maternal", None),
                ),
                (
                    "Jardín de infantes",
                    getattr(anexo, "actividades_jardin_infantes", None),
                ),
                ("Apoyo escolar", getattr(anexo, "apoyo_escolar", None)),
                (
                    "Actividades de alfabetización",
                    getattr(anexo, "alfabetizacion_terminalidad", None),
                ),
                ("Talleres y oficios", getattr(anexo, "capacitaciones_talleres", None)),
                ("Promoción de la salud", getattr(anexo, "promocion_salud", None)),
                (
                    "Actividades para discapacidad",
                    getattr(anexo, "actividades_discapacidad", None),
                ),
                (
                    "Necesidades alimentarias",
                    getattr(anexo, "necesidades_alimentarias", None),
                ),
                (
                    "Recreativas y deportivas",
                    getattr(anexo, "actividades_recreativas", None),
                ),
                (
                    "Actividades culturales",
                    getattr(anexo, "actividades_culturales", None),
                ),
                (
                    "Emprendimientos productivos",
                    getattr(anexo, "emprendimientos_productivos", None),
                ),
                (
                    "Actividades religiosas",
                    getattr(anexo, "actividades_religiosas", None),
                ),
                ("Actividades de huerta", getattr(anexo, "actividades_huerta", None)),
            ]
        )
        if anexo and anexo.otras_actividades and anexo.cuales_otras_actividades:
            tipos_actividad = (
                f"{tipos_actividad}, {anexo.cuales_otras_actividades}"
                if tipos_actividad != "Sin dato"
                else anexo.cuales_otras_actividades
            )

        fuentes_compra = self._join_truthy_labels(
            [
                ("Almacén cercano", getattr(compras, "almacen_cercano", None)),
                ("Verdulería", getattr(compras, "verduleria", None)),
                ("Granja", getattr(compras, "granja", None)),
                ("Carnicería", getattr(compras, "carniceria", None)),
                ("Pescadería", getattr(compras, "pescaderia", None)),
                ("Supermercado", getattr(compras, "supermercado", None)),
                ("Mercado central", getattr(compras, "mercado_central", None)),
                ("Ferias comunales", getattr(compras, "ferias_comunales", None)),
                ("Mayoristas", getattr(compras, "mayoristas", None)),
                ("Otro", getattr(compras, "otro", None)),
            ]
        )

        fuentes_insumos = self._join_truthy_labels(
            [
                (
                    "Donaciones particulares",
                    getattr(recursos, "recibe_donaciones_particulares", None),
                ),
                ("Estado nacional", getattr(recursos, "recibe_estado_nacional", None)),
                (
                    "Estado provincial",
                    getattr(recursos, "recibe_estado_provincial", None),
                ),
                (
                    "Estado municipal",
                    getattr(recursos, "recibe_estado_municipal", None),
                ),
                ("Otras fuentes", getattr(recursos, "recibe_otros", None)),
            ]
        )

        tipos_insumos = []
        frecuencias_insumos = []
        if recursos:
            for label, freq_attr, recursos_attr in (
                (
                    "Donaciones particulares",
                    "frecuencia_donaciones_particulares",
                    "recursos_donaciones_particulares",
                ),
                (
                    "Estado nacional",
                    "frecuencia_estado_nacional",
                    "recursos_estado_nacional",
                ),
                (
                    "Estado provincial",
                    "frecuencia_estado_provincial",
                    "recursos_estado_provincial",
                ),
                (
                    "Estado municipal",
                    "frecuencia_estado_municipal",
                    "recursos_estado_municipal",
                ),
                ("Otras fuentes", "frecuencia_otros", "recursos_otros"),
            ):
                recursos_qs = getattr(recursos, recursos_attr, None)
                recursos_names = (
                    self._join_names(recursos_qs.all())
                    if recursos_qs is not None
                    else "Sin dato"
                )
                if recursos_names != "Sin dato":
                    tipos_insumos.append(f"{label}: {recursos_names}")
                frecuencia = getattr(getattr(recursos, freq_attr, None), "nombre", None)
                if frecuencia:
                    frecuencias_insumos.append(f"{label}: {frecuencia}")

        tipo_espacio = getattr(
            getattr(espacio, "tipo_espacio_fisico", None), "nombre", None
        )
        if espacio and espacio.espacio_fisico_otro:
            tipo_espacio = (
                f"{tipo_espacio} / {espacio.espacio_fisico_otro}"
                if tipo_espacio
                else espacio.espacio_fisico_otro
            )

        frecuencia_limpieza = getattr(
            getattr(espacio_prestacion, "frecuencia_limpieza", None), "nombre", None
        )
        if espacio_prestacion and espacio_prestacion.frecuencia_limpieza_otro:
            frecuencia_limpieza = (
                f"{frecuencia_limpieza} / {espacio_prestacion.frecuencia_limpieza_otro}"
                if frecuencia_limpieza
                else espacio_prestacion.frecuencia_limpieza_otro
            )

        abastecimiento_agua = getattr(
            getattr(cocina, "abastecimiento_agua", None), "nombre", None
        )
        if cocina and cocina.abastecimiento_agua_otro:
            abastecimiento_agua = (
                f"{abastecimiento_agua} / {cocina.abastecimiento_agua_otro}"
                if abastecimiento_agua
                else cocina.abastecimiento_agua_otro
            )

        items = [
            {
                "pregunta": "¿Cuenta con espacio para almacenamiento de productos?",
                "respuesta": self._format_bool_answer(
                    getattr(cocina, "almacenamiento_alimentos_secos", None)
                ),
            },
            {
                "pregunta": "¿Cuenta con espacio para el almacenamiento de productos fríos?",
                "respuesta": self._format_bool_answer(
                    bool(
                        getattr(cocina, "heladera", False)
                        or getattr(cocina, "freezer", False)
                    )
                    if cocina
                    else None
                ),
            },
            {
                "pregunta": "¿Cuenta con espacio para residuos reciclables?",
                "respuesta": self._format_bool_answer(
                    getattr(cocina, "recipiente_residuos_reciclables", None)
                ),
            },
            {
                "pregunta": "¿Cuenta con espacio para la elaboración de alimentos?",
                "respuesta": self._format_bool_answer(
                    getattr(cocina, "espacio_elaboracion_alimentos", None)
                ),
            },
            {
                "pregunta": "¿Qué tipo de servicio presta?",
                "respuesta": (
                    getattr(
                        getattr(funcionamiento, "modalidad_prestacion", None),
                        "nombre",
                        None,
                    )
                    or "Sin dato"
                ),
            },
            {
                "pregunta": "¿Qué método utiliza para cocinar?",
                "respuesta": (
                    self._join_names(cocina.abastecimiento_combustible.all())
                    if cocina
                    else "Sin dato"
                ),
            },
            {
                "pregunta": "¿Cómo se abastece de agua?",
                "respuesta": abastecimiento_agua or "Sin dato",
            },
            {
                "pregunta": "¿Qué cantidad de personas prestan servicios en el Centro?",
                "respuesta": (
                    getattr(
                        getattr(colaboradores, "cantidad_colaboradores", None),
                        "nombre",
                        None,
                    )
                    or "Sin dato"
                ),
            },
            {
                "pregunta": "¿El Centro cuenta con personas capacitadas en bromatología?",
                "respuesta": self._format_bool_answer(
                    getattr(colaboradores, "colaboradores_capacitados_alimentos", None)
                ),
            },
            {
                "pregunta": "¿El Centro cuenta con personas capacitadas en Seguridad e Higiene?",
                "respuesta": self._format_bool_answer(
                    getattr(
                        colaboradores, "colaboradores_capacitados_salud_seguridad", None
                    )
                ),
            },
            {
                "pregunta": "¿El Centro cuenta con personas capacitadas en Violencia de Género?",
                "respuesta": self._format_bool_answer(
                    getattr(
                        colaboradores,
                        "colaboradores_recibieron_capacitacion_violencia",
                        None,
                    )
                ),
            },
            {
                "pregunta": "¿El Centro cuenta con personas capacitadas en respuesta ante emergencias?",
                "respuesta": self._format_bool_answer(
                    getattr(
                        colaboradores,
                        "colaboradores_recibieron_capacitacion_emergencias",
                        None,
                    )
                ),
            },
            {
                "pregunta": "¿En qué tipo de espacio funciona el Centro?",
                "respuesta": tipo_espacio or "Sin dato",
            },
            {
                "pregunta": "¿El Centro cuenta con salida de emergencia?",
                "respuesta": self._format_bool_answer(
                    getattr(espacio_prestacion, "tiene_salida_emergencia", None)
                ),
            },
            {
                "pregunta": "¿El Centro cuenta con señalización de seguridad?",
                "respuesta": self._format_bool_answer(
                    getattr(espacio_prestacion, "salida_emergencia_senializada", None)
                ),
            },
            {
                "pregunta": "¿El Centro cuenta con protección contra incendios?",
                "respuesta": self._format_bool_answer(
                    getattr(espacio_prestacion, "tiene_equipacion_incendio", None)
                ),
            },
            {
                "pregunta": "¿El Centro cuenta con botiquín de primeros auxilios?",
                "respuesta": self._format_bool_answer(
                    getattr(espacio_prestacion, "tiene_botiquin", None)
                ),
            },
            {
                "pregunta": "¿El Centro cuenta con instalación eléctrica?",
                "respuesta": self._format_bool_answer(
                    getattr(cocina, "instalacion_electrica", None)
                ),
            },
            {
                "pregunta": "¿El Centro cuenta con ventilación?",
                "respuesta": self._format_bool_answer(
                    getattr(espacio_prestacion, "tiene_ventilacion", None)
                ),
            },
            {
                "pregunta": "¿El Centro cuenta con sanitarios?",
                "respuesta": self._format_bool_answer(
                    getattr(espacio_prestacion, "tiene_sanitarios", None)
                ),
            },
            {
                "pregunta": "¿Qué tipo de desagüe poseen los sanitarios?",
                "respuesta": (
                    getattr(
                        getattr(espacio_prestacion, "desague_hinodoro", None),
                        "nombre",
                        None,
                    )
                    or "Sin dato"
                ),
            },
            {
                "pregunta": "¿Con qué frecuencia se realiza la limpieza del Centro?",
                "respuesta": frecuencia_limpieza or "Sin dato",
            },
            {
                "pregunta": "¿En qué lugar realiza sus compras?",
                "respuesta": fuentes_compra,
            },
            {
                "pregunta": "¿Recibe otro tipo de insumos?",
                "respuesta": fuentes_insumos,
            },
            {
                "pregunta": "¿Qué tipo de insumos recibe?",
                "respuesta": ", ".join(tipos_insumos) if tipos_insumos else "Sin dato",
            },
            {
                "pregunta": "¿Con qué frecuencia recibe estos insumos?",
                "respuesta": (
                    ", ".join(frecuencias_insumos)
                    if frecuencias_insumos
                    else "Sin dato"
                ),
            },
            {
                "pregunta": "¿El Centro cuenta con acceso a internet?",
                "respuesta": self._format_bool_answer(
                    getattr(anexo, "servicio_internet", None)
                ),
            },
            {
                "pregunta": "¿Con qué dispositivo se conecta?",
                "respuesta": (
                    getattr(getattr(anexo, "tecnologia", None), "nombre", None)
                    or "Sin dato"
                ),
            },
            {
                "pregunta": "¿El Centro se encuentra en una zona inundable?",
                "respuesta": self._format_bool_answer(
                    getattr(anexo, "zona_inundable", None)
                ),
            },
            {
                "pregunta": "¿A qué distancia se encuentra el Centro del transporte público?",
                "respuesta": (
                    getattr(
                        getattr(anexo, "distancia_transporte", None), "nombre", None
                    )
                    or "Sin dato"
                ),
            },
            {
                "pregunta": "¿El espacio brinda otro tipo de actividades?",
                "respuesta": self._format_bool_answer(
                    getattr(anexo, "otras_actividades", None)
                ),
            },
            {
                "pregunta": "¿Qué tipo de actividades se realizan?",
                "respuesta": tipos_actividad,
            },
        ]
        return items

    def get_relevamiento_actual_mobile(self, obj):
        relevamientos = getattr(obj, "relevamientos_optimized", None)
        relevamiento = relevamientos[0] if relevamientos else None
        if relevamiento is None:
            relevamiento = (
                Relevamiento.objects.select_related(
                    "funcionamiento",
                    "funcionamiento__modalidad_prestacion",
                    "espacio",
                    "espacio__tipo_espacio_fisico",
                    "espacio__cocina",
                    "espacio__cocina__abastecimiento_agua",
                    "espacio__prestacion",
                    "espacio__prestacion__desague_hinodoro",
                    "espacio__prestacion__frecuencia_limpieza",
                    "colaboradores",
                    "colaboradores__cantidad_colaboradores",
                    "recursos",
                    "compras",
                    "anexo",
                    "anexo__tecnologia",
                    "anexo__distancia_transporte",
                )
                .prefetch_related(
                    "espacio__cocina__abastecimiento_combustible",
                    "recursos__recursos_donaciones_particulares",
                    "recursos__recursos_estado_nacional",
                    "recursos__recursos_estado_provincial",
                    "recursos__recursos_estado_municipal",
                    "recursos__recursos_otros",
                )
                .filter(comedor=obj)
                .order_by("-fecha_visita", "-id")
                .first()
            )

        if not relevamiento:
            return None

        return {
            "fecha_visita": relevamiento.fecha_visita,
            "estado": relevamiento.estado,
            "items": self._build_relevamiento_mobile_items(relevamiento),
        }


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


class NoSaveSerializer(serializers.Serializer):
    """Serializer base para casos sin create/update."""

    def _raise_read_only(self):
        raise serializers.ValidationError("Serializer de solo lectura.")

    def create(self, validated_data):
        return self._raise_read_only()

    def update(self, instance, validated_data):
        return self._raise_read_only()


class DocumentoComedorSerializer(NoSaveSerializer):
    id = serializers.CharField()
    origen = serializers.CharField()
    tipo = serializers.CharField()
    nombre = serializers.CharField(allow_null=True)
    fecha = serializers.DateTimeField(allow_null=True)
    url = serializers.CharField(allow_null=True)
    path = serializers.CharField(allow_null=True, write_only=True)


class NominaCiudadanoSerializer(NoSaveSerializer):
    id = serializers.IntegerField()
    nombre = serializers.CharField(allow_null=True)
    apellido = serializers.CharField(allow_null=True)
    documento = serializers.CharField(allow_null=True)
    sexo = serializers.CharField(allow_null=True)


class NominaSerializer(NoSaveSerializer):
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


class NominaCreateSerializer(NoSaveSerializer):
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


class NominaUpdateSerializer(NoSaveSerializer):
    estado = serializers.CharField(required=False)
    observaciones = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        estado = attrs.get("estado")
        if estado and estado not in dict(Nomina.ESTADO_CHOICES):
            raise serializers.ValidationError("Estado inválido.")
        if not attrs:
            raise serializers.ValidationError("Debe enviar al menos un campo.")
        return attrs


class ComprobanteRendicionSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    estado_label = serializers.CharField(source="get_estado_display", read_only=True)
    estado_visual = serializers.SerializerMethodField()
    estado_label_visual = serializers.SerializerMethodField()
    categoria_label = serializers.CharField(
        source="get_categoria_display", read_only=True
    )
    subsanaciones = serializers.SerializerMethodField()

    class Meta:
        model = DocumentacionAdjunta
        fields = (
            "id",
            "nombre",
            "categoria",
            "categoria_label",
            "documento_subsanado",
            "url",
            "estado",
            "estado_label",
            "estado_visual",
            "estado_label_visual",
            "observaciones",
            "fecha_creacion",
            "ultima_modificacion",
            "subsanaciones",
        )

    def get_url(self, obj):
        if not obj.archivo:
            return None
        request = self.context.get("request")
        url = obj.archivo.url
        return request.build_absolute_uri(url) if request else url

    def get_estado_visual(self, obj):
        return obj.get_estado_visual()

    def get_estado_label_visual(self, obj):
        return obj.get_estado_visual_display()

    def get_subsanaciones(self, obj):
        return ComprobanteRendicionSerializer(
            getattr(obj, "subsanaciones_historial", []),
            many=True,
            context=self.context,
        ).data


class RendicionMensualListSerializer(serializers.ModelSerializer):
    estado_label = serializers.CharField(source="get_estado_display", read_only=True)
    periodo_inicio = serializers.DateField(read_only=True)
    periodo_fin = serializers.DateField(read_only=True)
    periodo_label = serializers.SerializerMethodField()

    class Meta:
        model = RendicionCuentaMensual
        fields = (
            "id",
            "convenio",
            "numero_rendicion",
            "mes",
            "anio",
            "periodo_inicio",
            "periodo_fin",
            "periodo_label",
            "estado",
            "estado_label",
            "documento_adjunto",
            "observaciones",
            "fecha_creacion",
            "ultima_modificacion",
        )

    def get_periodo_label(self, obj):
        if obj.periodo_inicio and obj.periodo_fin:
            return (
                f"{obj.periodo_inicio.strftime('%d/%m/%Y')} - "
                f"{obj.periodo_fin.strftime('%d/%m/%Y')}"
            )
        return f"{obj.get_mes_display()} {obj.anio}"


class RendicionMensualDetailSerializer(RendicionMensualListSerializer):
    comprobantes = ComprobanteRendicionSerializer(
        source="archivos_adjuntos", many=True, read_only=True
    )
    documentacion = serializers.SerializerMethodField()

    class Meta(RendicionMensualListSerializer.Meta):
        fields = RendicionMensualListSerializer.Meta.fields + (
            "comprobantes",
            "documentacion",
        )

    def get_documentacion(self, obj):
        grouped = RendicionCuentaMensualService._construir_documentacion_para_detalle(
            obj
        )
        serializer_context = {"request": self.context.get("request")}
        payload = []
        for categoria in DocumentacionAdjunta.categorias_mobile():
            payload.append(
                {
                    "codigo": categoria["codigo"],
                    "label": categoria["label"],
                    "required": categoria["required"],
                    "multiple": categoria["multiple"],
                    "order": categoria["order"],
                    "archivos": ComprobanteRendicionSerializer(
                        grouped.get(categoria["codigo"], []),
                        many=True,
                        context=serializer_context,
                    ).data,
                }
            )
        return payload


class RendicionMensualCreateSerializer(NoSaveSerializer):
    convenio = serializers.CharField(max_length=100)
    numero_rendicion = serializers.IntegerField(min_value=1)
    periodo_inicio = serializers.DateField()
    periodo_fin = serializers.DateField()
    observaciones = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    def validate(self, attrs):
        periodo_inicio = attrs.get("periodo_inicio")
        periodo_fin = attrs.get("periodo_fin")
        if periodo_inicio and periodo_fin and periodo_inicio > periodo_fin:
            raise serializers.ValidationError(
                {
                    "periodo_fin": "La fecha de fin debe ser posterior o igual a la fecha de inicio."
                }
            )
        attrs["convenio"] = (attrs.get("convenio") or "").strip()
        if not attrs["convenio"]:
            raise serializers.ValidationError(
                {"convenio": "Este campo es obligatorio."}
            )
        return attrs
