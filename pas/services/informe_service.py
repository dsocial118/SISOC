import csv
from datetime import datetime, time

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from core.services.csv_export import build_csv_response
from pas.models import PasHistorialEstado, PasInforme, PasPersona


CSV_COLUMNS = [
    ("id_persona", "IdPersona"),
    ("apellido", "Apellido"),
    ("nombre", "Nombre"),
    ("dni", "DNI"),
    ("cuit", "CUIT"),
    ("provincia", "Provincia"),
    ("municipio", "Municipio"),
    ("estado_actual", "Estado actual"),
    ("avisos_actuales", "Avisos actuales"),
    ("fecha_creacion", "Fecha creacion"),
    ("fecha_ultimo_cambio", "Fecha ultimo cambio"),
    ("fecha_cambio", "Fecha cambio"),
    ("estado_anterior", "Estado anterior"),
    ("estado_resultante", "Estado resultante"),
    ("avisos_cambio", "Avisos cambio"),
    ("usuario_cambio", "Usuario cambio"),
]


def buscar_informes(request_get):
    query = (request_get.get("q") or "").strip()
    informes = PasInforme.objects.select_related("usuario").order_by("-creado", "-id")
    if not query:
        return informes

    filters = (
        Q(usuario__username__icontains=query)
        | Q(usuario__first_name__icontains=query)
        | Q(usuario__last_name__icontains=query)
    )
    numero = query.upper().replace("PAS-INF-", "").strip()
    if numero.isdigit():
        filters |= Q(id=int(numero))
    return informes.filter(filters)


def construir_resultado_informe(form):
    personas = _filtrar_personas(form.cleaned_data)
    cambios = _filtrar_cambios(form.cleaned_data, personas)
    modo = "cambios" if _usa_filtros_de_cambios(form.cleaned_data) else "registros"

    if modo == "cambios":
        personas = personas.filter(historial_estados__in=cambios).distinct()
        rows = [_row_cambio(cambio) for cambio in cambios]
    else:
        rows = [_row_persona(persona) for persona in personas]

    return {
        "modo": modo,
        "personas": personas,
        "cambios": cambios,
        "rows": rows,
        "total_personas": personas.count(),
        "total_cambios": cambios.count(),
    }


@transaction.atomic
def generar_informe_pas(form, usuario=None):
    resultado = construir_resultado_informe(form)
    informe = PasInforme.objects.create(
        usuario=usuario,
        filtros=_serializar_filtros(form.cleaned_data),
        modo=resultado["modo"],
        resultado=resultado["rows"],
        total_personas=resultado["total_personas"],
        total_cambios=resultado["total_cambios"],
    )
    informe.personas.set(resultado["personas"])
    informe.cambios.set(resultado["cambios"])
    return informe


def csv_response_for_informe(informe):
    response = build_csv_response(f"{informe.numero.lower()}.csv")
    writer = csv.writer(response)
    writer.writerow([label for _, label in CSV_COLUMNS])
    for row in informe.resultado:
        writer.writerow([row.get(key, "") for key, _ in CSV_COLUMNS])
    return response


def preview_payload(form, limit=50):
    resultado = construir_resultado_informe(form)
    return {
        "ok": True,
        "modo": resultado["modo"],
        "total": len(resultado["rows"]),
        "total_personas": resultado["total_personas"],
        "total_cambios": resultado["total_cambios"],
        "columns": [{"key": key, "label": label} for key, label in CSV_COLUMNS],
        "rows": resultado["rows"][:limit],
        "limit": limit,
    }


def errors_payload(form):
    return {
        "ok": False,
        "errors": {
            field: [str(error) for error in errors]
            for field, errors in form.errors.items()
        },
    }


def _filtrar_personas(cleaned_data):
    personas = (
        PasPersona.objects.select_related("provincia", "municipio", "estado")
        .prefetch_related("avisos", "historial_estados")
        .order_by("apellidos", "nombres", "id")
    )

    fecha_desde = cleaned_data.get("fecha_creacion_desde")
    fecha_hasta = cleaned_data.get("fecha_creacion_hasta")
    if fecha_desde:
        personas = personas.filter(fecha_creacion__gte=_inicio_dia(fecha_desde))
    if fecha_hasta:
        personas = personas.filter(fecha_creacion__lte=_fin_dia(fecha_hasta))

    if cleaned_data.get("estado_actual"):
        personas = personas.filter(estado=cleaned_data["estado_actual"])
    if cleaned_data.get("provincia"):
        personas = personas.filter(provincia=cleaned_data["provincia"])
    if cleaned_data.get("municipio"):
        personas = personas.filter(municipio=cleaned_data["municipio"])
    if cleaned_data.get("aviso_actual"):
        personas = personas.filter(avisos=cleaned_data["aviso_actual"])
    if cleaned_data.get("dni"):
        personas = personas.filter(dni=cleaned_data["dni"])
    if cleaned_data.get("id_persona"):
        personas = personas.filter(id_persona=cleaned_data["id_persona"])

    return personas.distinct()


