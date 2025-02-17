from django import template

register = template.Library()


@register.filter
def has_group(user, group_name):
    # Si el usuario pertenece al grupo "Admin" o es superuser, siempre retorna True
    if user.groups.filter(name="Admin").exists() or user.is_superuser:
        return True
    # Si el usuario pertenece al grupo específico solicitado, retorna True
    return user.groups.filter(name=group_name).exists()
