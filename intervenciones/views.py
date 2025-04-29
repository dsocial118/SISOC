# intervenciones/views.py
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, DeleteView, UpdateView, TemplateView
from comedores.services.comedor_service import ComedorService
from intervenciones.models.intervenciones import Intervencion, SubIntervencion
from intervenciones.forms import IntervencionForm



@csrf_exempt
def sub_estados_intervenciones_ajax(request):
    request_id = request.GET.get("id")
    if request_id:
        sub_estados = SubIntervencion.objects.filter(tipo_intervencion=request_id)
    else:
        sub_estados = SubIntervencion.objects.all()

    data = [
        {"id": sub_estado.id, "text": sub_estado.nombre} for sub_estado in sub_estados
    ]
    return JsonResponse(data, safe=False)


class IntervencionDetail(TemplateView):
    template_name = "intervencion_detail.html"
    model = Intervencion

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor = ComedorService.get_comedor(self.kwargs["pk"])
        intervenciones, cantidad_intervenciones = (
            ComedorService.detalle_de_intervencion(self.kwargs)
        )
        intervenciones = Intervencion.objects.filter(comedor=comedor)
        fecha = self.request.GET.get("fecha")
        tipo_intervencion = self.request.GET.get("tipo_intervencion")
        destinatario = self.request.GET.get("destinatario")

        if fecha:
            intervenciones = intervenciones.filter(fecha__date=fecha)
        if tipo_intervencion:
            intervenciones = intervenciones.filter(tipo_intervencion_id=tipo_intervencion)
        if destinatario:
            intervenciones = intervenciones.filter(destinatario__icontains=destinatario)

        context["intervenciones"] = intervenciones
        context["object"] = comedor
        context["cantidad_intervenciones"] = cantidad_intervenciones
        return context


class IntervencionCreateView(CreateView):
    model = Intervencion
    template_name = "intervencion_form.html"
    form_class = IntervencionForm

    def form_valid(self, form):
        # Asociar la intervención con el comedor correspondiente
        form.instance.comedor_id = self.kwargs["pk"]
        form.save()
        # Redirigir al detalle de las intervenciones del comedor
        return redirect(reverse("comedor_intervencion_ver", kwargs={"pk": self.kwargs["pk"]}))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener el comedor asociado
        comedor = ComedorService.get_comedor(self.kwargs["pk"])
        context["object"] = comedor
        return context


class IntervencionUpdateView(UpdateView):
    model = Intervencion
    form_class = IntervencionForm
    template_name = "intervenciones/intervencion_form.html"

    def form_valid(self, form):
        pk = self.kwargs["pk2"]
        form.save()
        return redirect("intervencion_ver", pk=pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor = ComedorService.get_comedor(self.kwargs["pk2"])
        context["form"] = self.get_form()
        context["object"] = comedor
        return context


class IntervencionDeleteView(DeleteView):
    model = Intervencion
    template_name = "intervenciones/intervencion_confirm_delete.html"

    def form_valid(self, form):
        self.object.delete()
        return redirect("intervencion_ver", pk=self.kwargs["pk2"])