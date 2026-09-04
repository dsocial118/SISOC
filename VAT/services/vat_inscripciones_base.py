"""Queryset base compartido para vistas que recorren Inscripcion de VAT.

Inscripcion tiene dos rutas de vinculación con el centro/curso: `comision_curso`
(ComisionCurso -> Curso -> Centro) y `comision` (Comision -> OfertaInstitucional
-> Centro). Toda vista que necesite recorrer inscripciones respetando el alcance
del usuario debe resolver ambas rutas con Coalesce, no solo una, para no perder
registros. Esta función es la única fuente de esa resolución: reportes y el
buscador por ciudadano la comparten para evitar que diverjan.
"""

from __future__ import annotations

from django.db.models import F, Q, Value
from django.db.models.functions import Coalesce

from VAT.models import Centro, Inscripcion
from VAT.services.access_scope import filter_centros_queryset_for_user


def base_inscripciones_queryset_for_user(user):
    centros_ids = filter_centros_queryset_for_user(Centro.objects.all(), user).values(
        "id"
    )
    return (
        Inscripcion.objects.select_related(
            "comision",
            "comision__oferta",
            "comision__oferta__centro",
            "comision__oferta__centro__provincia",
            "comision__oferta__centro__municipio",
            "comision__oferta__programa",
            "comision__oferta__plan_curricular",
            "comision__oferta__plan_curricular__modalidad_cursada",
            "comision_curso",
            "comision_curso__curso",
            "comision_curso__curso__centro",
            "comision_curso__curso__centro__provincia",
            "comision_curso__curso__centro__municipio",
            "comision_curso__curso__modalidad",
            "comision_curso__curso__plan_estudio",
        )
        .filter(
            Q(comision_curso__curso__centro_id__in=centros_ids)
            | Q(comision__oferta__centro_id__in=centros_ids)
        )
        .annotate(
            centro_id_ref=Coalesce(
                F("comision_curso__curso__centro_id"),
                F("comision__oferta__centro_id"),
            ),
            centro_nombre_ref=Coalesce(
                F("comision_curso__curso__centro__nombre"),
                F("comision__oferta__centro__nombre"),
                Value("Sin centro"),
            ),
            provincia_id_ref=Coalesce(
                F("comision_curso__curso__centro__provincia_id"),
                F("comision__oferta__centro__provincia_id"),
            ),
            provincia_nombre_ref=Coalesce(
                F("comision_curso__curso__centro__provincia__nombre"),
                F("comision__oferta__centro__provincia__nombre"),
                Value("Sin provincia"),
            ),
            municipio_id_ref=Coalesce(
                F("comision_curso__curso__centro__municipio_id"),
                F("comision__oferta__centro__municipio_id"),
            ),
            municipio_nombre_ref=Coalesce(
                F("comision_curso__curso__centro__municipio__nombre"),
                F("comision__oferta__centro__municipio__nombre"),
                Value("Sin municipio"),
            ),
            unidad_formativa_id=Coalesce(
                F("comision_curso__curso_id"),
                F("comision__oferta_id"),
            ),
            unidad_formativa_nombre=Coalesce(
                F("comision_curso__curso__nombre"),
                F("comision__oferta__nombre_local"),
                F("comision__oferta__plan_curricular__nombre"),
                Value("Sin curso/oferta"),
            ),
            comision_id_ref=Coalesce(F("comision_curso_id"), F("comision_id")),
            comision_codigo_ref=Coalesce(
                F("comision_curso__codigo_comision"),
                F("comision__codigo_comision"),
                Value("Sin comisión"),
            ),
            programa_id_ref=Coalesce(
                Value(None),
                F("comision__oferta__programa_id"),
            ),
            programa_nombre_ref=Coalesce(
                F("comision__oferta__programa__nombre"),
                Value("Sin programa"),
            ),
            titulo_id_ref=Coalesce(
                F("comision_curso__curso__plan_estudio__titulos__id"),
                F("comision__oferta__plan_curricular__titulos__id"),
            ),
            titulo_nombre_ref=Coalesce(
                F("comision_curso__curso__plan_estudio__titulos__nombre"),
                F("comision__oferta__plan_curricular__titulos__nombre"),
                Value("Sin título"),
            ),
            modalidad_id_ref=Coalesce(
                F("comision_curso__curso__modalidad_id"),
                F("comision__oferta__plan_curricular__modalidad_cursada_id"),
            ),
            modalidad_nombre_ref=Coalesce(
                F("comision_curso__curso__modalidad__nombre"),
                F("comision__oferta__plan_curricular__modalidad_cursada__nombre"),
                Value("Sin modalidad"),
            ),
            usa_voucher_ref=Coalesce(
                F("comision_curso__curso__usa_voucher"),
                F("comision__oferta__usa_voucher"),
            ),
            estado_curso_ref=F("comision_curso__curso__estado"),
            estado_comision_ref=Coalesce(
                F("comision_curso__estado"),
                F("comision__estado"),
            ),
        )
    )
