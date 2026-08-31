from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import RedirectView

from centrodeinfancia.access import puede_generar_usuario_egp


class GenerarUsuarioEGPView(LoginRequiredMixin, UserPassesTestMixin, RedirectView):
    """Compatibilidad: el alta EGP se concentra en el ABM general de usuarios."""

    raise_exception = True
    pattern_name = "usuario_crear"
    permanent = False

    def test_func(self):
        return puede_generar_usuario_egp(self.request.user)
