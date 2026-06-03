from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.urls import reverse

from ciudadanos.models import Ciudadano
from core.models import Provincia, Sexo
from ver_para_ser_libre.forms import JornadaVPSLForm, RegistroNominalVPSLForm
from ver_para_ser_libre.models import (
    CasoLaboratorioVPSL,
    ChecklistJornadaVPSL,
    EstadoLaboratorio,
    EstadoItinerario,
    EstadoEvaluacionVPSL,
    EstadoJornada,
    HistorialEstadoVPSL,
    ItinerarioVPSL,
    JornadaVPSL,
    RegistroNominalVPSL,
    ResultadoAtencion,
    SedeVPSL,
)
from ver_para_ser_libre.services import workflow


pytestmark = pytest.mark.django_db


def crear_sede(**overrides):
    defaults = {
        "jurisdiccion": "Ciudad de Buenos Aires",
        "sector": "Privado",
        "ambito": "Urbano",
        "departamento": "Comuna 4",
        "codigo_departamento": "2104",
        "localidad": "CIUDAD DE BUENOS AIRES",
        "codigo_localidad": "2104001",
        "cueanexo": "20000100",
        "nombre": "INSTITUTO PRIVADO ESCUELA EVANGELICA WILLIAM C. MORRIS",
        "domicilio": "SUAREZ 684 BOCA",
        "codigo_postal": "C1162",
        "telefono": "011 4301-2922",
        "mail": "mail@example.com",
    }
    defaults.update(overrides)
    return SedeVPSL.objects.create(**defaults)


def crear_itinerario(**overrides):
    provincia = overrides.pop("provincia", None) or Provincia.objects.create(
        nombre="Buenos Aires"
    )
    defaults = {
        "provincia": provincia,
        "fecha_inicio": date(2026, 5, 1),
        "fecha_fin": date(2026, 5, 10),
        "localidades_tentativas": "La Plata",
        "sedes_tentativas": "Escuela 1",
        "referente_nombre": "Referente Provincial",
        "carta_archivo": SimpleUploadedFile(
            "carta.pdf",
            b"contenido",
            content_type="application/pdf",
        ),
    }
    defaults.update(overrides)
    sedes = defaults.pop("sedes", None) or [crear_sede()]
    itinerario = ItinerarioVPSL.objects.create(**defaults)
    itinerario.sedes.set(sedes)
    return itinerario


def crear_jornada(itinerario=None, **overrides):
    defaults = {
        "itinerario": itinerario or crear_itinerario(),
        "fecha": date(2026, 5, 2),
        "sede": "Escuela 1",
    }
    defaults.update(overrides)
    defaults.setdefault("sede_vpsl", defaults["itinerario"].sedes.first())
    return JornadaVPSL.objects.create(**defaults)


def completar_checklist_sede(jornada):
    for item in (
        ChecklistJornadaVPSL.Item.ELECTRICIDAD,
        ChecklistJornadaVPSL.Item.VIANDAS,
        ChecklistJornadaVPSL.Item.SEGURIDAD,
    ):
        ChecklistJornadaVPSL.objects.create(
            jornada=jornada,
            sede=jornada.sede_vpsl,
            item=item,
            critico=True,
            cumple=True,
        )


def aprobar_sedes_y_carta(itinerario):
    itinerario.carta_referencia_estado = EstadoEvaluacionVPSL.APROBADO
    itinerario.carta_archivo_estado = EstadoEvaluacionVPSL.APROBADO
    itinerario.save(update_fields=["carta_referencia_estado", "carta_archivo_estado"])
    workflow.asegurar_evaluaciones_sedes(itinerario)
    itinerario.evaluaciones_sedes.update(estado=EstadoEvaluacionVPSL.APROBADO)


def hacer_usuario_provincial(user, provincia):
    profile = user.profile
    profile.es_usuario_provincial = True
    profile.provincia = provincia
    profile.save(update_fields=["es_usuario_provincial", "provincia"])
    return user


def asignar_permiso(user, codename):
    user.user_permissions.add(Permission.objects.get(codename=codename))
    return user


def crear_ciudadano_validado(**overrides):
    sexo = overrides.pop("sexo", None) or Sexo.objects.create(sexo="Femenino")
    defaults = {
        "apellido": "Perez",
        "nombre": "Ana",
        "fecha_nacimiento": date(2016, 5, 1),
        "tipo_documento": Ciudadano.DOCUMENTO_DNI,
        "documento": 12345678,
        "sexo": sexo,
        "telefono": "221111111",
        "origen_dato": "renaper",
        "tipo_registro_identidad": Ciudadano.TIPO_REGISTRO_ESTANDAR,
        "estado_validacion_renaper": Ciudadano.RENAPER_VALIDADO,
    }
    defaults.update(overrides)
    return Ciudadano.objects.create(**defaults)


def test_jornada_debe_quedar_dentro_del_rango_del_itinerario():
    jornada = JornadaVPSL(
        itinerario=crear_itinerario(),
        fecha=date(2026, 6, 1),
        sede="Escuela fuera de rango",
    )

    with pytest.raises(ValidationError):
        jornada.full_clean()


def test_jornada_permite_repetir_fecha_en_mismo_itinerario_con_distinta_sede():
    sede_1 = crear_sede(cueanexo="FECHA001", nombre="Escuela fecha 1")
    sede_2 = crear_sede(cueanexo="FECHA002", nombre="Escuela fecha 2")
    itinerario = crear_itinerario(sedes=[sede_1, sede_2])
    crear_jornada(itinerario=itinerario, fecha=date(2026, 5, 2))
    jornada = JornadaVPSL(
        itinerario=itinerario,
        fecha=date(2026, 5, 2),
        sede=sede_2.nombre,
        sede_vpsl=sede_2,
    )

    jornada.full_clean()


def test_jornada_form_permite_fecha_ocupada_en_itinerario_con_distinta_sede():
    sede_1 = crear_sede(cueanexo="FORMFECHA001", nombre="Escuela form fecha 1")
    sede_2 = crear_sede(cueanexo="FORMFECHA002", nombre="Escuela form fecha 2")
    itinerario = crear_itinerario(sedes=[sede_1, sede_2])
    aprobar_sedes_y_carta(itinerario)
    crear_jornada(itinerario=itinerario, sede_vpsl=sede_1, fecha=date(2026, 5, 2))

    form = JornadaVPSLForm(
        data={
            "fecha": "2026-05-02",
            "sede_vpsl": str(sede_2.pk),
            "horario_inicio": "",
            "horario_fin": "",
            "referente_dni": "",
            "referente_sexo": "",
            "referente_telefono": "",
            "referente_email": "",
            "equipo_asignado": "",
            "observaciones": "",
        },
        itinerario=itinerario,
    )

    assert form.is_valid(), form.errors


def test_jornada_form_incluye_vehiculo_en_planificacion():
    itinerario = crear_itinerario()
    form = JornadaVPSLForm(itinerario=itinerario)

    assert "vehiculo" in form.fields
    assert ("vehiculo_1", "Vehiculo 1") in form.fields["vehiculo"].choices
    assert ("vehiculo_4", "Vehiculo 4") in form.fields["vehiculo"].choices


def test_jornada_create_permite_misma_fecha_con_distinta_sede(client):
    user = get_user_model().objects.create_superuser(
        username="vpsl-jornada-duplicada",
        email="vpsl-jornada-duplicada@example.com",
        password="testpass123",
    )
    sede_1 = crear_sede(cueanexo="VIEWFECHA001", nombre="Escuela view fecha 1")
    sede_2 = crear_sede(cueanexo="VIEWFECHA002", nombre="Escuela view fecha 2")
    itinerario = crear_itinerario(sedes=[sede_1, sede_2])
    workflow.presentar_itinerario(itinerario)
    aprobar_sedes_y_carta(itinerario)
    workflow.aprobar_itinerario(itinerario)
    crear_jornada(itinerario=itinerario, sede_vpsl=sede_1, fecha=date(2026, 5, 2))
    client.force_login(user)

    url = reverse("vpsl_jornada_create", kwargs={"itinerario_pk": itinerario.pk})
    response = client.get(url)

    assert response.status_code == 200
    html = response.content.decode()
    assert "fechas-ocupadas-json" not in html
    assert "Ya existe una jornada para este itinerario en esa fecha." not in html

    response = client.post(
        url,
        {
            "fecha": "2026-05-02",
            "sede_vpsl": str(sede_2.pk),
            "horario_inicio": "",
            "horario_fin": "",
            "referente_dni": "",
            "referente_sexo": "",
            "referente_telefono": "",
            "referente_email": "",
            "equipo_asignado": "",
            "observaciones": "",
        },
    )

    assert response.status_code == 302
    assert (
        JornadaVPSL.objects.filter(
            itinerario=itinerario, fecha=date(2026, 5, 2)
        ).count()
        == 2
    )


