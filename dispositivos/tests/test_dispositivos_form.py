import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from core.models import Municipio, Provincia
from dispositivos.forms import DispositivoForm
from dispositivos.models import Dispositivo


def _base_data(provincia, municipio, **overrides):
    data = {
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
        "tipo_dispositivo": "refugio",
        "modalidad_funcionamiento": "permanente",
        "capacidad_total_plazas": "16_30",
        "dias_atencion": ["lunes"],
        "horarios_funcionamiento": ["manana"],
    }
    data.update(overrides)
    return data


def _archivo(nombre, contenido=b"contenido", content_type="application/pdf"):
    return SimpleUploadedFile(nombre, contenido, content_type=content_type)


@pytest.mark.django_db
def test_form_requiere_texto_otro_tipo_dispositivo():
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)

    form = DispositivoForm(
        data=_base_data(provincia, municipio, tipo_dispositivo="otro")
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


@pytest.mark.django_db
def test_form_rechaza_documentacion_con_extension_no_permitida():
    provincia = Provincia.objects.create(nombre="Cordoba")
    municipio = Municipio.objects.create(nombre="Cordoba", provincia=provincia)

    form = DispositivoForm(
        data=_base_data(provincia, municipio),
        files={
            "documentacion_dispositivo": _archivo(
                "documentacion.html",
                b"<script>alert('x')</script>",
                content_type="text/html",
            )
        },
    )

    assert not form.is_valid()
    assert "documentacion_dispositivo" in form.errors


@pytest.mark.django_db
def test_form_rechaza_documentacion_con_content_type_no_permitido():
    provincia = Provincia.objects.create(nombre="Santa Fe")
    municipio = Municipio.objects.create(nombre="Rosario", provincia=provincia)

    form = DispositivoForm(
        data=_base_data(provincia, municipio),
        files={
            "documentacion_dispositivo": _archivo(
                "documentacion.pdf",
                b"texto plano",
                content_type="text/plain",
            )
        },
    )

    assert not form.is_valid()
    assert "documentacion_dispositivo" in form.errors


@pytest.mark.django_db
def test_modelo_rechaza_documentacion_demasiado_grande():
    provincia = Provincia.objects.create(nombre="Chaco")
    municipio = Municipio.objects.create(nombre="Resistencia", provincia=provincia)
    data = _base_data(provincia, municipio)
    data["provincia"] = provincia
    data["municipio"] = municipio
    dispositivo = Dispositivo(
        **data,
        documentacion_dispositivo=_archivo(
            "documentacion.pdf",
            b"x" * ((10 * 1024 * 1024) + 1),
            content_type="application/pdf",
        ),
    )

    with pytest.raises(ValidationError):
        dispositivo.full_clean()
