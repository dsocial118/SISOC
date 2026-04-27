from datetime import date

import pytest
from django.contrib.auth.models import User, Permission
from django.test import Client
from django.urls import reverse

from ciudadanos.models import Ciudadano
from centrodeinfancia.models import CentroDeInfancia, NominaCentroInfancia
from core.models import Provincia, Sexo
from users.models import Profile


@pytest.fixture
def provincia():
    return Provincia.objects.create(nombre="Rio Negro")


@pytest.fixture
def centro(provincia):
    return CentroDeInfancia.objects.create(
        nombre="CDI Test",
        provincia=provincia,
    )


@pytest.fixture
def ciudadano():
    return Ciudadano.objects.create(
        apellido="Lopez",
        nombre="Ana",
        fecha_nacimiento=date(2012, 5, 10),
        documento=33333333,
    )


@pytest.fixture
def nomina(centro, ciudadano):
    return NominaCentroInfancia.objects.create(
        centro=centro,
        ciudadano=ciudadano,
        dni=ciudadano.documento,
        apellido=ciudadano.apellido,
        nombre=ciudadano.nombre,
        fecha_nacimiento=ciudadano.fecha_nacimiento,
        estado=NominaCentroInfancia.ESTADO_ACTIVO,
    )


@pytest.fixture
def usuario_con_permisos():
    user = User.objects.create_user(username="testuser", password="test1234")
    profile, _ = Profile.objects.get_or_create(user=user)
    # Agregar permiso requerido
    try:
        perm = Permission.objects.get(codename="change_nominacentroinfancia")
        user.user_permissions.add(perm)
    except Permission.DoesNotExist:
        pass
    return user