def test_jornada_create_oculta_equipo_y_precarga_horarios(client):
    user = get_user_model().objects.create_superuser(
        username="vpsl-jornada-horarios",
        email="vpsl-jornada-horarios@example.com",
        password="testpass123",
    )
    itinerario = crear_itinerario()
    workflow.presentar_itinerario(itinerario)
    aprobar_sedes_y_carta(itinerario)
    workflow.aprobar_itinerario(itinerario)
    client.force_login(user)

    response = client.get(
        reverse("vpsl_jornada_create", kwargs={"itinerario_pk": itinerario.pk})
    )

    assert response.status_code == 200
    html = response.content.decode()
    assert 'name="equipo_asignado"' not in html
    assert 'name="prescripcion"' not in html
    assert 'name="horario_inicio" value="09:00:00"' in html
    assert 'name="horario_fin" value="18:00:00"' in html


def test_presentar_itinerario_requiere_carta_o_referencia():
    itinerario = crear_itinerario(carta_referencia="", carta_archivo=None)

    with pytest.raises(ValidationError):
        workflow.presentar_itinerario(itinerario)


def test_presentar_itinerario_cambia_estado_y_registra_historial():
    itinerario = crear_itinerario()

    workflow.presentar_itinerario(itinerario)

    itinerario.refresh_from_db()
    assert itinerario.estado == EstadoItinerario.PRESENTADO
    assert HistorialEstadoVPSL.objects.filter(object_id=itinerario.pk).count() == 1
    assert itinerario.evaluaciones_sedes.count() == itinerario.sedes.count()


def test_aprobar_itinerario_requiere_carta_y_sede_aprobadas():
    itinerario = crear_itinerario()
    workflow.presentar_itinerario(itinerario)
    aprobar_sedes_y_carta(itinerario)

    workflow.aprobar_itinerario(itinerario)

    itinerario.refresh_from_db()
    assert itinerario.estado == EstadoItinerario.APROBADO


def test_editar_itinerario_aprobado_no_cambia_estado_y_bloquea_campos_completos(
    client,
):
    user = get_user_model().objects.create_superuser(
        username="vpsl-edit-aprobado",
        email="vpsl-edit-aprobado@example.com",
        password="testpass123",
    )
    itinerario = crear_itinerario(matricula_estimada=None, observaciones="")
    workflow.presentar_itinerario(itinerario)
    aprobar_sedes_y_carta(itinerario)
    workflow.aprobar_itinerario(itinerario)
    client.force_login(user)

    response = client.post(
        reverse("vpsl_itinerario_update", kwargs={"pk": itinerario.pk}),
        {
            "provincia": str(itinerario.provincia_id),
            "fecha_inicio": "2026-06-01",
            "fecha_fin": "2026-06-10",
            "sedes": [str(sede.pk) for sede in itinerario.sedes.all()],
            "matricula_estimada": "150",
            "referente_nombre": "Otro referente",
            "referente_apellido": "Otro apellido",
            "referente_telefono": "111",
            "referente_email": "otro@example.com",
            "carta_referencia": "Otra carta",
            "observaciones": "Dato agregado luego de aprobacion.",
        },
    )

    assert response.status_code == 302
    itinerario.refresh_from_db()
    assert itinerario.estado == EstadoItinerario.APROBADO
    assert itinerario.fecha_inicio == date(2026, 5, 1)
    assert itinerario.referente_nombre == "Referente Provincial"
    assert itinerario.referente_apellido == "Otro apellido"
    assert itinerario.matricula_estimada is None
    assert itinerario.observaciones == "Dato agregado luego de aprobacion."


def test_itinerario_edit_muestra_fechas_en_inputs_date(client):
    user = get_user_model().objects.create_superuser(
        username="vpsl-edit-fechas",
        email="vpsl-edit-fechas@example.com",
        password="testpass123",
    )
    itinerario = crear_itinerario()
    client.force_login(user)

    response = client.get(
        reverse("vpsl_itinerario_update", kwargs={"pk": itinerario.pk})
    )

    assert response.status_code == 200
    html = response.content.decode()
    assert 'name="fecha_inicio" value="2026-05-01"' in html
    assert 'name="fecha_fin" value="2026-05-10"' in html


def test_itinerario_edit_aprobado_muestra_campos_bloqueados_oscuros(client):
    user = get_user_model().objects.create_superuser(
        username="vpsl-edit-bloqueados",
        email="vpsl-edit-bloqueados@example.com",
        password="testpass123",
    )
    itinerario = crear_itinerario()
    workflow.presentar_itinerario(itinerario)
    aprobar_sedes_y_carta(itinerario)
    workflow.aprobar_itinerario(itinerario)
    client.force_login(user)

    response = client.get(
        reverse("vpsl_itinerario_update", kwargs={"pk": itinerario.pk})
    )

    assert response.status_code == 200
    html = response.content.decode()
    assert 'name="provincia"' in html
    assert "bg-dark text-white" in html


def test_itinerario_subsanado_no_muestra_presentar_en_detail(client):
    user = get_user_model().objects.create_superuser(
        username="vpsl-subsanado-detail",
        email="vpsl-subsanado-detail@example.com",
        password="testpass123",
    )
    itinerario = crear_itinerario(estado=EstadoItinerario.SUBSANADO)
    client.force_login(user)

    response = client.get(
        reverse("vpsl_itinerario_detail", kwargs={"pk": itinerario.pk})
    )

    assert response.status_code == 200
    html = response.content.decode()
    assert "Presentar" not in html
    assert "Evaluar" in html


def test_itinerario_subsanar_muestra_solo_componentes_solicitados(client):
    user = get_user_model().objects.create_superuser(
        username="vpsl-subsanar-form",
        email="vpsl-subsanar-form@example.com",
        password="testpass123",
    )
    sede_a_subsanar = crear_sede(cueanexo="20000101", nombre="Sede observada")
    sede_aprobada = crear_sede(cueanexo="20000102", nombre="Sede aprobada")
    itinerario = crear_itinerario(
        estado=EstadoItinerario.EN_SUBSANACION,
        sedes=[sede_a_subsanar, sede_aprobada],
    )
    itinerario.carta_archivo_estado = EstadoEvaluacionVPSL.SUBSANAR
    itinerario.subsanacion_observaciones = "Corregir carta y sede observada."
    itinerario.save(update_fields=["carta_archivo_estado", "subsanacion_observaciones"])
    workflow.asegurar_evaluaciones_sedes(itinerario)
    evaluacion_observada = itinerario.evaluaciones_sedes.get(sede=sede_a_subsanar)
    evaluacion_observada.estado = EstadoEvaluacionVPSL.SUBSANAR
    evaluacion_observada.observacion = "Cambiar sede."
    evaluacion_observada.save(update_fields=["estado", "observacion"])
    itinerario.evaluaciones_sedes.filter(sede=sede_aprobada).update(
        estado=EstadoEvaluacionVPSL.APROBADO
    )
    client.force_login(user)

    response = client.get(
        reverse("vpsl_itinerario_subsanar", kwargs={"pk": itinerario.pk})
    )

    assert response.status_code == 200
    html = response.content.decode()
    assert 'name="carta_archivo"' in html
    assert f'name="subsanar_sede_{evaluacion_observada.pk}"' in html
    assert "select2-sede-subsanacion-vpsl" in html
    assert f'data-provincia="{itinerario.provincia_id}"' in html
    assert "Sede observada" in html
    assert "Sede aprobada" not in html
    assert 'name="sedes"' not in html
    assert 'name="fecha_inicio"' not in html
    assert 'name="referente_nombre"' not in html


