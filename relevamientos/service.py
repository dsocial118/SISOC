# pylint: disable=too-many-lines
import json
import logging
from django.shortcuts import get_object_or_404
from django.utils import timezone

from comedores.models import (
    Comedor,
    Referente,
    TipoDeComedor,
)
from core.models import Localidad, Municipio, Provincia
from core.utils import convert_string_to_int
from relevamientos.utils import (
    assign_values_to_instance,
    convert_to_boolean,
    get_object_or_none,
    get_recursos,
    populate_data,
)
from relevamientos.models import (
    Anexo,
    CantidadColaboradores,
    Colaboradores,
    Espacio,
    EspacioCocina,
    EspacioPrestacion,
    Excepcion,
    FrecuenciaLimpieza,
    FrecuenciaRecepcionRecursos,
    FuenteCompras,
    FuenteRecursos,
    FuncionamientoPrestacion,
    MotivoExcepcion,
    Prestacion,
    PuntoEntregas,
    Relevamiento,
    TipoAccesoComedor,
    TipoAgua,
    TipoCombustible,
    TipoDesague,
    TipoDistanciaTransporte,
    TipoEspacio,
    TipoFrecuenciaBolsones,
    TipoFrecuenciaInsumos,
    TipoGestionQuejas,
    TipoInsumos,
    TipoModalidadPrestacion,
    TipoModuloBolsones,
    TipoRecurso,
    TipoTecnologia,
)
from relevamientos.tasks import (
    AsyncSendRelevamientoToGestionar,
    build_relevamiento_payload,
)

logger = logging.getLogger("django")