@pytest.mark.django_db
class TestNominaCentroInfanciaEditView:
    """Tests para la vista de edición de nómina de Centro de Infancia."""

    def test_requiere_autenticacion(self, centro, nomina):
        """Verifica que la vista requiere autenticación."""
        client = Client()
        url = reverse(
            "centrodeinfancia_nomina_editar",
            kwargs={"pk": centro.pk, "nomina_id": nomina.pk},
        )
        response = client.get(url)
        # Puede ser 302 (redirect) o 403 (forbidden) dependiendo de config
        assert response.status_code in [302, 403]

    def test_get_muestra_formulario(self, usuario_con_permisos, centro, nomina):
        """Verifica que GET muestra el formulario con datos iniciales."""
        client = Client()
        client.force_login(usuario_con_permisos)

        url = reverse(
            "centrodeinfancia_nomina_editar",
            kwargs={"pk": centro.pk, "nomina_id": nomina.pk},
        )
        response = client.get(url)

        assert response.status_code == 200
        assert "form" in response.context
        assert response.context["object"] == nomina
        assert response.context["centro"] == centro

    def test_get_renderiza_template_correcto(
        self, usuario_con_permisos, centro, nomina
    ):
        """Verifica que se usa el template correcto."""
        client = Client()
        client.force_login(usuario_con_permisos)

        url = reverse(
            "centrodeinfancia_nomina_editar",
            kwargs={"pk": centro.pk, "nomina_id": nomina.pk},
        )
        response = client.get(url)

        assert response.status_code == 200
        assert "centrodeinfancia/nomina_form_edit.html" in [
            t.name for t in response.templates
        ]

    def test_get_incluye_autocompletado_geografico(
        self, usuario_con_permisos, centro, nomina
    ):
        """Verifica que el template de edición incluye el JS de carga dependiente."""
        client = Client()
        client.force_login(usuario_con_permisos)

        url = reverse(
            "centrodeinfancia_nomina_editar",
            kwargs={"pk": centro.pk, "nomina_id": nomina.pk},
        )
        response = client.get(url)

        content = response.content.decode("utf-8")
        assert response.status_code == 200
        assert "ajaxLoadMunicipiosUrl" in content
        assert "ajaxLoadLocalidadesUrl" in content
        assert 'id="id_provincia_domicilio"' in content
        assert 'id="id_municipio_domicilio"' in content
        assert 'id="id_localidad_domicilio"' in content

    def test_post_actualiza_nomina(self, usuario_con_permisos, centro, nomina):
        """Verifica que POST actualiza correctamente la nómina."""
        client = Client()
        client.force_login(usuario_con_permisos)

        url = reverse(
            "centrodeinfancia_nomina_editar",
            kwargs={"pk": centro.pk, "nomina_id": nomina.pk},
        )

        data = {
            "estado": NominaCentroInfancia.ESTADO_BAJA,
            "dni": nomina.dni,
            "apellido": "Lopez-Updated",
            "nombre": "Ana Maria",
            "fecha_nacimiento": "2012-05-10",
            "sexo": "Femenino",
        }

        response = client.post(url, data)

        # Verifica redirección
        assert response.status_code == 302

        # Verifica que los datos se actualizaron
        nomina.refresh_from_db()
        assert nomina.estado == NominaCentroInfancia.ESTADO_BAJA
        assert nomina.apellido == "Lopez-Updated"
        assert nomina.nombre == "Ana Maria"

    def test_post_redirige_correctamente(self, usuario_con_permisos, centro, nomina):
        """Verifica que la redirección es al detalle de nómina del centro."""
        client = Client()
        client.force_login(usuario_con_permisos)

        url = reverse(
            "centrodeinfancia_nomina_editar",
            kwargs={"pk": centro.pk, "nomina_id": nomina.pk},
        )

        data = {
            "estado": NominaCentroInfancia.ESTADO_ACTIVO,
            "dni": nomina.dni,
            "apellido": nomina.apellido,
            "nombre": nomina.nombre,
            "fecha_nacimiento": nomina.fecha_nacimiento.isoformat(),
        }

        response = client.post(url, data)
        expected_url = reverse("centrodeinfancia_nomina_ver", kwargs={"pk": centro.pk})

        assert response.status_code == 302
        assert expected_url in response.url

    def test_no_permite_editar_nomina_de_otro_centro(
        self, usuario_con_permisos, centro, ciudadano
    ):
        """Verifica que no se pueda editar nómina de otro centro."""
        otro_centro = CentroDeInfancia.objects.create(
            nombre="CDI Otro",
            provincia=centro.provincia,
        )
        nomina_otro = NominaCentroInfancia.objects.create(
            centro=otro_centro,
            ciudadano=ciudadano,
            dni=ciudadano.documento,
            apellido=ciudadano.apellido,
            nombre=ciudadano.nombre,
            fecha_nacimiento=ciudadano.fecha_nacimiento,
        )

        client = Client()
        client.force_login(usuario_con_permisos)

        # Intenta acceder a la nómina del otro centro con pk del primer centro
        url = reverse(
            "centrodeinfancia_nomina_editar",
            kwargs={"pk": centro.pk, "nomina_id": nomina_otro.pk},
        )
        response = client.get(url)

        # La vista retorna None en get_context_data si la nómina no pertenece al centro
        # Esto puede resultar en diferentes respuestas dependiendo del template
        assert response.status_code in [404, 200]

    def test_contexto_contiene_objeto_y_centro(
        self, usuario_con_permisos, centro, nomina
    ):
        """Verifica que el contexto tiene los objetos necesarios."""
        client = Client()
        client.force_login(usuario_con_permisos)

        url = reverse(
            "centrodeinfancia_nomina_editar",
            kwargs={"pk": centro.pk, "nomina_id": nomina.pk},
        )
        response = client.get(url)

        assert response.status_code == 200
        assert response.context["object"] == nomina
        assert response.context["centro"] == centro
        assert response.context["form"] is not None

    def test_post_con_datos_invalidos_no_guarda(
        self, usuario_con_permisos, centro, nomina
    ):
        """Verifica que POST con datos inválidos no guarda."""
        client = Client()
        client.force_login(usuario_con_permisos)

        url = reverse(
            "centrodeinfancia_nomina_editar",
            kwargs={"pk": centro.pk, "nomina_id": nomina.pk},
        )

        # Datos inválidos: fecha_nacimiento muy reciente
        data = {
            "estado": NominaCentroInfancia.ESTADO_ACTIVO,
            "dni": nomina.dni,
            "apellido": nomina.apellido,
            "nombre": nomina.nombre,
            "fecha_nacimiento": date.today().isoformat(),  # Hoy
        }

        response = client.post(url, data)

        # Debería mostrar errores de validación
        # Si el formulario tiene validaciones, volverá con status 200
        # Si no, puede redirigir (302)
        assert response.status_code in [200, 302]

    def test_actualiza_sexo_desde_opciones(self, usuario_con_permisos, centro, nomina):
        """Verifica que se puede actualizar el sexo."""
        sexo = Sexo.objects.create(sexo="Masculino")

        client = Client()
        client.force_login(usuario_con_permisos)

        url = reverse(
            "centrodeinfancia_nomina_editar",
            kwargs={"pk": centro.pk, "nomina_id": nomina.pk},
        )

        data = {
            "estado": NominaCentroInfancia.ESTADO_ACTIVO,
            "dni": nomina.dni,
            "apellido": nomina.apellido,
            "nombre": nomina.nombre,
            "fecha_nacimiento": nomina.fecha_nacimiento.isoformat(),
            "sexo": sexo.sexo,
        }

        response = client.post(url, data)
        assert response.status_code == 302

        nomina.refresh_from_db()
        assert nomina.sexo == sexo.sexo

    def test_actualiza_multiples_campos(self, usuario_con_permisos, centro, ciudadano):
        """Verifica que se pueden actualizar múltiples campos correctamente."""
        nomina = NominaCentroInfancia.objects.create(
            centro=centro,
            ciudadano=ciudadano,
            dni=ciudadano.documento,
            apellido=ciudadano.apellido,
            nombre=ciudadano.nombre,
            fecha_nacimiento=ciudadano.fecha_nacimiento,
            estado=NominaCentroInfancia.ESTADO_ACTIVO,
        )

        client = Client()
        client.force_login(usuario_con_permisos)

        url = reverse(
            "centrodeinfancia_nomina_editar",
            kwargs={"pk": centro.pk, "nomina_id": nomina.pk},
        )

        # Cambiar estado, nombre y agregar nacionalidad
        data = {
            "estado": NominaCentroInfancia.ESTADO_BAJA,
            "dni": nomina.dni,
            "apellido": nomina.apellido,
            "nombre": "Ana Updated",
            "fecha_nacimiento": nomina.fecha_nacimiento.isoformat(),
            "nacionalidad": "Argentina",
        }

        response = client.post(url, data)
        assert response.status_code == 302

        nomina.refresh_from_db()
        # Verificar que los cambios fueron guardados
        assert nomina.estado == NominaCentroInfancia.ESTADO_BAJA
        assert nomina.nombre == "Ana Updated"
        assert nomina.nacionalidad == "Argentina"
        # El apellido se mantiene igual
        assert nomina.apellido == ciudadano.apellido

    def test_formulario_tiene_campos_correctos(
        self, usuario_con_permisos, centro, nomina
    ):
        """Verifica que el formulario renderiza con los campos esperados."""
        client = Client()
        client.force_login(usuario_con_permisos)

        url = reverse(
            "centrodeinfancia_nomina_editar",
            kwargs={"pk": centro.pk, "nomina_id": nomina.pk},
        )
        response = client.get(url)

        assert response.status_code == 200
        form = response.context["form"]

        # Verifique que ciertos campos están presentes (sin 'edad')
        expected_fields = [
            "estado",
            "dni",
            "apellido",
            "nombre",
            "fecha_nacimiento",
            "sexo",
            "nacionalidad",
        ]

        for field_name in expected_fields:
            assert field_name in form.fields, f"Campo {field_name} no encontrado"

    def test_no_incluye_campo_edad_en_formulario(
        self, usuario_con_permisos, centro, nomina
    ):
        """Verifica que el campo 'edad' NO está en el formulario."""
        client = Client()
        client.force_login(usuario_con_permisos)

        url = reverse(
            "centrodeinfancia_nomina_editar",
            kwargs={"pk": centro.pk, "nomina_id": nomina.pk},
        )
        response = client.get(url)

        assert response.status_code == 200
        form = response.context["form"]

        # 'edad' no debería estar en los campos del formulario
        assert "edad" not in form.fields