def test_itinerario_subsanar_reemplaza_sede_y_deja_pendiente_evaluacion(client):
    user = get_user_model().objects.create_superuser(
        username="vpsl-subsanar-save",
        email="vpsl-subsanar-save@example.com",
        password="testpass123",
    )
    sede_observada = crear_sede(cueanexo="20000103", nombre="Sede a reemplazar")
    sede_nueva = crear_sede(cueanexo="20000104", nombre="Sede nueva")
    itinerario = crear_itinerario(
        estado=EstadoItinerario.EN_SUBSANACION,
        sedes=[sede_observada],
    )
    workflow.asegurar_evaluaciones_sedes(itinerario)
    evaluacion = itinerario.evaluaciones_sedes.get(sede=sede_observada)
    evaluacion.estado = EstadoEvaluacionVPSL.SUBSANAR
    evaluacion.save(update_fields=["estado"])
    client.force_login(user)

    response = client.post(
        reverse("vpsl_itinerario_subsanar", kwargs={"pk": itinerario.pk}),
        {f"subsanar_sede_{evaluacion.pk}": str(sede_nueva.pk)},
    )

    assert response.status_code == 302
    itinerario.refresh_from_db()
    assert itinerario.estado == EstadoItinerario.SUBSANADO
    assert sede_observada not in itinerario.sedes.all()
    assert sede_nueva in itinerario.sedes.all()
    assert (
        itinerario.evaluaciones_sedes.get(sede=sede_nueva).estado
        == EstadoEvaluacionVPSL.PENDIENTE
    )


def test_itinerario_create_bloquea_provincia_de_usuario_provincial(client):
    provincia = Provincia.objects.create(nombre="Cordoba")
    user = get_user_model().objects.create_superuser(
        username="vpsl-create-provincial",
        email="vpsl-create-provincial@example.com",
        password="testpass123",
    )
    hacer_usuario_provincial(user, provincia)
    client.force_login(user)

    response = client.get(reverse("vpsl_itinerario_create"))

    assert response.status_code == 200
    html = response.content.decode()
    assert 'name="provincia"' in html
    assert "disabled" in html
    assert "bg-dark text-white" in html
    assert f'value="{provincia.pk}" selected' in html
    assert html.index('name="referente_nombre"') < html.index(
        'name="referente_apellido"'
    )
    assert html.index('name="referente_telefono"') < html.index(
        'name="referente_email"'
    )
    assert 'name="carta_referencia"' not in html
    assert 'name="carta_archivo"' in html
    assert 'name="localidad_filtro"' in html


def test_itinerario_create_usa_provincia_del_usuario_aunque_posteen_otra(client):
    provincia_usuario = Provincia.objects.create(nombre="Cordoba")
    provincia_posteada = Provincia.objects.create(nombre="Buenos Aires")
    sede = crear_sede(jurisdiccion="Cordoba")
    user = get_user_model().objects.create_superuser(
        username="vpsl-create-provincia-server",
        email="vpsl-create-provincia-server@example.com",
        password="testpass123",
    )
    hacer_usuario_provincial(user, provincia_usuario)
    client.force_login(user)

    response = client.post(
        reverse("vpsl_itinerario_create"),
        {
            "provincia": str(provincia_posteada.pk),
            "fecha_inicio": "2026-05-01",
            "fecha_fin": "2026-05-10",
            "sedes": [str(sede.pk)],
            "matricula_estimada": "",
            "referente_nombre": "Referente",
            "referente_apellido": "Provincial",
            "referente_telefono": "351111111",
            "referente_email": "referente@example.com",
            "carta_archivo": SimpleUploadedFile(
                "carta.pdf",
                b"contenido",
                content_type="application/pdf",
            ),
            "observaciones": "",
        },
    )

    assert response.status_code == 302
    itinerario = ItinerarioVPSL.objects.get(referente_nombre="Referente")
    assert itinerario.provincia == provincia_usuario
    assert itinerario.referente_apellido == "Provincial"


def test_aprobar_itinerario_bloquea_si_sede_pendiente():
    itinerario = crear_itinerario()
    workflow.presentar_itinerario(itinerario)
    itinerario.carta_archivo_estado = EstadoEvaluacionVPSL.APROBADO
    itinerario.save(update_fields=["carta_archivo_estado"])

    with pytest.raises(ValidationError):
        workflow.aprobar_itinerario(itinerario)


def test_rechazar_itinerario_deja_estado_final_sin_edicion():
    itinerario = crear_itinerario()
    workflow.presentar_itinerario(itinerario)
    itinerario.carta_archivo_estado = EstadoEvaluacionVPSL.RECHAZADO
    itinerario.save(update_fields=["carta_archivo_estado"])
    workflow.asegurar_evaluaciones_sedes(itinerario)
    itinerario.evaluaciones_sedes.update(estado=EstadoEvaluacionVPSL.APROBADO)

    workflow.rechazar_itinerario(itinerario)

    itinerario.refresh_from_db()
    assert itinerario.estado == EstadoItinerario.RECHAZADO


def test_enviar_a_subsanacion_requiere_observacion_y_deja_estado():
    itinerario = crear_itinerario()
    workflow.presentar_itinerario(itinerario)
    itinerario.carta_archivo_estado = EstadoEvaluacionVPSL.SUBSANAR
    itinerario.save(update_fields=["carta_archivo_estado"])
    workflow.asegurar_evaluaciones_sedes(itinerario)
    itinerario.evaluaciones_sedes.update(estado=EstadoEvaluacionVPSL.APROBADO)

    workflow.enviar_itinerario_a_subsanacion(
        itinerario,
        observacion="Corregir carta referencia.",
    )

    itinerario.refresh_from_db()
    assert itinerario.estado == EstadoItinerario.EN_SUBSANACION
    assert itinerario.subsanacion_observaciones == "Corregir carta referencia."


def test_habilitar_jornada_bloquea_si_hay_checklist_critico_pendiente():
    jornada = crear_jornada()
    ChecklistJornadaVPSL.objects.create(
        jornada=jornada,
        sede=jornada.sede_vpsl,
        item=ChecklistJornadaVPSL.Item.ELECTRICIDAD,
        critico=True,
        cumple=False,
    )

    with pytest.raises(ValidationError):
        workflow.habilitar_jornada(jornada)


def test_habilitar_jornada_con_checklist_critico_completo():
    jornada = crear_jornada()
    completar_checklist_sede(jornada)

    workflow.habilitar_jornada(jornada)

    jornada.refresh_from_db()
    assert jornada.estado == EstadoJornada.HABILITADA


def test_registro_enviado_a_laboratorio_crea_caso_post_operativo():
    jornada = crear_jornada(estado=EstadoJornada.HABILITADA)
    registro = RegistroNominalVPSL(
        jornada=jornada,
        dni="12345678",
        nombre="Ana",
        apellido="Perez",
        numero_acta="A-1",
        resultado=ResultadoAtencion.ENVIADO_LABORATORIO,
        cantidad_lentes=1,
    )

    workflow.guardar_registro_nominal(registro)

    assert CasoLaboratorioVPSL.objects.filter(registro=registro).exists()


def test_flujo_laboratorio_incluye_envio_a_nacion_antes_de_provincia():
    jornada = crear_jornada(estado=EstadoJornada.HABILITADA)
    registro = RegistroNominalVPSL(
        jornada=jornada,
        dni="12345678",
        nombre="Ana",
        apellido="Perez",
        numero_acta="A-1",
        resultado=ResultadoAtencion.ENVIADO_LABORATORIO,
        cantidad_lentes=1,
    )
    workflow.guardar_registro_nominal(registro)
    caso = CasoLaboratorioVPSL.objects.get(registro=registro)
    caso.estado = EstadoLaboratorio.EN_PRODUCCION

    assert (
        workflow.siguiente_estado_laboratorio(caso) == EstadoLaboratorio.ENVIADO_NACION
    )

    caso.estado = EstadoLaboratorio.ENVIADO_NACION

    assert (
        workflow.siguiente_estado_laboratorio(caso)
        == EstadoLaboratorio.ENVIADO_PROVINCIA
    )


