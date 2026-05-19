import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.generic import FormView

from centrodeinfancia.access import (
    GRUPO_CDI_REFERENTE_CENTRO,
    puede_generar_usuario_cdi,
    usuarios_cdi_restantes,
)
from centrodeinfancia.forms_generar_usuario import GenerarUsuarioCDIForm
from centrodeinfancia.models import AccesoCDI, CentroDeInfancia
from users.services_generate_user import (
    DatosUsuarioDelegado,
    generar_usuario_delegado,
)

logger = logging.getLogger("django")


class GenerarUsuarioCDIView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    """Genera un usuario "CDI - Referente centro" precargado para un CDI."""

    template_name = "centrodeinfancia/generar_usuario_cdi.html"
    form_class = GenerarUsuarioCDIForm
    raise_exception = True

    def dispatch(self, request, *args, **kwargs):
        self.centro = get_object_or_404(CentroDeInfancia, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        return puede_generar_usuario_cdi(self.request.user, self.centro)

    def get_initial(self):
        # Solo el primer usuario del CDI se precarga con los datos del
        # referente; los siguientes van en blanco (son personas distintas).
        ya_tiene_usuarios = AccesoCDI.objects.filter(centro=self.centro).exists()
        if ya_tiene_usuarios:
            return {}
        return {
            "first_name": self.centro.nombre_referente or "",
            "last_name": self.centro.apellido_referente or "",
            "email": self.centro.email_referente or "",
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["centro"] = self.centro
        context["usuarios_restantes"] = usuarios_cdi_restantes(self.centro)
        return context

    def get_success_url(self):
        return reverse("centrodeinfancia_detalle", kwargs={"pk": self.centro.pk})

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
                grupo_nombre=GRUPO_CDI_REFERENTE_CENTRO,
                vinculo_callback=lambda nuevo_usuario: AccesoCDI.objects.create(
                    user=nuevo_usuario,
                    centro=self.centro,
                    creado_por=self.request.user,
                ),
                limite_check=lambda: usuarios_cdi_restantes(self.centro) > 0,
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
            "centrodeinfancia/usuario_cdi_generado.html",
            {
                "centro": self.centro,
                "usuario": usuario,
                "password": resultado["password"],
                "email_enviado": resultado["email_enviado"],
                "puede_generar_otro": usuarios_cdi_restantes(self.centro) > 0,
            },
        )
