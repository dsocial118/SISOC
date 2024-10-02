from django.utils import timezone

from comedores.models import Relevamiento
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
                "comedor__municipio__nombre_region",
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
                "espacio__cocina__recipiente_otros_residuos",
                "espacio__cocina__abastecimiento_agua__nombre",
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
                "espacio__prestacion__tiene_buzon_quejas",
                "espacio__prestacion__tiene_gestion_quejas",
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
