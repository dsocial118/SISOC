from datetime import date, timedelta

from django.core.cache import cache
from django.db import connection
from django.db.models import Count, Q

from configuraciones.models import Alertas
from legajos.models import EstadoDerivacion, LegajoAlertas, Legajos, LegajosDerivaciones

# FIXME: Este modulo puede ser optimizado mas aun


def table_exists(table_name):
    with connection.cursor() as cursor:
        cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
        return cursor.fetchone() is not None


today = date.today()
fecha_hace_18_anios = today - timedelta(days=18 * 365)
fecha_hace_40_dias = today - timedelta(days=40)


def obtener_legajos_total():
    legajos_total = cache.get("legajos_total")
    if legajos_total is None:
        legajos_total = (
            Legajos.objects.select_related("dimensioneconomia")
            .prefetch_related("m2m_alertas")
            .values("estado", "fecha_nacimiento", "dimensioneconomia__m2m_planes")
        )
        cache.set(
            "legajos_total", legajos_total, 60 * 15
        )  # Almacenar en caché por 15 minutos
    return legajos_total


def obtener_alarmas_activas():
    alarmas_activas = cache.get("alarmas_activas")
    if alarmas_activas is None:
        alarmas_activas = list(
            Alertas.objects.filter(gravedad="Critica").values_list("id")
        )
        cache.set(
            "alarmas_activas", alarmas_activas, 60 * 15
        )  # Almacenar en caché por 15 minutos
    return alarmas_activas


def obtener_legajos_counts():
    legajos_counts = cache.get("legajos_counts")
    if legajos_counts is None:
        alarmas_activas = obtener_alarmas_activas()
        legajos_counts = (
            Legajos.objects.select_related("dimensioneconomia")
            .prefetch_related("m2m_alertas")
            .aggregate(
                total_legajos=Count("id"),
                legajos_activos=Count("id", filter=Q(estado=True)),
                legajos_mayores_de_edad=Count(
                    "id", filter=Q(fecha_nacimiento__gte=fecha_hace_18_anios)
                ),
                total_40_dias=Count("id", distinct=True),
                con_alertas_activas=Count(
                    "id", filter=Q(m2m_alertas__in=alarmas_activas), distinct=True
                ),
                sin_aceptadas=Count(
                    "id",
                    filter=~Q(
                        legajosderivaciones__estado=EstadoDerivacion.objects.filter(
                            estado="Aceptada"
                        ).first()
                    ),
                    distinct=True,
                ),
                adolescente_riesgo=Count(
                    "id", filter=Q(m2m_alertas__in=alarmas_activas), distinct=True
                ),
                adolescente_sin_derivacion_aceptada=Count(
                    "id",
                    filter=~Q(
                        legajosderivaciones__estado=EstadoDerivacion.objects.filter(
                            estado="Aceptada"
                        ).first()
                    ),
                    distinct=True,
                ),
            )
        )
        cache.set(
            "legajos_counts", legajos_counts, 60 * 15
        )  # Almacenar en caché por 15 minutos
    return legajos_counts


def obtener_alertas_embarazo_ids():
    alertas_embarazo_ids = cache.get("alertas_embarazo_ids")
    if alertas_embarazo_ids is None:
        alertas_embarazo_ids = list(
            Alertas.objects.filter(
                fk_categoria__nombre__istartswith="embarazo"
            ).values_list("id", flat=True)
        )
        cache.set(
            "alertas_embarazo_ids", alertas_embarazo_ids, 60 * 15
        )  # Almacenar en caché por 15 minutos
    return alertas_embarazo_ids


def obtener_legajos_con_alerta_embarazo():
    legajos_con_alerta_embarazo = cache.get("legajos_con_alerta_embarazo")
    if legajos_con_alerta_embarazo is None:
        alertas_embarazo_ids = obtener_alertas_embarazo_ids()
        legajos_total = obtener_legajos_total()
        legajos_con_alerta_embarazo = legajos_total.filter(
            m2m_alertas__id__in=alertas_embarazo_ids
        )
        cache.set(
            "legajos_con_alerta_embarazo", legajos_con_alerta_embarazo, 60 * 15
        )  # Almacenar en caché por 15 minutos
    return legajos_con_alerta_embarazo


def contar_legajos():
    legajos_counts = obtener_legajos_counts()
    cantidad_total_legajos = legajos_counts["total_legajos"]
    cantidad_legajos_activos = legajos_counts["legajos_activos"]
    return cantidad_total_legajos, cantidad_legajos_activos


def contar_legajos_entre_0_y_18_anios():
    legajos_counts = obtener_legajos_counts()
    return legajos_counts["legajos_mayores_de_edad"]


def contar_adolescente_riesgo():
    legajos_counts = obtener_legajos_counts()
    return legajos_counts["adolescente_riesgo"]


def contar_adolescente_sin_derivacion_aceptada():
    legajos_counts = obtener_legajos_counts()
    return legajos_counts["adolescente_sin_derivacion_aceptada"]


def contar_legajos_entre_0_y_40_dias():
    legajos_counts = obtener_legajos_counts()
    return legajos_counts["total_40_dias"]


def contar_bb_riesgo():
    legajos_counts = obtener_legajos_counts()
    return legajos_counts["con_alertas_activas"]


def contar_bb_sin_derivacion_aceptada():
    legajos_counts = obtener_legajos_counts()
    return legajos_counts["sin_aceptadas"]


def contar_legajos_con_alarmas_activas():
    return (
        LegajoAlertas.objects.filter(fk_alerta__gravedad="Critica")
        .values_list("fk_legajo_id", flat=True)
        .distinct()
        .count()
    )


def contar_legajos_con_planes_sociales():
    legajos_total = obtener_legajos_total()
    return (
        legajos_total.filter(dimensioneconomia__m2m_planes__isnull=False)
        .distinct()
        .count()
    )


def calcular_porcentaje_respecto_a_poblacion(cantidad_legajos):
    poblacion_san_miguel = 327000  # FIXME: Cual es la poblacion que hay que poner????
    if poblacion_san_miguel > 0:
        return (cantidad_legajos / poblacion_san_miguel) * 100
    else:
        return 0  # Evita la división por cero si no hay población registrada


def deriv_pendientes():
    return (
        LegajosDerivaciones.objects.filter(
            estado=EstadoDerivacion.objects.filter(estado="Pendiente").first()
        )
        .distinct()
        .count()
    )


def contar_legajos_embarazados():
    legajos_con_alerta_embarazo = obtener_legajos_con_alerta_embarazo()
    return legajos_con_alerta_embarazo.count()


def contar_embarazos_sin_derivacion_aceptada():
    legajos_con_alerta_embarazo = obtener_legajos_con_alerta_embarazo()
    return legajos_con_alerta_embarazo.exclude(
        legajosderivaciones__estado=EstadoDerivacion.objects.filter(
            estado="Aceptada"
        ).first()
    ).count()


def contar_embarazos_en_riesgo():
    legajos_con_alerta_embarazo = obtener_legajos_con_alerta_embarazo()
    alarmas_activas = obtener_alarmas_activas()
    return (
        legajos_con_alerta_embarazo.filter(m2m_alertas__in=alarmas_activas)
        .distinct()
        .count()
    )
