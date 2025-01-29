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
    CategoriaComedor
)


class ClasificacionComedorService:
    @staticmethod
    def create_clasificacion_relevamiento(relevamiento: Relevamiento):
        calculoPuntuacion = ClasificacionComedorService.get_puntuacion_total(relevamiento)
        clasificacionFinal = ClasificacionComedorService.get_clasificacion(calculoPuntuacion)
        ClasificacionComedor.objects.create(
            relevamiento=relevamiento,
            clasificacion=clasificacionFinal,
            puntuacionTotal=calculoPuntuacion,
            comedor=relevamiento.comedor
        )
        return None
    
    @staticmethod
    def get_clasificacion(puntacionTotal):
        califiacion = CategoriaComedor.objects.filter(
            puntuacionMin__lte=puntacionTotal,
            puntuacionMax__gte=puntacionTotal
        )
        return califiacion[0].nombre if califiacion else None
    
    @staticmethod
    def get_puntuacion_total(relevamiento: Relevamiento):
        puntuacion = 0
        relevamiento_respuestas = []
        relevamiento_respuestas.append(relevamiento.espacio.tipo_espacio_fisico)
        relevamiento_respuestas.append(relevamiento.espacio.cocina.espacio_elaboracion_alimentos)
        relevamiento_respuestas.append(relevamiento.espacio.cocina.almacenamiento_alimentos_secos)
        relevamiento_respuestas.append(relevamiento.espacio.cocina.heladera)
        relevamiento_respuestas.append(relevamiento.espacio.cocina.recipiente_residuos_organicos)
        relevamiento_respuestas.append(relevamiento.espacio.cocina.recipiente_residuos_reciclables)
        relevamiento_respuestas.append(relevamiento.espacio.cocina.abastecimiento_combustible)
        relevamiento_respuestas.append(relevamiento.espacio.cocina.abastecimiento_agua)
        relevamiento_respuestas.append(relevamiento.espacio.cocina.abastecimiento_agua_otro)
        relevamiento_respuestas.append(relevamiento.espacio.cocina.instalacion_electrica)
        relevamiento_respuestas.append(relevamiento.prestacion.espacio_equipado)
        relevamiento_respuestas.append(relevamiento.prestacion.tiene_ventilacion)
        relevamiento_respuestas.append(relevamiento.prestacion.tiene_salida_emergencia)
        relevamiento_respuestas.append(relevamiento.prestacion.salida_emergencia_senializada)
        relevamiento_respuestas.append(relevamiento.prestacion.tiene_equipacion_incendio)
        relevamiento_respuestas.append(relevamiento.prestacion.tiene_botiquin)
        relevamiento_respuestas.append(relevamiento.prestacion.tiene_buena_iluminacion)
        relevamiento_respuestas.append(relevamiento.prestacion.tiene_sanitarios)
        relevamiento_respuestas.append(relevamiento.prestacion.desague_hinodoro)
        relevamiento_respuestas.append(relevamiento.anexo.tecnologia)
        relevamiento_respuestas.append(relevamiento.anexo.servicio_internet)
        relevamiento_respuestas.append(relevamiento.anexo.acceso_comedor)
        relevamiento_respuestas.append(relevamiento.anexo.zona_inundable)
        print(relevamiento_respuestas)
        return puntuacion