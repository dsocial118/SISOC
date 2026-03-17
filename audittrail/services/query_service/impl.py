"""Servicios de consulta y presentación para vistas de audittrail."""

from collections import Counter
from datetime import timedelta
import json
import re

from django.contrib.contenttypes.models import ContentType
from django.db import connections
from django.db.models import Q
from django.db.models.expressions import RawSQL
from django.http import Http404

from auditlog.models import LogEntry
from audittrail.constants import get_tracked_models, is_tracked_model
from audittrail.forms import MAX_EXPORT_RANGE_DAYS


GROUPING_WINDOW_SECONDS = 2
SYSTEM_ACTOR_LABEL = "Sistema/Proceso"
EXPORT_MAX_ROWS = 5000
BULK_METADATA_KEYS = (
    "audittrail_batch_key",
    "batch_id",
    "bulk_id",
    "job_id",
    "request_id",
    "correlation_id",
    "transaction_id",
    "cid",
)

_FIELD_NAME_SAFE_RE = re.compile(r"^[\w.\-: ]+$", re.IGNORECASE)


def get_base_queryset():
    """Query base del listado global, con relaciones necesarias precargadas."""
    qs = (
        LogEntry.objects.select_related("actor", "content_type", "audittrail_meta")
        .all()
        .order_by("-timestamp", "-id")
    )
    return apply_tracked_models_allowlist(qs)


def apply_tracked_models_allowlist(qs):
    """
    Restringe consultas a modelos auditables definidos en la fuente única.
    """
    allowed_models = get_tracked_models()
    if not allowed_models:
        return qs.none()

    allowlist_query = Q()
    for app_label, model_name, _label in allowed_models:
        allowlist_query |= Q(
            content_type__app_label=app_label,
            content_type__model=model_name,
        )
    return qs.filter(allowlist_query)


def get_instance_queryset(*, app_label: str, model_name: str, object_pk):
    """Queryset para una instancia puntual validando allowlist server-side."""
    content_type = get_tracked_content_type_or_404(
        app_label=app_label,
        model_name=model_name,
    )
    return (
        LogEntry.objects.select_related("actor", "content_type", "audittrail_meta")
        .filter(content_type=content_type, object_pk=str(object_pk))
        .order_by("-timestamp", "-id")
    )


def get_tracked_content_type_or_404(*, app_label: str, model_name: str):
    """
    Resuelve el ContentType sólo para modelos permitidos en la auditoría.
    """
    if not is_tracked_model(app_label, model_name):
        raise Http404("Modelo no auditable")

    content_type = ContentType.objects.filter(
        app_label=app_label,
        model=model_name,
    ).first()
    if content_type is None:
        raise Http404("Modelo no encontrado")
    return content_type


def get_keyword_terms(keyword: str | None):
    """
    Tokeniza palabras para filtro AND (trim + espacios múltiples).
    """
    if not keyword:
        return []
    return [term for term in str(keyword).strip().split() if term]


def _available_changes_field_lookups(*, prefer_text: bool = False):
    """
    Devuelve los campos disponibles para búsquedas en cambios.

    Por defecto prioriza `changes` (JSON estructurado) y usa `changes_text`
    como complemento. En rutas de texto puro se puede invertir el orden.
    """
    field_names = {field.name for field in LogEntry._meta.get_fields()}
    ordered = (
        ("changes_text", "changes") if prefer_text else ("changes", "changes_text")
    )
    return [field_name for field_name in ordered if field_name in field_names]


def _safe_changes_field_lookup():
    """
    Devuelve el primer lookup disponible para compatibilidad.
    """
    lookups = _available_changes_field_lookups()
    return lookups[0] if lookups else None


def _logentry_has_field(field_name: str) -> bool:
    return any(field.name == field_name for field in LogEntry._meta.get_fields())


