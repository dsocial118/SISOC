from datetime import date

from ciudadanos.models import Ciudadano


def test_buscar_por_documento_prefijo_corto_no_ejecuta_query(
    db, django_assert_num_queries
):
    with django_assert_num_queries(0):
        resultados = list(Ciudadano.buscar_por_documento("123456"))

    assert resultados == []


def test_buscar_por_documento_prefijo_siete_digitos_devuelve_coincidencias(db):
    ciudadano_a = Ciudadano.objects.create(
        nombre="Ana",
        apellido="Perez",
        fecha_nacimiento=date(1990, 1, 1),
        documento=12345678,
    )
    ciudadano_b = Ciudadano.objects.create(
        nombre="Beto",
        apellido="Lopez",
        fecha_nacimiento=date(1991, 1, 1),
        documento=12345679,
    )
    Ciudadano.objects.create(
        nombre="Caro",
        apellido="Diaz",
        fecha_nacimiento=date(1992, 1, 1),
        documento=99999999,
    )

    resultados = list(Ciudadano.buscar_por_documento("1234567", max_results=10))

    assert [c.pk for c in resultados] == [ciudadano_a.pk, ciudadano_b.pk]