def test_jornada_actualiza_laboratorio_masivo_si_comparten_estado(client):
    user = get_user_model().objects.create_superuser(
        username="vpsl-lab-bulk",
        email="vpsl-lab-bulk@example.com",
        password="testpass123",
    )
    jornada = crear_jornada(estado=EstadoJornada.EN_POST_OPERATIVO)
    casos = []
    for index, dni in enumerate(["12345678", "22345678"], start=1):
        registro = RegistroNominalVPSL.objects.create(
            jornada=jornada,
            dni=dni,
            nombre=f"Nombre {index}",
            apellido="Perez",
            numero_acta=f"A-{index}",
            resultado=ResultadoAtencion.ENVIADO_LABORATORIO,
            cantidad_lentes=1,
            validado_renaper=True,
        )
        casos.append(CasoLaboratorioVPSL.objects.create(registro=registro))
    client.force_login(user)

    response = client.post(
        reverse("vpsl_laboratorio_bulk_update", kwargs={"pk": jornada.pk}),
        {
            "casos": [str(caso.pk) for caso in casos],
            "fecha": "2026-05-04",
            "responsable": "Laboratorio",
        },
    )

    assert response.status_code == 302
    assert set(CasoLaboratorioVPSL.objects.values_list("estado", flat=True)) == {
        EstadoLaboratorio.ENVIADO
    }
    assert sum(caso.historial.count() for caso in casos) == 2


def test_jornada_detail_selecciona_casos_laboratorio_en_tabla(client):
    user = get_user_model().objects.create_superuser(
        username="vpsl-lab-select-table",
        email="vpsl-lab-select-table@example.com",
        password="testpass123",
    )
    jornada = crear_jornada(estado=EstadoJornada.EN_POST_OPERATIVO)
    registro = RegistroNominalVPSL.objects.create(
        jornada=jornada,
        dni="32345678",
        nombre="Maria",
        apellido="Lopez",
        numero_acta="A-1",
        resultado=ResultadoAtencion.ENVIADO_LABORATORIO,
        cantidad_lentes=1,
        validado_renaper=True,
    )
    caso = CasoLaboratorioVPSL.objects.create(registro=registro)
    client.force_login(user)

    response = client.get(reverse("vpsl_jornada_detail", kwargs={"pk": jornada.pk}))

    html = response.content.decode()
    assert response.status_code == 200
    assert 'class="form-check-input vpsl-lab-select"' in html
    assert f'value="{caso.pk}"' in html
    assert (
        'name="casos"'
        not in html.split("lab-bulk-selected-inputs")[1].split("</div>", 1)[0]
    )


def test_cierre_diario_no_finaliza_hasta_cierre_definitivo():
    jornada = crear_jornada(estado=EstadoJornada.HABILITADA)
    workflow.guardar_registro_nominal(
        RegistroNominalVPSL(
            jornada=jornada,
            dni="12345678",
            nombre="Ana",
            apellido="Perez",
            numero_acta="A-1",
            resultado=ResultadoAtencion.ENVIADO_LABORATORIO,
            cantidad_lentes=1,
        )
    )

    cierre = workflow.generar_cierre_diario(
        jornada,
        responsable="Coordinacion",
        cantidad_atenciones_registradas=1,
        cantidad_lentes_entregados_dia=0,
        cantidad_casos_laboratorio_reportados=1,
    )

    jornada.refresh_from_db()
    assert cierre.total_controles == 1
    assert cierre.casos_laboratorio == 1
    assert cierre.consistente is True
    assert jornada.estado == EstadoJornada.PENDIENTE_CIERRE

    workflow.cerrar_jornada_definitivamente(jornada)
    jornada.refresh_from_db()
    assert jornada.estado == EstadoJornada.EN_POST_OPERATIVO


def test_cierre_create_get_no_cambia_estado_de_jornada(client):
    user = get_user_model().objects.create_superuser(
        username="vpsl-cierre-get",
        email="vpsl-cierre-get@example.com",
        password="testpass123",
    )
    jornada = crear_jornada(estado=EstadoJornada.EN_PROGRESO)
    client.force_login(user)

    response = client.get(
        reverse("vpsl_cierre_create", kwargs={"jornada_pk": jornada.pk})
    )

    assert response.status_code == 200
    jornada.refresh_from_db()
    assert jornada.estado == EstadoJornada.EN_PROGRESO


def test_cierre_create_post_deja_pendiente_cierre_al_guardar(client):
    user = get_user_model().objects.create_superuser(
        username="vpsl-cierre-post",
        email="vpsl-cierre-post@example.com",
        password="testpass123",
    )
    jornada = crear_jornada(estado=EstadoJornada.EN_PROGRESO)
    workflow.guardar_registro_nominal(
        RegistroNominalVPSL(
            jornada=jornada,
            dni="12345678",
            nombre="Ana",
            apellido="Perez",
            numero_acta="A-1",
            resultado=ResultadoAtencion.NO_REQUIERE,
            cantidad_lentes=0,
        )
    )
    client.force_login(user)

    response = client.post(
        reverse("vpsl_cierre_create", kwargs={"jornada_pk": jornada.pk}),
        {
            "cantidad_atenciones_registradas": "1",
            "cantidad_lentes_entregados_dia": "0",
            "cantidad_casos_laboratorio_reportados": "0",
            "responsable_cierre": "Coordinacion",
            "observaciones": "",
            "acta_adjunta": SimpleUploadedFile(
                "acta.jpg",
                b"contenido",
                content_type="image/jpeg",
            ),
        },
    )

    assert response.status_code == 302
    jornada.refresh_from_db()
    assert jornada.estado == EstadoJornada.PENDIENTE_CIERRE


def test_registro_posterior_al_cierre_actualiza_consistencia_y_permite_subsanar():
    jornada = crear_jornada(estado=EstadoJornada.EN_PROGRESO)
    workflow.guardar_registro_nominal(
        RegistroNominalVPSL(
            jornada=jornada,
            dni="12345678",
            nombre="Ana",
            apellido="Perez",
            numero_acta="A-1",
            resultado=ResultadoAtencion.NO_REQUIERE,
            cantidad_lentes=0,
        )
    )
    cierre = workflow.generar_cierre_diario(
        jornada,
        responsable="Coordinacion",
        cantidad_atenciones_registradas=1,
        cantidad_lentes_entregados_dia=0,
        cantidad_casos_laboratorio_reportados=0,
    )
    assert cierre.consistente is True

    workflow.guardar_registro_nominal(
        RegistroNominalVPSL(
            jornada=jornada,
            dni="22333444",
            nombre="Juan",
            apellido="Gomez",
            numero_acta="A-2",
            resultado=ResultadoAtencion.NO_REQUIERE,
            cantidad_lentes=0,
        )
    )

    cierre.refresh_from_db()
    jornada.refresh_from_db()
    assert cierre.total_controles == 2
    assert cierre.consistente is False
    assert jornada.estado == EstadoJornada.PENDIENTE_CIERRE_OBSERVADA


def test_cierre_diario_resume_no_requiere_y_derivados_actualizados():
    jornada = crear_jornada(estado=EstadoJornada.EN_PROGRESO)
    RegistroNominalVPSL.objects.create(
        jornada=jornada,
        dni="12345678",
        nombre="Ana",
        apellido="Perez",
        numero_acta="A-1",
        resultado=ResultadoAtencion.NO_REQUIERE,
        cantidad_lentes=0,
    )
    RegistroNominalVPSL.objects.create(
        jornada=jornada,
        dni="22333444",
        nombre="Juan",
        apellido="Gomez",
        numero_acta="A-2",
        resultado=ResultadoAtencion.DERIVADO,
        cantidad_lentes=0,
    )

    cierre = workflow.generar_cierre_diario(
        jornada,
        responsable="Coordinacion",
        cantidad_atenciones_registradas=2,
        cantidad_lentes_entregados_dia=0,
        cantidad_casos_laboratorio_reportados=0,
    )

    assert cierre.no_requiere_anteojos == 1
    assert cierre.derivados == 1

    workflow.guardar_registro_nominal(
        RegistroNominalVPSL(
            jornada=jornada,
            dni="32333444",
            nombre="Maria",
            apellido="Lopez",
            numero_acta="A-3",
            resultado=ResultadoAtencion.DERIVADO,
            cantidad_lentes=0,
        )
    )
    cierre.refresh_from_db()

    assert cierre.no_requiere_anteojos == 1
    assert cierre.derivados == 2


