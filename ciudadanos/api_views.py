from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from ciudadanos.models import Ciudadano


def _etiqueta_ciudadano(c):
    nombre = f"{c['nombre']} {c['apellido']}"
    if c["tipo_registro_identidad"] == Ciudadano.TIPO_REGISTRO_SIN_DNI:
        return f"{nombre} (Sin DNI)"
    if c["tipo_documento"] == Ciudadano.DOCUMENTO_PASAPORTE:
        numero = c["documento_pasaporte"] or c["documento"]
        return f"{nombre} (Pasaporte {numero})" if numero else f"{nombre} (-)"
    return f"{nombre} ({c['documento'] or '-'})"


def _buscar_por_pasaporte(query, exclude_id=None):
    qs = Ciudadano.objects.filter(
        tipo_documento=Ciudadano.DOCUMENTO_PASAPORTE,
        documento_pasaporte__istartswith=query,
    )
    if exclude_id:
        qs = qs.exclude(pk=exclude_id)
    return qs.order_by("apellido", "nombre")[:10]


@require_GET
def buscar_ciudadanos(request):
    query = request.GET.get("q", "").strip()
    exclude_id = request.GET.get("exclude_id")
    # Opcional: acota la búsqueda a un tipo de documento. Sin este parámetro el
    # endpoint mantiene su comportamiento histórico (lo consumen otras vistas).
    tipo_documento = request.GET.get("tipo_documento", "").strip()

    if not query or len(query) < 3:
        return JsonResponse({"results": []})

    if tipo_documento == Ciudadano.DOCUMENTO_PASAPORTE:
        qs = _buscar_por_pasaporte(query.upper().replace(" ", ""), exclude_id)
    elif len(query) >= 7 and query.isdigit():
        # Búsqueda por documento (comportamiento original para dígitos largos)
        qs = Ciudadano.buscar_por_documento(
            query, max_results=10, exclude_id=exclude_id
        )
    else:
        # Búsqueda por nombre/apellido o identificador_interno (para SIN_DNI)
        qs = Ciudadano.objects.filter(
            Q(apellido__icontains=query)
            | Q(nombre__icontains=query)
            | Q(identificador_interno__icontains=query)
        )
        if exclude_id:
            qs = qs.exclude(pk=exclude_id)
        qs = qs.order_by("apellido", "nombre")[:10]

    results = [
        {"id": c["id"], "text": _etiqueta_ciudadano(c)}
        for c in qs.values(
            "id",
            "nombre",
            "apellido",
            "documento",
            "documento_pasaporte",
            "tipo_documento",
            "tipo_registro_identidad",
        )
    ]

    return JsonResponse({"results": results})
