from django import template

from core.constants import UserGroups
from dashboard.models import Tablero

register = template.Library()


@register.simple_tag(takes_context=True)
def tableros_para_sidebar(context):
    request = context.get("request")
    if not request:
        return []
    user = request.user
    if not user or not user.is_authenticated:
        return []

    tableros = list(Tablero.objects.filter(activo=True).order_by("orden", "nombre"))
    if user.is_superuser:
        return tableros

    grupos = Tablero.grupos_de_usuario(user)
    if UserGroups.ADMINISTRADOR in grupos:
        return tableros

    if not grupos:
        return []

    return [tablero for tablero in tableros if tablero.tiene_acceso_para_grupos(grupos)]
