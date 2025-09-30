from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count
from core.services.advanced_filters import AdvancedFilterEngine
from centrodefamilia.models import (
    Responsable,
    Beneficiario,
    PadronBeneficiarios,
    BeneficiarioResponsable,
    BeneficiariosResponsablesRenaper,
)
from centrodefamilia.forms import BeneficiarioForm, ResponsableForm
from centrodefamilia.services.consulta_renaper import consultar_datos_renaper
from centrodefamilia.services.beneficiarios_filter_config import (
    FIELD_MAP as BENEFICIARIO_FILTER_MAP,
    FIELD_TYPES as BENEFICIARIO_FIELD_TYPES,
    TEXT_OPS as BENEFICIARIO_TEXT_OPS,
    NUM_OPS as BENEFICIARIO_NUM_OPS,
)
from centrodefamilia.services.responsables_filter_config import (
    FIELD_MAP as RESPONSABLE_FILTER_MAP,
    FIELD_TYPES as RESPONSABLE_FIELD_TYPES,
    TEXT_OPS as RESPONSABLE_TEXT_OPS,
    NUM_OPS as RESPONSABLE_NUM_OPS,
)
from django.db import transaction


def obtener_o_crear_responsable(responsable_data, usuario):
    """Busca responsable existente por DNI o crea uno nuevo"""
    dni = responsable_data.get("dni")
    if not dni:
        return None, None, False

    try:
        responsable_existente = Responsable.objects.get(dni=dni)
        responsable_form = ResponsableForm(
            responsable_data, instance=responsable_existente
        )
        if responsable_form.is_valid():
            responsable_form.save()
            return responsable_existente, responsable_form, False
        else:
            return None, responsable_form, False
    except Responsable.DoesNotExist:
        responsable_form = ResponsableForm(responsable_data)
        if responsable_form.is_valid():
            responsable = responsable_form.save(commit=False)
            responsable.creado_por = usuario
            responsable.save()
            return responsable, responsable_form, True
        return None, responsable_form, False


def crear_beneficiario(beneficiario_data, responsable, vinculo_parental, usuario):
    """Crea beneficiario y maneja actividades"""
    form = BeneficiarioForm(beneficiario_data)
    if not form.is_valid():
        return None, form

    beneficiario = form.save(commit=False)
    beneficiario.responsable = responsable
    beneficiario.creado_por = usuario

    if "actividad_preferida" in beneficiario_data:
        actividades = beneficiario_data["actividad_preferida"]
        beneficiario.actividad_preferida = (
            actividades if isinstance(actividades, list) else [actividades]
        )

    beneficiario.save()

    BeneficiarioResponsable.objects.create(
        beneficiario=beneficiario,
        responsable=responsable,
        vinculo_parental=vinculo_parental,
    )

    if "actividades_detalle" in beneficiario_data:
        form.save_m2m()

    return beneficiario, form


BENEFICIARIO_ADVANCED_FILTER = AdvancedFilterEngine(
    field_map=BENEFICIARIO_FILTER_MAP,
    field_types=BENEFICIARIO_FIELD_TYPES,
    allowed_ops={
        "text": BENEFICIARIO_TEXT_OPS,
        "number": BENEFICIARIO_NUM_OPS,
    },
)


RESPONSABLE_ADVANCED_FILTER = AdvancedFilterEngine(
    field_map=RESPONSABLE_FILTER_MAP,
    field_types=RESPONSABLE_FIELD_TYPES,
    allowed_ops={
        "text": RESPONSABLE_TEXT_OPS,
        "number": RESPONSABLE_NUM_OPS,
    },
)


