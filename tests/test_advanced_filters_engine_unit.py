"""Tests for test advanced filters engine unit."""

from datetime import date, datetime

from django.db.models import Q

from core.services.advanced_filters import AdvancedFilterEngine


def _engine(allowed_ops=None, field_casts=None):
    return AdvancedFilterEngine(
        field_map={
            "name": "nombre",
            "age": "edad",
            "state": "estado",
            "dob": "nacimiento",
            "flag": "activo",
        },
        field_types={
            "name": "text",
            "age": "number",
            "state": "choice",
            "dob": "date",
            "flag": "boolean",
        },
        allowed_ops=allowed_ops,
        field_casts=field_casts,
    )


def test_init_requires_mapping_for_all_field_types():
    try:
        AdvancedFilterEngine(field_map={}, field_types={"x": "text"})
        assert False
    except ValueError:
        assert True


def test_extract_and_load_payload_variants():
    engine = _engine()

    assert engine._extract_raw_filters({}) is None
    assert engine._extract_raw_filters({"filters": "  "}) == "  "

    req = type("Req", (), {"GET": {"filters": '{"items": []}'}})()
    assert engine._extract_raw_filters(req) == '{"items": []}'
    assert engine._load_payload('{"items": []}') == {"items": []}
    assert engine._load_payload(b'{"items": []}') == {"items": []}
    assert engine._load_payload({"items": []}) == {"items": []}
    assert engine._load_payload([1, 2]) is None
    assert engine._load_payload("no-json") is None


def test_coerce_value_for_types_and_custom_cast():
    engine = _engine(field_casts={"age": lambda v: float(v)})
    assert engine._coerce_value("age", "2.5", "number") == (True, 2.5)

    engine2 = _engine()
    assert engine2._coerce_value("age", "10", "number") == (True, 10)
    assert engine2._coerce_value("age", "x", "number") == (False, None)

    assert engine2._coerce_value("dob", date(2026, 1, 1), "date") == (
        True,
        date(2026, 1, 1),
    )
    assert engine2._coerce_value("dob", datetime(2026, 1, 1, 10, 0), "date") == (
        True,
        date(2026, 1, 1),
    )
    assert engine2._coerce_value("dob", "2026-01-01", "date") == (
        True,
        date(2026, 1, 1),
    )
    assert engine2._coerce_value("dob", "01/02/2026", "date") == (
        True,
        date(2026, 2, 1),
    )
    assert engine2._coerce_value("dob", "x", "date") == (False, None)

    assert engine2._coerce_value("flag", "true", "boolean") == (True, True)
    assert engine2._coerce_value("flag", "0", "boolean") == (True, False)
    assert engine2._coerce_value("flag", "x", "boolean") == (False, None)


def test_build_q_for_item_text_choice_number_date_boolean_and_empty():
    engine = _engine()

    q = engine._build_q_for_item({"field": "name", "op": "contains", "value": "ana"})
    assert isinstance(q, Q)
    assert q.children == [("nombre__icontains", "ana")]

    q = engine._build_q_for_item({"field": "name", "op": "ne", "value": "ana"})
    assert q.negated is True

    q = engine._build_q_for_item({"field": "state", "op": "eq", "value": "A"})
    assert q.children == [("estado__iexact", "A")]

    q = engine._build_q_for_item({"field": "age", "op": "gt", "value": "3"})
    assert q.children == [("edad__gt", 3)]

    q = engine._build_q_for_item({"field": "dob", "op": "lt", "value": "2026-01-01"})
    assert q.children == [("nacimiento__lt", date(2026, 1, 1))]

    q = engine._build_q_for_item({"field": "flag", "op": "eq", "value": "yes"})
    assert q.children == [("activo__exact", True)]

    q = engine._build_q_for_item({"field": "name", "op": "empty", "empty_mode": "both"})
    assert isinstance(q, Q)

    q_null = engine._build_q_for_item(
        {"field": "name", "op": "empty", "empty_mode": "null"}
    )
    assert q_null.children == [("nombre__isnull", True)]

    q_blank = engine._build_q_for_item(
        {"field": "name", "op": "empty", "empty_mode": "blank"}
    )
    assert q_blank.children == [("nombre__exact", "")]


def test_build_q_for_item_invalid_returns_none():
    engine = _engine(allowed_ops={"text": {"eq"}})

    assert (
        engine._build_q_for_item({"field": "unknown", "op": "eq", "value": "x"}) is None
    )
    assert (
        engine._build_q_for_item({"field": "name", "op": "contains", "value": "x"})
        is None
    )
    assert engine._build_q_for_item({"field": "name", "op": "eq", "value": ""}) is None


def test_build_q_groups_by_field_and_applies_logic():
    engine = _engine()
    payload = {
        "logic": "AND",
        "items": [
            {"field": "name", "op": "contains", "value": "a"},
            {"field": "name", "op": "contains", "value": "b"},
            {"field": "age", "op": "gt", "value": 1},
        ],
    }
    q = engine.build_q({"filters": payload})
    assert isinstance(q, Q)

    q_or = engine.build_q({"filters": {**payload, "logic": "OR"}})
    assert isinstance(q_or, Q)

    assert engine.build_q({"filters": {"items": "x"}}) is None
    assert engine.build_q({"filters": ""}) is None
    assert engine.build_q({}) is None


def test_filter_queryset_returns_original_or_filtered(mocker):
    engine = _engine()
    qs = mocker.Mock()
    qs.filter.return_value = "filtered"

    assert engine.filter_queryset(qs, {}) is qs
    result = engine.filter_queryset(
        qs, {"filters": {"items": [{"field": "name", "op": "eq", "value": "Ana"}]}}
    )
    assert result == "filtered"
    qs.filter.assert_called_once()
