from django.http import JsonResponse
from django.views.decorators.http import require_GET
from ciudadanos.models import Ciudadano


@require_GET
def buscar_ciudadanos(request):
    query = request.GET.get("q", "").strip()
    exclude_id = request.GET.get("exclude_id")

    ciudadanos = Ciudadano.buscar_por_documento(
        query, max_results=10, exclude_id=exclude_id
    ).values("id", "nombre", "apellido", "documento")

    results = [
        {"id": c["id"], "text": f"{c['nombre']} {c['apellido']} ({c['documento']})"}
        for c in ciudadanos
    ]

    return JsonResponse({"results": results})
