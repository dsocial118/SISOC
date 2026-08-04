import zipfile
from datetime import date
from pathlib import Path
from types import SimpleNamespace

from django.conf import settings

from comedores.services.certificacion_prestaciones_service import _completar_plantilla


def test_plantilla_tradicional_incluye_merienda_reforzada(tmp_path):
    comedor = SimpleNamespace(
        nombre="Espacio",
        calle="Calle",
        numero=1,
        localidad=None,
        provincia=None,
        programa=SimpleNamespace(nombre="Abordaje Comunitario - Linea Tradicional"),
    )
    usuario = SimpleNamespace(username="operador", get_full_name=lambda: "Operador")
    source = SimpleNamespace(
        **{
            f"aprobadas_merienda_reforzada_{dia}": 2
            for dia in (
                "lunes",
                "martes",
                "miercoles",
                "jueves",
                "viernes",
                "sabado",
                "domingo",
            )
        }
    )
    destino = tmp_path / "certificacion.docx"

    _completar_plantilla(
        Path(settings.BASE_DIR) / "pwa/files/varios/PROGRAMA.ALIMENTAR.COMUNIDAD.docx",
        destino,
        comedor=comedor,
        periodo=date(2035, 1, 1),
        usuario=usuario,
        source=source,
    )

    with zipfile.ZipFile(destino) as archivo:
        contenido = archivo.read("word/document.xml").decode("utf-8")
    assert "Merienda Reforzada" in contenido
    assert ">14<" in contenido
