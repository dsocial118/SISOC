from django import template

register = template.Library()


@register.filter
def has_group(user, group_name):
    # Si el usuario pertenece al grupo "Admin", siempre retorna True
    if user.groups.filter(name="Admin").exists():
        return True
    # Si el usuario pertenece al grupo específico solicitado, retorna True
    return user.groups.filter(name=group_name).exists()
