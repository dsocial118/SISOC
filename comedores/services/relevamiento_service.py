import json
from django.shortcuts import get_object_or_404
from django.utils import timezone

from comedores.models.comedor import (
    Comedor,
    TipoDeComedor,
)
from comedores.models.relevamiento import (
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
    Referente,
    Relevamiento,
    TipoAccesoComedor,
    TipoAgua,
    TipoCombustible,
    TipoDesague,
    TipoDistanciaTransporte,
    TipoEspacio,
    TipoFrecuenciaInsumos,
    TipoGestionQuejas,
    TipoInsumos,
    TipoModalidadPrestacion,
    TipoRecurso,
    TipoTecnologia,
    PuntoEntregas,
    TipoModuloBolsones,
    FrecuenciaRecepcionRecursos,
    TipoFrecuenciaBolsones,
)
from comedores.tasks import AsyncSendRelevamientoToGestionar


class RelevamientoService:

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
    def convert_to_int(value):
        return int(value) if value != "" else None

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
        PuntoEntregas = extra_forms["punto_entregas_form"].save()
        relevamiento.punto_entregas = PuntoEntregas

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
                    "responsable_relevamiento__funcion",
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
                funcionamiento_data["servicio_por_turnos"] == "Y"
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
            for field, value in funcionamiento_data.items():
                setattr(funcionamiento_instance, field, value)
            funcionamiento_instance.save()

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
            for field, value in espacio_prestacion_data.items():
                setattr(espacio_prestacion_instance, field, value)
            espacio_prestacion_instance.save()

        return espacio_prestacion_instance

    @staticmethod
    def populate_espacio_prestacion_data(prestacion_data):
        if "espacio_equipado" in prestacion_data:
            prestacion_data["espacio_equipado"] = (
                prestacion_data["espacio_equipado"] == "Y"
            )
        if "tiene_ventilacion" in prestacion_data:
            prestacion_data["tiene_ventilacion"] = (
                prestacion_data["tiene_ventilacion"] == "Y"
            )
        if "tiene_salida_emergencia" in prestacion_data:
            prestacion_data["tiene_salida_emergencia"] = (
                prestacion_data["tiene_salida_emergencia"] == "Y"
            )
        if "salida_emergencia_senializada" in prestacion_data:
            prestacion_data["salida_emergencia_senializada"] = (
                prestacion_data["salida_emergencia_senializada"] == "Y"
            )
        if "tiene_equipacion_incendio" in prestacion_data:
            prestacion_data["tiene_equipacion_incendio"] = (
                prestacion_data["tiene_equipacion_incendio"] == "Y"
            )
        if "tiene_botiquin" in prestacion_data:
            prestacion_data["tiene_botiquin"] = prestacion_data["tiene_botiquin"] == "Y"
        if "tiene_buena_iluminacion" in prestacion_data:
            prestacion_data["tiene_buena_iluminacion"] = (
                prestacion_data["tiene_buena_iluminacion"] == "Y"
            )
        if "tiene_sanitarios" in prestacion_data:
            prestacion_data["tiene_sanitarios"] = (
                prestacion_data["tiene_sanitarios"] == "Y"
            )
        if "desague_hinodoro" in prestacion_data:
            prestacion_data["desague_hinodoro"] = (
                TipoDesague.objects.get(
                    nombre__iexact=prestacion_data["desague_hinodoro"]
                )
                if prestacion_data["desague_hinodoro"] != ""
                else None
            )
        if "gestion_quejas" in prestacion_data:
            prestacion_data["gestion_quejas"] = (
                TipoGestionQuejas.objects.get(nombre=prestacion_data["gestion_quejas"])
                if prestacion_data["gestion_quejas"] != ""
                else None
            )
        if "gestion_quejas_otro" in prestacion_data:
            prestacion_data["gestion_quejas_otro"] = prestacion_data[
                "gestion_quejas_otro"
            ]
        if "informacion_quejas" in prestacion_data:
            prestacion_data["informacion_quejas"] = (
                prestacion_data["informacion_quejas"] == "Y"
            )
        if "frecuencia_limpieza" in prestacion_data:
            prestacion_data["frecuencia_limpieza"] = (
                FrecuenciaLimpieza.objects.get(
                    nombre__iexact=prestacion_data["frecuencia_limpieza"]
                )
                if prestacion_data["frecuencia_limpieza"] != ""
                else None
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
        if "espacio_elaboracion_alimentos" in cocina_data:
            cocina_data["espacio_elaboracion_alimentos"] = (
                cocina_data["espacio_elaboracion_alimentos"] == "Y"
            )
        if "almacenamiento_alimentos_secos" in cocina_data:
            cocina_data["almacenamiento_alimentos_secos"] = (
                cocina_data["almacenamiento_alimentos_secos"] == "Y"
            )
        if "heladera" in cocina_data:
            cocina_data["heladera"] = cocina_data["heladera"] == "Y"
        if "freezer" in cocina_data:
            cocina_data["freezer"] = cocina_data["freezer"] == "Y"
        if "recipiente_residuos_organicos" in cocina_data:
            cocina_data["recipiente_residuos_organicos"] = (
                cocina_data["recipiente_residuos_organicos"] == "Y"
            )
        if "recipiente_residuos_reciclables" in cocina_data:
            cocina_data["recipiente_residuos_reciclables"] = (
                cocina_data["recipiente_residuos_reciclables"] == "Y"
            )
        if "otros_residuos" in cocina_data:
            cocina_data["otros_residuos"] = (
                cocina_data["recipiente_otros_residuos"] == "Y"
            )
        if "recipiente_otros_residuos" in cocina_data:
            cocina_data["recipiente_otros_residuos"] = (
                cocina_data["recipiente_otros_residuos"] == "Y"
            )
        if "abastecimiento_agua" in cocina_data:
            cocina_data["abastecimiento_agua"] = (
                TipoAgua.objects.get(nombre__iexact=cocina_data["abastecimiento_agua"])
                if cocina_data["abastecimiento_agua"] != ""
                else None
            )
        if "instalacion_electrica" in cocina_data:
            cocina_data["instalacion_electrica"] = (
                cocina_data["instalacion_electrica"] == "Y"
            )

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
            for field, value in espacio_data.items():
                setattr(espacio_instance, field, value)
            espacio_instance.save()

        return espacio_instance

    @staticmethod
    def create_or_update_colaboradores(colaboradores_data, colaboradores_instance=None):
        colaboradores_data = RelevamientoService.populate_colaboradores_data(
            colaboradores_data
        )

        if colaboradores_instance is None:
            colaboradores_instance = Colaboradores.objects.create(**colaboradores_data)
        else:
            for field, value in colaboradores_data.items():
                setattr(colaboradores_instance, field, value)
            colaboradores_instance.save()

        return colaboradores_instance

    @staticmethod
    def populate_colaboradores_data(colaboradores_data):
        if "cantidad_colaboradores" in colaboradores_data:
            colaboradores_data["cantidad_colaboradores"] = (
                CantidadColaboradores.objects.get(
                    nombre__iexact=colaboradores_data["cantidad_colaboradores"]
                )
                if colaboradores_data["cantidad_colaboradores"] != ""
                else None
            )
        if "colaboradores_capacitados_alimentos" in colaboradores_data:
            colaboradores_data["colaboradores_capacitados_alimentos"] = (
                colaboradores_data["colaboradores_capacitados_alimentos"] == "Y"
            )
        if "colaboradores_recibieron_capacitacion_alimentos" in colaboradores_data:
            colaboradores_data["colaboradores_recibieron_capacitacion_alimentos"] = (
                colaboradores_data["colaboradores_recibieron_capacitacion_alimentos"]
                == "Y"
            )
        if "colaboradores_capacitados_salud_seguridad" in colaboradores_data:
            colaboradores_data["colaboradores_capacitados_salud_seguridad"] = (
                colaboradores_data["colaboradores_capacitados_salud_seguridad"] == "Y"
            )
        if "colaboradores_recibieron_capacitacion_emergencias" in colaboradores_data:
            colaboradores_data["colaboradores_recibieron_capacitacion_emergencias"] = (
                colaboradores_data["colaboradores_recibieron_capacitacion_emergencias"]
                == "Y"
            )
        if "colaboradores_recibieron_capacitacion_violencia" in colaboradores_data:
            colaboradores_data["colaboradores_recibieron_capacitacion_violencia"] = (
                colaboradores_data["colaboradores_recibieron_capacitacion_violencia"]
                == "Y"
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
    def populate_recursos_data(recursos_data):
        def get_frecuencia_recepcion(nombre):
            return (
                FrecuenciaRecepcionRecursos.objects.get(
                    nombre__iexact=recursos_data[f"{nombre}"]
                )
                if recursos_data[f"{nombre}"] != ""
                else None
            )

        def get_recursos(nombre):
            recursos_str = recursos_data.pop(nombre, "")
            if recursos_str:
                recursos_arr = [nombre.strip() for nombre in recursos_str.split(",")]
                return TipoRecurso.objects.filter(nombre__in=recursos_arr)
            return TipoRecurso.objects.none()

        if "recibe_donaciones_particulares" in recursos_data:
            recursos_data["recibe_donaciones_particulares"] = (
                recursos_data["recibe_donaciones_particulares"] == "Y"
            )

        if "frecuencia_donaciones_particulares" in recursos_data:
            recursos_data["frecuencia_donaciones_particulares"] = (
                get_frecuencia_recepcion("frecuencia_donaciones_particulares")
            )

        if "recursos_donaciones_particulares" in recursos_data:
            recursos_data["recursos_donaciones_particulares"] = get_recursos(
                "recursos_donaciones_particulares"
            )

        if "recibe_estado_nacional" in recursos_data:
            recursos_data["recibe_estado_nacional"] = (
                recursos_data["recibe_estado_nacional"] == "Y"
            )

        if "frecuencia_estado_nacional" in recursos_data:
            recursos_data["frecuencia_estado_nacional"] = get_frecuencia_recepcion(
                "frecuencia_estado_nacional"
            )

        if "recursos_estado_nacional" in recursos_data:
            recursos_data["recursos_estado_nacional"] = get_recursos(
                "recursos_estado_nacional"
            )

        if "recibe_estado_provincial" in recursos_data:
            recursos_data["recibe_estado_provincial"] = (
                recursos_data["recibe_estado_provincial"] == "Y"
            )

        if "frecuencia_estado_provincial" in recursos_data:
            recursos_data["frecuencia_estado_provincial"] = get_frecuencia_recepcion(
                "frecuencia_estado_provincial"
            )

        if "recursos_estado_provincial" in recursos_data:
            recursos_data["recursos_estado_provincial"] = get_recursos(
                "recursos_estado_provincial"
            )

        if "recibe_estado_municipal" in recursos_data:
            recursos_data["recibe_estado_municipal"] = (
                recursos_data["recibe_estado_municipal"] == "Y"
            )

        if "frecuencia_estado_municipal" in recursos_data:
            recursos_data["frecuencia_estado_municipal"] = get_frecuencia_recepcion(
                "frecuencia_estado_municipal"
            )

        if "recursos_estado_municipal" in recursos_data:
            recursos_data["recursos_estado_municipal"] = get_recursos(
                "recursos_estado_municipal"
            )

        if "recibe_otros" in recursos_data:
            recursos_data["recibe_otros"] = recursos_data["recibe_otros"] == "Y"

        if "frecuencia_otros" in recursos_data:
            recursos_data["frecuencia_otros"] = get_frecuencia_recepcion(
                "frecuencia_otros"
            )

        if "recursos_otros" in recursos_data:
            recursos_data["recursos_otros"] = get_recursos("recursos_otros")

        return recursos_data

    @staticmethod
    def create_or_update_compras(compras_data, compras_instance=None):
        compras_data = RelevamientoService.populate_compras_data(compras_data)

        if compras_instance is None:
            compras_instance = FuenteCompras.objects.create(**compras_data)
        else:
            for field, value in compras_data.items():
                setattr(compras_instance, field, value)
            compras_instance.save()

        return compras_instance

    @staticmethod
    def create_or_update_anexo(anexo_data, anexo_instance=None):
        anexo_data = RelevamientoService.populate_anexo_data(anexo_data)

        if anexo_instance is None:
            anexo_instance = Anexo.objects.create(**anexo_data)
        else:
            for field, value in anexo_data.items():
                setattr(anexo_instance, field, value)
            anexo_instance.save()

        return anexo_instance

    @staticmethod
    def populate_anexo_data(anexo_data):
        if "tipo_insumo" in anexo_data and anexo_data["tipo_insumo"]:
            try:
                anexo_data["tipo_insumo"] = TipoInsumos.objects.get(
                    nombre__iexact=anexo_data["tipo_insumo"]
                )
            except TipoInsumos.DoesNotExist:
                anexo_data["tipo_insumo"] = None
        else:
            anexo_data["tipo_insumo"] = None
        if "frecuencia_insumo" in anexo_data and anexo_data["frecuencia_insumo"]:
            try:
                anexo_data["frecuencia_insumo"] = TipoFrecuenciaInsumos.objects.get(
                    nombre__iexact=anexo_data["frecuencia_insumo"]
                )
            except TipoFrecuenciaInsumos.DoesNotExist:
                anexo_data["frecuencia_insumo"] = None
        else:
            anexo_data["frecuencia_insumo"] = None

        if "tecnologia" in anexo_data and anexo_data["tecnologia"]:
            try:
                anexo_data["tecnologia"] = TipoTecnologia.objects.get(
                    nombre__iexact=anexo_data["tecnologia"]
                )
            except TipoTecnologia.DoesNotExist:
                anexo_data["tecnologia"] = None
        else:
            anexo_data["tecnologia"] = None

        if "acceso_comedor" in anexo_data and anexo_data["acceso_comedor"]:
            try:
                anexo_data["acceso_comedor"] = TipoAccesoComedor.objects.get(
                    nombre__iexact=anexo_data["acceso_comedor"]
                )
            except TipoAccesoComedor.DoesNotExist:
                anexo_data["acceso_comedor"] = None
        else:
            anexo_data["acceso_comedor"] = None

        if "distancia_transporte" in anexo_data and anexo_data["distancia_transporte"]:
            try:
                anexo_data["distancia_transporte"] = (
                    TipoDistanciaTransporte.objects.get(
                        nombre__iexact=anexo_data["distancia_transporte"]
                    )
                )
            except TipoDistanciaTransporte.DoesNotExist:
                anexo_data["distancia_transporte"] = None
        else:
            anexo_data["distancia_transporte"] = None
        if "comedor_merendero" in anexo_data:
            anexo_data["comedor_merendero"] = anexo_data["comedor_merendero"] == "Y"

        if "insumos_organizacion" in anexo_data:
            anexo_data["insumos_organizacion"] = (
                anexo_data["insumos_organizacion"] == "Y"
            )

        if "servicio_internet" in anexo_data:
            if (
                anexo_data["servicio_internet"] != ""
                and anexo_data["servicio_internet"] == "Y"
            ):
                anexo_data["servicio_internet"] = True
            elif (
                anexo_data["servicio_internet"] != ""
                and anexo_data["servicio_internet"] == "N"
            ):
                anexo_data["servicio_internet"] = False
            elif anexo_data["servicio_internet"] == "":
                anexo_data["servicio_internet"] = None

        if "zona_inundable" in anexo_data:
            anexo_data["zona_inundable"] = anexo_data["zona_inundable"] == "Y"

        if "actividades_jardin_maternal" in anexo_data:
            anexo_data["actividades_jardin_maternal"] = (
                anexo_data["actividades_jardin_maternal"] == "Y"
            )

        if "actividades_jardin_infantes" in anexo_data:
            anexo_data["actividades_jardin_infantes"] = (
                anexo_data["actividades_jardin_infantes"] == "Y"
            )

        if "apoyo_escolar" in anexo_data:
            anexo_data["apoyo_escolar"] = anexo_data["apoyo_escolar"] == "Y"

        if "alfabetizacion_terminalidad" in anexo_data:
            anexo_data["alfabetizacion_terminalidad"] = (
                anexo_data["alfabetizacion_terminalidad"] == "Y"
            )

        if "capacitaciones_talleres" in anexo_data:
            anexo_data["capacitaciones_talleres"] = (
                anexo_data["capacitaciones_talleres"] == "Y"
            )

        if "promocion_salud" in anexo_data:
            anexo_data["promocion_salud"] = anexo_data["promocion_salud"] == "Y"

        if "actividades_discapacidad" in anexo_data:
            anexo_data["actividades_discapacidad"] = (
                anexo_data["actividades_discapacidad"] == "Y"
            )

        if "necesidades_alimentarias" in anexo_data:
            anexo_data["necesidades_alimentarias"] = (
                anexo_data["necesidades_alimentarias"] == "Y"
            )

        if "actividades_recreativas" in anexo_data:
            anexo_data["actividades_recreativas"] = (
                anexo_data["actividades_recreativas"] == "Y"
            )

        if "actividades_culturales" in anexo_data:
            anexo_data["actividades_culturales"] = (
                anexo_data["actividades_culturales"] == "Y"
            )

        if "emprendimientos_productivos" in anexo_data:
            anexo_data["emprendimientos_productivos"] = (
                anexo_data["emprendimientos_productivos"] == "Y"
            )

        if "actividades_religiosas" in anexo_data:
            anexo_data["actividades_religiosas"] = (
                anexo_data["actividades_religiosas"] == "Y"
            )

        if "actividades_huerta" in anexo_data:
            anexo_data["actividades_huerta"] = anexo_data["actividades_huerta"] == "Y"

        if "espacio_huerta" in anexo_data:
            anexo_data["espacio_huerta"] = anexo_data["espacio_huerta"] == "Y"

        if "otras_actividades" in anexo_data:
            anexo_data["otras_actividades"] = anexo_data["otras_actividades"] == "Y"

        if "veces_recibio_insumos_2024" in anexo_data:
            anexo_data["veces_recibio_insumos_2024"] = (
                RelevamientoService.convert_to_int(
                    anexo_data["veces_recibio_insumos_2024"]
                )
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
        def get_frecuencia_entrega(nombre):
            return (
                TipoFrecuenciaBolsones.objects.get(
                    nombre__iexact=punto_entregas_data[f"{nombre}"]
                )
                if punto_entregas_data[f"{nombre}"] != ""
                else None
            )

        if "tipo_comedor" in punto_entregas_data:
            punto_entregas_data["tipo_comedor"] = (
                TipoDeComedor.objects.get(
                    nombre__iexact=punto_entregas_data["tipo_comedor"]
                )
                if punto_entregas_data["tipo_comedor"]
                else None
            )

        if "frecuencia_entrega_bolsones" in punto_entregas_data:
            punto_entregas_data["frecuencia_entrega_bolsones"] = get_frecuencia_entrega(
                "frecuencia_entrega_bolsones"
            )

        if "tipo_modulo_bolsones" in punto_entregas_data:
            punto_entregas_data["tipo_modulo_bolsones"] = (
                TipoModuloBolsones.objects.get(
                    nombre__iexact=punto_entregas_data["tipo_modulo_bolsones"]
                )
                if punto_entregas_data["tipo_modulo_bolsones"] != ""
                else None
            )
        else:
            punto_entregas_data["tipo_modulo_bolsones"] = None

        if "existe_punto_entregas" in punto_entregas_data:
            punto_entregas_data["existe_punto_entregas"] = (
                punto_entregas_data["existe_punto_entregas"] == "Y"
            )

        if "funciona_punto_entregas" in punto_entregas_data:
            punto_entregas_data["funciona_punto_entregas"] = (
                punto_entregas_data["funciona_punto_entregas"] == "Y"
            )

        if "observa_entregas" in punto_entregas_data:
            punto_entregas_data["observa_entregas"] = (
                punto_entregas_data["observa_entregas"] == "Y"
            )

        if "retiran_mercaderias_distribucion" in punto_entregas_data:
            punto_entregas_data["retiran_mercaderias_distribucion"] = (
                punto_entregas_data["retiran_mercaderias_distribucion"] == "Y"
            )

        if "retiran_mercaderias_comercio" in punto_entregas_data:
            punto_entregas_data["retiran_mercaderias_comercio"] = (
                punto_entregas_data["retiran_mercaderias_comercio"] == "Y"
            )

        if "reciben_dinero" in punto_entregas_data:
            punto_entregas_data["reciben_dinero"] = (
                punto_entregas_data["reciben_dinero"] == "Y"
            )

        if "registran_entrega_bolsones" in punto_entregas_data:
            punto_entregas_data["registran_entrega_bolsones"] = (
                punto_entregas_data["registran_entrega_bolsones"] == "Y"
            )

        return punto_entregas_data

    @staticmethod
    def populate_compras_data(compras_data):
        if "almacen_cercano" in compras_data:
            compras_data["almacen_cercano"] = compras_data["almacen_cercano"] == "Y"
        if "verduleria" in compras_data:
            compras_data["verduleria"] = compras_data["verduleria"] == "Y"
        if "granja" in compras_data:
            compras_data["granja"] = compras_data["granja"] == "Y"
        if "carniceria" in compras_data:
            compras_data["carniceria"] = compras_data["carniceria"] == "Y"
        if "pescaderia" in compras_data:
            compras_data["pescaderia"] = compras_data["pescaderia"] == "Y"
        if "supermercado" in compras_data:
            compras_data["supermercado"] = compras_data["supermercado"] == "Y"
        if "mercado_central" in compras_data:
            compras_data["mercado_central"] = compras_data["mercado_central"] == "Y"
        if "ferias_comunales" in compras_data:
            compras_data["ferias_comunales"] = compras_data["ferias_comunales"] == "Y"
        if "mayoristas" in compras_data:
            compras_data["mayoristas"] = compras_data["mayoristas"] == "Y"
        if "otro" in compras_data:
            compras_data["otro"] = compras_data["otro"] == "Y"

        return compras_data

    @staticmethod
    def create_or_update_prestacion(prestacion_data, prestacion_instance=None):
        prestacion_data = RelevamientoService.populate_prestacion_data(prestacion_data)

        if prestacion_instance is None:
            prestacion_instance = Prestacion.objects.create(**prestacion_data)
        else:
            for field, value in prestacion_data.items():
                setattr(prestacion_instance, field, value)
            prestacion_instance.save()

        return prestacion_instance

    @staticmethod
    def populate_prestacion_data(prestacion_data):

        if "lunes_desayuno_actual" in prestacion_data:
            prestacion_data["lunes_desayuno_actual"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["lunes_desayuno_actual"]
                )
            )
        if "lunes_desayuno_espera" in prestacion_data:
            prestacion_data["lunes_desayuno_espera"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["lunes_desayuno_espera"]
                )
            )
        if "lunes_almuerzo_actual" in prestacion_data:
            prestacion_data["lunes_almuerzo_actual"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["lunes_almuerzo_actual"]
                )
            )
        if "lunes_almuerzo_espera" in prestacion_data:
            prestacion_data["lunes_almuerzo_espera"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["lunes_almuerzo_espera"]
                )
            )
        if "lunes_merienda_actual" in prestacion_data:
            prestacion_data["lunes_merienda_actual"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["lunes_merienda_actual"]
                )
            )
        if "lunes_merienda_espera" in prestacion_data:
            prestacion_data["lunes_merienda_espera"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["lunes_merienda_espera"]
                )
            )
        if "lunes_cena_actual" in prestacion_data:
            prestacion_data["lunes_cena_actual"] = RelevamientoService.convert_to_int(
                prestacion_data["lunes_cena_actual"]
            )
        if "lunes_cena_espera" in prestacion_data:
            prestacion_data["lunes_cena_espera"] = RelevamientoService.convert_to_int(
                prestacion_data["lunes_cena_espera"]
            )
        if "martes_desayuno_actual" in prestacion_data:
            prestacion_data["martes_desayuno_actual"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["martes_desayuno_actual"]
                )
            )
        if "martes_desayuno_espera" in prestacion_data:
            prestacion_data["martes_desayuno_espera"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["martes_desayuno_espera"]
                )
            )
        if "martes_almuerzo_actual" in prestacion_data:
            prestacion_data["martes_almuerzo_actual"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["martes_almuerzo_actual"]
                )
            )
        if "martes_almuerzo_espera" in prestacion_data:
            prestacion_data["martes_almuerzo_espera"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["martes_almuerzo_espera"]
                )
            )
        if "martes_merienda_actual" in prestacion_data:
            prestacion_data["martes_merienda_actual"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["martes_merienda_actual"]
                )
            )
        if "martes_merienda_espera" in prestacion_data:
            prestacion_data["martes_merienda_espera"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["martes_merienda_espera"]
                )
            )
        if "martes_cena_actual" in prestacion_data:
            prestacion_data["martes_cena_actual"] = RelevamientoService.convert_to_int(
                prestacion_data["martes_cena_actual"]
            )
        if "martes_cena_espera" in prestacion_data:
            prestacion_data["martes_cena_espera"] = RelevamientoService.convert_to_int(
                prestacion_data["martes_cena_espera"]
            )
        if "miercoles_desayuno_actual" in prestacion_data:
            prestacion_data["miercoles_desayuno_actual"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["miercoles_desayuno_actual"]
                )
            )
        if "miercoles_desayuno_espera" in prestacion_data:
            prestacion_data["miercoles_desayuno_espera"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["miercoles_desayuno_espera"]
                )
            )
        if "miercoles_almuerzo_actual" in prestacion_data:
            prestacion_data["miercoles_almuerzo_actual"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["miercoles_almuerzo_actual"]
                )
            )
        if "miercoles_almuerzo_espera" in prestacion_data:
            prestacion_data["miercoles_almuerzo_espera"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["miercoles_almuerzo_espera"]
                )
            )
        if "miercoles_merienda_actual" in prestacion_data:
            prestacion_data["miercoles_merienda_actual"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["miercoles_merienda_actual"]
                )
            )
        if "miercoles_merienda_espera" in prestacion_data:
            prestacion_data["miercoles_merienda_espera"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["miercoles_merienda_espera"]
                )
            )
        if "miercoles_cena_actual" in prestacion_data:
            prestacion_data["miercoles_cena_actual"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["miercoles_cena_actual"]
                )
            )
        if "miercoles_cena_espera" in prestacion_data:
            prestacion_data["miercoles_cena_espera"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["miercoles_cena_espera"]
                )
            )
        if "jueves_desayuno_actual" in prestacion_data:
            prestacion_data["jueves_desayuno_actual"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["jueves_desayuno_actual"]
                )
            )
        if "jueves_desayuno_espera" in prestacion_data:
            prestacion_data["jueves_desayuno_espera"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["jueves_desayuno_espera"]
                )
            )
        if "jueves_almuerzo_actual" in prestacion_data:
            prestacion_data["jueves_almuerzo_actual"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["jueves_almuerzo_actual"]
                )
            )
        if "jueves_almuerzo_espera" in prestacion_data:
            prestacion_data["jueves_almuerzo_espera"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["jueves_almuerzo_espera"]
                )
            )
        if "jueves_merienda_actual" in prestacion_data:
            prestacion_data["jueves_merienda_actual"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["jueves_merienda_actual"]
                )
            )
        if "jueves_merienda_espera" in prestacion_data:
            prestacion_data["jueves_merienda_espera"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["jueves_merienda_espera"]
                )
            )
        if "jueves_cena_actual" in prestacion_data:
            prestacion_data["jueves_cena_actual"] = RelevamientoService.convert_to_int(
                prestacion_data["jueves_cena_actual"]
            )
        if "jueves_cena_espera" in prestacion_data:
            prestacion_data["jueves_cena_espera"] = RelevamientoService.convert_to_int(
                prestacion_data["jueves_cena_espera"]
            )
        if "viernes_desayuno_actual" in prestacion_data:
            prestacion_data["viernes_desayuno_actual"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["viernes_desayuno_actual"]
                )
            )
        if "viernes_desayuno_espera" in prestacion_data:
            prestacion_data["viernes_desayuno_espera"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["viernes_desayuno_espera"]
                )
            )
        if "viernes_almuerzo_actual" in prestacion_data:
            prestacion_data["viernes_almuerzo_actual"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["viernes_almuerzo_actual"]
                )
            )
        if "viernes_almuerzo_espera" in prestacion_data:
            prestacion_data["viernes_almuerzo_espera"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["viernes_almuerzo_espera"]
                )
            )
        if "viernes_merienda_actual" in prestacion_data:
            prestacion_data["viernes_merienda_actual"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["viernes_merienda_actual"]
                )
            )
        if "viernes_merienda_espera" in prestacion_data:
            prestacion_data["viernes_merienda_espera"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["viernes_merienda_espera"]
                )
            )
        if "viernes_cena_actual" in prestacion_data:
            prestacion_data["viernes_cena_actual"] = RelevamientoService.convert_to_int(
                prestacion_data["viernes_cena_actual"]
            )
        if "viernes_cena_espera" in prestacion_data:
            prestacion_data["viernes_cena_espera"] = RelevamientoService.convert_to_int(
                prestacion_data["viernes_cena_espera"]
            )
        if "sabado_desayuno_actual" in prestacion_data:
            prestacion_data["sabado_desayuno_actual"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["sabado_desayuno_actual"]
                )
            )
        if "sabado_desayuno_espera" in prestacion_data:
            prestacion_data["sabado_desayuno_espera"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["sabado_desayuno_espera"]
                )
            )
        if "sabado_almuerzo_actual" in prestacion_data:
            prestacion_data["sabado_almuerzo_actual"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["sabado_almuerzo_actual"]
                )
            )
        if "sabado_almuerzo_espera" in prestacion_data:
            prestacion_data["sabado_almuerzo_espera"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["sabado_almuerzo_espera"]
                )
            )
        if "sabado_merienda_actual" in prestacion_data:
            prestacion_data["sabado_merienda_actual"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["sabado_merienda_actual"]
                )
            )
        if "sabado_merienda_espera" in prestacion_data:
            prestacion_data["sabado_merienda_espera"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["sabado_merienda_espera"]
                )
            )
        if "sabado_cena_actual" in prestacion_data:
            prestacion_data["sabado_cena_actual"] = RelevamientoService.convert_to_int(
                prestacion_data["sabado_cena_actual"]
            )
        if "sabado_cena_espera" in prestacion_data:
            prestacion_data["sabado_cena_espera"] = RelevamientoService.convert_to_int(
                prestacion_data["sabado_cena_espera"]
            )
        if "domingo_desayuno_actual" in prestacion_data:
            prestacion_data["domingo_desayuno_actual"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["domingo_desayuno_actual"]
                )
            )
        if "domingo_desayuno_espera" in prestacion_data:
            prestacion_data["domingo_desayuno_espera"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["domingo_desayuno_espera"]
                )
            )
        if "domingo_almuerzo_actual" in prestacion_data:
            prestacion_data["domingo_almuerzo_actual"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["domingo_almuerzo_actual"]
                )
            )
        if "domingo_almuerzo_espera" in prestacion_data:
            prestacion_data["domingo_almuerzo_espera"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["domingo_almuerzo_espera"]
                )
            )
        if "domingo_merienda_actual" in prestacion_data:
            prestacion_data["domingo_merienda_actual"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["domingo_merienda_actual"]
                )
            )
        if "domingo_merienda_espera" in prestacion_data:
            prestacion_data["domingo_merienda_espera"] = (
                RelevamientoService.convert_to_int(
                    prestacion_data["domingo_merienda_espera"]
                )
            )
        if "domingo_cena_actual" in prestacion_data:
            prestacion_data["domingo_cena_actual"] = RelevamientoService.convert_to_int(
                prestacion_data["domingo_cena_actual"]
            )
        if "domingo_cena_espera" in prestacion_data:
            prestacion_data["domingo_cena_espera"] = RelevamientoService.convert_to_int(
                prestacion_data["domingo_cena_espera"]
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
            for field, value in excepcion_data.items():
                setattr(excepcion_instance, field, value)
            excepcion_instance.save()

        return excepcion_instance

    @staticmethod
    def populate_excepcion_data(excepcion_data):
        if "motivo" in excepcion_data:
            excepcion_data["motivo"] = (
                MotivoExcepcion.objects.get(nombre__iexact=excepcion_data["motivo"])
                if excepcion_data["motivo"] != ""
                else None
            )
        if "adjuntos" in excepcion_data:
            excepcion_data["adjuntos"] = [
                url.strip() for url in excepcion_data["adjuntos"].split(",")
            ]

        return excepcion_data