def guardar_datos_renaper(request, persona, tipo, es_nuevo=True):
    """Usa datos cacheados de RENAPER o consulta si no están disponibles"""
    if not es_nuevo and tipo == "Responsable":
        return

    if hasattr(persona, "dni"):
        dni = persona.dni
        genero = persona.genero
    else:
        dni = persona.responsable.dni if hasattr(persona, "responsable") else None
        genero = persona.responsable.genero if hasattr(persona, "responsable") else None

    if not dni or not genero:
        return

    cache_key = f"{tipo.lower()}_{dni}_{genero}"
    datos_api = None

    if (
        "renaper_cache" in request.session
        and cache_key in request.session["renaper_cache"]
    ):
        datos_api = request.session["renaper_cache"][cache_key]
    else:
        renaper_resp = consultar_datos_renaper(dni, genero)
        if renaper_resp["success"]:
            datos_api = renaper_resp["datos_api"]

    if datos_api:
        dni_valor = datos_api.get("dni", dni)
        genero_valor = datos_api.get("genero", genero)
        BeneficiariosResponsablesRenaper.objects.update_or_create(
            dni=dni_valor,
            genero=genero_valor,
            tipo=tipo,
            defaults={
                "iD_TRAMITE_PRINCIPAL": datos_api.get("iD_TRAMITE_PRINCIPAL"),
                "iD_TRAMITE_TARJETA_REIMPRESA": datos_api.get(
                    "iD_TRAMITE_TARJETA_REIMPRESA"
                ),
                "ejemplar": datos_api.get("ejemplar"),
                "vencimiento": datos_api.get("vencimiento"),
                "emision": datos_api.get("emision"),
                "apellido": datos_api.get("apellido"),
                "nombres": datos_api.get("nombres"),
                "fechaNacimiento": datos_api.get("fechaNacimiento"),
                "cuil": datos_api.get("cuil"),
                "calle": datos_api.get("calle"),
                "numero": datos_api.get("numero"),
                "piso": datos_api.get("piso"),
                "departamento": datos_api.get("departamento"),
                "cpostal": datos_api.get("cpostal"),
                "barrio": datos_api.get("barrio"),
                "monoblock": datos_api.get("monoblock"),
                "ciudad": datos_api.get("ciudad"),
                "municipio": datos_api.get("municipio"),
                "provincia": datos_api.get("provincia"),
                "pais": datos_api.get("pais"),
                "codigoError": datos_api.get("codigoError"),
                "codigof": datos_api.get("codigof"),
                "mensaf": datos_api.get("mensaf"),
                "origenf": datos_api.get("origenf"),
                "fechaf": datos_api.get("fechaf"),
                "idciudadano": datos_api.get("idciudadano"),
                "nroError": datos_api.get("nroError"),
                "descripcionError": datos_api.get("descripcionError"),
            },
        )


def procesar_formularios(request, beneficiario_data, responsable_data):
    """Procesa ambos formularios y maneja RENAPER"""
    vinculo_parental = responsable_data.get("vinculo_parental")
    if not vinculo_parental:
        return None, None, None

    with transaction.atomic():
        responsable, responsable_form, es_responsable_nuevo = (
            obtener_o_crear_responsable(responsable_data, request.user)
        )
        if not responsable:
            return None, None, responsable_form

        beneficiario, beneficiario_form = crear_beneficiario(
            beneficiario_data, responsable, vinculo_parental, request.user
        )
        if not beneficiario:
            return None, beneficiario_form, responsable_form

        guardar_datos_renaper(request, responsable, "Responsable", es_responsable_nuevo)
        guardar_datos_renaper(request, beneficiario, "Beneficiario")

    return beneficiario, beneficiario_form, responsable_form


def separar_datos_post(request):
    """Separa datos POST por prefijo"""
    beneficiario_data, responsable_data = {}, {}
    for key, value_list in request.POST.lists():
        clean_key = (
            key.replace("beneficiario_", "")
            if key.startswith("beneficiario_")
            else key.replace("responsable_", "")
        )

        if clean_key == "actividades_detalle":
            value = value_list
        elif clean_key == "actividad_preferida":
            value = value_list
        else:
            value = value_list[0] if len(value_list) == 1 else value_list

        if key.startswith("beneficiario_"):
            beneficiario_data[clean_key] = value
        elif key.startswith("responsable_"):
            responsable_data[clean_key] = value
    return beneficiario_data, responsable_data


