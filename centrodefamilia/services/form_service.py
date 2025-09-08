from core.models import Provincia, Municipio, Localidad


def setup_location_fields(
    form,
    provincia_field="provincia",
    municipio_field="municipio",
    localidad_field="localidad",
):
    """Configura campos de ubicación dinámicos para formularios"""
    form.fields[provincia_field].queryset = Provincia.objects.all()
    form.fields[municipio_field].queryset = Municipio.objects.none()
    form.fields[localidad_field].queryset = Localidad.objects.none()

    form.fields[provincia_field].required = True
    form.fields[municipio_field].required = False
    form.fields[localidad_field].required = False

    if form.data:
        provincia_id = form.data.get(provincia_field)
        if provincia_id:
            form.fields[municipio_field].queryset = Municipio.objects.filter(
                provincia_id=provincia_id
            )
        municipio_id = form.data.get(municipio_field)
        if municipio_id:
            form.fields[localidad_field].queryset = Localidad.objects.filter(
                municipio_id=municipio_id
            )
    elif form.instance.pk:
        provincia = getattr(form.instance, provincia_field, None)
        if provincia:
            form.fields[municipio_field].queryset = Municipio.objects.filter(
                provincia=provincia
            )
        municipio = getattr(form.instance, municipio_field, None)
        if municipio:
            form.fields[localidad_field].queryset = Localidad.objects.filter(
                municipio=municipio
            )


def set_readonly_fields(form, fields):
    """Configura campos como readonly"""
    for campo in fields:
        if campo in form.fields:
            form.fields[campo].widget.attrs.update(
                {"readonly": True, "class": "form-control bg-secondary"}
            )