def test_cierre_definitivo_bloquea_si_cierre_inconsistente():
    jornada = crear_jornada(estado=EstadoJornada.EN_PROGRESO)
    workflow.guardar_registro_nominal(
        RegistroNominalVPSL(
            jornada=jornada,
            dni="12345678",
            nombre="Ana",
            apellido="Perez",
            numero_acta="A-1",
            resultado=ResultadoAtencion.NO_REQUIERE,
            cantidad_lentes=0,
        )
    )
    workflow.generar_cierre_diario(
        jornada,
        responsable="Coordinacion",
        cantidad_atenciones_registradas=2,
        cantidad_lentes_entregados_dia=0,
        cantidad_casos_laboratorio_reportados=0,
    )

    with pytest.raises(ValidationError):
        workflow.cerrar_jornada_definitivamente(jornada)


def test_paginas_principales_renderizan(client):
    user = get_user_model().objects.create_superuser(
        username="vpsl-admin",
        email="vpsl-admin@example.com",
        password="testpass123",
    )
    client.force_login(user)
    itinerario = crear_itinerario()
    hacer_usuario_provincial(user, itinerario.provincia)
    workflow.presentar_itinerario(itinerario)
    aprobar_sedes_y_carta(itinerario)
    workflow.aprobar_itinerario(itinerario)
    jornada = crear_jornada(itinerario=itinerario, estado=EstadoJornada.HABILITADA)

    urls = [
        reverse("vpsl_itinerario_create"),
        reverse("vpsl_itinerario_detail", kwargs={"pk": itinerario.pk}),
        reverse("vpsl_jornada_create", kwargs={"itinerario_pk": itinerario.pk}),
        reverse("vpsl_jornada_detail", kwargs={"pk": jornada.pk}),
        reverse("vpsl_checklist_create", kwargs={"jornada_pk": jornada.pk}),
        reverse("vpsl_registro_create", kwargs={"jornada_pk": jornada.pk}),
        reverse("vpsl_sede_list"),
        reverse("vpsl_sede_create"),
        reverse("vpsl_sede_update", kwargs={"pk": jornada.sede_vpsl.pk}),
    ]

    for url in urls:
        response = client.get(url)
        assert response.status_code == 200


def test_itinerario_list_restringe_usuario_provincial_y_filtra(client):
    provincia_visible = Provincia.objects.create(nombre="Cordoba")
    provincia_oculta = Provincia.objects.create(nombre="Santa Fe")
    itinerario_visible = crear_itinerario(
        provincia=provincia_visible,
        referente_nombre="Laura",
        estado=EstadoItinerario.APROBADO,
        sedes=[crear_sede(cueanexo="CB001", jurisdiccion="Cordoba")],
    )
    itinerario_oculto = crear_itinerario(
        provincia=provincia_oculta,
        referente_nombre="Sofia",
        sedes=[crear_sede(cueanexo="SF001", jurisdiccion="Santa Fe")],
    )
    user = get_user_model().objects.create_user(
        username="vpsl-list-provincial",
        email="vpsl-list-provincial@example.com",
        password="testpass123",
    )
    hacer_usuario_provincial(user, provincia_visible)
    asignar_permiso(user, "view_itinerariovpsl")
    client.force_login(user)

    response = client.get(
        reverse("vpsl_itinerario_list"),
        {"estado": EstadoItinerario.APROBADO, "busqueda": "Laura"},
    )

    html = response.content.decode()
    assert response.status_code == 200
    assert itinerario_visible.codigo in html
    assert itinerario_oculto.codigo not in html
    assert "Cordoba" in html
    assert "Santa Fe" not in html


def test_itinerario_detail_muestra_localidad_de_sede_en_jornadas(client):
    user = get_user_model().objects.create_superuser(
        username="vpsl-jornada-localidad",
        email="vpsl-jornada-localidad@example.com",
        password="testpass123",
    )
    sede = crear_sede(localidad="ABEL AYERZA", nombre="ESCUELA 1")
    itinerario = crear_itinerario(sedes=[sede])
    workflow.presentar_itinerario(itinerario)
    aprobar_sedes_y_carta(itinerario)
    workflow.aprobar_itinerario(itinerario)
    crear_jornada(itinerario=itinerario, sede_vpsl=sede, sede=sede.nombre)
    client.force_login(user)

    response = client.get(
        reverse("vpsl_itinerario_detail", kwargs={"pk": itinerario.pk})
    )

    assert response.status_code == 200
    assert "ABEL AYERZA" in response.content.decode()


def test_itinerario_detail_muestra_vehiculo_de_jornada(client):
    user = get_user_model().objects.create_superuser(
        username="vpsl-jornada-vehiculo",
        email="vpsl-jornada-vehiculo@example.com",
        password="testpass123",
    )
    itinerario = crear_itinerario()
    crear_jornada(
        itinerario=itinerario,
        fecha=date(2026, 5, 2),
        vehiculo="vehiculo_3",
    )
    client.force_login(user)

    response = client.get(
        reverse("vpsl_itinerario_detail", kwargs={"pk": itinerario.pk})
    )

    html = response.content.decode()
    assert response.status_code == 200
    assert "Vehiculo" in html
    assert "Vehiculo 3" in html


def test_jornada_detail_muestra_escuela_en_resumen_de_ubicacion(client):
    user = get_user_model().objects.create_superuser(
        username="vpsl-jornada-ubicacion",
        email="vpsl-jornada-ubicacion@example.com",
        password="testpass123",
    )
    sede = crear_sede(
        nombre="ESCUELA PRIMARIA 1",
        jurisdiccion="Buenos Aires",
        localidad="ABEL AYERZA",
        domicilio="CALLE 1 123",
    )
    itinerario = crear_itinerario(sedes=[sede])
    jornada = crear_jornada(itinerario=itinerario, sede_vpsl=sede, sede=sede.nombre)
    client.force_login(user)

    response = client.get(reverse("vpsl_jornada_detail", kwargs={"pk": jornada.pk}))

    assert response.status_code == 200
    html = response.content.decode()
    assert "Escuela" in html
    assert "ESCUELA PRIMARIA 1" in html
    assert html.index("Escuela") < html.index("Provincia")
    assert html.index("Provincia") < html.index("Localidad")
    assert html.index("Localidad") < html.index("Calle y altura")


def test_jornada_detail_muestra_resumen_cierre_compacto(client):
    user = get_user_model().objects.create_superuser(
        username="vpsl-cierre-resumen",
        email="vpsl-cierre-resumen@example.com",
        password="testpass123",
    )
    jornada = crear_jornada(estado=EstadoJornada.EN_PROGRESO)
    RegistroNominalVPSL.objects.create(
        jornada=jornada,
        dni="12345678",
        nombre="Ana",
        apellido="Perez",
        numero_acta="A-1",
        resultado=ResultadoAtencion.NO_REQUIERE,
        cantidad_lentes=0,
    )
    RegistroNominalVPSL.objects.create(
        jornada=jornada,
        dni="22333444",
        nombre="Juan",
        apellido="Gomez",
        numero_acta="A-2",
        resultado=ResultadoAtencion.DERIVADO,
        cantidad_lentes=0,
    )
    workflow.generar_cierre_diario(
        jornada,
        responsable="Coordinacion",
        cantidad_atenciones_registradas=2,
        cantidad_lentes_entregados_dia=0,
        cantidad_casos_laboratorio_reportados=0,
    )
    client.force_login(user)

    response = client.get(reverse("vpsl_jornada_detail", kwargs={"pk": jornada.pk}))

    html = response.content.decode()
    assert response.status_code == 200
    assert "No requiere anteojos" in html
    assert "Derivados" in html
    assert "vpsl-cierre-summary" in html


