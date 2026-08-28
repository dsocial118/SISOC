"""Adaptador temporal del catálogo territorial compartido del monolito."""

from core.models import Municipio, Provincia


class CatalogoTerritorialMonolito:
    """Implementa el puerto territorial mientras las FKs legacy siguen vigentes."""

    def obtener_provincia(self, source_id: int | None):
        return Provincia.objects.filter(pk=source_id).first()

    def obtener_municipio(self, source_id: int | None):
        return Municipio.objects.filter(pk=source_id).first()

    def provincias_disponibles(self, alcance: dict[int, set[int] | None] | None):
        queryset = Provincia.objects.all().order_by("nombre")
        if alcance is not None:
            queryset = queryset.filter(pk__in=alcance)
        return queryset

    def municipios_disponibles(
        self,
        provincia,
        alcance: dict[int, set[int] | None] | None,
    ):
        queryset = Municipio.objects.filter(provincia=provincia).order_by("nombre")
        if alcance is None:
            return queryset
        if provincia.pk not in alcance:
            return queryset.none()
        if alcance[provincia.pk] is not None:
            return queryset.filter(pk__in=alcance[provincia.pk])
        return queryset

    def municipios_vacios(self):
        return Municipio.objects.none()


def get_catalogo_territorial() -> CatalogoTerritorialMonolito:
    return CatalogoTerritorialMonolito()
