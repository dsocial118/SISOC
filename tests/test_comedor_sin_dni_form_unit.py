from comedores.forms.comedor_form import CiudadanoSinDniFormParaNomina


def test_ciudadano_sin_dni_para_nomina_exige_motivo():
    form = CiudadanoSinDniFormParaNomina(
        data={
            "apellido": "Pérez",
            "nombre": "Ana",
            "fecha_nacimiento": "1990-01-01",
            "motivo_sin_dni": "",
        }
    )

    assert not form.is_valid()
    assert "motivo_sin_dni" in form.errors