def test_itinerario_exporta_csv_con_jornadas(client):
    user = get_user_model().objects.create_superuser(
        username="vpsl-export-itinerario",
        email="vpsl-export-itinerario@example.com",
        password="testpass123",
    )
    sede = crear_sede(nombre="Escuela export", localidad="LA PLATA")
    itinerario = crear_itinerario(sedes=[sede])
    jornada = crear_jornada(
        itinerario=itinerario,
        fecha=date(2026, 5, 3),
        sede_vpsl=sede,
    )
    RegistroNominalVPSL.objects.create(
        jornada=jornada,
        dni="12345678",
        nombre="Ana",
        apellido="Perez",
        numero_acta="A-1",
        resultado=ResultadoAtencion.NO_REQUIERE,
        cantidad_lentes=0,
        validado_renaper=True,
    )
    client.force_login(user)

    response = client.get(
        reverse("vpsl_itinerario_export", kwargs={"pk": itinerario.pk})
    )

    content = b"".join(response.streaming_content).decode("utf-8")
    assert response.status_code == 200
    assert "Codigo itinerario;Provincia;Estado itinerario" in content
    assert "Sedes tentativas" not in content
    assert itinerario.codigo in content
    assert "Escuela export" in content
    assert ";1;" in content


def test_jornada_exporta_csv_con_registros(client):
    user = get_user_model().objects.create_superuser(
        username="vpsl-export-jornada",
        email="vpsl-export-jornada@example.com",
        password="testpass123",
    )
    jornada = crear_jornada(sede="Escuela jornada export")
    RegistroNominalVPSL.objects.create(
        jornada=jornada,
        dni="22333444",
        nombre="Luis",
        apellido="Gomez",
        genero="Masculino",
        numero_acta="A-2",
        resultado=ResultadoAtencion.ENTREGADO_DIA,
        cantidad_lentes=1,
        validado_renaper=True,
    )
    client.force_login(user)

    response = client.get(reverse("vpsl_jornada_export", kwargs={"pk": jornada.pk}))

    content = b"".join(response.streaming_content).decode("utf-8")
    assert response.status_code == 200
    assert "Itinerario;Provincia;Jornada fecha" in content
    assert "Gomez" in content
    assert "Masculino" in content
    assert "Entregado en el dia" in content


def test_sedes_autocomplete_filtra_por_provincia_y_busqueda(client):
    user = get_user_model().objects.create_superuser(
        username="vpsl-autocomplete",
        email="vpsl-autocomplete@example.com",
        password="testpass123",
    )
    provincia_ba = Provincia.objects.create(nombre="Buenos Aires")
    crear_sede(
        jurisdiccion="Buenos Aires",
        nombre="Escuela Primaria 1",
        cueanexo="BA001",
        localidad="LA PLATA",
    )
    crear_sede(
        jurisdiccion="Buenos Aires",
        nombre="Escuela Primaria 3",
        cueanexo="BA003",
        localidad="QUILMES",
    )
    crear_sede(
        jurisdiccion="Cordoba",
        nombre="Escuela Primaria 2",
        cueanexo="CBA001",
    )
    client.force_login(user)

    response = client.get(
        reverse("vpsl_sedes_autocomplete"),
        {"provincia": provincia_ba.pk, "localidad": "LA PLATA", "q": "primaria"},
    )

    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["cueanexo"] == "BA001"
    assert response.json()["pagination"]["more"] is False


def test_sedes_autocomplete_excluye_ids_solicitados(client):
    user = get_user_model().objects.create_superuser(
        username="vpsl-autocomplete-exclude",
        email="vpsl-autocomplete-exclude@example.com",
        password="testpass123",
    )
    provincia = Provincia.objects.create(nombre="Cordoba")
    sede_excluida = crear_sede(
        jurisdiccion="Cordoba",
        localidad="Centro",
        nombre="Escuela Excluida",
        cueanexo="CBA100",
    )
    sede_visible = crear_sede(
        jurisdiccion="Cordoba",
        localidad="Centro",
        nombre="Escuela Visible",
        cueanexo="CBA101",
    )
    client.force_login(user)

    response = client.get(
        reverse("vpsl_sedes_autocomplete"),
        {
            "q": "escuela",
            "provincia": provincia.pk,
            "exclude": [str(sede_excluida.pk)],
        },
    )

    assert response.status_code == 200
    ids = [item["id"] for item in response.json()["results"]]
    assert sede_visible.pk in ids
    assert sede_excluida.pk not in ids


def test_sedes_autocomplete_pagina_de_a_50(client):
    user = get_user_model().objects.create_superuser(
        username="vpsl-autocomplete-page",
        email="vpsl-autocomplete-page@example.com",
        password="testpass123",
    )
    provincia = Provincia.objects.create(nombre="Cordoba")
    for index in range(55):
        crear_sede(
            jurisdiccion="Cordoba",
            localidad="Centro",
            nombre=f"Escuela Paginada {index:02d}",
            cueanexo=f"CBAP{index:03d}",
        )
    client.force_login(user)

    response_page_1 = client.get(
        reverse("vpsl_sedes_autocomplete"),
        {"q": "Paginada", "provincia": provincia.pk, "page": 1},
    )
    response_page_2 = client.get(
        reverse("vpsl_sedes_autocomplete"),
        {"q": "Paginada", "provincia": provincia.pk, "page": 2},
    )

    assert response_page_1.status_code == 200
    assert response_page_2.status_code == 200
    assert len(response_page_1.json()["results"]) == 50
    assert response_page_1.json()["pagination"]["more"] is True
    assert len(response_page_2.json()["results"]) == 5
    assert response_page_2.json()["pagination"]["more"] is False


def test_sedes_autocomplete_sin_texto_devuelve_primera_pagina_de_50(client):
    user = get_user_model().objects.create_superuser(
        username="vpsl-autocomplete-empty",
        email="vpsl-autocomplete-empty@example.com",
        password="testpass123",
    )
    provincia = Provincia.objects.create(nombre="Cordoba")
    for index in range(55):
        crear_sede(
            jurisdiccion="Cordoba",
            localidad="Centro",
            nombre=f"Escuela Sin Texto {index:02d}",
            cueanexo=f"CBAS{index:03d}",
        )
    client.force_login(user)

    response = client.get(
        reverse("vpsl_sedes_autocomplete"),
        {"provincia": provincia.pk, "page": 1},
    )

    assert response.status_code == 200
    assert len(response.json()["results"]) == 50
    assert response.json()["pagination"]["more"] is True