# TODO: Refactorizar todo esto, pylint esta muriendo aca
class RelevamientoService:  # pylint: disable=too-many-public-methods
    """Service layer for managing Relevamiento persistence and business rules."""

    @staticmethod
    def update_comedor(comedor_data, comedor_instance):
        """
        Actualiza los campos de un comedor que envia GESTIONAR via API.
        Si no existe municipio o localidad, los crea.
        """
        try:
            provincia = (
                Provincia.objects.get(nombre=comedor_data["provincia"])
                if comedor_data.get("provincia")
                else comedor_instance.provincia
            )

            municipio = (
                Municipio.objects.get_or_create(
                    nombre=comedor_data["municipio"],
                    provincia=provincia,
                )[0]
                if comedor_data.get("municipio")
                else comedor_instance.municipio
            )

            localidad = (
                Localidad.objects.get_or_create(
                    nombre=comedor_data["localidad"],
                    municipio=municipio,
                )[0]
                if comedor_data.get("localidad")
                else comedor_instance.localidad
            )

            comedor_instance.provincia = provincia
            comedor_instance.municipio = municipio
            comedor_instance.localidad = localidad

            comedor_instance.numero = convert_string_to_int(
                comedor_data.get("numero", comedor_instance.numero)
            )
            comedor_instance.calle = comedor_data.get("calle", comedor_instance.calle)
            comedor_instance.entre_calle_1 = comedor_data.get(
                "entre_calle_1", comedor_instance.entre_calle_1
            )
            comedor_instance.entre_calle_2 = comedor_data.get(
                "entre_calle_2", comedor_instance.entre_calle_2
            )
            comedor_instance.barrio = comedor_data.get(
                "barrio", comedor_instance.barrio
            )
            comedor_instance.codigo_postal = convert_string_to_int(
                comedor_data.get("codigo_postal", comedor_instance.codigo_postal)
            )
            comedor_instance.partido = comedor_data.get(
                "partido", comedor_instance.partido
            )
            comedor_instance.manzana = comedor_data.get(
                "manzana", comedor_instance.manzana
            )
            comedor_instance.piso = comedor_data.get("piso", comedor_instance.piso)
            comedor_instance.departamento = comedor_data.get(
                "departamento", comedor_instance.departamento
            )
            comedor_instance.lote = comedor_data.get("lote", comedor_instance.lote)
            comedor_instance.comienzo = (
                convert_string_to_int(comedor_data.get("comienzo", "").split("/")[-1])
                if comedor_data.get("comienzo")
                else comedor_instance.comienzo
            )
            comedor_instance.save()

            return comedor_instance.id
        except Exception:
            logger.exception(
                "Error en RelevamientoService.update_comedor",
                extra={"comedor_data": comedor_data},
            )
            raise

    @staticmethod
    def create_pendiente(request, comedor_id):
        try:
            comedor = get_object_or_404(Comedor, id=comedor_id)
            relevamiento = Relevamiento(comedor=comedor, estado="Pendiente")
            territorial_data = request.POST.get("territorial")

            if territorial_data:
                territorial_data = json.loads(territorial_data)
                relevamiento.territorial_uid = territorial_data.get("gestionar_uid")
                relevamiento.territorial_nombre = territorial_data.get("nombre")
                relevamiento.estado = "Visita pendiente"

            relevamiento.save()

            return relevamiento
        except Exception:
            logger.exception(
                "Error en RelevamientoService.create_pendiente",
                extra={"comedor_id": comedor_id},
            )
            raise

    @staticmethod
    def update_territorial(request):
        try:
            relevamiento_id = request.POST.get("relevamiento_id")
            relevamiento = Relevamiento.objects.get(id=relevamiento_id)
            territorial_data = request.POST.get("territorial_editar")

            if territorial_data:
                territorial_data = json.loads(territorial_data)
                relevamiento.territorial_uid = territorial_data.get("gestionar_uid")
                relevamiento.territorial_nombre = territorial_data.get("nombre")
                relevamiento.estado = "Visita pendiente"
            else:
                relevamiento.territorial_nombre = None
                relevamiento.territorial_uid = None
                relevamiento.estado = "Pendiente"

            relevamiento.save()

            payload = build_relevamiento_payload(relevamiento)
            AsyncSendRelevamientoToGestionar(relevamiento.id, payload).start()

            return relevamiento
        except Relevamiento.DoesNotExist:
            logger.exception(
                "RelevamientoService.update_territorial: Relevamiento no encontrado",
                extra={"relevamiento_id": relevamiento_id},
            )
            return None
        except Exception:
            logger.exception(
                "Error en RelevamientoService.update_territorial",
                extra={"relevamiento_id": relevamiento_id},
            )
            raise

    @staticmethod
    def populate_relevamiento(relevamiento_form, extra_forms):
        try:
            relevamiento = relevamiento_form.save(commit=False)

            funcionamiento = extra_forms["funcionamiento_form"].save()
            relevamiento.funcionamiento = funcionamiento

            espacio = extra_forms["espacio_form"].save(commit=False)
            cocina = extra_forms["espacio_cocina_form"].save(commit=True)
            espacio.cocina = cocina
            prestacion = extra_forms["espacio_prestacion_form"].save(commit=True)
            espacio.prestacion = prestacion
            espacio.save()
            relevamiento.espacio = espacio

            colaboradores = extra_forms["colaboradores_form"].save()
            relevamiento.colaboradores = colaboradores

            recursos = extra_forms["recursos_form"].save()
            relevamiento.recursos = recursos

            anexo = extra_forms["anexo_form"].save()
            relevamiento.anexo = anexo

            compras = extra_forms["compras_form"].save()
            relevamiento.compras = compras

            prestacion = extra_forms["prestacion_form"].save()
            relevamiento.prestacion = prestacion

            referente = extra_forms["referente_form"].save()
            relevamiento.responsable = referente
            relevamiento.responsable_es_referente = (
                relevamiento_form.cleaned_data["responsable_es_referente"] == "True"
            )
            punto_entregas = extra_forms["punto_entregas_form"].save()
            relevamiento.punto_entregas = punto_entregas

            relevamiento.fecha_visita = timezone.now()

            relevamiento.save()

            return relevamiento
        except Exception:
            logger.exception(
                "Error en RelevamientoService.populate_relevamiento",
                extra={"relevamiento_form": relevamiento_form.data},
            )
            raise

    @staticmethod
    def separate_string(tipos):
        try:
            tipos_list = [str(tipo) for tipo in tipos]

            if len(tipos_list) == 0:
                tipos_str = "-"
            elif len(tipos_list) > 1:
                tipos_str = ", ".join(tipos_list[:-1]) + " y " + tipos_list[-1]
            else:
                tipos_str = tipos_list[0]

            return tipos_str
        except Exception:
            logger.exception("Error en RelevamientoService.separate_string")
            raise

    @staticmethod
    def get_relevamiento_detail_object(relevamiento_id):
        try:
            relevamiento = (
                # TODO: No listar todo lo necesario
                Relevamiento.objects.prefetch_related(
                    "comedor",
                    "funcionamiento",
                    "espacio",
                    "colaboradores",
                    "recursos",
                    "compras",
                    "referente",
                    "anexo",
                    "punto_entregas",
                )
                .values(
                    "id",
                    "estado",
                    "docPDF",
                    "comedor__nombre",
                    "fecha_visita",
                    "observacion",
                    "funcionamiento__modalidad_prestacion__nombre",
                    "funcionamiento__servicio_por_turnos",
                    "funcionamiento__cantidad_turnos",
                    "territorial_nombre",
                    "responsable_es_referente",
                    "responsable_relevamiento__nombre",
                    "responsable_relevamiento__apellido",
                    "responsable_relevamiento__mail",
                    "responsable_relevamiento__celular",
                    "responsable_relevamiento__documento",
                    "comedor__comienzo",
                    "comedor__id",
                    "comedor__calle",
                    "comedor__numero",
                    "comedor__entre_calle_1",
                    "comedor__entre_calle_2",
                    "comedor__provincia__nombre",
                    "comedor__municipio__nombre",
                    "comedor__localidad__nombre",
                    "comedor__partido",
                    "comedor__barrio",
                    "comedor__codigo_postal",
                    "comedor__referente__nombre",
                    "comedor__referente__apellido",
                    "comedor__referente__mail",
                    "comedor__referente__celular",
                    "comedor__referente__documento",
                    "espacio__tipo_espacio_fisico__nombre",
                    "espacio__espacio_fisico_otro",
                    "espacio__cocina__espacio_elaboracion_alimentos",
                    "espacio__cocina__almacenamiento_alimentos_secos",
                    "espacio__cocina__heladera",
                    "espacio__cocina__freezer",
                    "espacio__cocina__recipiente_residuos_organicos",
                    "espacio__cocina__recipiente_residuos_reciclables",
                    "espacio__cocina__otros_residuos",
                    "espacio__cocina__recipiente_otros_residuos",
                    "espacio__cocina__abastecimiento_agua__nombre",
                    "espacio__cocina__abastecimiento_agua_otro",
                    "espacio__cocina__instalacion_electrica",
                    "espacio__prestacion__espacio_equipado",
                    "espacio__prestacion__tiene_ventilacion",
                    "espacio__prestacion__tiene_salida_emergencia",
                    "espacio__prestacion__salida_emergencia_senializada",
                    "espacio__prestacion__tiene_equipacion_incendio",
                    "espacio__prestacion__tiene_botiquin",
                    "espacio__prestacion__tiene_buena_iluminacion",
                    "espacio__prestacion__tiene_sanitarios",
                    "espacio__prestacion__desague_hinodoro__nombre",
                    "espacio__prestacion__gestion_quejas__nombre",
                    "espacio__prestacion__gestion_quejas_otro",
                    "espacio__prestacion__informacion_quejas",
                    "espacio__prestacion__frecuencia_limpieza__nombre",
                    "colaboradores__cantidad_colaboradores__nombre",
                    "colaboradores__colaboradores_capacitados_alimentos",
                    "colaboradores__colaboradores_recibieron_capacitacion_alimentos",
                    "colaboradores__colaboradores_capacitados_salud_seguridad",
                    "colaboradores__colaboradores_recibieron_capacitacion_emergencias",
                    "colaboradores__colaboradores_recibieron_capacitacion_violencia",
                    "recursos__recibe_donaciones_particulares",
                    "recursos__frecuencia_donaciones_particulares__nombre",
                    "recursos__recibe_estado_nacional",
                    "recursos__frecuencia_estado_nacional__nombre",
                    "recursos__recibe_estado_provincial",
                    "recursos__frecuencia_estado_provincial__nombre",
                    "recursos__recibe_estado_municipal",
                    "recursos__frecuencia_estado_municipal__nombre",
                    "recursos__recibe_otros",
                    "recursos__frecuencia_otros__nombre",
                    "compras__almacen_cercano",
                    "compras__verduleria",
                    "compras__granja",
                    "compras__carniceria",
                    "compras__pescaderia",
                    "compras__supermercado",
                    "compras__mercado_central",
                    "compras__ferias_comunales",
                    "compras__mayoristas",
                    "compras__otro",
                    "prestacion__id",
                    "anexo__tipo_insumo__nombre",
                    "anexo__frecuencia_insumo__nombre",
                    "anexo__tecnologia__nombre",
                    "anexo__acceso_comedor__nombre",
                    "anexo__distancia_transporte__nombre",
                    "anexo__comedor_merendero",
                    "anexo__insumos_organizacion",
                    "anexo__servicio_internet",
                    "anexo__zona_inundable",
                    "anexo__actividades_jardin_maternal",
                    "anexo__actividades_jardin_infantes",
                    "anexo__apoyo_escolar",
                    "anexo__alfabetizacion_terminalidad",
                    "anexo__capacitaciones_talleres",
                    "anexo__promocion_salud",
                    "anexo__actividades_discapacidad",
                    "anexo__necesidades_alimentarias",
                    "anexo__actividades_recreativas",
                    "anexo__actividades_culturales",
                    "anexo__emprendimientos_productivos",
                    "anexo__actividades_religiosas",
                    "anexo__actividades_huerta",
                    "anexo__espacio_huerta",
                    "anexo__otras_actividades",
                    "anexo__cuales_otras_actividades",
                    "anexo__veces_recibio_insumos_2024",
                    "excepcion__adjuntos",
                    "excepcion__descripcion",
                    "excepcion__motivo__nombre",
                    "excepcion__longitud",
                    "excepcion__latitud",
                    "excepcion__firma",
                    "imagenes",
                    "punto_entregas__tipo_comedor__nombre",
                    "punto_entregas__reciben_otros_recepcion",
                    "punto_entregas__frecuencia_entrega_bolsones__nombre",
                    "punto_entregas__tipo_modulo_bolsones__nombre",
                    "punto_entregas__otros_punto_entregas",
                    "punto_entregas__existe_punto_entregas",
                    "punto_entregas__funciona_punto_entregas",
                    "punto_entregas__observa_entregas",
                    "punto_entregas__retiran_mercaderias_distribucion",
                    "punto_entregas__retiran_mercaderias_comercio",
                    "punto_entregas__reciben_dinero",
                    "punto_entregas__registran_entrega_bolsones",
                )
                .get(pk=relevamiento_id)
            )

            # Asegurar que `excepcion__adjuntos` sea una lista
            if isinstance(relevamiento.get("excepcion__adjuntos"), str):
                relevamiento["excepcion__adjuntos"] = [
                    relevamiento["excepcion__adjuntos"]
                ]

            if isinstance(relevamiento.get("imagenes"), str):
                relevamiento["imagenes"] = [relevamiento["imagenes"]]
            return relevamiento

        except Relevamiento.DoesNotExist:
            return None
        except Exception:
            logger.exception(
                "Error en RelevamientoService.get_relevamiento_detail_object",
                extra={"relevamiento_id": relevamiento_id},
            )
            raise

    @staticmethod
    def create_or_update_funcionamiento(
        funcionamiento_data, funcionamiento_instance=None
    ):
        try:
            if "modalidad_prestacion" in funcionamiento_data:
                modalidad_prestacion = funcionamiento_data.get(
                    "modalidad_prestacion", ""
                ).strip()
                funcionamiento_data["modalidad_prestacion"] = (
                    TipoModalidadPrestacion.objects.filter(
                        nombre__iexact=modalidad_prestacion
                    ).first()
                    if modalidad_prestacion
                    else None
                )

            if "servicio_por_turnos" in funcionamiento_data:
                funcionamiento_data["servicio_por_turnos"] = convert_to_boolean(
                    funcionamiento_data["servicio_por_turnos"]
                )

            if "cantidad_turnos" in funcionamiento_data:
                funcionamiento_data["cantidad_turnos"] = (
                    None
                    if funcionamiento_data["cantidad_turnos"] == ""
                    else int(funcionamiento_data["cantidad_turnos"])
                )

            if funcionamiento_instance is None:
                funcionamiento_instance = FuncionamientoPrestacion.objects.create(
                    **funcionamiento_data
                )
            else:
                funcionamiento_instance = assign_values_to_instance(
                    funcionamiento_instance, funcionamiento_data
                )

            return funcionamiento_instance
        except Exception:
            logger.exception(
                "Error en RelevamientoService.create_or_update_funcionamiento",
                extra={"funcionamiento_data": funcionamiento_data},
            )
            payload = {
                "metodo": "create_or_update_funcionamiento",
                "body": {"excepcion": funcionamiento_data},
            }
            logger.info("payload", extra={"data": payload})
            raise

    @staticmethod
    def create_or_update_espacio_prestacion(
        espacio_prestacion_data, espacio_prestacion_instance=None
    ):
        try:
            espacio_prestacion_data = (
                RelevamientoService.populate_espacio_prestacion_data(
                    espacio_prestacion_data
                )
            )

            if espacio_prestacion_instance is None:
                espacio_prestacion_instance = EspacioPrestacion.objects.create(
                    **espacio_prestacion_data
                )
            else:
                espacio_prestacion_instance = assign_values_to_instance(
                    espacio_prestacion_instance, espacio_prestacion_data
                )
            return espacio_prestacion_instance
        except Exception:
            logger.exception(
                "Error en RelevamientoService.create_or_update_espacio_prestacion",
                extra={"espacio_prestacion_data": espacio_prestacion_data},
            )
            payload = {
                "metodo": "create_or_update_espacio_prestacion",
                "body": {"excepcion": espacio_prestacion_data},
            }
            logger.info("payload", extra={"data": payload})
            raise

    @staticmethod
    def populate_espacio_prestacion_data(
        prestacion_data,
    ):  # pylint: disable=too-many-statements,too-many-branches
        # Esto es una lista de metodos a ejecutar para cada item de la prestacion_data
        transformations = {
            "espacio_equipado": convert_to_boolean,
            "tiene_ventilacion": convert_to_boolean,
            "tiene_salida_emergencia": convert_to_boolean,
            "salida_emergencia_senializada": convert_to_boolean,
            "tiene_equipacion_incendio": convert_to_boolean,
            "tiene_botiquin": convert_to_boolean,
            "tiene_buena_iluminacion": convert_to_boolean,
            "tiene_sanitarios": convert_to_boolean,
            "informacion_quejas": convert_to_boolean,
            "desague_hinodoro": lambda x: get_object_or_none(
                TipoDesague, "nombre__iexact", x
            ),
            "gestion_quejas": lambda x: get_object_or_none(
                TipoGestionQuejas, "nombre__iexact", x
            ),
            "gestion_quejas_otro": lambda x: x,
            "frecuencia_limpieza": lambda x: get_object_or_none(
                FrecuenciaLimpieza, "nombre__iexact", x
            ),
            "frecuencia_limpieza_otro": lambda x: x,
        }
        # Se ejecuta el metodo populate_data que recorre la prestacion_data y aplica las transformaciones
        prestacion_data = populate_data(prestacion_data, transformations)

        return prestacion_data

    @staticmethod
    def create_or_update_cocina(cocina_data, cocina_instance=None):
        try:
            cocina_data = RelevamientoService.populate_cocina_data(cocina_data)
            combustibles_queryset = TipoCombustible.objects.none()

            if "abastecimiento_combustible" in cocina_data:
                combustible_str = cocina_data.pop("abastecimiento_combustible")
                combustibles_arr = [
                    nombre.strip() for nombre in combustible_str.split(",")
                ]
                combustibles_queryset = TipoCombustible.objects.filter(
                    nombre__in=combustibles_arr
                )

            if cocina_instance is None:
                cocina_instance = EspacioCocina.objects.create(**cocina_data)
            else:
                for field, value in cocina_data.items():
                    setattr(cocina_instance, field, value)

            if combustibles_queryset.exists():
                cocina_instance.abastecimiento_combustible.set(combustibles_queryset)

            cocina_instance.save()

            return cocina_instance
        except Exception:
            logger.exception(
                "Error en RelevamientoService.create_or_update_cocina",
                extra={"cocina_data": cocina_data},
            )
            payload = {
                "metodo": "create_or_update_cocina",
                "body": {"excepcion": cocina_data},
            }
            logger.info("payload", extra={"data": payload})
            raise

    @staticmethod
    def populate_cocina_data(cocina_data):
        # Esto es una lista de metodos a ejecutar para cada item de la cocina_data
        transformations = {
            "espacio_elaboracion_alimentos": convert_to_boolean,
            "almacenamiento_alimentos_secos": convert_to_boolean,
            "heladera": convert_to_boolean,
            "freezer": convert_to_boolean,
            "recipiente_residuos_organicos": convert_to_boolean,
            "recipiente_residuos_reciclables": convert_to_boolean,
            "otros_residuos": convert_to_boolean,
            "recipiente_otros_residuos": convert_to_boolean,
            "abastecimiento_agua": lambda x: (
                get_object_or_none(TipoAgua, "nombre__iexact", x) if x else None
            ),
            "instalacion_electrica": convert_to_boolean,
        }
        # Se ejecuta el metodo populate_data que recorre la cocina_data y aplica las transformaciones
        cocina_data = populate_data(cocina_data, transformations)
        return cocina_data

    @staticmethod
    def create_or_update_espacio(espacio_data, espacio_instance=None):
        try:
            if "cocina" in espacio_data:
                cocina_data = espacio_data["cocina"]
                cocina_instance = RelevamientoService.create_or_update_cocina(
                    cocina_data, getattr(espacio_instance, "cocina", None)
                )
                espacio_data["cocina"] = cocina_instance
            if "prestacion" in espacio_data:
                prestacion_data = espacio_data["prestacion"]
                prestacion_instance = (
                    RelevamientoService.create_or_update_espacio_prestacion(
                        prestacion_data, getattr(espacio_instance, "prestacion", None)
                    )
                )
                espacio_data["prestacion"] = prestacion_instance

            if "tipo_espacio_fisico" in espacio_data:
                espacio_data["tipo_espacio_fisico"] = (
                    TipoEspacio.objects.get(
                        nombre__iexact=espacio_data["tipo_espacio_fisico"]
                    )
                    if espacio_data["tipo_espacio_fisico"] != ""
                    else None
                )

            if espacio_instance is None:
                espacio_instance = Espacio.objects.create(**espacio_data)
            else:
                espacio_instance = assign_values_to_instance(
                    espacio_instance, espacio_data
                )

            return espacio_instance
        except Exception:
            logger.exception(
                "Error en RelevamientoService.create_or_update_espacio",
                extra={"espacio_data": espacio_data},
            )
            payload = {
                "metodo": "create_or_update_espacio",
                "body": {"excepcion": espacio_data},
            }
            logger.info("payload", extra={"data": payload})
            raise

    @staticmethod
    def create_or_update_colaboradores(colaboradores_data, colaboradores_instance=None):
        colaboradores_data = RelevamientoService.populate_colaboradores_data(
            colaboradores_data
        )
        try:
            if colaboradores_instance is None:
                colaboradores_instance = Colaboradores.objects.create(
                    **colaboradores_data
                )
            else:
                colaboradores_instance = assign_values_to_instance(
                    colaboradores_instance, colaboradores_data
                )

            return colaboradores_instance
        except Exception:
            logger.exception(
                "Error en RelevamientoService.create_or_update_colaboradores",
                extra={"colaboradores_data": colaboradores_data},
            )
            payload = {
                "metodo": "create_or_update_colaboradores",
                "body": {"excepcion": colaboradores_data},
            }
            logger.info("payload", extra={"data": payload})
            raise

    @staticmethod
    def populate_colaboradores_data(colaboradores_data):
        # Esto es una lista de metodos a ejecutar para cada item de la colaboradores_data
        transformations = {
            "colaboradores_capacitados_alimentos": convert_to_boolean,
            "colaboradores_recibieron_capacitacion_alimentos": convert_to_boolean,
            "colaboradores_capacitados_salud_seguridad": convert_to_boolean,
            "colaboradores_recibieron_capacitacion_emergencias": convert_to_boolean,
            "colaboradores_recibieron_capacitacion_violencia": convert_to_boolean,
            "cantidad_colaboradores": lambda x: get_object_or_none(
                CantidadColaboradores, "nombre__iexact", x
            ),
        }
        # Se ejecuta el metodo populate_data que recorre la colaboradores_data y aplica las transformaciones
        colaboradores_data = populate_data(colaboradores_data, transformations)
        return colaboradores_data

    @staticmethod
    def create_or_update_recursos(recursos_data, recursos_instance=None):
        try:
            recursos_data = RelevamientoService.populate_recursos_data(recursos_data)

            # Separar campos ManyToMany de otros campos
            many_to_many_fields = [
                "recursos_donaciones_particulares",
                "recursos_estado_nacional",
                "recursos_estado_provincial",
                "recursos_estado_municipal",
                "recursos_otros",
            ]

            # Campos que NO son ManyToMany
            scalar_fields = {
                k: v for k, v in recursos_data.items() if k not in many_to_many_fields
            }

            if recursos_instance is None:
                recursos_instance = FuenteRecursos.objects.create(**scalar_fields)
            else:
                for field, value in scalar_fields.items():
                    setattr(recursos_instance, field, value)

            if "recibe_donaciones_particulares" in recursos_data:
                recursos_instance.recibe_donaciones_particulares = recursos_data[
                    "recibe_donaciones_particulares"
                ]

            if "recursos_donaciones_particulares" in recursos_data:
                recursos_instance.recursos_donaciones_particulares.set(
                    recursos_data["recursos_donaciones_particulares"]
                )

            if "recursos_estado_nacional" in recursos_data:
                recursos_instance.recursos_estado_nacional.set(
                    recursos_data["recursos_estado_nacional"]
                )

            if "recursos_estado_provincial" in recursos_data:
                recursos_instance.recursos_estado_provincial.set(
                    recursos_data["recursos_estado_provincial"]
                )

            if "recursos_estado_municipal" in recursos_data:
                recursos_instance.recursos_estado_municipal.set(
                    recursos_data["recursos_estado_municipal"]
                )

            if "recursos_otros" in recursos_data:
                recursos_instance.recursos_otros.set(recursos_data["recursos_otros"])

            recursos_instance.save()

            return recursos_instance
        except Exception:
            logger.exception(
                "Error en RelevamientoService.create_or_update_recursos",
                extra={"recursos_data": recursos_data},
            )
            payload = {
                "metodo": "create_or_update_recursos",
                "body": {"excepcion": recursos_data},
            }
            logger.info("payload", extra={"data": payload})
            raise

    @staticmethod
    def populate_recursos_data(
        recursos_data,
    ):  # pylint: disable=too-many-statements,too-many-branches
        # Esto es una lista de metodos a ejecutar para cada item de la recursos_data
        transformations = {
            "recibe_donaciones_particulares": convert_to_boolean,
            "frecuencia_donaciones_particulares": lambda x: get_object_or_none(
                FrecuenciaRecepcionRecursos, "nombre__iexact", x
            ),
            "recibe_estado_nacional": convert_to_boolean,
            "frecuencia_estado_nacional": lambda x: get_object_or_none(
                FrecuenciaRecepcionRecursos, "nombre__iexact", x
            ),
            "recibe_estado_provincial": convert_to_boolean,
            "frecuencia_estado_provincial": lambda x: get_object_or_none(
                FrecuenciaRecepcionRecursos, "nombre__iexact", x
            ),
            "recibe_estado_municipal": convert_to_boolean,
            "frecuencia_estado_municipal": lambda x: get_object_or_none(
                FrecuenciaRecepcionRecursos, "nombre__iexact", x
            ),
            "recibe_otros": convert_to_boolean,
            "frecuencia_otros": lambda x: get_object_or_none(
                FrecuenciaRecepcionRecursos, "nombre__iexact", x
            ),
            "recursos_donaciones_particulares": lambda x: get_recursos(
                "recursos_donaciones_particulares", recursos_data, TipoRecurso
            ),
            "recursos_estado_nacional": lambda x: get_recursos(
                "recursos_estado_nacional", recursos_data, TipoRecurso
            ),
            "recursos_estado_provincial": lambda x: get_recursos(
                "recursos_estado_provincial", recursos_data, TipoRecurso
            ),
            "recursos_estado_municipal": lambda x: get_recursos(
                "recursos_estado_municipal", recursos_data, TipoRecurso
            ),
            "recursos_otros": lambda x: get_recursos(
                "recursos_otros", recursos_data, TipoRecurso
            ),
        }
        # Se ejecuta el metodo populate_data que recorre la recursos_data y aplica las transformaciones
        recursos_data = populate_data(recursos_data, transformations)
        return recursos_data

    @staticmethod
    def create_or_update_compras(compras_data, compras_instance=None):
        try:
            compras_data = RelevamientoService.populate_compras_data(compras_data)

            if compras_instance is None:
                compras_instance = FuenteCompras.objects.create(**compras_data)
            else:
                compras_instance = assign_values_to_instance(
                    compras_instance, compras_data
                )
            return compras_instance
        except Exception:
            logger.exception(
                "Error en RelevamientoService.create_or_update_compras",
                extra={"compras_data": compras_data},
            )
            payload = {
                "metodo": "create_or_update_compras",
                "body": {"excepcion": compras_data},
            }
            logger.info("payload", extra={"data": payload})
            raise

    @staticmethod
    def create_or_update_anexo(anexo_data, anexo_instance=None):
        try:
            anexo_data = RelevamientoService.populate_anexo_data(anexo_data)

            if anexo_instance is None:
                anexo_instance = Anexo.objects.create(**anexo_data)
            else:
                anexo_instance = assign_values_to_instance(anexo_instance, anexo_data)
            return anexo_instance
        except Exception:
            logger.exception(
                "Error en RelevamientoService.create_or_update_anexo",
                extra={"anexo_data": anexo_data},
            )
            payload = {
                "metodo": "create_or_update_anexo",
                "body": {"anexo": anexo_data},
            }
            logger.info("payload", extra={"data": payload})
            raise

    @staticmethod
    def populate_anexo_data(  # pylint: disable=too-many-statements,too-many-branches
        anexo_data,
    ):
        # Esto es una lista de metodos a ejecutar para cada item de la anexo_data
        transformations = {
            "tipo_insumo": lambda x: get_object_or_none(
                TipoInsumos, "nombre__iexact", x
            ),
            "frecuencia_insumo": lambda x: get_object_or_none(
                TipoFrecuenciaInsumos, "nombre__iexact", x
            ),
            "tecnologia": lambda x: get_object_or_none(
                TipoTecnologia, "nombre__iexact", x
            ),
            "acceso_comedor": lambda x: get_object_or_none(
                TipoAccesoComedor, "nombre__iexact", x
            ),
            "distancia_transporte": lambda x: get_object_or_none(
                TipoDistanciaTransporte, "nombre__iexact", x
            ),
            "comedor_merendero": convert_to_boolean,
            "insumos_organizacion": convert_to_boolean,
            "servicio_internet": convert_to_boolean,
            "zona_inundable": convert_to_boolean,
            "actividades_jardin_maternal": convert_to_boolean,
            "actividades_jardin_infantes": convert_to_boolean,
            "apoyo_escolar": convert_to_boolean,
            "alfabetizacion_terminalidad": convert_to_boolean,
            "capacitaciones_talleres": convert_to_boolean,
            "promocion_salud": convert_to_boolean,
            "actividades_discapacidad": convert_to_boolean,
            "necesidades_alimentarias": convert_to_boolean,
            "actividades_recreativas": convert_to_boolean,
            "actividades_culturales": convert_to_boolean,
            "emprendimientos_productivos": convert_to_boolean,
            "actividades_religiosas": convert_to_boolean,
            "actividades_huerta": convert_to_boolean,
            "espacio_huerta": convert_to_boolean,
            "otras_actividades": convert_to_boolean,
        }
        # Se ejecuta el metodo populate_data que recorre la anexo_data y aplica las transformaciones
        anexo_data = populate_data(anexo_data, transformations)

        if "veces_recibio_insumos_2024" in anexo_data:
            anexo_data["veces_recibio_insumos_2024"] = convert_string_to_int(
                anexo_data["veces_recibio_insumos_2024"]
            )

        return anexo_data

    @staticmethod
    def create_or_update_punto_entregas(
        punto_entregas_data, punto_entregas_instance=None
    ):
        try:
            punto_entregas_data = RelevamientoService.populate_punto_entregas_data(
                punto_entregas_data
            )

            frecuencia_recepcion_mercaderias_queryset = (
                TipoFrecuenciaBolsones.objects.none()
            )
            if "frecuencia_recepcion_mercaderias" in punto_entregas_data:
                frecuencia_str = punto_entregas_data.pop(
                    "frecuencia_recepcion_mercaderias", ""
                )
                frecuencia_arr = [
                    nombre.strip() for nombre in frecuencia_str.split(",")
                ]
                frecuencia_recepcion_mercaderias_queryset = (
                    TipoFrecuenciaBolsones.objects.filter(nombre__in=frecuencia_arr)
                )

            if punto_entregas_instance is None:
                punto_entregas_instance = PuntoEntregas.objects.create(
                    **punto_entregas_data
                )
            else:
                for field, value in punto_entregas_data.items():
                    if field not in [
                        "frecuencia_recepcion_mercaderias",
                    ]:
                        setattr(punto_entregas_instance, field, value)

            if frecuencia_recepcion_mercaderias_queryset.exists():
                punto_entregas_instance.frecuencia_recepcion_mercaderias.set(
                    frecuencia_recepcion_mercaderias_queryset
                )

            punto_entregas_instance.save()

            return punto_entregas_instance
        except Exception:
            logger.exception(
                "Error en RelevamientoService.create_or_update_punto_entregas",
                extra={"punto_entregas_data": punto_entregas_data},
            )
            payload = {
                "metodo": "create_or_update_punto_entregas",
                "body": {"punto_entregas": punto_entregas_data},
            }
            logger.info("payload", extra={"data": payload})
            raise

    @staticmethod
    def populate_punto_entregas_data(punto_entregas_data):
        # Esto es una lista de metodos a ejecutar para cada item de la punto_entregas_data
        transformations = {
            "tipo_comedor": lambda x: get_object_or_none(
                TipoDeComedor, "nombre__iexact", x
            ),
            "frecuencia_entrega_bolsones": lambda x: get_object_or_none(
                TipoFrecuenciaBolsones, "nombre__iexact", x
            ),
            "tipo_modulo_bolsones": lambda x: get_object_or_none(
                TipoModuloBolsones, "nombre__iexact", x
            ),
            "existe_punto_entregas": convert_to_boolean,
            "funciona_punto_entregas": convert_to_boolean,
            "observa_entregas": convert_to_boolean,
            "retiran_mercaderias_distribucion": convert_to_boolean,
            "retiran_mercaderias_comercio": convert_to_boolean,
            "reciben_dinero": convert_to_boolean,
            "registran_entrega_bolsones": convert_to_boolean,
        }
        # Se ejecuta el metodo populate_data que recorre la punto_entregas_data y aplica las transformaciones
        punto_entregas_data = populate_data(punto_entregas_data, transformations)

        return punto_entregas_data

    @staticmethod
    def populate_compras_data(compras_data):
        # Esto es una lista de metodos a ejecutar para cada item de la compras_data
        transformations = {
            "almacen_cercano": convert_to_boolean,
            "verduleria": convert_to_boolean,
            "granja": convert_to_boolean,
            "carniceria": convert_to_boolean,
            "pescaderia": convert_to_boolean,
            "supermercado": convert_to_boolean,
            "mercado_central": convert_to_boolean,
            "ferias_comunales": convert_to_boolean,
            "mayoristas": convert_to_boolean,
            "otro": convert_to_boolean,
        }
        # Se ejecuta el metodo populate_data que recorre la compras_data y aplica las transformaciones
        compras_data = populate_data(compras_data, transformations)

        return compras_data

    @staticmethod
    def create_or_update_prestacion(prestacion_data, prestacion_instance=None):
        try:
            prestacion_data = RelevamientoService.populate_prestacion_data(
                prestacion_data
            )

            if prestacion_instance is None:
                prestacion_instance = Prestacion.objects.create(**prestacion_data)
            else:
                prestacion_instance = assign_values_to_instance(
                    prestacion_instance, prestacion_data
                )
            return prestacion_instance
        except Exception:
            logger.exception(
                "Error en RelevamientoService.create_or_update_prestacion",
                extra={"prestacion_data": prestacion_data},
            )
            payload = {
                "metodo": "create_or_update_prestacion",
                "body": {"prestacion": prestacion_data},
            }
            logger.info("payload", extra={"data": payload})
            raise

    @staticmethod
    def populate_prestacion_data(
        prestacion_data,
    ):  # pylint: disable=too-many-statements,too-many-branches
        try:
            dias = [
                "lunes",
                "martes",
                "miercoles",
                "jueves",
                "viernes",
                "sabado",
                "domingo",
            ]
            comidas = ["desayuno", "almuerzo", "merienda", "cena", "merienda_reforzada"]
            aoe = [
                "actual",
                "espera",
            ]

            for dia in dias:
                for comida in comidas:
                    for estado in aoe:
                        key = f"{dia}_{comida}_{estado}"
                        if key in prestacion_data:
                            prestacion_data[key] = convert_string_to_int(
                                prestacion_data[key]
                            )

            return prestacion_data
        except Exception as e:
            logger.exception(
                "Error en RelevamientoService.populate_prestacion_data",
                extra={"error": str(e)},
            )
            raise

    @staticmethod
    def create_or_update_responsable_y_referente(
        responsable_es_referente, responsable_data, referente_data, sisoc_id
    ):
        try:
            responsable = None
            referente = None

            if responsable_data and any(responsable_data.values()):
                responsable = Referente.objects.filter(
                    documento=responsable_data.get("documento")
                ).last()

                if responsable:
                    for key, value in responsable_data.items():
                        setattr(responsable, key, value)
                    responsable.save()
                else:
                    responsable = Referente.objects.create(
                        nombre=responsable_data.get("nombre", None),
                        apellido=responsable_data.get("apellido", None),
                        mail=responsable_data.get("mail", None),
                        celular=responsable_data.get("celular", None),
                        documento=responsable_data.get("documento", None),
                        funcion=responsable_data.get("funcion", None),
                    )

            if responsable_es_referente:
                referente = responsable  # Referente y Responsable son el mismo
            elif referente_data and any(referente_data.values()):
                referente = Referente.objects.filter(
                    documento=referente_data.get("documento")
                ).last()

                if referente:
                    for key, value in referente_data.items():
                        setattr(
                            referente, key, value
                        )  # Asignar incluso si el valor es None
                    referente.save()

                else:
                    referente = Referente.objects.create(
                        nombre=referente_data.get("nombre", None),
                        apellido=referente_data.get("apellido", None),
                        mail=referente_data.get("mail", None),
                        celular=referente_data.get("celular", None),
                        documento=referente_data.get("documento", None),
                        funcion=referente_data.get("funcion", None),
                    )

            if sisoc_id and referente:
                com_rel = Relevamiento.objects.get(pk=sisoc_id)
                comedor = com_rel.comedor
                comedor.referente = referente
                comedor.save()

            return responsable.id if responsable else None, (
                referente.id if referente else None
            )
        except Exception:
            logger.exception(
                "Error en RelevamientoService.create_or_update_responsable_y_referente",
                extra={
                    "responsable_data": responsable_data,
                    "referente_data": referente_data,
                    "sisoc_id": sisoc_id,
                },
            )
            payload = {
                "metodo": "create_or_update_responsable_y_referente",
                "body": {"responsable": responsable_data, "sisoc_id": sisoc_id},
            }
            logger.info("payload", extra={"data": payload})
            payload2 = {
                "metodo": "create_or_update_responsable_y_referente",
                "body": {"referente": referente_data, "sisoc_id": sisoc_id},
            }
            logger.info("payload", extra={"data": payload2})
            raise

    @staticmethod
    def create_or_update_excepcion(excepcion_data, excepcion_instance=None):
        try:
            excepcion_data = RelevamientoService.populate_excepcion_data(excepcion_data)

            if excepcion_instance is None:
                excepcion_instance = Excepcion.objects.create(**excepcion_data)
            else:
                excepcion_instance = assign_values_to_instance(
                    excepcion_instance, excepcion_data
                )
            return excepcion_instance
        except Exception:
            logger.exception(
                "Error en RelevamientoService.create_or_update_excepcion",
                extra={"excepcion_data": excepcion_data},
            )
            payload = {
                "metodo": "create_or_update_excepcion",
                "body": {"excepcion": excepcion_data},
            }
            logger.info("payload", extra={"data": payload})
            raise

    @staticmethod
    def populate_excepcion_data(excepcion_data):
        try:
            if "motivo" in excepcion_data:
                excepcion_data["motivo"] = get_object_or_none(
                    MotivoExcepcion, "nombre__iexact", excepcion_data["motivo"]
                )
            if "adjuntos" in excepcion_data:
                excepcion_data["adjuntos"] = [
                    url.strip() for url in excepcion_data["adjuntos"].split(",")
                ]

            return excepcion_data
        except Exception as e:
            logger.exception(
                "Error en RelevamientoService.populate_excepcion_data",
                extra={"error": str(e)},
            )
            raise
