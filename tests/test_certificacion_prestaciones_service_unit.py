"""Tests unitarios para el fallback de certificaciones de prestaciones."""

from datetime import date
from pathlib import Path
from types import SimpleNamespace
import zipfile

from lxml import etree

from comedores.services.certificacion_prestaciones_service import (
    FUENTE_PRESTACIONES_SIN_DATOS,
    LEYENDA_PRESTACIONES_NO_DISPONIBLES,
    NS,
    _completar_plantilla,
)


def test_fallback_inserta_leyenda_en_plantilla(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "comedores.services.certificacion_prestaciones_service."
        "is_abordaje_comunitario_linea_tradicional_program",
        lambda comedor: False,
    )
    comedor = SimpleNamespace(
        nombre="Espacio sin fuente",
        calle="Calle 1",
        numero=10,
        localidad=SimpleNamespace(nombre="Localidad"),
        provincia=SimpleNamespace(nombre="Provincia"),
    )
    usuario = SimpleNamespace(
        username="usuario",
        get_full_name=lambda: "Usuario de prueba",
    )
    template_path = (
        Path(__file__).resolve().parents[1]
        / "pwa"
        / "files"
        / "varios"
        / "PRESTACIONES.1.docx"
    )
    output_path = tmp_path / "certificacion.docx"

    _completar_plantilla(
        template_path,
        output_path,
        comedor=comedor,
        periodo=date(2026, 7, 1),
        usuario=usuario,
        source=FUENTE_PRESTACIONES_SIN_DATOS,
    )

    with zipfile.ZipFile(output_path) as document:
        root = etree.fromstring(document.read("word/document.xml"))
    text = "".join(root.xpath(".//w:t/text()", namespaces=NS))

    assert LEYENDA_PRESTACIONES_NO_DISPONIBLES in text
