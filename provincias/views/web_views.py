from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from django.shortcuts import redirect
from django.contrib.auth.models import User
from provincias.models import Proyecto, AnexoSocioProductivo
from provincias.forms import (
    LineaDeAccionForm,
    ProyectoForm,
    AnexoSocioProductivoForm,
    PersonaJuridicaForm,
    PersonaFisicaForm,
    DiagnosticoJuridicaForm,
    DiagnosticoFisicaForm,
)


class ProyectoCreateView(CreateView):
    model = Proyecto
    form_class = ProyectoForm
    template_name = "proyecto_form.html"

    def form_valid(self, form):
        form.instance.creador = User.objects.get(pk=self.request.user.id)
        tipo_anexo = form.cleaned_data["tipo_anexo"]
        if tipo_anexo == "SOCIO_PRODUCTIVO":
            return redirect("anexo_create")
        elif tipo_anexo == "FORMACION":
            return redirect("formacion_create")

        return super().form_valid(form)


class ProyectoListView(ListView):
    model = Proyecto
    template_name = "proyecto_list.html"
    context_object_name = "proyectos"
    paginate_by = 10  # Paginación de 10 elementos por página


class ProyectoUpdateView(UpdateView):
    model = Proyecto
    form_class = ProyectoForm
    template_name = "proyecto_form.html"  # FIXME:


class ProyectoDeleteView(DeleteView):
    model = Proyecto
    template_name = "proyecto_confirm_delete.html"
    success_url = reverse_lazy("proyecto_list")


class AnexoSocioProductivoCreateView(CreateView):
    model = AnexoSocioProductivo
    form_class = AnexoSocioProductivoForm
    template_name = "anexo_socio_productivo_form.html"
    success_url = reverse_lazy("datos_proyecto_create")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["juridica_form"] = PersonaJuridicaForm(self.request.POST)
            context["fisica_form"] = PersonaFisicaForm(self.request.POST)
            context["persona_juridica_form"] = PersonaJuridicaForm(self.request.POST)
            context["linea_de_accion_form"] = LineaDeAccionForm(self.request.POST)
            context["diagnostico_juridica_form"] = DiagnosticoJuridicaForm(
                self.request.POST
            )
            context["diagnostico_fisica_form"] = DiagnosticoFisicaForm(
                self.request.POST
            )
        else:
            context["juridica_form"] = PersonaJuridicaForm()
            context["fisica_form"] = PersonaFisicaForm()
            context["persona_juridica_form"] = PersonaJuridicaForm()
            context["linea_de_accion_form"] = LineaDeAccionForm()
            context["diagnostico_juridica_form"] = DiagnosticoJuridicaForm()
            context["diagnostico_fisica_form"] = DiagnosticoFisicaForm()

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        juridica_form = context["juridica_form"]
        fisica_form = context["fisica_form"]
        if form.cleaned_data["tipo_persona"] == "juridica" and juridica_form.is_valid():
            juridica = juridica_form.save()
            form.instance.persona_juridica = juridica
        elif form.cleaned_data["tipo_persona"] == "humana" and fisica_form.is_valid():
            fisica = fisica_form.save()
            form.instance.persona_fisica = fisica
        else:
            return self.form_invalid(form)
        return super().form_valid(form)