def _build_field_name_variants(field_name: str):
    """
    Variantes para filtrar por nombre de campo dentro del payload de changes.
    """
    normalized = " ".join((field_name or "").strip().split())
    if not normalized:
        return []
    if not _FIELD_NAME_SAFE_RE.match(normalized):
        normalized = re.sub(r"[^\w.\-: ]+", " ", normalized, flags=re.UNICODE).strip()
        normalized = " ".join(normalized.split())
        if not normalized:
            return []
    variants = [normalized]
    snake = normalized.replace(" ", "_")
    if snake != normalized:
        variants.append(snake)
    lower = normalized.lower()
    if lower not in variants:
        variants.append(lower)
    return variants


def apply_field_name_filter(qs, field_name: str | None):
    """
    Filtro por nombre de campo dentro de changes (best-effort, compatible).
    """
    variants = _build_field_name_variants(field_name)
    if not variants:
        return qs

    field_lookups = _available_changes_field_lookups()
    if not field_lookups:
        return qs

    has_key_query = Q()
    text_query = Q()
    supports_has_key = False

    for field_lookup in field_lookups:
        changes_field = LogEntry._meta.get_field(field_lookup)
        internal_type = getattr(changes_field, "get_internal_type", lambda: "")()
        if internal_type == "JSONField":
            supports_has_key = True
            for variant in variants:
                has_key_query |= Q(**{f"{field_lookup}__has_key": variant})
        for variant in variants:
            text_query |= Q(**{f"{field_lookup}__icontains": variant})

    if supports_has_key:
        # MySQL y PostgreSQL soportan `has_key`; si no, cae al fallback textual.
        try:
            return qs.filter(has_key_query | text_query)
        except Exception:  # noqa: BLE001
            pass

    return qs.filter(text_query)


def apply_origin_filter(qs, origin: str | None):
    """
    Filtro por origen lógico (Web / Comando / Sistema).
    """
    origin = (origin or "").strip()
    if not origin:
        return qs

    if origin == "web":
        legacy_web_fallback = Q(audittrail_meta__isnull=True) & Q(actor__isnull=False)
        if _logentry_has_field("cid"):
            legacy_web_fallback |= Q(audittrail_meta__isnull=True) & Q(
                cid__isnull=False
            )
        return qs.filter(
            Q(audittrail_meta__source="http")
            | Q(audittrail_meta__source__startswith="http:")
            | legacy_web_fallback
        )

    if origin == "command":
        return qs.filter(audittrail_meta__source__startswith="management_command:")

    if origin == "system":
        return qs.filter(
            Q(audittrail_meta__source="system")
            | Q(audittrail_meta__source__startswith="thread:")
            | Q(audittrail_meta__source__startswith="job:")
            | (Q(audittrail_meta__isnull=True) & Q(actor__isnull=True))
        )

    return qs


def apply_batch_key_filter(qs, batch_key: str | None):
    """
    Filtro por batch_key persistido (Fase 2).
    """
    batch_key = (batch_key or "").strip()
    if not batch_key:
        return qs
    return qs.filter(audittrail_meta__batch_key__icontains=batch_key)


def _normalize_mysql_version(version):
    if version is None:
        return ()
    if isinstance(version, tuple):
        return version
    if isinstance(version, str):
        digits = []
        for part in version.split("."):
            if part.isdigit():
                digits.append(int(part))
            else:
                break
        return tuple(digits)
    if isinstance(version, int):
        # Django puede exponer 80034 / similar
        text = str(version)
        if len(text) >= 5:
            return (int(text[0]), int(text[1:3]), int(text[3:]))
    return ()


def _mysql_can_use_fulltext(qs):
    """
    MySQL 8.0+ con columna `changes_text` presente.
    """
    if "changes_text" not in _available_changes_field_lookups(prefer_text=True):
        return False

    try:
        connection = connections[qs.db]
    except Exception:  # noqa: BLE001
        return False

    if getattr(connection, "vendor", "") != "mysql":
        return False

    version = _normalize_mysql_version(getattr(connection, "mysql_version", None))
    if version and version < (8, 0, 0):
        return False
    return True