def generar_respuesta(
    request,
    beneficiario,
    beneficiario_form,
    responsable_form,
    beneficiario_data,
    template_name,
):
    """Genera respuesta apropiada según resultado"""
    if beneficiario:
        messages.success(request, "Datos cargados con éxito")
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "status": "success",
                    "message": "Preinscripción confirmada exitosamente",
                }
            )
        return redirect("beneficiarios_crear")

    errors = {}
    if beneficiario_form and not beneficiario_form.is_valid():
        errors["beneficiario"] = beneficiario_form.errors
    if responsable_form and not responsable_form.is_valid():
        errors["responsable"] = responsable_form.errors

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"status": "error", "errors": errors}, status=400)

    return render(
        request,
        template_name,
        {
            "form": beneficiario_form or BeneficiarioForm(beneficiario_data),
            "responsable_form": responsable_form or ResponsableForm(),
        },
    )


def manejar_request_beneficiarios(request, template_name):
    """Maneja todo el request de beneficiarios"""
    try:
        beneficiario_data, responsable_data = separar_datos_post(request)
        beneficiario, beneficiario_form, responsable_form = procesar_formularios(
            request, beneficiario_data, responsable_data
        )

        if beneficiario and "renaper_cache" in request.session:
            del request.session["renaper_cache"]
            request.session.modified = True

        return generar_respuesta(
            request,
            beneficiario,
            beneficiario_form,
            responsable_form,
            beneficiario_data,
            template_name,
        )

    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": f"Error al guardar: {str(e)}"}, status=500
        )


def buscar_responsable_renaper(request, dni, sexo):
    """Busca datos del responsable en RENAPER y cachea en sesión"""
    try:
        if not dni or not sexo:
            return JsonResponse(
                {"status": "error", "message": "Debe ingresar DNI y sexo"}, status=400
            )

        try:
            responsable_existente = Responsable.objects.get(dni=dni)
            cantidad_beneficiarios = responsable_existente.beneficiarios.count()
            data = {
                "nombre": responsable_existente.nombre,
                "apellido": responsable_existente.apellido,
                "genero": responsable_existente.genero,
                "fecha_nacimiento": (
                    responsable_existente.fecha_nacimiento.strftime("%Y-%m-%d")
                    if responsable_existente.fecha_nacimiento
                    else None
                ),
                "cuil": responsable_existente.cuil,
                "dni": responsable_existente.dni,
                "correo_electronico": responsable_existente.correo_electronico,
                "calle": responsable_existente.calle,
                "altura": responsable_existente.altura,
                "piso_vivienda": responsable_existente.piso_vivienda,
                "departamento_vivienda": responsable_existente.departamento_vivienda,
                "codigo_postal": responsable_existente.codigo_postal,
                "barrio": responsable_existente.barrio,
                "monoblock": responsable_existente.monoblock,
                "provincia": (
                    responsable_existente.provincia.id
                    if responsable_existente.provincia
                    else None
                ),
                "municipio": (
                    responsable_existente.municipio.id
                    if responsable_existente.municipio
                    else None
                ),
                "localidad": (
                    responsable_existente.localidad.id
                    if responsable_existente.localidad
                    else None
                ),
                "prefijo_celular": responsable_existente.prefijo_celular,
                "numero_celular": responsable_existente.numero_celular,
                "prefijo_telefono_fijo": responsable_existente.prefijo_telefono_fijo,
                "numero_telefono_fijo": responsable_existente.numero_telefono_fijo,
            }

            return JsonResponse(
                {
                    "status": "exists",
                    "data": data,
                    "cantidad_beneficiarios": cantidad_beneficiarios,
                    "message": f"Este Responsable ya tiene {cantidad_beneficiarios} beneficiario{'s' if cantidad_beneficiarios != 1 else ''} a su cargo",
                }
            )

        except Responsable.DoesNotExist:
            pass

        resultado = consultar_datos_renaper(dni, sexo)
        if not resultado["success"]:
            return JsonResponse(
                {
                    "status": "not_found",
                    "message": resultado.get("error", "No se encontró el Responsable"),
                }
            )

        if "renaper_cache" not in request.session:
            request.session["renaper_cache"] = {}

        cache_key = f"responsable_{dni}_{sexo}"
        request.session["renaper_cache"][cache_key] = resultado["datos_api"]
        request.session.modified = True

        return JsonResponse({"status": "possible", "data": resultado["data"]})

    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": f"Error interno del servidor: {str(e)}"},
            status=500,
        )


