# pylint: disable=too-many-lines
import json
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone

from comedores.models import (
    Comedor,
    Referente,
    TipoDeComedor,
)
from core.models import Localidad, Municipio, Provincia
from core.utils import convert_string_to_int
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
from relevamientos.tasks import AsyncSendRelevamientoToGestionar


# TODO: Refactorizar todo esto, pylint esta muriendo aca
class RelevamientoService:  # pylint: disable=too-many-public-methods

    # TODO: Mover metodos no genericos al utils.py

    # Este metodo recibe el nombre del campo de la base, el array de datos y el modelo
    # y devuelve un queryset de los recursos que existen en la base de datos
    @staticmethod
    def get_recursos(nombre, recursos_data, model):
        recursos_str = recursos_data.pop(nombre, "")
        if recursos_str:
            recursos_arr = [n.strip() for n in recursos_str.split(",")]
            return model.objects.filter(nombre__in=recursos_arr)
        return model.objects.none()

    # Convierte un valor de string a booleano
    # Si el valor es "Y" devuelve True, si es "N" devuelve False
    @staticmethod
    def convert_to_boolean(value):
        if value in {"Y", "N"}:
            return value == "Y"
        raise ValueError(f"Valor inesperado para booleano: {value}")

    # Obtiene un objeto del modelo dado, filtrando por el nombre del campo y el valor
    # Si el valor es None o una cadena vacía, devuelve None
    @staticmethod
    def get_object_or_none(model, field_name, value):
        try:
            return model.objects.get(**{field_name: value})
        except model.DoesNotExist:
            return None
        except model.MultipleObjectsReturned:
            return model.objects.filter(**{field_name: value}).first()

    # Asigna los valores del diccionario data a los campos del instance
    # y guarda el instance en la base de datos
    @staticmethod
    def assign_values_to_instance(instance, data):
        for field, value in data.items():
            setattr(instance, field, value)
        instance.save()
        return instance

    @staticmethod
    def populate_data(data, transformations):
        for key, func in transformations.items():
            if key in data:
                data[key] = func(data[key])
        return data

    @staticmethod
    def create_or_update_instance(model, data, instance=None):
        if instance is None:
            instance = model.objects.create(**data)
        else:
            instance = RelevamientoService.assign_values_to_instance(instance, data)
        return instance

    @staticmethod
    def update_comedor(comedor_data, comedor_instance):
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
        comedor_instance.barrio = comedor_data.get("barrio", comedor_instance.barrio)
        comedor_instance.codigo_postal = convert_string_to_int(
            comedor_data.get("codigo_postal", comedor_instance.codigo_postal)
        )
        comedor_instance.provincia = (
            Provincia.objects.get(nombre=comedor_data.get("provincia"))
            if comedor_data.get("provincia")
            else comedor_instance.provincia
        )
        comedor_instance.municipio = (
            Municipio.objects.get(
                nombre=comedor_data.get("municipio"),
            )
            if comedor_data.get("municipio")
            else comedor_instance.municipio
        )
        comedor_instance.localidad = Localidad.objects.get(
            nombre=comedor_data.get("localidad", comedor_instance.localidad),
            municipio=(
                Municipio.objects.get(
                    nombre=comedor_data.get("municipio"),
                    provincia=(
                        Provincia.objects.get(nombre=comedor_data.get("provincia"))
                        if comedor_data.get("provincia")
                        else comedor_instance.provincia
                    ),
                )
                if comedor_data.get("municipio")
                else comedor_instance.municipio
            ),
        )
        comedor_instance.partido = comedor_data.get("partido", comedor_instance.partido)
        comedor_instance.manzana = comedor_data.get("manzana", comedor_instance.manzana)
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

    @staticmethod
    def create_pendiente(request, comedor_id):
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

    @staticmethod
    def update_territorial(request):
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

        AsyncSendRelevamientoToGestionar(relevamiento.id).start()

        return relevamiento

    @staticmethod
    def populate_relevamiento(relevamiento_form, extra_forms):
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

    @staticmethod
    def separate_string(tipos):
        tipos_list = [str(tipo) for tipo in tipos]

        if len(tipos_list) == 0:
            tipos_str = "-"
        elif len(tipos_list) > 1:
            tipos_str = ", ".join(tipos_list[:-1]) + " y " + tipos_list[-1]
        else:
            tipos_str = tipos_list[0]

        return tipos_str

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

    @staticmethod
    def create_or_update_funcionamiento(
        funcionamiento_data, funcionamiento_instance=None
    ):
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
            funcionamiento_data["servicio_por_turnos"] = (
                RelevamientoService.convert_to_boolean(
                    funcionamiento_data["servicio_por_turnos"]
                )
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
            funcionamiento_instance = RelevamientoService.assign_values_to_instance(
                funcionamiento_instance, funcionamiento_data
            )

        return funcionamiento_instance

    @staticmethod
    def create_or_update_espacio_prestacion(
        espacio_prestacion_data, espacio_prestacion_instance=None
    ):
        espacio_prestacion_data = RelevamientoService.populate_espacio_prestacion_data(
            espacio_prestacion_data
        )

        if espacio_prestacion_instance is None:
            espacio_prestacion_instance = EspacioPrestacion.objects.create(
                **espacio_prestacion_data
            )
        else:
            espacio_prestacion_instance = RelevamientoService.assign_values_to_instance(
                espacio_prestacion_instance, espacio_prestacion_data
            )
        return espacio_prestacion_instance

    @staticmethod
    def populate_espacio_prestacion_data(
        prestacion_data,
    ):  # pylint: disable=too-many-statements,too-many-branches
        # Esto es una lista de metodos a ejecutar para cada item de la prestacion_data
        transformations = {
            "espacio_equipado": RelevamientoService.convert_to_boolean,
            "tiene_ventilacion": RelevamientoService.convert_to_boolean,
            "tiene_salida_emergencia": RelevamientoService.convert_to_boolean,
            "salida_emergencia_senializada": RelevamientoService.convert_to_boolean,
            "tiene_equipacion_incendio": RelevamientoService.convert_to_boolean,
            "tiene_botiquin": RelevamientoService.convert_to_boolean,
            "tiene_buena_iluminacion": RelevamientoService.convert_to_boolean,
            "tiene_sanitarios": RelevamientoService.convert_to_boolean,
            "informacion_quejas": RelevamientoService.convert_to_boolean,
            "desague_hinodoro": lambda x: RelevamientoService.get_object_or_none(
                TipoDesague, "nombre__iexact", x
            ),
            "gestion_quejas": lambda x: RelevamientoService.get_object_or_none(
                TipoGestionQuejas, "nombre__iexact", x
            ),
            "gestion_quejas_otro": lambda x: x,
            "frecuencia_limpieza": lambda x: RelevamientoService.get_object_or_none(
                FrecuenciaLimpieza, "nombre__iexact", x
            ),
        }
        # Se ejecuta el metodo populate_data que recorre la prestacion_data y aplica las transformaciones
        prestacion_data = RelevamientoService.populate_data(
            prestacion_data, transformations
        )

        return prestacion_data

    @staticmethod
    def create_or_update_cocina(cocina_data, cocina_instance=None):
        cocina_data = RelevamientoService.populate_cocina_data(cocina_data)
        combustibles_queryset = TipoCombustible.objects.none()

        if "abastecimiento_combustible" in cocina_data:
            combustible_str = cocina_data.pop("abastecimiento_combustible")
            combustibles_arr = [nombre.strip() for nombre in combustible_str.split(",")]
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

    @staticmethod
    def populate_cocina_data(cocina_data):
        # Esto es una lista de metodos a ejecutar para cada item de la cocina_data
        transformations = {
            "espacio_elaboracion_alimentos": RelevamientoService.convert_to_boolean,
            "almacenamiento_alimentos_secos": RelevamientoService.convert_to_boolean,
            "heladera": RelevamientoService.convert_to_boolean,
            "freezer": RelevamientoService.convert_to_boolean,
            "recipiente_residuos_organicos": RelevamientoService.convert_to_boolean,
            "recipiente_residuos_reciclables": RelevamientoService.convert_to_boolean,
            "otros_residuos": RelevamientoService.convert_to_boolean,
            "recipiente_otros_residuos": RelevamientoService.convert_to_boolean,
            "abastecimiento_agua": lambda x: (
                RelevamientoService.get_object_or_none(TipoAgua, "nombre__iexact", x)
                if x
                else None
            ),
            "instalacion_electrica": RelevamientoService.convert_to_boolean,
        }
        # Se ejecuta el metodo populate_data que recorre la cocina_data y aplica las transformaciones
        cocina_data = RelevamientoService.populate_data(cocina_data, transformations)
        return cocina_data

    @staticmethod
    def create_or_update_espacio(espacio_data, espacio_instance=None):
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
            espacio_instance = RelevamientoService.assign_values_to_instance(
                espacio_instance, espacio_data
            )

        return espacio_instance

    @staticmethod
    def create_or_update_colaboradores(colaboradores_data, colaboradores_instance=None):
        colaboradores_data = RelevamientoService.populate_colaboradores_data(
            colaboradores_data
        )

        if colaboradores_instance is None:
            colaboradores_instance = Colaboradores.objects.create(**colaboradores_data)
        else:
            colaboradores_instance = RelevamientoService.assign_values_to_instance(
                colaboradores_instance, colaboradores_data
            )

        return colaboradores_instance

    @staticmethod
    def populate_colaboradores_data(colaboradores_data):
        # Esto es una lista de metodos a ejecutar para cada item de la colaboradores_data
        transformations = {
            "colaboradores_capacitados_alimentos": RelevamientoService.convert_to_boolean,
            "colaboradores_recibieron_capacitacion_alimentos": RelevamientoService.convert_to_boolean,
            "colaboradores_capacitados_salud_seguridad": RelevamientoService.convert_to_boolean,
            "colaboradores_recibieron_capacitacion_emergencias": RelevamientoService.convert_to_boolean,
            "colaboradores_recibieron_capacitacion_violencia": RelevamientoService.convert_to_boolean,
            "cantidad_colaboradores": lambda x: RelevamientoService.get_object_or_none(
                CantidadColaboradores, "nombre__iexact", x
            ),
        }
        # Se ejecuta el metodo populate_data que recorre la colaboradores_data y aplica las transformaciones
        colaboradores_data = RelevamientoService.populate_data(
            colaboradores_data, transformations
        )
        return colaboradores_data

    @staticmethod
    def create_or_update_recursos(recursos_data, recursos_instance=None):
        recursos_data = RelevamientoService.populate_recursos_data(recursos_data)

        if recursos_instance is None:
            recursos_instance = FuenteRecursos.objects.create()
        else:
            for field, value in recursos_data.items():
                if field not in [
                    "recursos_donaciones_particulares",
                    "recursos_estado_nacional",
                    "recursos_estado_provincial",
                    "recursos_estado_municipal",
                    "recursos_otros",
                ]:
                    setattr(recursos_instance, field, value)

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

    @staticmethod
    def populate_recursos_data(
        recursos_data,
    ):  # pylint: disable=too-many-statements,too-many-branches
        # Esto es una lista de metodos a ejecutar para cada item de la recursos_data
        transformations = {
            "recibe_donaciones_particulares": RelevamientoService.convert_to_boolean,
            "frecuencia_donaciones_particulares": lambda x: RelevamientoService.get_object_or_none(
                FrecuenciaRecepcionRecursos, "nombre__iexact", x
            ),
            "recibe_estado_nacional": RelevamientoService.convert_to_boolean,
            "frecuencia_estado_nacional": lambda x: RelevamientoService.get_object_or_none(
                FrecuenciaRecepcionRecursos, "nombre__iexact", x
            ),
            "recibe_estado_provincial": RelevamientoService.convert_to_boolean,
            "frecuencia_estado_provincial": lambda x: RelevamientoService.get_object_or_none(
                FrecuenciaRecepcionRecursos, "nombre__iexact", x
            ),
            "recibe_estado_municipal": RelevamientoService.convert_to_boolean,
            "frecuencia_estado_municipal": lambda x: RelevamientoService.get_object_or_none(
                FrecuenciaRecepcionRecursos, "nombre__iexact", x
            ),
            "recibe_otros": RelevamientoService.convert_to_boolean,
            "frecuencia_otros": lambda x: RelevamientoService.get_object_or_none(
                FrecuenciaRecepcionRecursos, "nombre__iexact", x
            ),
            "recursos_donaciones_particulares": lambda x: RelevamientoService.get_recursos(
                "recursos_donaciones_particulares", recursos_data, TipoRecurso
            ),
            "recursos_estado_nacional": lambda x: RelevamientoService.get_recursos(
                "recursos_estado_nacional", recursos_data, TipoRecurso
            ),
            "recursos_estado_provincial": lambda x: RelevamientoService.get_recursos(
                "recursos_estado_provincial", recursos_data, TipoRecurso
            ),
            "recursos_estado_municipal": lambda x: RelevamientoService.get_recursos(
                "recursos_estado_municipal", recursos_data, TipoRecurso
            ),
            "recursos_otros": lambda x: RelevamientoService.get_recursos(
                "recursos_otros", recursos_data, TipoRecurso
            ),
        }
        # Se ejecuta el metodo populate_data que recorre la recursos_data y aplica las transformaciones
        recursos_data = RelevamientoService.populate_data(
            recursos_data, transformations
        )
        return recursos_data

    @staticmethod
    def create_or_update_compras(compras_data, compras_instance=None):
        compras_data = RelevamientoService.populate_compras_data(compras_data)

        if compras_instance is None:
            compras_instance = FuenteCompras.objects.create(**compras_data)
        else:
            compras_instance = RelevamientoService.assign_values_to_instance(
                compras_instance, compras_data
            )
        return compras_instance

    @staticmethod
    def create_or_update_anexo(anexo_data, anexo_instance=None):
        anexo_data = RelevamientoService.populate_anexo_data(anexo_data)

        if anexo_instance is None:
            anexo_instance = Anexo.objects.create(**anexo_data)
        else:
            anexo_instance = RelevamientoService.assign_values_to_instance(
                anexo_instance, anexo_data
            )
        return anexo_instance

    @staticmethod
    def populate_anexo_data(  # pylint: disable=too-many-statements,too-many-branches
        anexo_data,
    ):
        # Esto es una lista de metodos a ejecutar para cada item de la anexo_data
        transformations = {
            "tipo_insumo": lambda x: RelevamientoService.get_object_or_none(
                TipoInsumos, "nombre__iexact", x
            ),
            "frecuencia_insumo": lambda x: RelevamientoService.get_object_or_none(
                TipoFrecuenciaInsumos, "nombre__iexact", x
            ),
            "tecnologia": lambda x: RelevamientoService.get_object_or_none(
                TipoTecnologia, "nombre__iexact", x
            ),
            "acceso_comedor": lambda x: RelevamientoService.get_object_or_none(
                TipoAccesoComedor, "nombre__iexact", x
            ),
            "distancia_transporte": lambda x: RelevamientoService.get_object_or_none(
                TipoDistanciaTransporte, "nombre__iexact", x
            ),
            "comedor_merendero": RelevamientoService.convert_to_boolean,
            "insumos_organizacion": RelevamientoService.convert_to_boolean,
            "servicio_internet": RelevamientoService.convert_to_boolean,
            "zona_inundable": RelevamientoService.convert_to_boolean,
            "actividades_jardin_maternal": RelevamientoService.convert_to_boolean,
            "actividades_jardin_infantes": RelevamientoService.convert_to_boolean,
            "apoyo_escolar": RelevamientoService.convert_to_boolean,
            "alfabetizacion_terminalidad": RelevamientoService.convert_to_boolean,
            "capacitaciones_talleres": RelevamientoService.convert_to_boolean,
            "promocion_salud": RelevamientoService.convert_to_boolean,
            "actividades_discapacidad": RelevamientoService.convert_to_boolean,
            "necesidades_alimentarias": RelevamientoService.convert_to_boolean,
            "actividades_recreativas": RelevamientoService.convert_to_boolean,
            "actividades_culturales": RelevamientoService.convert_to_boolean,
            "emprendimientos_productivos": RelevamientoService.convert_to_boolean,
            "actividades_religiosas": RelevamientoService.convert_to_boolean,
            "actividades_huerta": RelevamientoService.convert_to_boolean,
            "espacio_huerta": RelevamientoService.convert_to_boolean,
            "otras_actividades": RelevamientoService.convert_to_boolean,
        }
        # Se ejecuta el metodo populate_data que recorre la anexo_data y aplica las transformaciones
        anexo_data = RelevamientoService.populate_data(anexo_data, transformations)

        if "veces_recibio_insumos_2024" in anexo_data:
            anexo_data["veces_recibio_insumos_2024"] = convert_string_to_int(
                anexo_data["veces_recibio_insumos_2024"]
            )

        return anexo_data

    @staticmethod
    def create_or_update_punto_entregas(
        punto_entregas_data, punto_entregas_instance=None
    ):
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
            frecuencia_arr = [nombre.strip() for nombre in frecuencia_str.split(",")]
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

    @staticmethod
    def populate_punto_entregas_data(punto_entregas_data):
        # Esto es una lista de metodos a ejecutar para cada item de la punto_entregas_data
        transformations = {
            "tipo_comedor": lambda x: RelevamientoService.get_object_or_none(
                TipoDeComedor, "nombre__iexact", x
            ),
            "frecuencia_entrega_bolsones": lambda x: RelevamientoService.get_object_or_none(
                TipoFrecuenciaBolsones, "nombre__iexact", x
            ),
            "tipo_modulo_bolsones": lambda x: RelevamientoService.get_object_or_none(
                TipoModuloBolsones, "nombre__iexact", x
            ),
            "existe_punto_entregas": RelevamientoService.convert_to_boolean,
            "funciona_punto_entregas": RelevamientoService.convert_to_boolean,
            "observa_entregas": RelevamientoService.convert_to_boolean,
            "retiran_mercaderias_distribucion": RelevamientoService.convert_to_boolean,
            "retiran_mercaderias_comercio": RelevamientoService.convert_to_boolean,
            "reciben_dinero": RelevamientoService.convert_to_boolean,
            "registran_entrega_bolsones": RelevamientoService.convert_to_boolean,
        }
        # Se ejecuta el metodo populate_data que recorre la punto_entregas_data y aplica las transformaciones
        punto_entregas_data = RelevamientoService.populate_data(
            punto_entregas_data, transformations
        )

        return punto_entregas_data

    @staticmethod
    def populate_compras_data(compras_data):
        # Esto es una lista de metodos a ejecutar para cada item de la compras_data
        transformations = {
            "almacen_cercano": RelevamientoService.convert_to_boolean,
            "verduleria": RelevamientoService.convert_to_boolean,
            "granja": RelevamientoService.convert_to_boolean,
            "carniceria": RelevamientoService.convert_to_boolean,
            "pescaderia": RelevamientoService.convert_to_boolean,
            "supermercado": RelevamientoService.convert_to_boolean,
            "mercado_central": RelevamientoService.convert_to_boolean,
            "ferias_comunales": RelevamientoService.convert_to_boolean,
            "mayoristas": RelevamientoService.convert_to_boolean,
            "otro": RelevamientoService.convert_to_boolean,
        }
        # Se ejecuta el metodo populate_data que recorre la compras_data y aplica las transformaciones
        compras_data = RelevamientoService.populate_data(compras_data, transformations)

        return compras_data

    @staticmethod
    def create_or_update_prestacion(prestacion_data, prestacion_instance=None):
        prestacion_data = RelevamientoService.populate_prestacion_data(prestacion_data)

        if prestacion_instance is None:
            prestacion_instance = Prestacion.objects.create(**prestacion_data)
        else:
            prestacion_instance = RelevamientoService.assign_values_to_instance(
                prestacion_instance, prestacion_data
            )
        return prestacion_instance

    @staticmethod
    def populate_prestacion_data(
        prestacion_data,
    ):  # pylint: disable=too-many-statements,too-many-branches
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

    @staticmethod
    def create_or_update_responsable_y_referente(
        responsable_es_referente, responsable_data, referente_data, sisoc_id
    ):
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

    @staticmethod
    def create_or_update_excepcion(excepcion_data, excepcion_instance=None):
        excepcion_data = RelevamientoService.populate_excepcion_data(excepcion_data)

        if excepcion_instance is None:
            excepcion_instance = Excepcion.objects.create(**excepcion_data)
        else:
            excepcion_instance = RelevamientoService.assign_values_to_instance(
                excepcion_instance, excepcion_data
            )
        return excepcion_instance

    @staticmethod
    def populate_excepcion_data(excepcion_data):
        if "motivo" in excepcion_data:
            excepcion_data["motivo"] = RelevamientoService.get_object_or_none(
                MotivoExcepcion, "nombre__iexact", excepcion_data["motivo"]
            )
        if "adjuntos" in excepcion_data:
            excepcion_data["adjuntos"] = [
                url.strip() for url in excepcion_data["adjuntos"].split(",")
            ]

        return excepcion_data
