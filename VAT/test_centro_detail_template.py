"""Guarda estructural del template del detalle de Centro VAT.

`djlint --check` reindenta alrededor de etiquetas sin cerrar en vez de
fallar, y ningun test renderiza `centro_detail.html`, asi que un `<div>`
sin cerrar (por ejemplo tras resolver un conflicto de merge) pasa
desapercibido. Este test verifica que los `<div>`/`<section>` queden
balanceados y bien anidados.

Asume la convencion del repo de no abrir/cerrar una misma etiqueta en
ramas distintas de un `{% if %}` (cada rama condicional del template
balancea sus etiquetas por separado).
"""

import re
from html.parser import HTMLParser
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent / "templates/vat/centros/centro_detail.html"

TRACKED_TAGS = {"div", "section"}


def _strip_django(text):
    """Reemplaza tags de plantilla por espacios para preservar el nro de linea."""

    def blank(match):
        return re.sub(r"[^\n]", " ", match.group(0))

    text = re.sub(r"{%.*?%}", blank, text, flags=re.DOTALL)
    text = re.sub(r"{{.*?}}", blank, text, flags=re.DOTALL)
    text = re.sub(r"<!--.*?-->", blank, text, flags=re.DOTALL)
    return text


class _StructureParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.problems = []

    def handle_starttag(self, tag, attrs):
        if tag in TRACKED_TAGS:
            self.stack.append((tag, self.getpos()[0]))

    def handle_endtag(self, tag):
        if tag not in TRACKED_TAGS:
            return
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                for orphan, line in self.stack[index + 1 :]:
                    self.problems.append(
                        f"<{orphan}> abierto en linea {line} quedo sin cerrar "
                        f"(lo cierra </{tag}> en linea {self.getpos()[0]})"
                    )
                del self.stack[index:]
                return
        self.problems.append(f"</{tag}> huerfano en linea {self.getpos()[0]}")


def test_centro_detail_template_bien_formado():
    parser = _StructureParser()
    parser.feed(_strip_django(TEMPLATE.read_text(encoding="utf-8")))

    problemas = list(parser.problems)
    problemas += [
        f"<{tag}> abierto en linea {line} quedo sin cerrar al final del archivo"
        for tag, line in parser.stack
    ]

    assert not problemas, "Estructura HTML invalida en {}:\n{}".format(
        TEMPLATE.name, "\n".join(problemas)
    )