def _build_mysql_boolean_fulltext_query(keyword: str | None):
    """
    Construye consulta safe para MATCH ... AGAINST (... IN BOOLEAN MODE).
    """
    tokens = []
    for term in get_keyword_terms(keyword):
        normalized = re.sub(r"[^\w]+", " ", term, flags=re.UNICODE).strip()
        for token in normalized.split():
            if len(token) < 2:
                continue
            tokens.append(token)

    if not tokens:
        return ""

    # AND semántico con prefijo + y wildcard final para prefijos.
    unique_tokens = []
    seen = set()
    for token in tokens:
        lowered = token.casefold()
        if lowered in seen:
            continue
        seen.add(lowered)
        unique_tokens.append(token)

    return " ".join(f"+{token}*" for token in unique_tokens)


def apply_optimized_keyword_filter(qs, keyword: str | None):
    """
    Aplica búsqueda por keyword priorizando FULLTEXT en MySQL 8 (changes_text).
    Fallback a `icontains` AND si no aplica.
    """
    terms_query = _build_keyword_terms_query(keyword)
    if terms_query is None:
        return qs

    if _mysql_can_use_fulltext(qs):
        boolean_query = _build_mysql_boolean_fulltext_query(keyword)
        if boolean_query:
            table_name = LogEntry._meta.db_table
            sql = f"MATCH({table_name}.changes_text) AGAINST (%s IN BOOLEAN MODE)"
            return qs.annotate(
                _audittrail_changes_rank=RawSQL(sql, [boolean_query])
            ).filter(Q(_audittrail_changes_rank__gt=0) | terms_query)

    return qs.filter(terms_query)


def _normalize_text_filter(value: str | None) -> str:
    return " ".join(str(value or "").strip().split())


def apply_model_filter(qs, model_value: str | None):
    """
    Filtro por modelo, soportando formato `app.model` o términos parciales.
    """
    normalized = _normalize_text_filter(model_value)
    if not normalized:
        return qs

    if "." in normalized:
        app_label, model_name = normalized.split(".", 1)
        app_label = app_label.strip()
        model_name = model_name.strip()
        if app_label and model_name:
            return qs.filter(
                content_type__app_label__iexact=app_label,
                content_type__model__iexact=model_name,
            )

    return qs.filter(
        Q(content_type__app_label__icontains=normalized)
        | Q(content_type__model__icontains=normalized)
    )


def apply_object_pk_filter(qs, object_pk):
    """
    Filtro por PK de instancia, normalizando espacios.
    """
    normalized = _normalize_text_filter(object_pk)
    if not normalized:
        return qs
    return qs.filter(object_pk=str(normalized))


def apply_actor_filter(qs, actor: str | None):
    """
    Filtro por actor considerando relación viva y snapshots persistidos.

    Usa términos AND para soportar búsquedas por nombre/apellido compuestos.
    """
    terms = get_keyword_terms(_normalize_text_filter(actor))
    if not terms:
        return qs

    for term in terms:
        qs = qs.filter(
            Q(actor__username__icontains=term)
            | Q(actor__email__icontains=term)
            | Q(actor__first_name__icontains=term)
            | Q(actor__last_name__icontains=term)
            | Q(audittrail_meta__actor_username_snapshot__icontains=term)
            | Q(audittrail_meta__actor_full_name_snapshot__icontains=term)
            | Q(audittrail_meta__actor_display_snapshot__icontains=term)
        )
    return qs


