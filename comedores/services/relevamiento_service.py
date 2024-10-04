import datetime

from django.utils import timezone

from comedores.models import (
    CantidadColaboradores,
    Colaboradores,
    Espacio,
    EspacioCocina,
    EspacioPrestacion,
    FrecuenciaLimpieza,
    FrecuenciaRecepcionRecursos,
    FuenteCompras,
    FuenteRecursos,
    FuncionamientoPrestacion,
    Prestacion,
    Relevamiento,
    TipoAgua,
    TipoCombustible,
    TipoDesague,
    TipoEspacio,
    TipoGestionQuejas,
    TipoModalidadPrestacion,
    TipoRecurso,
)
from usuarios.models import Usuarios


class RelevamientoService:
    @staticmethod
    def populate_relevamiento(relevamiento_form, extra_forms, user_id):
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

        compras = extra_forms["compras_form"].save()
        relevamiento.compras = compras

        prestacion = extra_forms["prestacion_form"].save()
        relevamiento.prestacion = prestacion

        usuario = Usuarios.objects.get(pk=user_id).usuario
        relevamiento.relevador = f"{usuario.first_name} {usuario.last_name}"
        relevamiento.fecha_visita = timezone.now()

        relevamiento.save()

        return relevamiento

    @staticmethod
    def generar_string_gas(relevamiento_id):
        tipos = Relevamiento.objects.get(
            pk=relevamiento_id
        ).espacio.cocina.abastecimiento_combustible.all()

        tipos_list = [str(tipo) for tipo in tipos]

        if len(tipos_list) > 1:
            tipos_str = ", ".join(tipos_list[:-1]) + " y " + tipos_list[-1]
        else:
            tipos_str = tipos_list[0]
        return tipos_str

    @staticmethod
    def get_relevamiento_detail_object(relevamiento_id):
        return (
            Relevamiento.objects.prefetch_related(
                "comedor",
                "funcionamiento",
                "espacio",
                "colaboradores",
                "recursos",
                "compras",
            )
            .filter(pk=relevamiento_id)
            .values(
                "id",
                "relevador",
                "comedor__nombre",
                "fecha_visita",
                "comedor__comienzo",
                "funcionamiento__modalidad_prestacion__nombre",
                "funcionamiento__servicio_por_turnos",
                "funcionamiento__cantidad_turnos",
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
                "espacio__prestacion__gestion_quejas",
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
                "recursos__recursos_donaciones_particulares__nombre",
                "recursos__recibe_estado_nacional",
                "recursos__frecuencia_estado_nacional__nombre",
                "recursos__recursos_estado_nacional__nombre",
                "recursos__recibe_estado_provincial",
                "recursos__frecuencia_estado_provincial__nombre",
                "recursos__recursos_estado_provincial__nombre",
                "recursos__recibe_estado_municipal",
                "recursos__frecuencia_estado_municipal__nombre",
                "recursos__recursos_estado_municipal__nombre",
                "recursos__recibe_otros",
                "recursos__frecuencia_otros__nombre",
                "recursos__recursos_otros__nombre",
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
            )
            .first()
        )

    @staticmethod
    def format_fecha_visita(fecha_visita):
        fecha_formateada = datetime.datetime.strptime(fecha_visita, "%d/%m/%Y %H:%M")
        return timezone.make_aware(fecha_formateada, timezone.get_default_timezone())

    @staticmethod
    def create_or_update_funcionamiento(
        funcionamiento_data, funcionamiento_instance=None
    ):
        if "modalidad_prestacion" in funcionamiento_data:
            funcionamiento_data["modalidad_prestacion"] = (
                TipoModalidadPrestacion.objects.get(
                    nombre__iexact=funcionamiento_data["modalidad_prestacion"]
                )
            )
        if "servicio_por_turnos" in funcionamiento_data:
            funcionamiento_data["servicio_por_turnos"] = (
                funcionamiento_data["servicio_por_turnos"] == "Y"
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
        epacio_prestacion_data, espacio_prestacion_instance=None
    ):
        epacio_prestacion_data = RelevamientoService.populate_espacio_prestacion_data(
            epacio_prestacion_data
        )

        if espacio_prestacion_instance is None:
            espacio_prestacion_instance = EspacioPrestacion.objects.create(
                **epacio_prestacion_data
            )
        else:
            for field, value in epacio_prestacion_data.items():
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
            prestacion_data["gestion_quejas"] = TipoGestionQuejas.objects.get(
                nombre=prestacion_data["gestion_quejas"]
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
                ),
            )

        return prestacion_data

    @staticmethod
    def create_or_update_cocina(cocina_data, cocina_instance=None):
        cocina_data = RelevamientoService.populate_cocina_data(cocina_data)

        if cocina_instance is None:
            cocina_instance = EspacioCocina.objects.create(**cocina_data)
        else:
            for field, value in cocina_data.items():
                setattr(cocina_instance, field, value)
            cocina_instance.save()

        if "abastecimiento_combustible" in cocina_data:
            combustible_str = cocina_data["abastecimiento_combustible"]
            combustibles_arr = [nombre.strip() for nombre in combustible_str.split(",")]
            combustibles_queryset = TipoCombustible.objects.filter(
                nombre__in=combustibles_arr
            )
            cocina_instance.abastecimiento_combustible.set(combustibles_queryset)

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
            cocina_data["abastecimiento_agua"] = TipoAgua.objects.get(
                nombre__iexact=cocina_data["abastecimiento_agua"]
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
            espacio_data["tipo_espacio_fisico"] = TipoEspacio.objects.get(
                nombre__iexact=espacio_data["tipo_espacio_fisico"]
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
            colaboradores_instance = Espacio.objects.create(**colaboradores_data)
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
            )

        if "colaboradores_capacitados_alimentos" in colaboradores_data:
            colaboradores_data["colaboradores_capacitados_alimentos"] = (
                colaboradores_data["cantidad_colaboradores"] == "Y"
            )
        if "colaboradores_recibieron_capacitacion_alimentos" in colaboradores_data:
            colaboradores_data["colaboradores_recibieron_capacitacion_alimentos"] = (
                colaboradores_data["cantidad_colaboradores"] == "Y"
            )
        if "colaboradores_capacitados_salud_seguridad" in colaboradores_data:
            colaboradores_data["colaboradores_capacitados_salud_seguridad"] = (
                colaboradores_data["cantidad_colaboradores"] == "Y"
            )
        if "colaboradores_recibieron_capacitacion_emergencias" in colaboradores_data:
            colaboradores_data["colaboradores_recibieron_capacitacion_emergencias"] = (
                colaboradores_data["cantidad_colaboradores"] == "Y"
            )
        if "colaboradores_recibieron_capacitacion_violencia" in colaboradores_data:
            colaboradores_data["colaboradores_recibieron_capacitacion_violencia"] = (
                colaboradores_data["cantidad_colaboradores"] == "Y"
            )

        return colaboradores_data

    @staticmethod
    def create_or_update_recursos(recursos_data, recursos_instance=None):
        recursos_data = RelevamientoService.populate_recursos_data(recursos_data)

        if recursos_instance is None:
            recursos_instance = FuenteRecursos.objects.create(**recursos_data)
        else:
            for field, value in recursos_data.items():
                setattr(recursos_instance, field, value)
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
            return (
                TipoRecurso.objects.get(nombre__iexact=recursos_data[f"{nombre}"])
                if recursos_data[f"{nombre}"] != ""
                else None
            )

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
                recursos_data["recibe_donaciones_particulares"] == "Y"
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
                recursos_data["recibe_donaciones_particulares"] == "Y"
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
                recursos_data["recibe_donaciones_particulares"] == "Y"
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
            recursos_data["recibe_otros"] = (
                recursos_data["recibe_donaciones_particulares"] == "Y",
            )

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
        def convert_to_int(value):
            return int(value) if value != "" else None

        if "lunes_desayuno_actual" in prestacion_data:
            prestacion_data["lunes_desayuno_actual"] = convert_to_int(
                prestacion_data["lunes_desayuno_actual"]
            )
        if "lunes_desayuno_espera" in prestacion_data:
            prestacion_data["lunes_desayuno_espera"] = convert_to_int(
                prestacion_data["lunes_desayuno_espera"]
            )
        if "lunes_almuerzo_actual" in prestacion_data:
            prestacion_data["lunes_almuerzo_actual"] = convert_to_int(
                prestacion_data["lunes_almuerzo_actual"]
            )
        if "lunes_almuerzo_espera" in prestacion_data:
            prestacion_data["lunes_almuerzo_espera"] = convert_to_int(
                prestacion_data["lunes_almuerzo_espera"]
            )
        if "lunes_merienda_actual" in prestacion_data:
            prestacion_data["lunes_merienda_actual"] = convert_to_int(
                prestacion_data["lunes_merienda_actual"]
            )
        if "lunes_merienda_espera" in prestacion_data:
            prestacion_data["lunes_merienda_espera"] = convert_to_int(
                prestacion_data["lunes_merienda_espera"]
            )
        if "lunes_cena_actual" in prestacion_data:
            prestacion_data["lunes_cena_actual"] = convert_to_int(
                prestacion_data["lunes_cena_actual"]
            )
        if "lunes_cena_espera" in prestacion_data:
            prestacion_data["lunes_cena_espera"] = convert_to_int(
                prestacion_data["lunes_cena_espera"]
            )
        if "martes_desayuno_actual" in prestacion_data:
            prestacion_data["martes_desayuno_actual"] = convert_to_int(
                prestacion_data["martes_desayuno_actual"]
            )
        if "martes_desayuno_espera" in prestacion_data:
            prestacion_data["martes_desayuno_espera"] = convert_to_int(
                prestacion_data["martes_desayuno_espera"]
            )
        if "martes_almuerzo_actual" in prestacion_data:
            prestacion_data["martes_almuerzo_actual"] = convert_to_int(
                prestacion_data["martes_almuerzo_actual"]
            )
        if "martes_almuerzo_espera" in prestacion_data:
            prestacion_data["martes_almuerzo_espera"] = convert_to_int(
                prestacion_data["martes_almuerzo_espera"]
            )
        if "martes_merienda_actual" in prestacion_data:
            prestacion_data["martes_merienda_actual"] = convert_to_int(
                prestacion_data["martes_merienda_actual"]
            )
        if "martes_merienda_espera" in prestacion_data:
            prestacion_data["martes_merienda_espera"] = convert_to_int(
                prestacion_data["martes_merienda_espera"]
            )
        if "martes_cena_actual" in prestacion_data:
            prestacion_data["martes_cena_actual"] = convert_to_int(
                prestacion_data["martes_cena_actual"]
            )
        if "martes_cena_espera" in prestacion_data:
            prestacion_data["martes_cena_espera"] = convert_to_int(
                prestacion_data["martes_cena_espera"]
            )
        if "miercoles_desayuno_actual" in prestacion_data:
            prestacion_data["miercoles_desayuno_actual"] = convert_to_int(
                prestacion_data["miercoles_desayuno_actual"]
            )
        if "miercoles_desayuno_espera" in prestacion_data:
            prestacion_data["miercoles_desayuno_espera"] = convert_to_int(
                prestacion_data["miercoles_desayuno_espera"]
            )
        if "miercoles_almuerzo_actual" in prestacion_data:
            prestacion_data["miercoles_almuerzo_actual"] = convert_to_int(
                prestacion_data["miercoles_almuerzo_actual"]
            )
        if "miercoles_almuerzo_espera" in prestacion_data:
            prestacion_data["miercoles_almuerzo_espera"] = convert_to_int(
                prestacion_data["miercoles_almuerzo_espera"]
            )
        if "miercoles_merienda_actual" in prestacion_data:
            prestacion_data["miercoles_merienda_actual"] = convert_to_int(
                prestacion_data["miercoles_merienda_actual"]
            )
        if "miercoles_merienda_espera" in prestacion_data:
            prestacion_data["miercoles_merienda_espera"] = convert_to_int(
                prestacion_data["miercoles_merienda_espera"]
            )
        if "miercoles_cena_actual" in prestacion_data:
            prestacion_data["miercoles_cena_actual"] = convert_to_int(
                prestacion_data["miercoles_cena_actual"]
            )
        if "miercoles_cena_espera" in prestacion_data:
            prestacion_data["miercoles_cena_espera"] = convert_to_int(
                prestacion_data["miercoles_cena_espera"]
            )
        if "jueves_desayuno_actual" in prestacion_data:
            prestacion_data["jueves_desayuno_actual"] = convert_to_int(
                prestacion_data["jueves_desayuno_actual"]
            )
        if "jueves_desayuno_espera" in prestacion_data:
            prestacion_data["jueves_desayuno_espera"] = convert_to_int(
                prestacion_data["jueves_desayuno_espera"]
            )
        if "jueves_almuerzo_actual" in prestacion_data:
            prestacion_data["jueves_almuerzo_actual"] = convert_to_int(
                prestacion_data["jueves_almuerzo_actual"]
            )
        if "jueves_almuerzo_espera" in prestacion_data:
            prestacion_data["jueves_almuerzo_espera"] = convert_to_int(
                prestacion_data["jueves_almuerzo_espera"]
            )
        if "jueves_merienda_actual" in prestacion_data:
            prestacion_data["jueves_merienda_actual"] = convert_to_int(
                prestacion_data["jueves_merienda_actual"]
            )
        if "jueves_merienda_espera" in prestacion_data:
            prestacion_data["jueves_merienda_espera"] = convert_to_int(
                prestacion_data["jueves_merienda_espera"]
            )
        if "jueves_cena_actual" in prestacion_data:
            prestacion_data["jueves_cena_actual"] = convert_to_int(
                prestacion_data["jueves_cena_actual"]
            )
        if "jueves_cena_espera" in prestacion_data:
            prestacion_data["jueves_cena_espera"] = convert_to_int(
                prestacion_data["jueves_cena_espera"]
            )
        if "viernes_desayuno_actual" in prestacion_data:
            prestacion_data["viernes_desayuno_actual"] = convert_to_int(
                prestacion_data["viernes_desayuno_actual"]
            )
        if "viernes_desayuno_espera" in prestacion_data:
            prestacion_data["viernes_desayuno_espera"] = convert_to_int(
                prestacion_data["viernes_desayuno_espera"]
            )
        if "viernes_almuerzo_actual" in prestacion_data:
            prestacion_data["viernes_almuerzo_actual"] = convert_to_int(
                prestacion_data["viernes_almuerzo_actual"]
            )
        if "viernes_almuerzo_espera" in prestacion_data:
            prestacion_data["viernes_almuerzo_espera"] = convert_to_int(
                prestacion_data["viernes_almuerzo_espera"]
            )
        if "viernes_merienda_actual" in prestacion_data:
            prestacion_data["viernes_merienda_actual"] = convert_to_int(
                prestacion_data["viernes_merienda_actual"]
            )
        if "viernes_merienda_espera" in prestacion_data:
            prestacion_data["viernes_merienda_espera"] = convert_to_int(
                prestacion_data["viernes_merienda_espera"]
            )
        if "viernes_cena_actual" in prestacion_data:
            prestacion_data["viernes_cena_actual"] = convert_to_int(
                prestacion_data["viernes_cena_actual"]
            )
        if "viernes_cena_espera" in prestacion_data:
            prestacion_data["viernes_cena_espera"] = convert_to_int(
                prestacion_data["viernes_cena_espera"]
            )
        if "sabado_desayuno_actual" in prestacion_data:
            prestacion_data["sabado_desayuno_actual"] = convert_to_int(
                prestacion_data["sabado_desayuno_actual"]
            )
        if "sabado_desayuno_espera" in prestacion_data:
            prestacion_data["sabado_desayuno_espera"] = convert_to_int(
                prestacion_data["sabado_desayuno_espera"]
            )
        if "sabado_almuerzo_actual" in prestacion_data:
            prestacion_data["sabado_almuerzo_actual"] = convert_to_int(
                prestacion_data["sabado_almuerzo_actual"]
            )
        if "sabado_almuerzo_espera" in prestacion_data:
            prestacion_data["sabado_almuerzo_espera"] = convert_to_int(
                prestacion_data["sabado_almuerzo_espera"]
            )
        if "sabado_merienda_actual" in prestacion_data:
            prestacion_data["sabado_merienda_actual"] = convert_to_int(
                prestacion_data["sabado_merienda_actual"]
            )
        if "sabado_merienda_espera" in prestacion_data:
            prestacion_data["sabado_merienda_espera"] = convert_to_int(
                prestacion_data["sabado_merienda_espera"]
            )
        if "sabado_cena_actual" in prestacion_data:
            prestacion_data["sabado_cena_actual"] = convert_to_int(
                prestacion_data["sabado_cena_actual"]
            )
        if "sabado_cena_espera" in prestacion_data:
            prestacion_data["sabado_cena_espera"] = convert_to_int(
                prestacion_data["sabado_cena_espera"]
            )
        if "domingo_desayuno_actual" in prestacion_data:
            prestacion_data["domingo_desayuno_actual"] = convert_to_int(
                prestacion_data["domingo_desayuno_actual"]
            )
        if "domingo_desayuno_espera" in prestacion_data:
            prestacion_data["domingo_desayuno_espera"] = convert_to_int(
                prestacion_data["domingo_desayuno_espera"]
            )
        if "domingo_almuerzo_actual" in prestacion_data:
            prestacion_data["domingo_almuerzo_actual"] = convert_to_int(
                prestacion_data["domingo_almuerzo_actual"]
            )
        if "domingo_almuerzo_espera" in prestacion_data:
            prestacion_data["domingo_almuerzo_espera"] = convert_to_int(
                prestacion_data["domingo_almuerzo_espera"]
            )
        if "domingo_merienda_actual" in prestacion_data:
            prestacion_data["domingo_merienda_actual"] = convert_to_int(
                prestacion_data["domingo_merienda_actual"]
            )
        if "domingo_merienda_espera" in prestacion_data:
            prestacion_data["domingo_merienda_espera"] = convert_to_int(
                prestacion_data["domingo_merienda_espera"]
            )
        if "domingo_cena_actual" in prestacion_data:
            prestacion_data["domingo_cena_actual"] = convert_to_int(
                prestacion_data["domingo_cena_actual"]
            )
        if "domingo_cena_espera" in prestacion_data:
            prestacion_data["domingo_cena_espera"] = convert_to_int(
                prestacion_data["domingo_cena_espera"]
            )
        return prestacion_data
