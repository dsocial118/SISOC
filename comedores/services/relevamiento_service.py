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
    def guardar_relevamiento(relevamiento_form, extra_forms, user_id):
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
    def api_create_funcionamiento(funcionamiento_data):
        modalidad_prestacion = TipoModalidadPrestacion.objects.get(
            nombre__iexact=funcionamiento_data["modalidad_prestacion"]
        )

        return FuncionamientoPrestacion.objects.create(
            modalidad_prestacion=modalidad_prestacion,
            servicio_por_turnos=funcionamiento_data["servicio_por_turnos"] == "Y",
            cantidad_turnos=funcionamiento_data["cantidad_turnos"],
        )

    @staticmethod
    def api_format_fecha_visita(fecha_visita):
        fecha_formateada = datetime.datetime.strptime(fecha_visita, "%d/%m/%Y %H:%M")
        return timezone.make_aware(fecha_formateada, timezone.get_default_timezone())

    @staticmethod
    def api_create_espacio_prestacion(prestacion_data):
        tipo_desague = (
            TipoDesague.objects.get(nombre__iexact=prestacion_data["desague_hinodoro"])
            if prestacion_data["desague_hinodoro"] != ""
            else None
        )

        return EspacioPrestacion.objects.create(
            espacio_equipado=prestacion_data["espacio_equipado"] == "Y",
            tiene_ventilacion=prestacion_data["tiene_ventilacion"] == "Y",
            tiene_salida_emergencia=prestacion_data["tiene_salida_emergencia"] == "Y",
            salida_emergencia_senializada=prestacion_data[
                "salida_emergencia_senializada"
            ]
            == "Y",
            tiene_equipacion_incendio=prestacion_data["tiene_equipacion_incendio"]
            == "Y",
            tiene_botiquin=prestacion_data["tiene_botiquin"] == "Y",
            tiene_buena_iluminacion=prestacion_data["tiene_buena_iluminacion"] == "Y",
            tiene_sanitarios=prestacion_data["tiene_sanitarios"] == "Y",
            desague_hinodoro=tipo_desague,
            gestion_quejas=TipoGestionQuejas.objects.get(
                nombre=prestacion_data["gestion_quejas"]
            ),
            gestion_quejas_otro=prestacion_data["gestion_quejas_otro"],
            informacion_quejas=prestacion_data["informacion_quejas"] == "Y",
            frecuencia_limpieza=FrecuenciaLimpieza.objects.get(
                nombre__iexact=prestacion_data["frecuencia_limpieza"]
            ),
        )

    @staticmethod
    def api_create_cocina(cocina_data):
        cocina = EspacioCocina.objects.create(
            espacio_elaboracion_alimentos=cocina_data["espacio_elaboracion_alimentos"]
            == "Y",
            almacenamiento_alimentos_secos=cocina_data["almacenamiento_alimentos_secos"]
            == "Y",
            heladera=cocina_data["heladera"] == "Y",
            freezer=cocina_data["freezer"] == "Y",
            recipiente_residuos_organicos=cocina_data["recipiente_residuos_organicos"]
            == "Y",
            recipiente_residuos_reciclables=cocina_data[
                "recipiente_residuos_reciclables"
            ]
            == "Y",
            otros_residuos=cocina_data["recipiente_otros_residuos"] == "Y",
            recipiente_otros_residuos=cocina_data["recipiente_otros_residuos"] == "Y",
            abastecimiento_agua=TipoAgua.objects.get(
                nombre__iexact=cocina_data["abastecimiento_agua"]
            ),
            abastecimiento_agua_otro=cocina_data["abastecimiento_agua_otro"],
            instalacion_electrica=cocina_data["instalacion_electrica"] == "Y",
        )

        combustible_str = cocina_data["abastecimiento_combustible"]
        if combustible_str:
            combustibles_arr = [nombre.strip() for nombre in combustible_str.split(",")]
            combustibles_queryset = TipoCombustible.objects.filter(
                nombre__in=combustibles_arr
            )
            cocina.abastecimiento_combustible.set(combustibles_queryset)

        return cocina

    @staticmethod
    def api_create_espacio(espacio_data):
        cocina_data = espacio_data["cocina"]
        prestacion_data = espacio_data["prestacion"]

        cocina_instance = RelevamientoService.api_create_cocina(cocina_data)

        prestacion_instance = RelevamientoService.api_create_espacio_prestacion(
            prestacion_data
        )

        return Espacio.objects.create(
            tipo_espacio_fisico=TipoEspacio.objects.get(
                nombre__iexact=espacio_data["tipo_espacio_fisico"]
            ),
            espacio_fisico_otro=espacio_data["espacio_fisico_otro"],
            cocina=cocina_instance,
            prestacion=prestacion_instance,
        )

    @staticmethod
    def api_create_colaboradores(colaboradores_data):
        return Colaboradores.objects.create(
            cantidad_colaboradores=CantidadColaboradores.objects.get(
                nombre__iexact=colaboradores_data["cantidad_colaboradores"]
            ),
            colaboradores_capacitados_alimentos=colaboradores_data[
                "cantidad_colaboradores"
            ]
            == "Y",
            colaboradores_recibieron_capacitacion_alimentos=colaboradores_data[
                "cantidad_colaboradores"
            ]
            == "Y",
            colaboradores_capacitados_salud_seguridad=colaboradores_data[
                "cantidad_colaboradores"
            ]
            == "Y",
            colaboradores_recibieron_capacitacion_emergencias=colaboradores_data[
                "cantidad_colaboradores"
            ]
            == "Y",
            colaboradores_recibieron_capacitacion_violencia=colaboradores_data[
                "cantidad_colaboradores"
            ]
            == "Y",
        )

    @staticmethod
    def api_create_recursos(recursos_data):
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

        return FuenteRecursos.objects.create(
            recibe_donaciones_particulares=recursos_data[
                "recibe_donaciones_particulares"
            ]
            == "Y",
            frecuencia_donaciones_particulares=get_frecuencia_recepcion(
                "frecuencia_donaciones_particulares"
            ),
            recursos_donaciones_particulares=get_recursos(
                "recursos_donaciones_particulares"
            ),
            recibe_estado_nacional=recursos_data["recibe_donaciones_particulares"]
            == "Y",
            frecuencia_estado_nacional=get_frecuencia_recepcion(
                "frecuencia_estado_nacional"
            ),
            recursos_estado_nacional=get_recursos("recursos_estado_nacional"),
            recibe_estado_provincial=recursos_data["recibe_donaciones_particulares"]
            == "Y",
            frecuencia_estado_provincial=get_frecuencia_recepcion(
                "frecuencia_estado_provincial"
            ),
            recursos_estado_provincial=get_recursos("recursos_estado_provincial"),
            recibe_estado_municipal=recursos_data["recibe_donaciones_particulares"]
            == "Y",
            frecuencia_estado_municipal=get_frecuencia_recepcion(
                "frecuencia_estado_municipal"
            ),
            recursos_estado_municipal=get_recursos("recursos_estado_municipal"),
            recibe_otros=recursos_data["recibe_donaciones_particulares"] == "Y",
            frecuencia_otros=get_frecuencia_recepcion("frecuencia_otros"),
            recursos_otros=get_recursos("recursos_otros"),
        )

    @staticmethod
    def api_create_compras(compras_data):
        return FuenteCompras.objects.create(
            almacen_cercano=compras_data["almacen_cercano"] == "Y",
            verduleria=compras_data["verduleria"] == "Y",
            granja=compras_data["granja"] == "Y",
            carniceria=compras_data["carniceria"] == "Y",
            pescaderia=compras_data["pescaderia"] == "Y",
            supermercado=compras_data["supermercado"] == "Y",
            mercado_central=compras_data["mercado_central"] == "Y",
            ferias_comunales=compras_data["ferias_comunales"] == "Y",
            mayoristas=compras_data["mayoristas"] == "Y",
            otro=compras_data["otro"] == "Y",
        )

    @staticmethod
    def api_create_prestacion(prestacion_data):
        def convert_to_int(value):
            return int(value) if value != "" else None

        return Prestacion.objects.create(
            lunes_desayuno_actual=convert_to_int(
                prestacion_data["lunes_desayuno_actual"]
            ),
            lunes_desayuno_espera=convert_to_int(
                prestacion_data["lunes_desayuno_espera"]
            ),
            lunes_almuerzo_actual=convert_to_int(
                prestacion_data["lunes_almuerzo_actual"]
            ),
            lunes_almuerzo_espera=convert_to_int(
                prestacion_data["lunes_almuerzo_espera"]
            ),
            lunes_merienda_actual=convert_to_int(
                prestacion_data["lunes_merienda_actual"]
            ),
            lunes_merienda_espera=convert_to_int(
                prestacion_data["lunes_merienda_espera"]
            ),
            lunes_cena_actual=convert_to_int(prestacion_data["lunes_cena_actual"]),
            lunes_cena_espera=convert_to_int(prestacion_data["lunes_cena_espera"]),
            martes_desayuno_actual=convert_to_int(
                prestacion_data["martes_desayuno_actual"]
            ),
            martes_desayuno_espera=convert_to_int(
                prestacion_data["martes_desayuno_espera"]
            ),
            martes_almuerzo_actual=convert_to_int(
                prestacion_data["martes_almuerzo_actual"]
            ),
            martes_almuerzo_espera=convert_to_int(
                prestacion_data["martes_almuerzo_espera"]
            ),
            martes_merienda_actual=convert_to_int(
                prestacion_data["martes_merienda_actual"]
            ),
            martes_merienda_espera=convert_to_int(
                prestacion_data["martes_merienda_espera"]
            ),
            martes_cena_actual=convert_to_int(prestacion_data["martes_cena_actual"]),
            martes_cena_espera=convert_to_int(prestacion_data["martes_cena_espera"]),
            miercoles_desayuno_actual=convert_to_int(
                prestacion_data["miercoles_desayuno_actual"]
            ),
            miercoles_desayuno_espera=convert_to_int(
                prestacion_data["miercoles_desayuno_espera"]
            ),
            miercoles_almuerzo_actual=convert_to_int(
                prestacion_data["miercoles_almuerzo_actual"]
            ),
            miercoles_almuerzo_espera=convert_to_int(
                prestacion_data["miercoles_almuerzo_espera"]
            ),
            miercoles_merienda_actual=convert_to_int(
                prestacion_data["miercoles_merienda_actual"]
            ),
            miercoles_merienda_espera=convert_to_int(
                prestacion_data["miercoles_merienda_espera"]
            ),
            miercoles_cena_actual=convert_to_int(
                prestacion_data["miercoles_cena_actual"]
            ),
            miercoles_cena_espera=convert_to_int(
                prestacion_data["miercoles_cena_espera"]
            ),
            jueves_desayuno_actual=convert_to_int(
                prestacion_data["jueves_desayuno_actual"]
            ),
            jueves_desayuno_espera=convert_to_int(
                prestacion_data["jueves_desayuno_espera"]
            ),
            jueves_almuerzo_actual=convert_to_int(
                prestacion_data["jueves_almuerzo_actual"]
            ),
            jueves_almuerzo_espera=convert_to_int(
                prestacion_data["jueves_almuerzo_espera"]
            ),
            jueves_merienda_actual=convert_to_int(
                prestacion_data["jueves_merienda_actual"]
            ),
            jueves_merienda_espera=convert_to_int(
                prestacion_data["jueves_merienda_espera"]
            ),
            jueves_cena_actual=convert_to_int(prestacion_data["jueves_cena_actual"]),
            jueves_cena_espera=convert_to_int(prestacion_data["jueves_cena_espera"]),
            viernes_desayuno_actual=convert_to_int(
                prestacion_data["viernes_desayuno_actual"]
            ),
            viernes_desayuno_espera=convert_to_int(
                prestacion_data["viernes_desayuno_espera"]
            ),
            viernes_almuerzo_actual=convert_to_int(
                prestacion_data["viernes_almuerzo_actual"]
            ),
            viernes_almuerzo_espera=convert_to_int(
                prestacion_data["viernes_almuerzo_espera"]
            ),
            viernes_merienda_actual=convert_to_int(
                prestacion_data["viernes_merienda_actual"]
            ),
            viernes_merienda_espera=convert_to_int(
                prestacion_data["viernes_merienda_espera"]
            ),
            viernes_cena_actual=convert_to_int(prestacion_data["viernes_cena_actual"]),
            viernes_cena_espera=convert_to_int(prestacion_data["viernes_cena_espera"]),
            sabado_desayuno_actual=convert_to_int(
                prestacion_data["sabado_desayuno_actual"]
            ),
            sabado_desayuno_espera=convert_to_int(
                prestacion_data["sabado_desayuno_espera"]
            ),
            sabado_almuerzo_actual=convert_to_int(
                prestacion_data["sabado_almuerzo_actual"]
            ),
            sabado_almuerzo_espera=convert_to_int(
                prestacion_data["sabado_almuerzo_espera"]
            ),
            sabado_merienda_actual=convert_to_int(
                prestacion_data["sabado_merienda_actual"]
            ),
            sabado_merienda_espera=convert_to_int(
                prestacion_data["sabado_merienda_espera"]
            ),
            sabado_cena_actual=convert_to_int(prestacion_data["sabado_cena_actual"]),
            sabado_cena_espera=convert_to_int(prestacion_data["sabado_cena_espera"]),
            domingo_desayuno_actual=convert_to_int(
                prestacion_data["domingo_desayuno_actual"]
            ),
            domingo_desayuno_espera=convert_to_int(
                prestacion_data["domingo_desayuno_espera"]
            ),
            domingo_almuerzo_actual=convert_to_int(
                prestacion_data["domingo_almuerzo_actual"]
            ),
            domingo_almuerzo_espera=convert_to_int(
                prestacion_data["domingo_almuerzo_espera"]
            ),
            domingo_merienda_actual=convert_to_int(
                prestacion_data["domingo_merienda_actual"]
            ),
            domingo_merienda_espera=convert_to_int(
                prestacion_data["domingo_merienda_espera"]
            ),
            domingo_cena_actual=convert_to_int(prestacion_data["domingo_cena_actual"]),
            domingo_cena_espera=convert_to_int(prestacion_data["domingo_cena_espera"]),
        )