def apply_filters(qs, cleaned_data: dict):
    """
    Aplica filtros del formulario al queryset de auditlog.
    """
    data = cleaned_data or {}

    qs = apply_model_filter(qs, data.get("model"))
    qs = apply_object_pk_filter(qs, data.get("object_pk"))
    qs = apply_actor_filter(qs, data.get("actor"))

    field_name = data.get("field_name")
    if field_name:
        qs = apply_field_name_filter(qs, field_name)

    origin = data.get("origin")
    if origin:
        qs = apply_origin_filter(qs, origin)

    batch_key = data.get("batch_key")
    if batch_key:
        qs = apply_batch_key_filter(qs, batch_key)

    action = data.get("action")
    if action not in (None, ""):
        qs = qs.filter(action=action)

    start_date = data.get("start_date")
    if start_date:
        qs = qs.filter(timestamp__date__gte=start_date)

    end_date = data.get("end_date")
    if end_date:
        # incluir el día completo
        qs = qs.filter(timestamp__lt=end_date + timedelta(days=1))

    qs = apply_optimized_keyword_filter(qs, data.get("keyword"))
    return qs


def apply_keyword_filter(qs, keyword: str | None):
    """
    Filtro AND por palabras en `changes`.
    """
    terms_query = _build_keyword_terms_query(keyword)
    if terms_query is None:
        return qs
    return qs.filter(terms_query)


def _build_keyword_terms_query(keyword: str | None):
    """
    Construye un Q con semántica AND por término y OR por campo de changes.
    """
    terms = get_keyword_terms(keyword)
    if not terms:
        return None

    field_lookups = _available_changes_field_lookups()
    if not field_lookups:
        return None

    query = Q()
    for term in terms:
        term_query = Q()
        for field_lookup in field_lookups:
            term_query |= Q(**{f"{field_lookup}__icontains": term})
        query &= term_query
    return query


def validate_export_request(cleaned_data: dict):
    """
    Guardas para exportaciones amplias (performance/operación).
    """
    data = cleaned_data or {}
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    object_pk = data.get("object_pk")
    model_value = data.get("model")
    errors = []

    if object_pk:
        return errors

    if not (start_date and end_date):
        errors.append(
            "Para exportar resultados, indicá un rango de fechas (Desde y Hasta)."
        )
        return errors

    if start_date > end_date:
        errors.append("La fecha 'Hasta' no puede ser anterior a 'Desde'.")
        return errors

    if (end_date - start_date).days > MAX_EXPORT_RANGE_DAYS and not model_value:
        errors.append(
            f"Para exportar más de {MAX_EXPORT_RANGE_DAYS} días, filtrá al menos por modelo o instancia."
        )

    return errors


def get_actor_display(actor):
    """
    Devuelve representación legible del actor para UI.
    """
    if not actor:
        return SYSTEM_ACTOR_LABEL

    is_authenticated = getattr(actor, "is_authenticated", None)
    if is_authenticated is False:
        return SYSTEM_ACTOR_LABEL

    username = ""
    if hasattr(actor, "get_username"):
        try:
            username = (actor.get_username() or "").strip()
        except Exception:  # noqa: BLE001
            username = ""
    if not username:
        username = str(getattr(actor, "username", "") or "").strip()

    first_name = str(getattr(actor, "first_name", "") or "").strip()
    last_name = str(getattr(actor, "last_name", "") or "").strip()
    full_name = " ".join(part for part in [first_name, last_name] if part).strip()

    if username and full_name:
        if username == full_name:
            return username
        return f"{username} ({full_name})"
    if username:
        return username
    if full_name:
        return full_name
    return SYSTEM_ACTOR_LABEL


def format_actor_display(actor, fallback_label="Sistema"):
    """
    Devuelve estructura UI para actor (username + nombre/apellido), con fallback.
    """
    if not actor:
        return {
            "primary": fallback_label,
            "secondary": "",
            "is_fallback": True,
        }

    username = ""
    if hasattr(actor, "get_username"):
        try:
            username = (actor.get_username() or "").strip()
        except Exception:  # noqa: BLE001
            username = ""
    if not username:
        username = (
            getattr(actor, "username", "") or getattr(actor, "email", "") or "Usuario"
        )

    first_name = (getattr(actor, "first_name", "") or "").strip()
    last_name = (getattr(actor, "last_name", "") or "").strip()
    full_name = " ".join(part for part in (first_name, last_name) if part).strip()
    if full_name and full_name.casefold() == str(username).strip().casefold():
        full_name = ""

    return {
        "primary": username,
        "secondary": full_name,
        "is_fallback": False,
    }