def _filtrar_cambios(cleaned_data, personas):
    cambios = (
        PasHistorialEstado.objects.select_related(
            "persona",
            "persona__provincia",
            "persona__municipio",
            "persona__estado",
            "estado_anterior",
            "estado_nuevo",
            "usuario",
        )
        .prefetch_related("persona__avisos", "avisos_nuevos")
        .filter(persona__in=personas)
        .order_by("-fecha_cambio", "-id")
    )

    fecha_desde = cleaned_data.get("fecha_cambio_desde")
    fecha_hasta = cleaned_data.get("fecha_cambio_hasta")
    if fecha_desde:
        cambios = cambios.filter(fecha_cambio__gte=_inicio_dia(fecha_desde))
    if fecha_hasta:
        cambios = cambios.filter(fecha_cambio__lte=_fin_dia(fecha_hasta))
    if cleaned_data.get("estado_anterior"):
        cambios = cambios.filter(estado_anterior=cleaned_data["estado_anterior"])
    if cleaned_data.get("estado_nuevo"):
        cambios = cambios.filter(estado_nuevo=cleaned_data["estado_nuevo"])
    if cleaned_data.get("aviso_cambio"):
        cambios = cambios.filter(avisos_nuevos=cleaned_data["aviso_cambio"])

    usuario_cambio = (cleaned_data.get("usuario_cambio") or "").strip()
    if usuario_cambio:
        cambios = cambios.filter(
            Q(usuario__username__icontains=usuario_cambio)
            | Q(usuario__first_name__icontains=usuario_cambio)
            | Q(usuario__last_name__icontains=usuario_cambio)
        )

    return cambios.distinct()


def _row_persona(persona):
    ultimo = persona.historial_estados.order_by("-fecha_cambio", "-id").first()
    return {
        "id_persona": persona.id_persona,
        "apellido": persona.apellidos,
        "nombre": persona.nombres,
        "dni": persona.dni,
        "cuit": persona.cuit,
        "provincia": persona.provincia.nombre,
        "municipio": persona.municipio.nombre,
        "estado_actual": persona.estado.nombre,
        "avisos_actuales": _join_avisos(persona.avisos.all()),
        "fecha_creacion": _format_dt(persona.fecha_creacion),
        "fecha_ultimo_cambio": _format_dt(ultimo.fecha_cambio) if ultimo else "",
        "fecha_cambio": "",
        "estado_anterior": "",
        "estado_resultante": "",
        "avisos_cambio": "",
        "usuario_cambio": "",
    }


def _row_cambio(cambio):
    persona = cambio.persona
    return {
        "id_persona": persona.id_persona,
        "apellido": persona.apellidos,
        "nombre": persona.nombres,
        "dni": persona.dni,
        "cuit": persona.cuit,
        "provincia": persona.provincia.nombre,
        "municipio": persona.municipio.nombre,
        "estado_actual": persona.estado.nombre,
        "avisos_actuales": _join_avisos(persona.avisos.all()),
        "fecha_creacion": _format_dt(persona.fecha_creacion),
        "fecha_ultimo_cambio": _format_dt(
            persona.historial_estados.order_by("-fecha_cambio", "-id")
            .first()
            .fecha_cambio
        ),
        "fecha_cambio": _format_dt(cambio.fecha_cambio),
        "estado_anterior": (
            cambio.estado_anterior.nombre if cambio.estado_anterior else ""
        ),
        "estado_resultante": cambio.estado_nuevo.nombre,
        "avisos_cambio": _join_avisos(cambio.avisos_nuevos.all()),
        "usuario_cambio": _user_label(cambio.usuario),
    }


def _usa_filtros_de_cambios(cleaned_data):
    keys = (
        "fecha_cambio_desde",
        "fecha_cambio_hasta",
        "estado_anterior",
        "estado_nuevo",
        "aviso_cambio",
        "usuario_cambio",
    )
    return any(cleaned_data.get(key) for key in keys)


def _serializar_filtros(cleaned_data):
    labels = {}
    for key, value in cleaned_data.items():
        if value in ("", None):
            continue
        if isinstance(value, (int, str)):
            labels[key] = value
        elif hasattr(value, "pk"):
            labels[key] = {"id": value.pk, "label": str(value)}
        elif hasattr(value, "isoformat"):
            labels[key] = value.isoformat()
        else:
            labels[key] = str(value)
    return labels


def _join_avisos(avisos):
    return " | ".join(str(aviso) for aviso in avisos)


def _user_label(user):
    if not user:
        return ""
    return user.get_full_name() or user.username


def _format_dt(value):
    if not value:
        return ""
    return timezone.localtime(value).strftime("%d/%m/%Y %H:%M")


def _inicio_dia(value):
    return timezone.make_aware(datetime.combine(value, time.min))


def _fin_dia(value):
    return timezone.make_aware(datetime.combine(value, time.max))
