from .models import Insumo, InsumoCategoria


def get_insumos_queryset():
    return Insumo.objects.select_related(
        "categoria", "programa", "usuario_creacion"
    ).order_by("categoria__orden", "categoria__nombre", "-fecha_creacion")


def get_categorias_queryset():
    return InsumoCategoria.objects.select_related("programa").order_by(
        "orden", "nombre"
    )


def save_insumo_from_form(form, user, *, instance=None):
    insumo = form.save(commit=False)
    if instance is not None:
        insumo.pk = instance.pk
        if instance.usuario_creacion_id:
            insumo.usuario_creacion_id = instance.usuario_creacion_id
    if insumo.usuario_creacion_id is None and getattr(user, "is_authenticated", False):
        insumo.usuario_creacion = user
    if getattr(user, "is_authenticated", False):
        insumo.usuario_actualizacion = user
    insumo.save()
    return insumo


def delete_insumo(instance):
    archivo = instance.archivo
    instance.delete()
    if archivo:
        archivo.delete(save=False)


def save_categoria_from_form(form, *, instance=None):
    categoria = form.save(commit=False)
    if instance is not None:
        categoria.pk = instance.pk
    categoria.save()
    return categoria


def delete_categoria(instance):
    instance.delete()
