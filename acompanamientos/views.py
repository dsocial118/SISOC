from django.shortcuts import render, get_object_or_404
from acompanamientos.models.acompanamiento import InformacionRelevante, Prestacion
from admisiones.models.admisiones import Admision
from comedores.models.comedor import Comedor
from comedores.models.relevamiento import Relevamiento

def detalle_acompanamiento(request, comedor_id):
    comedor = get_object_or_404(Comedor, pk=comedor_id)
    info_relevante = InformacionRelevante.objects.filter(comedor=comedor).first()
    relevamiento = (
        Relevamiento.objects.filter(comedor=comedor)
        .order_by("-fecha_visita")
        .first()
    )
    prestacion = relevamiento.prestacion if relevamiento and relevamiento.prestacion else None
    dias = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]

    prestaciones_dias = []
    if prestacion:
        for dia in dias:
            prestaciones_dias.append({
                "dia": dia,
                "desayuno": getattr(prestacion, f"{dia}_desayuno_actual", "-"),
                "almuerzo": getattr(prestacion, f"{dia}_almuerzo_actual", "-"),
                "merienda": getattr(prestacion, f"{dia}_merienda_actual", "-"),
                "cena": getattr(prestacion, f"{dia}_cena_actual", "-"),
            })

    return render(
        request,
        "acompañamiento_detail.html",
        {
            "comedor": comedor,
            "info_relevante": info_relevante,
            "prestaciones_dias": prestaciones_dias,
        },
    )

def lista_comedores_acompanamiento(request):
    admisiones = Admision.objects.filter(estado__nombre="Test")
    return render(request, "lista_comedores.html", {"admisiones": admisiones})