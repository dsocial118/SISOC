import pytest

from intervenciones.api import obtener_configuracion_formulario_cdi
from intervenciones.models.intervenciones import SubIntervencion, TipoIntervencion


@pytest.mark.django_db
def test_catalogo_cdi_expone_solo_tipos_permitidos_y_subtipo_seleccionado():
    tipo_cdi = TipoIntervencion.objects.create(nombre="CDI", programa="cdi")
    tipo_comedor = TipoIntervencion.objects.create(
        nombre="Comedor", programa="comedores"
    )
    subtipo = SubIntervencion.objects.create(
        nombre="Seguimiento", tipo_intervencion=tipo_cdi
    )

    configuracion = obtener_configuracion_formulario_cdi(tipo_cdi.pk, subtipo.pk)

    assert tipo_cdi in configuracion.tipos
    assert tipo_comedor not in configuracion.tipos
    assert list(configuracion.subtipos) == [subtipo]
