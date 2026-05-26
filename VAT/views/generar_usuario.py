import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.generic import FormView

from VAT.forms_generar_usuario import GenerarUsuarioCentroVATForm
from VAT.models import Centro
from VAT.services.access_scope import (
    GRUPO_REFERENTE_CENTRO_VAT,
    puede_generar_usuario_centro_vat,
    usuarios_centro_vat_restantes,
)
from users.services_generate_user import (
    DatosUsuarioDelegado,
    generar_usuario_delegado,
)

logger = logging.getLogger("django")


class GenerarUsuarioCentroVATView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    """Genera un usuario referente CFP precargado para un Centro VAT."""

    template_name = "vat/centros/generar_usuario.html"
    form_class = GenerarUsuarioCentroVATForm
    raise_exception = True

    def dispatch(self, request, *args, **kwargs):
        self.centro = get_object_or_404(Centro, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        return puede_generar_usuario_centro_vat(self.request.user, self.centro)

    def get_initial(self):
        # Solo el primer usuario del centro se precarga con los datos del
        # referente; los siguientes van en blanco (personas distintas).
        ya_tiene_usuarios = (
            self.centro.referentes.exists() or self.centro.referente_id is not None
        )
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
        context["usuarios_restantes"] = usuarios_centro_vat_restantes(self.centro)
        return context

    def get_success_url(self):
        return reverse("vat_centro_detail", kwargs={"pk": self.centro.pk})

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
                grupo_nombre=GRUPO_REFERENTE_CENTRO_VAT,
                vinculo_callback=lambda nuevo_usuario: self.centro.referentes.add(
                    nuevo_usuario
                ),
                limite_check=lambda: usuarios_centro_vat_restantes(self.centro) > 0,
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
            "vat/centros/usuario_generado.html",
            {
                "centro": self.centro,
                "usuario": usuario,
                "password": resultado["password"],
                "email_enviado": resultado["email_enviado"],
                "puede_generar_otro": usuarios_centro_vat_restantes(self.centro) > 0,
            },
        )
