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
            categoria=clasificacionFinal,
            puntuacionTotal=calculoPuntuacion,
            comedor=relevamiento.comedor
        )
        return None
    
    @staticmethod
    def get_clasificacion(puntacionTotal):
        califiacion = CategoriaComedor.objects.filter(
            puntuacionMin__lte=puntacionTotal,
            puntuacionMax__gte=puntacionTotal
        ).first()
        return califiacion if califiacion else None
    
    @staticmethod
    def get_puntuacion_total(relevamiento: Relevamiento):
        puntuacion = 0
        relevamiento_respuestas = []

        if relevamiento.espacio.tipo_espacio_fisico.nombre == 'Espacio alquilado':
            puntuacion += 3
        elif relevamiento.espacio.tipo_espacio_fisico.nombre == 'Espacio Prestado':
            puntuacion += 2
        elif relevamiento.espacio.tipo_espacio_fisico.nombre == 'Comunitario compartido':
            puntuacion += 2
        elif relevamiento.espacio.tipo_espacio_fisico.nombre == 'Casa de familia':
            puntuacion += 3
        elif relevamiento.espacio.espacio_fisico_otro is not "":
            puntuacion += 3
        else:
            puntuacion += 0

        
        if relevamiento.espacio.cocina.espacio_elaboracion_alimentos is False:
            puntuacion += 3
        else:
            puntuacion += 0

        if relevamiento.espacio.cocina.almacenamiento_alimentos_secos is False:
            puntuacion += 2
        else:
            puntuacion += 0

        if relevamiento.espacio.cocina.heladera is False:
            puntuacion += 3
        else:
            puntuacion += 0
        
        if relevamiento.espacio.cocina.recipiente_residuos_organicos is False:
            puntuacion += 1
        else:
            puntuacion += 0
        
        if relevamiento.espacio.cocina.recipiente_residuos_reciclables is False:
            puntuacion += 1
        else:
            puntuacion += 0
        
        if relevamiento.espacio.cocina.abastecimiento_combustible.filter(nombre='Leña').exists():
            puntuacion += 3
        elif relevamiento.espacio.cocina.abastecimiento_combustible.filter(nombre='Otro').exists():
            puntuacion += 2
        elif relevamiento.espacio.cocina.abastecimiento_combustible.filter(nombre='Gas envasado').exists():
            puntuacion += 1
        else:
            puntuacion += 0

        if relevamiento.espacio.cocina.abastecimiento_agua.nombre == 'Pozo':
            puntuacion += 2
        elif relevamiento.espacio.cocina.abastecimiento_agua_otro != "":
            puntuacion += 3
        else:
            puntuacion += 0
        
        if relevamiento.espacio.cocina.instalacion_electrica is False:
            puntuacion += 3
        else:
            puntuacion += 0
        
        if relevamiento.espacio.prestacion.espacio_equipado is False:
            puntuacion += 2
        else:  
            puntuacion += 0
        
        if relevamiento.espacio.prestacion.tiene_ventilacion is False:
            puntuacion += 3
        else:
            puntuacion += 0
        
        if relevamiento.espacio.prestacion.tiene_salida_emergencia is False:
            puntuacion += 2
        else:
            puntuacion += 0
        
        if relevamiento.espacio.prestacion.salida_emergencia_senializada is False:
            puntuacion += 1
        else:
            puntuacion += 0
        
        if relevamiento.espacio.prestacion.tiene_equipacion_incendio is False:
            puntuacion += 3
        else:
            puntuacion += 0

        if relevamiento.espacio.prestacion.tiene_botiquin is False:
            puntuacion += 3
        else:
            puntuacion += 0
        
        if relevamiento.espacio.prestacion.tiene_buena_iluminacion is False:
            puntuacion += 2
        else:
            puntuacion += 0
        
        if relevamiento.espacio.prestacion.tiene_sanitarios is False:
            puntuacion += 3
        else:
            puntuacion += 0
        
        if relevamiento.espacio.prestacion.desague_hinodoro.nombre == 'Pozo ciego':
            puntuacion += 2
        elif relevamiento.espacio.prestacion.desague_hinodoro.nombre == 'Letrina':
            puntuacion += 3
        else:
            puntuacion += 0

        if relevamiento.anexo.tecnologia == "Computadora":
            puntuacion += 2
        elif relevamiento.anexo.tecnologia == "Celular":
            puntuacion += 2
        elif relevamiento.anexo.tecnologia == "Ninguno":
            puntuacion += 3
        else:
            puntuacion += 0

        if relevamiento.anexo.servicio_internet is False:
            puntuacion += 1
        else:
            puntuacion += 0
        
        if relevamiento.anexo.acceso_comedor == "Calle de tierra":
            puntuacion += 3
        elif relevamiento.anexo.acceso_comedor == "Calle con mejorado":
            puntuacion += 2
        else:
            puntuacion += 0
        
        if relevamiento.anexo.zona_inundable is False:
            puntuacion += 3
        else:
            puntuacion += 0

        relevamiento_respuestas.append(relevamiento.espacio.tipo_espacio_fisico.nombre)
        relevamiento_respuestas.append(relevamiento.espacio.cocina.almacenamiento_alimentos_secos)
        relevamiento_respuestas.append(relevamiento.espacio.cocina.heladera)
        relevamiento_respuestas.append(relevamiento.espacio.cocina.recipiente_residuos_organicos)
        relevamiento_respuestas.append(relevamiento.espacio.cocina.recipiente_residuos_reciclables)

        relevamiento_respuestas.append(relevamiento.espacio.cocina.abastecimiento_combustible)

        relevamiento_respuestas.append(relevamiento.espacio.cocina.abastecimiento_agua.nombre)
        relevamiento_respuestas.append(relevamiento.espacio.cocina.abastecimiento_agua_otro)
        relevamiento_respuestas.append(relevamiento.espacio.cocina.instalacion_electrica)
        relevamiento_respuestas.append(relevamiento.espacio.prestacion.espacio_equipado)
        relevamiento_respuestas.append(relevamiento.espacio.prestacion.tiene_ventilacion)
        relevamiento_respuestas.append(relevamiento.espacio.prestacion.tiene_salida_emergencia)
        relevamiento_respuestas.append(relevamiento.espacio.prestacion.salida_emergencia_senializada)
        relevamiento_respuestas.append(relevamiento.espacio.prestacion.tiene_equipacion_incendio)
        relevamiento_respuestas.append(relevamiento.espacio.prestacion.tiene_botiquin)
        relevamiento_respuestas.append(relevamiento.espacio.prestacion.tiene_buena_iluminacion)
        relevamiento_respuestas.append(relevamiento.espacio.prestacion.tiene_sanitarios)
        relevamiento_respuestas.append(relevamiento.espacio.prestacion.desague_hinodoro.nombre)
        relevamiento_respuestas.append(relevamiento.anexo.tecnologia)
        relevamiento_respuestas.append(relevamiento.anexo.servicio_internet)
        relevamiento_respuestas.append(relevamiento.anexo.acceso_comedor)
        relevamiento_respuestas.append(relevamiento.anexo.zona_inundable)

        print(relevamiento_respuestas)
        return puntuacion