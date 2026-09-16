from django.db.models import Q


CABA_JURISDICCIONES = (
    "Ciudad Autónoma de Buenos Aires",
    "Ciudad de Buenos Aires",
)


def filtrar_sedes_por_provincia(queryset, provincia):
    """Filtra por jurisdicción exacta, aceptando ambos nombres de CABA."""
    nombres = (provincia.nombre,)
    if provincia.nombre.casefold() in {
        nombre.casefold() for nombre in CABA_JURISDICCIONES
    }:
        nombres = CABA_JURISDICCIONES
    filtro = Q(jurisdiccion__iexact=nombres[0])
    for nombre in nombres[1:]:
        filtro |= Q(jurisdiccion__iexact=nombre)
    return queryset.filter(filtro)
