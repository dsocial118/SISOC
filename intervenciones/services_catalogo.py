import json
from pathlib import Path

from django.db.models import Q

from intervenciones.models.intervenciones import SubIntervencion, TipoIntervencion


FIXTURE_CATALOGO_PATH = Path(
    "intervenciones/fixtures/subintervencion_tipointervencion.json"
)


def _load_catalogo_fixture(path=FIXTURE_CATALOGO_PATH):
    data = json.loads(path.read_text())
    tipos = {}
    subtipos = []

    for row in data:
        model = row.get("model")
        fields = row.get("fields", {})
        if model == "intervenciones.tipointervencion":
            nombre = (fields.get("nombre") or "").strip()
            if not nombre:
                continue
            tipos[nombre] = {
                "programa": (fields.get("programa") or "").strip() or None,
                "subtipos": [],
            }
        elif model == "intervenciones.subintervencion":
            nombre = (fields.get("nombre") or "").strip()
            if not nombre:
                continue
            subtipos.append(
                {
                    "nombre": nombre,
                    "tipo_pk": fields.get("tipo_intervencion"),
                }
            )

    tipos_por_pk = {
        row["pk"]: (row.get("fields", {}).get("nombre") or "").strip()
        for row in data
        if row.get("model") == "intervenciones.tipointervencion"
    }
    for subtipo in subtipos:
        tipo_nombre = tipos_por_pk.get(subtipo["tipo_pk"])
        if not tipo_nombre or tipo_nombre not in tipos:
            continue
        tipos[tipo_nombre]["subtipos"].append(subtipo["nombre"])

    return tipos


def sync_catalogo_intervenciones(path=FIXTURE_CATALOGO_PATH):
    """Normalizar tipos y subtipos de intervenciones según el fixture fuente."""

    catalogo = _load_catalogo_fixture(path)
    tipos_sincronizados = 0
    subtipos_sincronizados = 0
    subtipos_vacios_eliminados, _ = SubIntervencion.objects.filter(
        Q(nombre__isnull=True) | Q(nombre="")
    ).delete()

    for tipo_nombre, definition in catalogo.items():
        programa = definition["programa"]
        tipo = (
            TipoIntervencion.objects.filter(nombre=tipo_nombre).order_by("id").first()
        )
        if tipo is None:
            tipo = TipoIntervencion.objects.create(
                nombre=tipo_nombre, programa=programa
            )
            tipos_sincronizados += 1
        elif tipo.programa != programa:
            tipo.programa = programa
            tipo.save(update_fields=["programa"])
            tipos_sincronizados += 1

        for subtipo_nombre in definition["subtipos"]:
            subtipo = SubIntervencion.objects.filter(
                nombre=subtipo_nombre,
                tipo_intervencion=tipo,
            ).first()
            if subtipo:
                continue

            subtipo = (
                SubIntervencion.objects.filter(nombre=subtipo_nombre)
                .filter(
                    Q(tipo_intervencion__isnull=True)
                    | Q(tipo_intervencion__programa=programa)
                    | Q(tipo_intervencion__nombre=tipo_nombre)
                )
                .order_by("id")
                .first()
            )
            if subtipo is None:
                SubIntervencion.objects.create(
                    nombre=subtipo_nombre,
                    tipo_intervencion=tipo,
                )
            else:
                subtipo.tipo_intervencion = tipo
                subtipo.save(update_fields=["tipo_intervencion"])
            subtipos_sincronizados += 1

    return {
        "tipos_sincronizados": tipos_sincronizados,
        "subtipos_sincronizados": subtipos_sincronizados,
        "subtipos_vacios_eliminados": subtipos_vacios_eliminados,
    }
