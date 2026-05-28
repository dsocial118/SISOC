import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.generic import FormView

from centrodefamilia.access import (
    GRUPO_CDF_REFERENTE_CENTRO,
    puede_generar_usuario_cdf,
    usuarios_cdf_restantes,
)
from centrodefamilia.forms_generar_usuario import GenerarUsuarioCDFForm
from centrodefamilia.models import AccesoCDF, Centro
from users.services_generate_user import (
    DatosUsuarioDelegado,
    generar_usuario_delegado,
)

logger = logging.getLogger("django")


class GenerarUsuarioCDFView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    """Genera un usuario "CDF - Referente centro" precargado para un Centro de Familia."""

    template_name = "centros/generar_usuario_cdf.html"
    form_class = GenerarUsuarioCDFForm
    raise_exception = True

    def dispatch(self, request, *args, **kwargs):
        self.centro = get_object_or_404(Centro, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        return puede_generar_usuario_cdf(self.request.user, self.centro)

    def get_initial(self):
        # Solo el primer usuario del CDF se precarga con los datos del
        # responsable; los siguientes van en blanco (son personas distintas).
        ya_tiene_usuarios = AccesoCDF.objects.filter(centro=self.centro).exists()
        if ya_tiene_usuarios:
            return {}
        return {
            "first_name": self.centro.nombre_referente or "",
            "last_name": self.centro.apellido_referente or "",
            "email": self.centro.correo_referente or "",
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["centro"] = self.centro
        context["usuarios_restantes"] = usuarios_cdf_restantes(self.centro)
        return context

    def get_success_url(self):
        return reverse("centro_detail", kwargs={"pk": self.centro.pk})

    def form_valid(self, form):
        datos = DatosUsuarioDelegado(
            first_name=form.cleaned_data["first_name"],
            last_name=form.cleaned_data["last_name"],
            email=form.cleaned_data["email"],
        )
        try:
            resultado = generar_usuario_delegado(
                actor=self.request.user,
                datos=datos,
                grupo_nombre=GRUPO_CDF_REFERENTE_CENTRO,
                vinculo_callback=lambda nuevo_usuario: AccesoCDF.objects.create(
                    user=nuevo_usuario,
                    centro=self.centro,
                    creado_por=self.request.user,
                ),
                limite_check=lambda: usuarios_cdf_restantes(self.centro) > 0,
                request=self.request,
            )
        except ValidationError as exc:
            for mensaje in exc.messages:
                form.add_error(None, mensaje)
            return self.form_invalid(form)

        usuario = resultado["user"]
        messages.success(
            self.request,
            f"Usuario «{usuario.username}» creado correctamente.",
        )
        return TemplateResponse(
            self.request,
            "centros/usuario_cdf_generado.html",
            {
                "centro": self.centro,
                "usuario": usuario,
                "password": resultado["password"],
                "email_enviado": resultado["email_enviado"],
                "puede_generar_otro": usuarios_cdf_restantes(self.centro) > 0,
            },
        )
