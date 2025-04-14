from comedores.models.relevamiento import (
    Relevamiento,
    ClasificacionComedor,
    CategoriaComedor,
)
from django.db.models import Case, When, IntegerField


class ClasificacionComedorService:
    @staticmethod
    def create_clasificacion_relevamiento(relevamiento: Relevamiento):
        calculo_puntuacion = ClasificacionComedorService.get_puntuacion_total(
            relevamiento
        )
        clasificacion_final = ClasificacionComedorService.get_clasificacion(
            calculo_puntuacion
        )
        clasificacion = ClasificacionComedor.objects.create(
            relevamiento=relevamiento,
            categoria=clasificacion_final,
            puntuacion_total=calculo_puntuacion,
            comedor=relevamiento.comedor,
        )

        return clasificacion

    @staticmethod
    def get_clasificacion(puntacion_total):
        califiacion = CategoriaComedor.objects.filter(
            puntuacion_min__lte=puntacion_total, puntuacion_max__gte=puntacion_total
        ).first()
        return califiacion if califiacion else None

    @staticmethod
    def get_puntuacion_total(relevamiento: Relevamiento) -> int:
        puntuacion = 0

        # Puntuación por tipo de espacio físico
        if relevamiento.espacio and relevamiento.espacio.tipo_espacio_fisico:
            tipo_espacio = relevamiento.espacio.tipo_espacio_fisico.nombre
            puntuacion += {
                "Espacio alquilado": 3,
                "Espacio prestado (uso exclusivo)": 2,
                "Espacio comunitario compartido": 2,
                "Casa de familia": 3,
            }.get(tipo_espacio, 0)

            if relevamiento.espacio.espacio_fisico_otro:
                puntuacion += 3

        # Puntuación por cocina
        if relevamiento.espacio and relevamiento.espacio.cocina:
            cocina = relevamiento.espacio.cocina
            puntuacion += sum(
                [
                    3 if not cocina.espacio_elaboracion_alimentos else 0,
                    2 if not cocina.almacenamiento_alimentos_secos else 0,
                    3 if not cocina.heladera else 0,
                    3 if not cocina.freezer else 0,
                    1 if not cocina.recipiente_residuos_organicos else 0,
                    1 if not cocina.recipiente_residuos_reciclables else 0,
                    1 if not cocina.otros_residuos else 0,
                ]
            )

            if cocina.abastecimiento_combustible:
                respuesta = cocina.abastecimiento_combustible.annotate(
                    order=Case(
                        When(nombre="Leña", then=1),
                        When(nombre="Otro", then=2),
                        When(nombre="Gas envasado", then=3),
                        default=4,
                        output_field=IntegerField(),
                    )
                ).order_by("order")

                for item in respuesta:
                    respuesta_str = str(item)  # Convertir cada item a cadena

                    if "Leña" in respuesta_str:
                        puntuacion += 3
                        break

                    if "Otro" in respuesta_str:
                        puntuacion += 2
                        break

                    if "Gas envasado" in respuesta_str:
                        puntuacion += 1
                        break
                    else:
                        puntuacion += 0
                        break

            if cocina.abastecimiento_agua:
                if cocina.abastecimiento_agua.nombre == "Pozo":
                    puntuacion += 2
                elif cocina.abastecimiento_agua_otro:
                    puntuacion += 3

            if not cocina.instalacion_electrica:
                puntuacion += 3

        # Puntuación por prestación
        if relevamiento.espacio and relevamiento.espacio.prestacion:
            prestacion = relevamiento.espacio.prestacion
            puntuacion += sum(
                [
                    2 if not prestacion.espacio_equipado else 0,
                    3 if not prestacion.tiene_ventilacion else 0,
                    2 if not prestacion.tiene_salida_emergencia else 0,
                    1 if not prestacion.salida_emergencia_senializada else 0,
                    3 if not prestacion.tiene_equipacion_incendio else 0,
                    3 if not prestacion.tiene_botiquin else 0,
                    2 if not prestacion.tiene_buena_iluminacion else 0,
                    3 if not prestacion.tiene_sanitarios else 0,
                ]
            )

            if prestacion.desague_hinodoro:
                puntuacion += {"Pozo ciego": 2, "Letrina": 3}.get(
                    prestacion.desague_hinodoro.nombre, 0
                )

        # Puntuación por colaboradores
        if relevamiento.colaboradores:
            colaboradores = relevamiento.colaboradores
            puntuacion += sum(
                [
                    1 if not colaboradores.colaboradores_capacitados_alimentos else 0,
                    (
                        1
                        if not colaboradores.colaboradores_recibieron_capacitacion_alimentos
                        else 0
                    ),
                    (
                        1
                        if not colaboradores.colaboradores_capacitados_salud_seguridad
                        else 0
                    ),
                    (
                        1
                        if not colaboradores.colaboradores_recibieron_capacitacion_emergencias
                        else 0
                    ),
                    (
                        1
                        if not colaboradores.colaboradores_recibieron_capacitacion_violencia
                        else 0
                    ),
                ]
            )

        # Puntuación por anexo
        if relevamiento.anexo:
            anexo = relevamiento.anexo
            if anexo.tecnologia:
                puntuacion += {"Computadora": 2, "Celular": 2, "Ninguno": 3}.get(
                    anexo.tecnologia.nombre, 0
                )

            if anexo.servicio_internet is False:
                puntuacion += 1

            if anexo.acceso_comedor:
                puntuacion += {"Calle de tierra": 3, "Calle con mejorado": 2}.get(
                    anexo.acceso_comedor.nombre, 0
                )

            if anexo.zona_inundable:
                puntuacion += 3

            puntuacion += {"Entre 6 y 10 cuadras": 2, "Más de 10 cuadras": 3}.get(
                anexo.distancia_transporte, 0
            )

        return puntuacion
