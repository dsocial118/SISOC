import pytest

from dispositivos.forms import DispositivoForm
from core.models import Municipio, Provincia


@pytest.mark.django_db
def test_form_requiere_texto_otro_tipo_dispositivo():
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)

    form = DispositivoForm(
        data={
            "nombre_institucion": "Hogar Test",
            "tipo_gestion": "estatal",
            "cuit_institucion": "20123456789",
            "provincia": provincia.id,
            "municipio": municipio.id,
            "domicilio_institucion": "Calle 1 123",
            "telefono_contacto": "2211234567",
            "correo_electronico": "test@example.com",
            "responsable_nombre_completo": "Juan Perez",
            "responsable_dni": "12345678",
            "tipo_dispositivo": "otro",
            "modalidad_funcionamiento": "permanente",
            "capacidad_total_plazas": "16_30",
            "dias_atencion": ["lunes"],
            "horarios_funcionamiento": ["manana"],
        }
    )

    assert not form.is_valid()
    assert "tipo_dispositivo_otro" in form.errors


@pytest.mark.django_db
def test_form_configura_municipios_por_provincia_instancia():
    provincia = Provincia.objects.create(nombre="Mendoza")
    municipio = Municipio.objects.create(nombre="Capital", provincia=provincia)

    form = DispositivoForm(initial={"provincia": provincia.id})
    form.fields["municipio"].queryset = Municipio.objects.filter(provincia=provincia)

    assert municipio in form.fields["municipio"].queryset
