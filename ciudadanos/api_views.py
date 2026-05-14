from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from ciudadanos.models import Ciudadano


@require_GET
def buscar_ciudadanos(request):
    query = request.GET.get("q", "").strip()
    exclude_id = request.GET.get("exclude_id")

    if not query or len(query) < 3:
        return JsonResponse({"results": []})

    # Búsqueda por documento (comportamiento original para dígitos largos)
    if len(query) >= 7 and query.isdigit():
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
        qs = qs.only(
            "id", "nombre", "apellido", "documento", "tipo_registro_identidad"
        ).order_by("apellido", "nombre")[:10]

    results = []
    for c in qs.values(
        "id", "nombre", "apellido", "documento", "tipo_registro_identidad"
    ):
        if c["tipo_registro_identidad"] == Ciudadano.TIPO_REGISTRO_SIN_DNI:
            label = f"{c['nombre']} {c['apellido']} (Sin DNI)"
        else:
            label = f"{c['nombre']} {c['apellido']} ({c['documento'] or '-'})"
        results.append({"id": c["id"], "text": label})

    return JsonResponse({"results": results})
