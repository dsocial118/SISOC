from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import TemplateView, View
from django.views.generic.edit import FormView

from core.models import Municipio
from pas.forms import PasDeclaracionJuradaForm, PasTitularesImportForm
from pas.models import PasDeclaracionJurada, PasInvitacionDDJJ
from pas.services.ddjj_service import presentar_ddjj
from pas.services.titulares_import_service import (
    generar_excel_tokens_vigentes,
    importar_titulares_csv,
)


class PasTitularesImportView(LoginRequiredMixin, FormView):
    template_name = "pas/titulares_import.html"
    form_class = PasTitularesImportForm

    def form_valid(self, form):
        try:
            resultado = importar_titulares_csv(
                form.cleaned_data["archivo"], usuario=self.request.user
            )
        except ValidationError as exc:
            form.add_error("archivo", exc)
            return self.form_invalid(form)
        context = self.get_context_data(form=PasTitularesImportForm())
        context["resultado"] = resultado
        return self.render_to_response(context)


class PasTokensExportView(LoginRequiredMixin, View):
    def get(self, request):
        contenido = generar_excel_tokens_vigentes(usuario=request.user)
        response = HttpResponse(
            contenido,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = (
            'attachment; filename="pas_tokens_ddjj_vigentes.xlsx"'
        )
        return response


class PasDDJJFormularioView(View):
    template_name = "pas/ddjj_formulario.html"

    def _invitacion(self, token):
        return get_object_or_404(
            PasInvitacionDDJJ.objects.select_related(
                "persona", "persona__provincia", "persona__municipio"
            ),
            token=token,
        )

    def get(self, request, token):
        invitacion = self._invitacion(token)
        if not invitacion.disponible:
            return HttpResponse(
                "Este enlace ya fue utilizado o se encuentra vencido.", status=410
            )
        return self._render(
            request, invitacion, PasDeclaracionJuradaForm(persona=invitacion.persona)
        )

    def post(self, request, token):
        invitacion = self._invitacion(token)
        if not invitacion.disponible:
            return HttpResponse(
                "Este enlace ya fue utilizado o se encuentra vencido.", status=410
            )
        form = PasDeclaracionJuradaForm(request.POST, persona=invitacion.persona)
        if not form.is_valid():
            return self._render(request, invitacion, form, status=400)
        try:
            presentar_ddjj(invitacion, form)
        except ValueError:
            return HttpResponse(
                "Este enlace ya fue utilizado o se encuentra vencido.", status=410
            )
        return redirect("pas_ddjj_confirmacion")

    def _render(self, request, invitacion, form, status=200):
        return render(
            request,
            self.template_name,
            {"invitacion": invitacion, "persona": invitacion.persona, "form": form},
            status=status,
        )


class PasDDJJMunicipiosView(View):
    def get(self, request, token):
        invitacion = get_object_or_404(PasInvitacionDDJJ, token=token)
        if not invitacion.disponible:
            return JsonResponse({"detalle": "Invitacion no disponible."}, status=410)
        provincia_id = request.GET.get("provincia_id")
        if not provincia_id or not provincia_id.isdigit():
            return JsonResponse([], safe=False)
        municipios = (
            Municipio.objects.filter(provincia_id=provincia_id)
            .order_by("nombre")
            .values("id", "nombre")
        )
        return JsonResponse(list(municipios), safe=False)


class PasDDJJConfirmacionView(TemplateView):
    template_name = "pas/ddjj_confirmacion.html"


class PasDDJJPrivateMediaView(View):
    def get(self, request, path):
        raise Http404("Archivo no disponible por acceso directo.")


class PasDDJJDownloadView(LoginRequiredMixin, View):
    def get(self, request, pk):
        declaracion = get_object_or_404(
            PasDeclaracionJurada.objects.select_related("persona"), pk=pk
        )
        if not declaracion.archivo_pdf:
            raise Http404("La DDJJ no tiene un PDF asociado.")
        return FileResponse(
            declaracion.archivo_pdf.open("rb"),
            as_attachment=True,
            filename=f"DDJJ_PAS_{declaracion.persona.dni}_v{declaracion.version}.pdf",
            content_type="application/pdf",
        )