def buscar_cuil_beneficiario(request, cuil):
    """
    Busca CUIL en beneficiarios y padrón, consulta RENAPER y cachea.
    Siempre devuelve JSON.
    """
    try:
        if not cuil:
            return JsonResponse(
                {"status": "error", "message": "Debe ingresar un CUIL"}, status=400
            )

        if Beneficiario.objects.filter(cuil=cuil).exists():
            return JsonResponse(
                {
                    "status": "exists",
                    "message": "El CUIL ingresado ya se encuentra en el programa.",
                }
            )

        posible = PadronBeneficiarios.objects.filter(cuil=cuil).first()

        if not posible:
            return JsonResponse(
                {
                    "status": "not_found",
                    "message": "El CUIL ingresado no se encuentra en la base de datos",
                }
            )

        dni = posible.dni
        genero = posible.genero

        resultado = consultar_datos_renaper(dni, genero)

        if not resultado.get("success"):
            return JsonResponse(
                {
                    "status": "not_found",
                    "message": resultado.get(
                        "error", "No se encontraron datos en RENAPER"
                    ),
                }
            )

        datos_api = resultado.get("datos_api", {})

        if "renaper_cache" not in request.session:
            request.session["renaper_cache"] = {}

        cache_key = f"beneficiario_{dni}_{genero}"
        request.session["renaper_cache"][cache_key] = datos_api
        request.session.modified = True

        domicilio_parts = []
        if datos_api.get("calle"):
            domicilio_parts.append(datos_api.get("calle"))
        if datos_api.get("numero"):
            domicilio_parts.append(datos_api.get("numero"))
        if datos_api.get("piso"):
            domicilio_parts.append(f"Piso {datos_api.get('piso')}")
        if datos_api.get("departamento"):
            domicilio_parts.append(f"Depto {datos_api.get('departamento')}")

        data = {
            "nombre": datos_api.get("nombres", ""),
            "apellido": datos_api.get("apellido", ""),
            "genero": genero,
            "fecha_nacimiento": datos_api.get("fechaNacimiento", ""),
            "domicilio": " ".join(domicilio_parts),
            "cuil": datos_api.get("cuil", cuil),
            "dni": dni,
            "calle": datos_api.get("calle", ""),
            "altura": datos_api.get("numero"),
            "piso_vivienda": datos_api.get("piso") or None,
            "departamento_vivienda": datos_api.get("departamento") or None,
            "codigo_postal": datos_api.get("cpostal"),
            "barrio": datos_api.get("barrio") or None,
            "monoblock": datos_api.get("monoblock") or None,
            "provincia_tabla": posible.provincia_tabla or "",
            "municipio_tabla": posible.municipio_tabla or "",
            "provincia_api": datos_api.get("provincia") or "",
            "municipio_api": datos_api.get("municipio") or "",
            "localidad_api": datos_api.get("ciudad") or "",
        }

        return JsonResponse({"status": "possible", "data": data})

    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": f"Error al buscar CUIL: {str(e)}"},
            status=500,
        )


