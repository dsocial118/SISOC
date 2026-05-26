from datetime import date


def parse_periodo_referencia(value: str | None) -> date | None:
    """Convierte un string de periodo (YYYY-MM o YYYY-MM-DD) a date con day=1."""
    raw_value = (value or "").strip()
    if not raw_value:
        return None
    if len(raw_value) == 7:
        raw_value = f"{raw_value}-01"
    try:
        return date.fromisoformat(raw_value).replace(day=1)
    except ValueError:
        return None