def _get_entry_meta(entry):
    """
    Obtiene metadata de Fase 2 sin romper en rows legacy (sin meta).
    """
    try:
        return getattr(entry, "audittrail_meta", None)
    except Exception:  # noqa: BLE001
        return None


def format_actor_snapshot_display(meta, fallback_label="Sistema"):
    """
    Formatea actor desde snapshot persistido en `AuditEntryMeta`.
    """
    if not meta:
        return {
            "primary": fallback_label,
            "secondary": "",
            "is_fallback": True,
        }

    username = (getattr(meta, "actor_username_snapshot", "") or "").strip()
    full_name = (getattr(meta, "actor_full_name_snapshot", "") or "").strip()
    display = (getattr(meta, "actor_display_snapshot", "") or "").strip()

    if username:
        primary = username
    elif display:
        primary = display
    else:
        primary = fallback_label

    if full_name and full_name.casefold() == primary.casefold():
        full_name = ""

    return {
        "primary": primary,
        "secondary": full_name,
        "is_fallback": primary == fallback_label and not username and not display,
    }


def get_entry_source(entry):
    """
    Devuelve el origen persistido (Fase 2), si existe.
    """
    meta = _get_entry_meta(entry)
    source = (getattr(meta, "source", "") or "").strip() if meta else ""
    return source


def source_label(source: str | None):
    """
    Etiqueta amigable para origen de eventos.
    """
    labels = {
        "http": "Web",
        "system": "Sistema",
        "thread": "Thread",
    }
    if not source:
        return ""
    if source in labels:
        return labels[source]
    if source.startswith("management_command:"):
        return f"Comando ({source.split(':', 1)[1]})"
    if source.startswith("thread:"):
        return f"Thread ({source.split(':', 1)[1]})"
    if source.startswith("job:"):
        return f"Job ({source.split(':', 1)[1]})"
    return source


def get_entry_actor_ui(entry, fallback_label="Sistema"):
    """
    Prioriza snapshot persistido (Fase 2) y luego relación `actor`.
    """
    meta = _get_entry_meta(entry)
    has_snapshot = bool(
        meta
        and (
            getattr(meta, "actor_username_snapshot", None)
            or getattr(meta, "actor_full_name_snapshot", None)
            or getattr(meta, "actor_display_snapshot", None)
        )
    )
    if has_snapshot:
        return format_actor_snapshot_display(meta, fallback_label=fallback_label)
    return format_actor_display(
        getattr(entry, "actor", None), fallback_label=fallback_label
    )


def get_entry_actor_display(entry):
    """
    Devuelve label legible para el actor asociado a una entrada.
    """
    return get_actor_display(getattr(entry, "actor", None))


def should_group_entries(
    previous_entry,
    current_entry,
    window_seconds: int = GROUPING_WINDOW_SECONDS,
):
    """
    Heurística para agrupar eventos consecutivos del mismo actor/objeto/acción.
    """
    if not previous_entry or not current_entry:
        return False

    comparable_attrs = ("action", "object_pk", "content_type_id", "actor_id")
    for attr in comparable_attrs:
        if getattr(previous_entry, attr, None) != getattr(current_entry, attr, None):
            return False

    previous_timestamp = getattr(previous_entry, "timestamp", None)
    current_timestamp = getattr(current_entry, "timestamp", None)
    if not previous_timestamp or not current_timestamp:
        return False

    try:
        delta = previous_timestamp - current_timestamp
    except TypeError:
        return False

    return abs(delta.total_seconds()) <= window_seconds