def get_beneficiarios_list_context():
    """Configuración para la lista de beneficiarios"""
    return {
        "table_headers": [
            {"title": "CUIL", "width": "12%"},
            {"title": "Apellido y Nombre", "width": "20%"},
            {"title": "DNI", "width": "10%"},
            {"title": "Género", "width": "8%"},
            {"title": "Responsable", "width": "20%"},
            {"title": "Provincia", "width": "15%"},
            {"title": "Municipio", "width": "15%"},
        ],
        "table_fields": [
            {"name": "cuil"},
            {"name": "apellido_nombre"},
            {"name": "dni"},
            {"name": "genero_display"},
            {"name": "responsable_nombre"},
            {"name": "provincia"},
            {"name": "municipio"},
        ],
        "table_actions": [
            {
                "url_name": "beneficiarios_detail",
                "type": "info",
                "label": "Ver",
                "class": "btn-sm",
            },
        ],
    }


def get_responsables_list_context():
    """Configuración para la lista de responsables"""
    return {
        "table_headers": [
            {"title": "CUIL", "width": "15%"},
            {"title": "Apellido y Nombre", "width": "25%"},
            {"title": "DNI", "width": "10%"},
            {"title": "Género", "width": "15%"},
            {"title": "Beneficiarios", "width": "10%"},
            {"title": "Provincia", "width": "15%"},
            {"title": "Municipio", "width": "10%"},
        ],
        "table_fields": [
            {"name": "cuil"},
            {"name": "apellido_nombre"},
            {"name": "dni"},
            {"name": "genero_display"},
            {"name": "cantidad_beneficiarios"},
            {"name": "provincia"},
            {"name": "municipio"},
        ],
        "table_actions": [
            {
                "url_name": "responsables_detail",
                "type": "info",
                "label": "Ver",
                "class": "btn-sm",
            },
        ],
    }


def prepare_beneficiarios_for_display(beneficiarios):
    """Agrega campos personalizados a beneficiarios"""
    for beneficiario in beneficiarios:
        beneficiario.apellido_nombre = f"{beneficiario.apellido}, {beneficiario.nombre}"
        beneficiario.genero_display = beneficiario.get_genero_display()
        beneficiario.responsable_nombre = (
            f"{beneficiario.responsable.apellido}, {beneficiario.responsable.nombre}"
        )


def prepare_responsables_for_display(responsables):
    """Agrega campos personalizados a responsables"""
    for responsable in responsables:
        responsable.apellido_nombre = f"{responsable.apellido}, {responsable.nombre}"
        responsable.genero_display = responsable.get_genero_display()
        responsable.vinculo_display = responsable.get_vinculo_parental_display()


def get_filtered_beneficiarios(request_or_get):
    """Aplica filtros combinables sobre el listado de beneficiarios."""

    base_qs = get_beneficiarios_queryset()
    return BENEFICIARIO_ADVANCED_FILTER.filter_queryset(base_qs, request_or_get)


def get_filtered_responsables(request_or_get):
    """Aplica filtros combinables sobre el listado de responsables."""

    base_qs = get_responsables_queryset()
    return RESPONSABLE_ADVANCED_FILTER.filter_queryset(base_qs, request_or_get)


def get_beneficiarios_queryset():
    """Query optimizada para beneficiarios"""
    return Beneficiario.objects.select_related(
        "responsable", "provincia", "municipio"
    ).order_by("-id", "apellido", "nombre")


def get_responsables_queryset():
    """Query optimizada para responsables"""
    return (
        Responsable.objects.annotate(cantidad_beneficiarios=Count("beneficiarios"))
        .select_related("provincia", "municipio")
        .order_by("-id", "apellido", "nombre")
    )


def get_responsable_detail_context(responsable):
    """Contexto para detalle de responsable"""
    return {
        "vinculos_beneficiarios": BeneficiarioResponsable.objects.filter(
            responsable=responsable
        ).select_related("beneficiario")
    }


def get_beneficiario_detail_queryset():
    """Query optimizada para detalle de beneficiario"""
    return Beneficiario.objects.select_related("responsable").prefetch_related(
        "actividades_detalle"
    )
