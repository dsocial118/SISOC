from django.shortcuts import render, get_object_or_404
from acompanamientos.models.acompanamiento import InformacionRelevante, Prestacion
from admisiones.models.admisiones import Admision
from comedores.models.comedor import Comedor

def detalle_acompanamiento(request, comedor_id):
    comedor = get_object_or_404(Comedor, pk=comedor_id)
    info_relevante = InformacionRelevante.objects.filter(comedor=comedor).first()
    prestaciones = Prestacion.objects.filter(comedor=comedor)

    return render(
        request,
        "acompañamiento_detail.html",
        {"comedor": comedor, "info_relevante": info_relevante, "prestaciones": prestaciones},
    )

def lista_comedores_acompanamiento(request):
    admisiones = Admision.objects.filter(estado__nombre="Test")
    return render(request, "lista_comedores.html", {"admisiones": admisiones})