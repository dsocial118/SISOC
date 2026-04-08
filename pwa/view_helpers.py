def build_mensaje_espacio_summary(serialized_items):
    unread_count = sum(1 for item in serialized_items if not item["visto"])
    unread_general_ids = sorted(
        {
            item["id"]
            for item in serialized_items
            if item["seccion"] == "general" and not item["visto"]
        }
    )
    unread_rendicion_ids = sorted(
        {
            item["accion"]["rendicion_id"]
            for item in serialized_items
            if item["seccion"] == "espacio"
            and not item["visto"]
            and item["accion"]
            and item["accion"].get("tipo") == "rendicion_detalle"
            and item["accion"].get("rendicion_id")
        }
    )
    unread_espacio_non_rendicion_count = sum(
        1
        for item in serialized_items
        if item["seccion"] == "espacio"
        and not item["visto"]
        and not (
            item["accion"]
            and item["accion"].get("tipo") == "rendicion_detalle"
            and item["accion"].get("rendicion_id")
        )
    )
    return {
        "unread_count": unread_count,
        "unread_general_count": len(unread_general_ids),
        "unread_espacio_count": sum(
            1
            for item in serialized_items
            if item["seccion"] == "espacio" and not item["visto"]
        ),
        "unread_grouped_count": (
            len(unread_general_ids)
            + unread_espacio_non_rendicion_count
            + len(unread_rendicion_ids)
        ),
        "unread_general_ids": unread_general_ids,
        "unread_rendicion_ids": unread_rendicion_ids,
        "unread_espacio_non_rendicion_count": unread_espacio_non_rendicion_count,
    }


def renaper_unavailable_message():
    return (
        "No se pudo conectar con RENAPER en este momento. "
        "Probá nuevamente en unos minutos."
    )


def normalize_renaper_error_message(message):
    normalized_message = str(message or "No se pudieron obtener datos desde RENAPER.")
    lowered = normalized_message.lower()
    if (
        "timed out" in lowered
        or "connectionpool" in lowered
        or "max retries exceeded" in lowered
    ):
        return renaper_unavailable_message()
    return normalized_message


def serialize_ciudadano_local(ciudadano, dni):
    sexo_local = (
        getattr(ciudadano.sexo, "sexo", "") if getattr(ciudadano, "sexo", None) else ""
    )
    fecha_local = (
        ciudadano.fecha_nacimiento.isoformat()
        if getattr(ciudadano, "fecha_nacimiento", None)
        else None
    )
    return {
        "nombre": ciudadano.nombre or "",
        "apellido": ciudadano.apellido or "",
        "documento": str(ciudadano.documento or dni),
        "fecha_nacimiento": fecha_local,
        "sexo": sexo_local,
    }


def resolve_sexo_label(sexo_value, sexo_model):
    sexo_label = ""
    if not sexo_value:
        return sexo_label
    if hasattr(sexo_value, "sexo"):
        sexo_label = getattr(sexo_value, "sexo", "") or ""
    elif isinstance(sexo_value, str):
        sexo_normalizado = sexo_value.strip().upper()
        if sexo_normalizado in ("M", "MASCULINO"):
            sexo_label = "Masculino"
        elif sexo_normalizado in ("F", "FEMENINO"):
            sexo_label = "Femenino"
        elif sexo_normalizado in ("X", "NO BINARIO", "NB"):
            sexo_label = "X"
        else:
            sexo_label = sexo_value.strip()
    else:
        sexo_obj = sexo_model.objects.filter(pk=sexo_value).first()
        sexo_label = getattr(sexo_obj, "sexo", "") if sexo_obj else ""
    return sexo_label


def serialize_renaper_data(data, dni, sexo_model):
    fecha_nacimiento = data.get("fecha_nacimiento")
    if fecha_nacimiento and hasattr(fecha_nacimiento, "isoformat"):
        fecha_nacimiento = fecha_nacimiento.isoformat()

    return {
        "nombre": data.get("nombre") or "",
        "apellido": data.get("apellido") or "",
        "documento": str(data.get("documento") or dni),
        "fecha_nacimiento": fecha_nacimiento,
        "sexo": resolve_sexo_label(data.get("sexo"), sexo_model),
    }
