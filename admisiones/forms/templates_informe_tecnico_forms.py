import re
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlsplit

from django import forms

from admisiones.models.admisiones import (
    IncidenciaTemplateInformeTecnico,
    PlantillaInformeTecnico,
    PlantillaInformeTecnicoVersion,
    TipoConvenio,
)


class _SanitizadorContenidoTemplate(HTMLParser):
    """Conserva el HTML que el generador DOCX admite y elimina contenido activo."""

    ETIQUETAS_PERMITIDAS = frozenset(
        {
            "a",
            "b",
            "blockquote",
            "br",
            "div",
            "em",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "hr",
            "i",
            "li",
            "ol",
            "p",
            "pre",
            "s",
            "span",
            "strike",
            "strong",
            "table",
            "tbody",
            "td",
            "th",
            "thead",
            "tr",
            "u",
            "ul",
        }
    )
    ETIQUETAS_SIN_CIERRE = frozenset({"br", "hr"})
    ETIQUETAS_CON_CONTENIDO_A_DESCARTAR = frozenset(
        {"embed", "iframe", "math", "object", "script", "style", "svg", "template"}
    )
    PATRON_COLOR = re.compile(
        r"^(?:#[0-9a-f]{3,8}|rgba?\([\d\s.,%]+\)|[a-z]+)$", re.IGNORECASE
    )
    VALORES_ALINEACION = frozenset({"left", "right", "center", "justify"})

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self._partes = []
        self._profundidad_descartada = 0

    def html_limpio(self):
        return "".join(self._partes).strip()

    @classmethod
    def _limpiar_estilos(cls, estilos):
        estilos_limpios = []
        for declaracion in estilos.split(";"):
            propiedad, separador, valor = declaracion.partition(":")
            if not separador:
                continue
            propiedad = propiedad.strip().lower()
            valor = valor.strip().lower()
            if propiedad == "text-align" and valor in cls.VALORES_ALINEACION:
                estilos_limpios.append(f"{propiedad}: {valor}")
            elif propiedad in {
                "background-color",
                "color",
            } and cls.PATRON_COLOR.fullmatch(valor):
                estilos_limpios.append(f"{propiedad}: {valor}")
        return "; ".join(estilos_limpios)

    @staticmethod
    def _url_segura(valor):
        try:
            esquema = urlsplit(valor.strip()).scheme.lower()
        except ValueError:
            return False
        return esquema in {"http", "https", "mailto"}

    @classmethod
    def _limpiar_atributos(cls, etiqueta, atributos):
        atributos_limpios = []
        for nombre, valor in atributos:
            nombre = (nombre or "").lower()
            valor = valor or ""
            if nombre == "style":
                estilos = cls._limpiar_estilos(valor)
                if estilos:
                    atributos_limpios.append((nombre, estilos))
            elif etiqueta == "a" and nombre == "href" and cls._url_segura(valor):
                atributos_limpios.append((nombre, valor.strip()))
            elif etiqueta == "a" and nombre == "title":
                atributos_limpios.append((nombre, valor.strip()))
            elif etiqueta in {"td", "th"} and nombre in {"colspan", "rowspan"}:
                if valor.isdigit() and 0 < int(valor) <= 100:
                    atributos_limpios.append((nombre, valor))
        return atributos_limpios

    def handle_starttag(self, tag, attrs):
        etiqueta = tag.lower()
        if etiqueta in self.ETIQUETAS_CON_CONTENIDO_A_DESCARTAR:
            self._profundidad_descartada += 1
            return
        if self._profundidad_descartada or etiqueta not in self.ETIQUETAS_PERMITIDAS:
            return
        atributos_limpios = self._limpiar_atributos(etiqueta, attrs)
        atributos_html = "".join(
            f' {nombre}="{escape(valor, quote=True)}"'
            for nombre, valor in atributos_limpios
        )
        self._partes.append(f"<{etiqueta}{atributos_html}>")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        etiqueta = tag.lower()
        if etiqueta in self.ETIQUETAS_CON_CONTENIDO_A_DESCARTAR:
            self._profundidad_descartada = max(0, self._profundidad_descartada - 1)
            return
        if self._profundidad_descartada:
            return
        if (
            etiqueta in self.ETIQUETAS_PERMITIDAS
            and etiqueta not in self.ETIQUETAS_SIN_CIERRE
        ):
            self._partes.append(f"</{etiqueta}>")

    def handle_data(self, data):
        if not self._profundidad_descartada:
            self._partes.append(escape(data, quote=False))

    def handle_entityref(self, name):
        if not self._profundidad_descartada:
            self._partes.append(f"&{name};")

    def handle_charref(self, name):
        if not self._profundidad_descartada:
            self._partes.append(f"&#{name};")


