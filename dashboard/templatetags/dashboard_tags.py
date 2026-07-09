from django import template

from dashboard.models import Tablero

register = template.Library()


@register.simple_tag(takes_context=True)
def tableros_para_sidebar(context):
    """Devuelve los tableros visibles agrupados para el menú lateral.

    Cada elemento de la lista es un dict con ``tipo``:

    - ``single``: enlace directo (``nombre``, ``url``, ``activo``).
    - ``grupo``: submenú colapsable (``nombre``, ``activo`` y ``hijos``,
      lista de dicts ``single``).

    Los tableros sin ``grupo_menu`` (o cuyo grupo tiene un único tablero
    visible) se muestran como enlaces directos, sin el "Ver" intermedio.

    La posición de un grupo queda anclada al primer tablero encontrado de ese
    grupo (menor ``orden`` según el queryset). Los tableros posteriores del
    mismo grupo se agregan a sus ``hijos`` y no mueven la posición del grupo,
    aunque su propio ``orden`` los ubicaría después de otros elementos.
    """
    request = context.get("request")
    if not request:
        return []
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return []

    tableros = list(Tablero.objects.filter(activo=True).order_by("orden", "nombre"))
    if not user.is_superuser:
        permission_codes = Tablero.permission_codes_de_usuario(user)
        if not permission_codes:
            return []
        tableros = [tablero for tablero in tableros if tablero.usuario_puede_ver(user)]

    current_path = request.get_full_path()

    items = []
    grupos_por_nombre = {}
    for tablero in tableros:
        url = tablero.get_absolute_url()
        hijo = {
            "tipo": "single",
            "nombre": tablero.nombre,
            "url": url,
            "activo": current_path == url,
        }

        grupo_menu = (tablero.grupo_menu or "").strip()
        if not grupo_menu:
            items.append(hijo)
            continue

        grupo = grupos_por_nombre.get(grupo_menu)
        if grupo is None:
            grupo = {
                "tipo": "grupo",
                "nombre": grupo_menu,
                "activo": False,
                "hijos": [],
            }
            grupos_por_nombre[grupo_menu] = grupo
            items.append(grupo)
        grupo["hijos"].append(hijo)
        if hijo["activo"]:
            grupo["activo"] = True

    # Un grupo con un solo tablero visible se colapsa a enlace directo.
    resultado = []
    for item in items:
        if item["tipo"] == "grupo" and len(item["hijos"]) == 1:
            resultado.append(item["hijos"][0])
        else:
            resultado.append(item)
    return resultado
