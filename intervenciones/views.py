from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, DeleteView, UpdateView, TemplateView
from comedores.services.comedor_service import ComedorService
from intervenciones.models.intervenciones import Intervencion, SubIntervencion, TipoIntervencion, EstadosIntervencion, TipoDestinatario
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

        context["tipos_intervencion"] = TipoIntervencion.objects.all()
        context["destinatarios"] = TipoDestinatario.objects.all()
        context["intervenciones"] = intervenciones
        context["object"] = comedor
        context["cantidad_intervenciones"] = cantidad_intervenciones
        return context


class IntervencionCreateView(CreateView):
    model = Intervencion
    form_class = IntervencionForm
    template_name = "intervencion_form.html"

    def form_valid(self, form):
        form.instance.comedor_id = self.kwargs["pk"]
        field_mapping = {
            "tipo_intervencion": TipoIntervencion,
            "subintervencion": SubIntervencion,
            "estado": EstadosIntervencion,
            "destinatario": "Destinatario",
            "fecha": "Fecha",
            "forma_contacto": "Forma de Contacto",
            "observaciones": "Descripción",
            "tiene_documentacion": "Documentación Adjunta",
        }

        for field, model in field_mapping.items():
            if isinstance(model, str):
                setattr(form.instance, field, form.cleaned_data[field])
            else:
                # Asegúrate de que el valor sea un ID antes de buscar el objeto
                value = form.cleaned_data[field]
                if isinstance(value, model):
                    value = value.id
                setattr(form.instance, field, model.objects.get(id=value))
        form.instance.save()
        return redirect(reverse("comedor_intervencion_ver", kwargs={"pk": self.kwargs["pk"]}))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener el comedor asociado
        comedor = ComedorService.get_comedor(self.kwargs["pk"])
        context["object"] = comedor
        return context

    def get_success_url(self):
        # Usa el pk del objeto recién creado para construir la URL
        return reverse("comedor_intervencion_ver", kwargs={"pk": self.object.pk})


class IntervencionUpdateView(UpdateView):
    model = Intervencion
    form_class = IntervencionForm
    template_name = "intervencion_form.html"

    def form_valid(self, form):
        pk = self.kwargs["pk2"]
        form.save()
        return redirect("comedor_intervencion_ver", pk=pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor = ComedorService.get_comedor(self.kwargs["pk2"])
        context["form"] = self.get_form()
        context["object"] = comedor
        return context


class IntervencionDeleteView(DeleteView):
    model = Intervencion
    template_name = "intervencion_confirm_delete.html"

    def form_valid(self, form):
        self.object.delete()
        return redirect("comedor_intervencion_ver", pk=self.kwargs["pk2"])