def extract_bulk_marker(entry, bulk_metadata_keys=BULK_METADATA_KEYS):
    """
    Extrae marcador heurístico para agrupar acciones masivas.
    """
    meta = _get_entry_meta(entry)
    if meta:
        batch_key = (getattr(meta, "batch_key", "") or "").strip()
        if batch_key:
            return ("batch_key", batch_key)

    cid = getattr(entry, "cid", None)
    if cid not in (None, ""):
        return ("cid", str(cid))

    additional_data = getattr(entry, "additional_data", None)
    if isinstance(additional_data, str):
        try:
            additional_data = json.loads(additional_data)
        except Exception:  # noqa: BLE001
            additional_data = None

    if isinstance(additional_data, dict):
        for key in bulk_metadata_keys:
            value = additional_data.get(key)
            if value not in (None, ""):
                return (key, str(value))

    return (None, None)


def bulk_source_label(source):
    """
    Label de UI para la fuente del marcador de agrupación.
    """
    labels = {
        "batch_key": "lote",
        "cid": "correlación",
        "batch_id": "lote",
        "bulk_id": "lote",
        "job_id": "job",
        "request_id": "request",
        "correlation_id": "correlación",
        "transaction_id": "transacción",
    }
    return labels.get(source, "lote")


def decorate_entry_for_display(
    *,
    entry,
    action_ui: dict,
    bulk_metadata_keys=BULK_METADATA_KEYS,
):
    """
    Anota una entrada con campos de UI (actor legible y metadata de agrupación).
    """
    entry.ui_action_label = action_ui["label"]
    entry.ui_action_badge_class = action_ui["badge_class"]
    entry.ui_action_is_delete = action_ui["is_delete"]
    entry.ui_has_diffs = bool(getattr(entry, "resolved_changes", None))
    entry.ui_changes_count = len(getattr(entry, "resolved_changes", {}) or {})
    entry.ui_source = get_entry_source(entry)
    entry.ui_source_label = source_label(entry.ui_source)
    entry.ui_has_meta = bool(_get_entry_meta(entry))

    bulk_source, bulk_value = extract_bulk_marker(
        entry,
        bulk_metadata_keys=bulk_metadata_keys,
    )
    entry.ui_bulk_source = bulk_source
    entry.ui_bulk_value = bulk_value
    entry.ui_bulk_marker = (
        f"{bulk_source}:{bulk_value}" if bulk_source and bulk_value else None
    )

    fallback_actor = "Sistema"
    if entry.ui_bulk_marker or (entry.ui_source and entry.ui_source != "http"):
        fallback_actor = "Proceso"
    actor_ui = get_entry_actor_ui(entry, fallback_actor)
    entry.ui_actor_primary = actor_ui["primary"]
    entry.ui_actor_secondary = actor_ui["secondary"]
    entry.ui_actor_is_fallback = actor_ui["is_fallback"]
    return entry


def decorate_entries_for_display(*, entries, decorate_entry):
    """
    Agrupa heurísticamente por marcador de lote/correlación y anota secuencias.
    """
    decorated = [decorate_entry(entry) for entry in (entries or [])]

    marker_counts = Counter(
        entry.ui_bulk_marker
        for entry in decorated
        if getattr(entry, "ui_bulk_marker", None)
    )
    prev_marker = None
    for entry in decorated:
        marker = getattr(entry, "ui_bulk_marker", None)
        grouped = bool(marker and marker_counts.get(marker, 0) > 1)
        entry.ui_bulk_grouped = grouped
        entry.ui_bulk_count = marker_counts.get(marker, 0) if grouped else 0
        entry.ui_bulk_sequence_start = bool(grouped and marker != prev_marker)
        entry.ui_bulk_sequence_continuation = bool(grouped and marker == prev_marker)
        entry.ui_bulk_source_label = (
            bulk_source_label(getattr(entry, "ui_bulk_source", None)) if grouped else ""
        )
        prev_marker = marker
    return decorated


def enrich_entries_for_display(entries):
    """
    Anota helpers de presentación (actor legible + agrupación heurística).
    """
    previous_entry = None
    for entry in entries or []:
        entry.actor_display = get_entry_actor_display(entry)
        entry.is_grouped_with_previous = should_group_entries(previous_entry, entry)
        previous_entry = entry
    return entries
