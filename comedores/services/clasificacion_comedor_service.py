import os
import json
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import models
import requests

from comedores.models.relevamiento import Relevamiento
from comedores.models.comedor import (
    Comedor,
)
from comedores.models.relevamiento import (
    Relevamiento,
    ClasificacionComedor,
    CategoriaComedor,
)


class ClasificacionComedorService:
    @staticmethod
    def create_clasificacion_relevamiento(relevamiento: Relevamiento):
        calculoPuntuacion = ClasificacionComedorService.get_puntuacion_total(
            relevamiento
        )
        clasificacionFinal = ClasificacionComedorService.get_clasificacion(
            calculoPuntuacion
        )
        ClasificacionComedor.objects.create(
            relevamiento=relevamiento,
            categoria=clasificacionFinal,
            puntuacion_total=calculoPuntuacion,
            comedor=relevamiento.comedor,
        )
        return None

    @staticmethod
    def get_clasificacion(puntacionTotal):
        califiacion = CategoriaComedor.objects.filter(
            puntuacion_min__lte=puntacionTotal, puntuacion_max__gte=puntacionTotal
        ).first()
        return califiacion if califiacion else None

    @staticmethod
    def get_puntuacion_total(relevamiento: Relevamiento):
        puntuacion = 0
        if relevamiento.espacio:
            if relevamiento.espacio.tipo_espacio_fisico.nombre == "Espacio alquilado":
                puntuacion += 3
            elif (
                relevamiento.espacio.tipo_espacio_fisico.nombre
                == "Espacio prestado (uso exclusivo)"
            ):
                puntuacion += 2
            elif (
                relevamiento.espacio.tipo_espacio_fisico.nombre
                == "Espacio comunitario compartido"
            ):
                puntuacion += 2
            elif relevamiento.espacio.tipo_espacio_fisico.nombre == "Casa de familia":
                puntuacion += 3
            elif relevamiento.espacio.espacio_fisico_otro != "":
                puntuacion += 3

            if relevamiento.espacio.cocina.espacio_elaboracion_alimentos is False:
                puntuacion += 3

            if relevamiento.espacio.cocina.almacenamiento_alimentos_secos is False:
                puntuacion += 2

            if relevamiento.espacio.cocina.heladera is False:
                puntuacion += 3

            if relevamiento.espacio.cocina.freezer is False:
                puntuacion += 3

            if relevamiento.espacio.cocina.recipiente_residuos_organicos is False:
                puntuacion += 1

            if relevamiento.espacio.cocina.recipiente_residuos_reciclables is False:
                puntuacion += 1

            if relevamiento.espacio.cocina.otros_residuos is False:
                puntuacion += 1

            if (
                relevamiento.espacio.cocina.abastecimiento_combustible.filter(
                    nombre="Gas envasado"
                )
                .order_by("nombre")
                .exists()
            ):
                puntuacion += 1
            elif (
                relevamiento.espacio.cocina.abastecimiento_combustible.filter(
                    nombre="Leña"
                )
                .order_by("nombre")
                .exists()
            ):
                puntuacion += 3
            elif (
                relevamiento.espacio.cocina.abastecimiento_combustible.filter(
                    nombre="Otro"
                )
                .order_by("nombre")
                .exists()
            ):
                puntuacion += 2

            if relevamiento.espacio.cocina.abastecimiento_agua.nombre == "Pozo":
                puntuacion += 2
            elif relevamiento.espacio.cocina.abastecimiento_agua_otro != "":
                puntuacion += 3

            if relevamiento.espacio.cocina.instalacion_electrica is False:
                puntuacion += 3

            if relevamiento.espacio.prestacion.espacio_equipado is False:
                puntuacion += 2

            if relevamiento.espacio.prestacion.tiene_ventilacion is False:
                puntuacion += 3

            if relevamiento.espacio.prestacion.tiene_salida_emergencia is False:
                puntuacion += 2

            if relevamiento.espacio.prestacion.salida_emergencia_senializada is False:
                puntuacion += 1

            if relevamiento.espacio.prestacion.tiene_equipacion_incendio is False:
                puntuacion += 3

            if relevamiento.espacio.prestacion.tiene_botiquin is False:
                puntuacion += 3

            if relevamiento.espacio.prestacion.tiene_buena_iluminacion is False:
                puntuacion += 2

            if relevamiento.espacio.prestacion.tiene_sanitarios is False:
                puntuacion += 3

            if relevamiento.espacio.prestacion.desague_hinodoro.nombre == "Pozo ciego":
                puntuacion += 2
            elif relevamiento.espacio.prestacion.desague_hinodoro.nombre == "Letrina":
                puntuacion += 3

        if relevamiento.colaboradores:
            if relevamiento.colaboradores.colaboradores_capacitados_alimentos is False:
                puntuacion += 1
            if (
                relevamiento.colaboradores.colaboradores_recibieron_capacitacion_alimentos
                is False
            ):
                puntuacion += 1
            if (
                relevamiento.colaboradores.colaboradores_capacitados_salud_seguridad
                is False
            ):
                puntuacion += 1
            if (
                relevamiento.colaboradores.colaboradores_recibieron_capacitacion_emergencias
                is False
            ):
                puntuacion += 1
            if (
                relevamiento.colaboradores.colaboradores_recibieron_capacitacion_violencia
                is False
            ):
                puntuacion += 1

        if relevamiento.anexo:
            if relevamiento.anexo.tecnologia == "Computadora":
                puntuacion += 2
            elif relevamiento.anexo.tecnologia == "Celular":
                puntuacion += 2
            elif relevamiento.anexo.tecnologia == "Ninguno":
                puntuacion += 3

            if relevamiento.anexo.servicio_internet is False:
                puntuacion += 1

            if relevamiento.anexo.acceso_comedor == "Calle de tierra":
                puntuacion += 3
            elif relevamiento.anexo.acceso_comedor == "Calle con mejorado":
                puntuacion += 2

            if relevamiento.anexo.zona_inundable is True:
                puntuacion += 3

            if relevamiento.anexo.distancia_transporte == "Entre 6 y 10 cuadras":
                puntuacion += 2
            elif relevamiento.anexo.distancia_transporte == "Más de 10 cuadras":
                puntuacion += 3

        return puntuacion
