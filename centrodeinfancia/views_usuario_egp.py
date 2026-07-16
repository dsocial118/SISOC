from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ValidationError
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.generic import FormView

from centrodeinfancia.access import puede_generar_usuario_egp
from centrodeinfancia.forms_usuario_egp import GenerarUsuarioEGPForm
from centrodeinfancia.services_user_provisioning import vincular_scope_provincial_egp
from core.constants import UserGroups
from users.services_generate_user import (
    DatosUsuarioDelegado,
    generar_usuario_delegado,
)


class GenerarUsuarioEGPView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    """Genera un referente provincial con rol fijo "SIMEPI - EGP"."""

    template_name = "centrodeinfancia/generar_usuario_egp.html"
    form_class = GenerarUsuarioEGPForm
    raise_exception = True

    def test_func(self):
        return puede_generar_usuario_egp(self.request.user)

    def get_success_url(self):
        return reverse("usuarios")

    def form_valid(self, form):
        provincia = form.cleaned_data["provincia"]
        datos = DatosUsuarioDelegado(
            first_name=form.cleaned_data["first_name"],
            last_name=form.cleaned_data["last_name"],
            email=form.cleaned_data["email"],
        )

        def vincular_scope_provincial(nuevo_usuario):
            vincular_scope_provincial_egp(nuevo_usuario, provincia)

        try:
            resultado = generar_usuario_delegado(
                actor=self.request.user,
                datos=datos,
                grupo_nombre=UserGroups.SIMEPI_EGP,
                vinculo_callback=vincular_scope_provincial,
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
            "centrodeinfancia/usuario_egp_generado.html",
            {
                "usuario": usuario,
                "password": resultado["password"],
                "email_enviado": resultado["email_enviado"],
                "provincia": provincia,
            },
        )