def sanitizar_contenido_template(contenido_html):
    """Limpia el HTML editable sin modificar los tokens ``{{ variable }}``."""

    sanitizador = _SanitizadorContenidoTemplate()
    sanitizador.feed(contenido_html or "")
    sanitizador.close()
    return sanitizador.html_limpio()


class PlantillaInformeTecnicoForm(forms.ModelForm):
    """Formulario de condiciones para una plantilla lógica de Informe Técnico."""

    # El catálogo operativo conserva el nombre histórico "Organización Base".
    # En el Gestor se presenta con el nombre funcional "Asociación de hecho",
    # sin modificar el valor que la admisión ya guarda en TipoConvenio.
    TIPOS_CONVENIO_DISPONIBLES = (
        ("Personería Jurídica", "Personería jurídica"),
        ("Personería Jurídica Eclesiástica", "Personería jurídica eclesiástica"),
        ("Organización Base", "Asociación de hecho"),
    )

    class Meta:
        model = PlantillaInformeTecnico
        fields = [
            "nombre",
            "descripcion",
            "tipo_admision",
            "tipo_convenio",
            "es_ex_pnud",
            "estado_convenio_pnud",
            "tipo_renovacion",
            "estado_financiamiento",
        ]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "tipo_admision": forms.Select(attrs={"class": "form-select"}),
            "tipo_convenio": forms.Select(attrs={"class": "form-select"}),
            "es_ex_pnud": forms.Select(attrs={"class": "form-select"}),
            "estado_convenio_pnud": forms.Select(attrs={"class": "form-select"}),
            "tipo_renovacion": forms.Select(attrs={"class": "form-select"}),
            "estado_financiamiento": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        etiquetas_por_nombre = dict(self.TIPOS_CONVENIO_DISPONIBLES)
        nombres_permitidos = list(etiquetas_por_nombre)
        campo_tipo_convenio = self.fields["tipo_convenio"]
        campo_tipo_convenio.queryset = TipoConvenio.objects.filter(
            nombre__in=nombres_permitidos
        ).order_by("nombre")
        campo_tipo_convenio.empty_label = "Seleccione un tipo de convenio"
        campo_tipo_convenio.label_from_instance = lambda tipo_convenio: (
            etiquetas_por_nombre[tipo_convenio.nombre]
        )

    def clean(self):
        cleaned_data = super().clean()
        tipo_admision = cleaned_data.get("tipo_admision")

        if tipo_admision == "incorporacion":
            es_ex_pnud = cleaned_data.get("es_ex_pnud")
            if es_ex_pnud == "no":
                cleaned_data["estado_convenio_pnud"] = None
            cleaned_data["tipo_renovacion"] = None
            cleaned_data["estado_financiamiento"] = None
        elif tipo_admision == "renovacion":
            cleaned_data["es_ex_pnud"] = None
            cleaned_data["estado_convenio_pnud"] = None

        return cleaned_data


class PlantillaInformeTecnicoVersionForm(forms.ModelForm):
    class Meta:
        model = PlantillaInformeTecnicoVersion
        fields = ["contenido_html", "observaciones"]
        widgets = {
            "contenido_html": forms.Textarea(
                attrs={
                    "class": "form-control font-monospace",
                    "data-template-editor-source": "true",
                    "rows": 22,
                    "placeholder": "Escribí el contenido HTML o insertá una variable desde el catálogo.",
                }
            ),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
        labels = {
            "contenido_html": "Contenido del template",
            "observaciones": "Observaciones de la versión",
        }

    def clean_contenido_html(self):
        return sanitizar_contenido_template(
            self.cleaned_data.get("contenido_html") or ""
        )


class IncidenciaTemplateInformeTecnicoForm(forms.ModelForm):
    class Meta:
        model = IncidenciaTemplateInformeTecnico
        fields = ["estado", "plantilla", "observaciones"]
        widgets = {
            "estado": forms.Select(attrs={"class": "form-select"}),
            "plantilla": forms.Select(attrs={"class": "form-select"}),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["plantilla"].queryset = PlantillaInformeTecnico.objects.filter(
            estado="activa"
        ).order_by("codigo")
        self.fields["plantilla"].required = False