def test_consultar_renaper_vpsl_devuelve_datos_normalizados(client, mocker):
    user = get_user_model().objects.create_superuser(
        username="vpsl-renaper",
        email="vpsl-renaper@example.com",
        password="testpass123",
    )
    client.force_login(user)
    renaper = mocker.patch(
        "ver_para_ser_libre.views.ComedorService.obtener_datos_ciudadano_desde_renaper",
        return_value={
            "success": True,
            "message": "Datos obtenidos desde RENAPER.",
            "data": {
                "documento": 12345678,
                "nombre": "Ana",
                "apellido": "Perez",
                "genero": "Femenino",
                "sexo": "F",
                "fecha_nacimiento": "2016-05-01",
            },
            "datos_api": {"id": "raw"},
        },
    )

    response = client.get(
        reverse("vpsl_renaper_consultar"), {"dni": "12345678", "sexo": "F"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["dni"] == "12345678"
    assert body["data"]["nombre"] == "Ana"
    assert body["data"]["apellido"] == "Perez"
    assert body["data"]["sexo"] == "F"
    assert body["data"]["genero"] == "Femenino"
    assert body["data"]["fecha_nacimiento"] == "2016-05-01"
    renaper.assert_called_once_with("12345678", sexo="F")


def test_consultar_renaper_vpsl_normaliza_sexo_display_si_viene_codigo(client, mocker):
    user = get_user_model().objects.create_superuser(
        username="vpsl-renaper-sexo-display",
        email="vpsl-renaper-sexo-display@example.com",
        password="testpass123",
    )
    client.force_login(user)
    mocker.patch(
        "ver_para_ser_libre.views.ComedorService.obtener_datos_ciudadano_desde_renaper",
        return_value={
            "success": True,
            "data": {
                "documento": 12345678,
                "nombre": "Juan",
                "apellido": "Perez",
                "sexo": "M",
                "fechaNacimiento": "01/05/2016",
            },
            "datos_api": {},
        },
    )

    response = client.get(
        reverse("vpsl_renaper_consultar"), {"dni": "12345678", "sexo": "M"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["sexo"] == "M"
    assert body["data"]["genero"] == "Masculino"
    assert body["data"]["fecha_nacimiento"] == "01/05/2016"


@pytest.mark.parametrize(
    ("codigo_renaper", "sexo_esperado", "display_esperado"),
    [
        ("1", "F", "Femenino"),
        ("2", "M", "Masculino"),
        ("01", "F", "Femenino"),
        ("02", "M", "Masculino"),
    ],
)
def test_consultar_renaper_vpsl_normaliza_codigos_numericos_de_sexo(
    client,
    mocker,
    codigo_renaper,
    sexo_esperado,
    display_esperado,
):
    user = get_user_model().objects.create_superuser(
        username=f"vpsl-renaper-sexo-{codigo_renaper}",
        email=f"vpsl-renaper-sexo-{codigo_renaper}@example.com",
        password="testpass123",
    )
    client.force_login(user)
    mocker.patch(
        "ver_para_ser_libre.views.ComedorService.obtener_datos_ciudadano_desde_renaper",
        return_value={
            "success": True,
            "data": {
                "documento": 12345678,
                "nombre": "Persona",
                "apellido": "Renaper",
                "sexo": codigo_renaper,
            },
            "datos_api": {},
        },
    )

    response = client.get(
        reverse("vpsl_renaper_consultar"),
        {"dni": "12345678", "sexo": sexo_esperado},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["sexo"] == sexo_esperado
    assert body["data"]["genero"] == display_esperado


def test_consultar_renaper_vpsl_registro_usa_ciudadano_existente_sin_renaper(
    client, mocker
):
    user = get_user_model().objects.create_superuser(
        username="vpsl-renaper-ciudadano-existente",
        email="vpsl-renaper-ciudadano-existente@example.com",
        password="testpass123",
    )
    ciudadano = crear_ciudadano_validado(documento=12345678)
    renaper = mocker.patch(
        "comedores.services.comedor_service.impl.ComedorService.obtener_datos_ciudadano_desde_renaper"
    )
    client.force_login(user)

    response = client.get(
        reverse("vpsl_renaper_consultar"),
        {"dni": "12345678", "sexo": "F", "registro_nominal": "1"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ciudadano_created"] is False
    assert body["data"]["ciudadano_id"] == ciudadano.pk
    assert body["data"]["nombre"] == "Ana"
    assert body["data"]["sexo"] == "F"
    renaper.assert_not_called()


def test_consultar_renaper_vpsl_registro_consulta_renaper_sin_crear_ciudadano(
    client, mocker
):
    user = get_user_model().objects.create_superuser(
        username="vpsl-renaper-crea-ciudadano",
        email="vpsl-renaper-crea-ciudadano@example.com",
        password="testpass123",
    )
    renaper = mocker.patch(
        "comedores.services.comedor_service.impl.ComedorService.obtener_datos_ciudadano_desde_renaper",
        return_value={
            "success": True,
            "message": "Datos obtenidos desde RENAPER.",
            "data": {
                "apellido": "Gomez",
                "nombre": "Juan",
                "fecha_nacimiento": date(2010, 1, 10),
                "documento": 22333444,
                "tipo_documento": Ciudadano.DOCUMENTO_DNI,
                "sexo": "M",
                "origen_dato": "renaper",
            },
            "datos_api": {"origen": "renaper"},
        },
    )
    client.force_login(user)

    response = client.get(
        reverse("vpsl_renaper_consultar"),
        {"dni": "22333444", "sexo": "M", "registro_nominal": "1"},
    )

    assert response.status_code == 200
    body = response.json()
    assert not Ciudadano.objects.filter(documento=22333444).exists()
    assert body["ciudadano_created"] is False
    assert body["ciudadano_pendiente_creacion"] is True
    assert body["data"]["nombre"] == "Juan"
    assert body["data"]["sexo"] == "M"
    renaper.assert_called_once_with("22333444", sexo="M")


def test_consultar_renaper_vpsl_registro_bloquea_duplicado_en_itinerario(client):
    user = get_user_model().objects.create_superuser(
        username="vpsl-renaper-duplicado",
        email="vpsl-renaper-duplicado@example.com",
        password="testpass123",
    )
    crear_ciudadano_validado(documento=12345678)
    itinerario = crear_itinerario()
    jornada_existente = crear_jornada(
        itinerario=itinerario,
        fecha=date(2026, 5, 2),
        estado=EstadoJornada.HABILITADA,
    )
    jornada_nueva = crear_jornada(
        itinerario=itinerario,
        fecha=date(2026, 5, 3),
        estado=EstadoJornada.HABILITADA,
    )
    RegistroNominalVPSL.objects.create(
        jornada=jornada_existente,
        dni="12345678",
        sexo="F",
        nombre="Ana",
        apellido="Perez",
        numero_acta="A-1",
        resultado=ResultadoAtencion.NO_REQUIERE,
        cantidad_lentes=0,
    )
    client.force_login(user)

    response = client.get(
        reverse("vpsl_renaper_consultar"),
        {
            "dni": "12345678",
            "sexo": "F",
            "registro_nominal": "1",
            "jornada": str(jornada_nueva.pk),
        },
    )

    assert response.status_code == 409
    body = response.json()
    assert body["success"] is False
    assert "ya tiene un registro nominal" in body["message"]


def test_registro_create_guarda_y_continua_con_datos_de_jornada(client):
    user = get_user_model().objects.create_superuser(
        username="vpsl-registro",
        email="vpsl-registro@example.com",
        password="testpass123",
    )
    jornada = crear_jornada(estado=EstadoJornada.HABILITADA)
    ciudadano = crear_ciudadano_validado(documento=12345678)
    client.force_login(user)

    response = client.post(
        reverse("vpsl_registro_create", kwargs={"jornada_pk": jornada.pk}),
        {
            "dni": "12345678",
            "sexo": "F",
            "nombre": "Ana",
            "apellido": "Perez",
            "edad": "10",
            "genero": "Femenino",
            "telefono": "221111111",
            "escuela_sede": "No debe persistir",
            "numero_acta": "A-101",
            "numero_sobre": "",
            "fecha_atencion": "2026-01-01",
            "prescripcion": "",
            "resultado": ResultadoAtencion.NO_REQUIERE,
            "cantidad_lentes": "0",
            "observaciones": "",
            "renaper_estado": "validado",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse(
        "vpsl_registro_create", kwargs={"jornada_pk": jornada.pk}
    )
    registro = RegistroNominalVPSL.objects.get(numero_acta="A-101")
    assert registro.fecha_atencion == date(2026, 1, 1)
    assert registro.escuela_sede == jornada.sede
    assert registro.validado_renaper is True
    assert registro.datos_renaper["ciudadano_id"] == ciudadano.pk
    assert registro.datos_renaper["origen_validacion"] == "ciudadanos"
    jornada.refresh_from_db()
    assert jornada.estado == EstadoJornada.EN_PROGRESO


def test_registro_create_sugiere_numero_acta_incremental_editable(client):
    user = get_user_model().objects.create_superuser(
        username="vpsl-registro-acta-incremental",
        email="vpsl-registro-acta-incremental@example.com",
        password="testpass123",
    )
    jornada = crear_jornada(estado=EstadoJornada.HABILITADA)
    client.force_login(user)
    url = reverse("vpsl_registro_create", kwargs={"jornada_pk": jornada.pk})

    response = client.get(url)

    assert response.status_code == 200
    assert 'name="numero_acta"' in response.content.decode()
    assert 'value="-1"' in response.content.decode()

    RegistroNominalVPSL.objects.create(
        jornada=jornada,
        dni="11111111",
        nombre="Ana",
        apellido="Perez",
        numero_acta="200-1",
        resultado=ResultadoAtencion.NO_REQUIERE,
        cantidad_lentes=0,
    )
    response = client.get(url)

    assert response.status_code == 200
    assert 'value="200-2"' in response.content.decode()

    RegistroNominalVPSL.objects.create(
        jornada=jornada,
        dni="22222222",
        nombre="Luis",
        apellido="Gomez",
        numero_acta="999-20",
        resultado=ResultadoAtencion.NO_REQUIERE,
        cantidad_lentes=0,
    )
    response = client.get(url)

    assert response.status_code == 200
    assert 'value="200-3"' in response.content.decode()


def test_registro_form_inicializa_numero_acta_con_jornada():
    jornada = crear_jornada(estado=EstadoJornada.HABILITADA)

    form = RegistroNominalVPSLForm(jornada=jornada)

    assert form["numero_acta"].value() == "-1"

    RegistroNominalVPSL.objects.create(
        jornada=jornada,
        dni="33333333",
        nombre="Ana",
        apellido="Perez",
        numero_acta="200-1",
        resultado=ResultadoAtencion.NO_REQUIERE,
        cantidad_lentes=0,
    )
    form = RegistroNominalVPSLForm(jornada=jornada)

    assert form["numero_acta"].value() == "200-2"


def test_registro_create_no_permite_persona_duplicada_en_itinerario(client):
    user = get_user_model().objects.create_superuser(
        username="vpsl-registro-duplicado",
        email="vpsl-registro-duplicado@example.com",
        password="testpass123",
    )
    ciudadano = crear_ciudadano_validado(documento=12345678)
    itinerario = crear_itinerario()
    jornada_existente = crear_jornada(
        itinerario=itinerario,
        fecha=date(2026, 5, 2),
        estado=EstadoJornada.HABILITADA,
    )
    jornada_nueva = crear_jornada(
        itinerario=itinerario,
        fecha=date(2026, 5, 3),
        estado=EstadoJornada.HABILITADA,
    )
    RegistroNominalVPSL.objects.create(
        jornada=jornada_existente,
        dni=str(ciudadano.documento),
        sexo="F",
        nombre="Ana",
        apellido="Perez",
        numero_acta="A-1",
        resultado=ResultadoAtencion.NO_REQUIERE,
        cantidad_lentes=0,
    )
    client.force_login(user)

    response = client.post(
        reverse("vpsl_registro_create", kwargs={"jornada_pk": jornada_nueva.pk}),
        {
            "dni": "12345678",
            "sexo": "F",
            "nombre": "Ana",
            "apellido": "Perez",
            "edad": "10",
            "genero": "Femenino",
            "telefono": "",
            "escuela_sede": "No debe persistir",
            "numero_acta": "A-2",
            "numero_sobre": "",
            "fecha_atencion": "2026-01-01",
            "prescripcion": "",
            "resultado": ResultadoAtencion.NO_REQUIERE,
            "cantidad_lentes": "0",
            "observaciones": "",
            "renaper_estado": "validado",
        },
    )

    assert response.status_code == 200
    assert "ya tiene un registro nominal" in response.content.decode()
    assert (
        RegistroNominalVPSL.objects.filter(
            jornada__itinerario=itinerario,
            dni="12345678",
        ).count()
        == 1
    )


def test_registro_create_crea_ciudadano_al_guardar_si_no_existe(client, mocker):
    user = get_user_model().objects.create_superuser(
        username="vpsl-registro-crea-ciudadano",
        email="vpsl-registro-crea-ciudadano@example.com",
        password="testpass123",
    )
    jornada = crear_jornada(estado=EstadoJornada.HABILITADA)
    sexo = Sexo.objects.create(sexo="Masculino")
    renaper = mocker.patch(
        "comedores.services.comedor_service.impl.ComedorService.obtener_datos_ciudadano_desde_renaper",
        return_value={
            "success": True,
            "message": "Datos obtenidos desde RENAPER.",
            "data": {
                "apellido": "Gomez",
                "nombre": "Juan",
                "fecha_nacimiento": date(2010, 1, 10),
                "documento": 22333444,
                "tipo_documento": Ciudadano.DOCUMENTO_DNI,
                "sexo": sexo.pk,
                "origen_dato": "renaper",
            },
            "datos_api": {"origen": "renaper"},
        },
    )
    client.force_login(user)

    response = client.post(
        reverse("vpsl_registro_create", kwargs={"jornada_pk": jornada.pk}),
        {
            "dni": "22333444",
            "sexo": "M",
            "nombre": "Juan",
            "apellido": "Gomez",
            "edad": "16",
            "genero": "Masculino",
            "telefono": "",
            "escuela_sede": "No debe persistir",
            "numero_acta": "A-102",
            "numero_sobre": "",
            "fecha_atencion": "2026-01-01",
            "prescripcion": "",
            "resultado": ResultadoAtencion.NO_REQUIERE,
            "cantidad_lentes": "0",
            "observaciones": "",
            "renaper_estado": "validado",
        },
    )

    assert response.status_code == 302
    ciudadano = Ciudadano.objects.get(documento=22333444)
    registro = RegistroNominalVPSL.objects.get(numero_acta="A-102")
    assert registro.validado_renaper is True
    assert registro.datos_renaper["ciudadano_id"] == ciudadano.pk
    assert registro.datos_renaper["ciudadano_created"] is True
    assert registro.datos_renaper["origen_validacion"] == "renaper"
    renaper.assert_called_once_with("22333444", sexo="M")


def test_registro_create_precarga_fecha_de_jornada(client):
    user = get_user_model().objects.create_superuser(
        username="vpsl-registro-fecha",
        email="vpsl-registro-fecha@example.com",
        password="testpass123",
    )
    jornada = crear_jornada(estado=EstadoJornada.HABILITADA)
    client.force_login(user)

    response = client.get(
        reverse("vpsl_registro_create", kwargs={"jornada_pk": jornada.pk})
    )

    assert response.status_code == 200
    assert 'name="fecha_atencion" value="2026-05-02"' in response.content.decode()


def test_registro_create_usa_estilo_oscuro_para_campos_renaper_bloqueados(client):
    user = get_user_model().objects.create_superuser(
        username="vpsl-registro-renaper-style",
        email="vpsl-registro-renaper-style@example.com",
        password="testpass123",
    )
    jornada = crear_jornada(estado=EstadoJornada.HABILITADA)
    client.force_login(user)

    response = client.get(
        reverse("vpsl_registro_create", kwargs={"jornada_pk": jornada.pk})
    )

    assert response.status_code == 200
    html = response.content.decode()
    assert 'classList.toggle("bg-dark", readonly)' in html
    assert 'classList.toggle("text-white", readonly)' in html


def test_registro_create_muestra_genero_como_sexo_y_calcula_edad_renaper(client):
    user = get_user_model().objects.create_superuser(
        username="vpsl-registro-renaper-edad",
        email="vpsl-registro-renaper-edad@example.com",
        password="testpass123",
    )
    jornada = crear_jornada(estado=EstadoJornada.HABILITADA)
    client.force_login(user)

    response = client.get(
        reverse("vpsl_registro_create", kwargs={"jornada_pk": jornada.pk})
    )

    assert response.status_code == 200
    html = response.content.decode()
    assert 'for="id_genero">Sexo</label>' in html
    assert 'registro_nominal: "1"' in html
    assert "calcularEdadRenaper(data.fecha_nacimiento)" in html
    assert "No verificar RENAPER" not in html
    assert 'name="prescripcion"' in html
    assert 'id="id_prescripcion"' in html
    assert "diagnostico 1" in html
    assert 'max="2"' in html
    assert "syncCantidadLentes" in html
    assert 'name="primera_vez_anteojos"' in html
    assert html.index('name="adjunto"') < html.index('name="primera_vez_anteojos"')
    assert html.index('name="primera_vez_anteojos"') < html.index(
        'name="observaciones"'
    )


def test_sede_delete_es_logico(client):
    user = get_user_model().objects.create_superuser(
        username="vpsl-sede-delete",
        email="vpsl-sede-delete@example.com",
        password="testpass123",
    )
    sede = crear_sede()
    client.force_login(user)

    response = client.post(reverse("vpsl_sede_delete", kwargs={"pk": sede.pk}))

    assert response.status_code == 302
    assert not SedeVPSL.objects.filter(pk=sede.pk).exists()
    assert SedeVPSL.all_objects.filter(pk=sede.pk, deleted_at__isnull=False).exists()
