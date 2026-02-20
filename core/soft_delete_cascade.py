"""Cascade planning and execution for soft-delete and restore operations."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from functools import lru_cache

from django.db import models, transaction
from django.utils import timezone


MODE_SOFT = "soft"
MODE_HARD = "hard"
OP_DELETE = "delete"
OP_RESTORE = "restore"


@dataclass(frozen=True)
class CascadeRelation:
    """Minimal metadata for a CASCADE reverse relation."""

    model: type[models.Model]
    field_name: str


@dataclass
class CascadeNode:
    """One affected object in a planned cascade operation."""

    instance: models.Model
    mode: str
    depth: int = 0


@dataclass
class CascadePlan:
    """A full cascade plan for delete/restore."""

    operation: str
    root: models.Model
    nodes: dict[tuple[type[models.Model], int], CascadeNode] = field(
        default_factory=dict
    )

    @property
    def total(self) -> int:
        return len(self.nodes)

    def iter_nodes(self):
        return self.nodes.values()

    def iter_nodes_by_mode(self, mode: str):
        return (node for node in self.nodes.values() if node.mode == mode)


def _node_key(instance: models.Model) -> tuple[type[models.Model], int]:
    return (instance.__class__, int(instance.pk))


def _is_soft_delete_model(model: type[models.Model]) -> bool:
    return (
        hasattr(model, "deleted_at")
        and hasattr(model, "all_objects")
        and hasattr(model, "restore")
    )


def _is_soft_delete_instance(instance: models.Model) -> bool:
    return _is_soft_delete_model(instance.__class__)


@lru_cache(maxsize=None)
def _get_reverse_cascade_relations(
    model: type[models.Model],
) -> tuple[CascadeRelation, ...]:
    relations: list[CascadeRelation] = []
    for relation in model._meta.get_fields():  # noqa: SLF001
        if not relation.auto_created or relation.concrete:
            continue
        if not (relation.one_to_many or relation.one_to_one):
            continue

        relation_field = getattr(relation, "field", None)
        if relation_field is None:
            continue

        remote = getattr(relation_field, "remote_field", None)
        on_delete = getattr(remote, "on_delete", None)
        if on_delete is not models.CASCADE:
            continue
        if getattr(remote, "parent_link", False):
            continue

        relations.append(
            CascadeRelation(
                model=relation.related_model,
                field_name=relation_field.name,
            )
        )
    return tuple(relations)


def _related_queryset(
    instance: models.Model,
    relation: CascadeRelation,
    *,
    operation: str,
    child_mode: str = MODE_SOFT,
):
    model = relation.model
    field_filter = {relation.field_name: instance.pk}

    if _is_soft_delete_model(model):
        queryset = model.all_objects.filter(**field_filter)
        if operation == OP_DELETE and child_mode == MODE_SOFT:
            return queryset.filter(deleted_at__isnull=True)
        if operation == OP_RESTORE:
            return queryset.filter(deleted_at__isnull=False)
        return queryset

    return model._meta.base_manager.filter(**field_filter)  # noqa: SLF001


def _protected_related_ids_from_parent(
    parent: models.Model, child_model: type[models.Model]
) -> set[int]:
    """
    IDs del modelo hijo que el padre referencia por FK/O2O con PROTECT/RESTRICT.

    Si el padre queda en soft-delete, esos hijos no se pueden hard-delete porque
    la referencia protegida sigue vigente.
    """
    protected_ids: set[int] = set()
    restricted_delete = getattr(models, "RESTRICT", None)
    protected_behaviors = {models.PROTECT}
    if restricted_delete is not None:
        protected_behaviors.add(restricted_delete)

    for relation_field in parent._meta.get_fields():  # noqa: SLF001
        if not getattr(relation_field, "concrete", False):
            continue
        if not getattr(relation_field, "is_relation", False):
            continue
        if getattr(relation_field, "many_to_many", False):
            continue

        remote_field = getattr(relation_field, "remote_field", None)
        if remote_field is None:
            continue
        if remote_field.model is not child_model:
            continue
        if getattr(remote_field, "on_delete", None) not in protected_behaviors:
            continue

        rel_id = getattr(parent, relation_field.attname, None)
        if rel_id is not None:
            protected_ids.add(int(rel_id))

    return protected_ids


def _visit_delete(
    plan: CascadePlan,
    instance: models.Model,
    mode: str,
    depth: int,
):
    if instance.pk is None:
        return

    key = _node_key(instance)
    existing = plan.nodes.get(key)

    if existing is not None:
        if existing.mode == MODE_HARD:
            return
        if existing.mode == MODE_SOFT and mode == MODE_SOFT:
            return
        # Upgrade soft -> hard and continue walking to propagate hard mode.
        existing.mode = MODE_HARD
        existing.depth = max(existing.depth, depth)
    else:
        if (
            mode == MODE_SOFT
            and _is_soft_delete_instance(instance)
            and getattr(instance, "deleted_at", None) is not None
        ):
            return
        plan.nodes[key] = CascadeNode(instance=instance, mode=mode, depth=depth)

    for relation in _get_reverse_cascade_relations(instance.__class__):
        child_mode = (
            MODE_HARD
            if mode == MODE_HARD or not _is_soft_delete_model(relation.model)
            else MODE_SOFT
        )
        queryset = _related_queryset(
            instance,
            relation,
            operation=OP_DELETE,
            child_mode=child_mode,
        )
        if mode == MODE_SOFT and child_mode == MODE_HARD:
            protected_ids = _protected_related_ids_from_parent(
                instance,
                relation.model,
            )
            if protected_ids:
                queryset = queryset.exclude(pk__in=protected_ids)
        for child in queryset.iterator():
            _visit_delete(plan, child, child_mode, depth + 1)


def _visit_restore(plan: CascadePlan, instance: models.Model, depth: int):
    if instance.pk is None or not _is_soft_delete_instance(instance):
        return
    if getattr(instance, "deleted_at", None) is None:
        return

    key = _node_key(instance)
    existing = plan.nodes.get(key)
    if existing is not None:
        existing.depth = max(existing.depth, depth)
        return
    plan.nodes[key] = CascadeNode(instance=instance, mode=MODE_SOFT, depth=depth)

    for relation in _get_reverse_cascade_relations(instance.__class__):
        if not _is_soft_delete_model(relation.model):
            continue
        queryset = _related_queryset(
            instance,
            relation,
            operation=OP_RESTORE,
            child_mode=MODE_SOFT,
        )
        for child in queryset.iterator():
            _visit_restore(plan, child, depth + 1)


def build_delete_plan(instance: models.Model) -> CascadePlan:
    """Build a recursive delete plan from an instance root."""
    plan = CascadePlan(operation=OP_DELETE, root=instance)
    _visit_delete(plan, instance, MODE_SOFT, 0)
    return plan


def build_restore_plan(instance: models.Model) -> CascadePlan:
    """Build a recursive restore plan from an instance root."""
    plan = CascadePlan(operation=OP_RESTORE, root=instance)
    _visit_restore(plan, instance, 0)
    return plan


def _summarize_group_key(node: CascadeNode) -> tuple[str, str, str]:
    model = node.instance.__class__
    return (
        f"{model._meta.app_label}.{model.__name__}",  # noqa: SLF001
        str(model._meta.verbose_name_plural).title(),  # noqa: SLF001
        node.mode,
    )


def _collect_summary_groups(
    plan: CascadePlan,
    sample_limit: int,
) -> tuple[dict[tuple[str, str, str], int], dict[tuple[str, str, str], list[str]]]:
    grouped_counts: dict[tuple[str, str, str], int] = defaultdict(int)
    grouped_examples: dict[tuple[str, str, str], list[str]] = defaultdict(list)

    for node in sorted(
        plan.iter_nodes(), key=lambda item: (item.depth, str(item.instance))
    ):
        group_key = _summarize_group_key(node)
        grouped_counts[group_key] += 1
        examples = grouped_examples[group_key]
        if len(examples) < sample_limit:
            examples.append(f"{node.instance} (ID {node.instance.pk})")
    return grouped_counts, grouped_examples


def summarize_plan(plan: CascadePlan, *, sample_limit: int = 5) -> dict:
    """Return UI-friendly preview payload for a plan."""
    grouped_counts, grouped_examples = _collect_summary_groups(plan, sample_limit)
    breakdown = []
    ejemplos_por_modelo = {}
    totals = defaultdict(int)

    for (model_key, model_label, mode), cantidad in sorted(
        grouped_counts.items(),
        key=lambda item: (item[0][1].lower(), item[0][2]),
    ):
        totals[mode] += cantidad
        examples = grouped_examples[(model_key, model_label, mode)]
        breakdown.append(
            {
                "modelo_key": model_key,
                "modelo": model_label,
                "cantidad": cantidad,
                "modo": "baja_logica" if mode == MODE_SOFT else "borrado_fisico",
                "ejemplos": examples,
            }
        )
        ejemplos_por_modelo[f"{model_label} [{mode}]"] = examples

    return {
        "total_afectados": sum(grouped_counts.values()),
        "total_baja_logica": totals[MODE_SOFT],
        "total_borrado_fisico": totals[MODE_HARD],
        "desglose_por_modelo": breakdown,
        "ejemplos_por_modelo": ejemplos_por_modelo,
    }


def _hard_delete_instance(instance: models.Model):
    if hasattr(instance, "hard_delete"):
        return instance.hard_delete()
    return instance.delete()


def _group_soft_nodes(plan: CascadePlan):
    by_model: dict[type[models.Model], list[int]] = defaultdict(list)
    for node in plan.iter_nodes_by_mode(MODE_SOFT):
        by_model[node.instance.__class__].append(int(node.instance.pk))
    return by_model


def _emit_soft_delete_signals(
    plan: CascadePlan,
    updated_by_model: dict[type[models.Model], set[int]],
    *,
    user=None,
):
    from core.soft_delete_signals import post_soft_delete

    for node in plan.iter_nodes_by_mode(MODE_SOFT):
        model = node.instance.__class__
        if int(node.instance.pk) not in updated_by_model.get(model, set()):
            continue
        node.instance.deleted_at = timezone.now()
        node.instance.deleted_by = user
        post_soft_delete.send(
            sender=model,
            instance=node.instance,
            user=user,
            cascade=True,
            root=plan.root,
        )


def _emit_restore_signals(
    plan: CascadePlan,
    updated_by_model: dict[type[models.Model], set[int]],
    *,
    user=None,
):
    from core.soft_delete_signals import post_restore

    for node in plan.iter_nodes_by_mode(MODE_SOFT):
        model = node.instance.__class__
        if int(node.instance.pk) not in updated_by_model.get(model, set()):
            continue
        node.instance.deleted_at = None
        node.instance.deleted_by = None
        post_restore.send(
            sender=model,
            instance=node.instance,
            user=user,
            cascade=True,
            root=plan.root,
        )


def execute_delete_plan(plan: CascadePlan, *, user=None) -> tuple[int, dict]:
    """Execute a delete plan (soft + hard where needed)."""
    if plan.operation != OP_DELETE:
        raise ValueError("execute_delete_plan requiere un plan de delete")

    now = timezone.now()
    updated_by_model: dict[type[models.Model], set[int]] = defaultdict(set)

    hard_nodes = sorted(
        list(plan.iter_nodes_by_mode(MODE_HARD)),
        key=lambda node: node.depth,
        reverse=True,
    )

    with transaction.atomic():
        for node in hard_nodes:
            model = node.instance.__class__
            pk = int(node.instance.pk)
            if _is_soft_delete_model(model):
                instance = model.all_objects.filter(pk=pk).first()
            else:
                instance = model._meta.base_manager.filter(pk=pk).first()  # noqa: SLF001
            if instance is None:
                continue
            _hard_delete_instance(instance)

        for model, ids in _group_soft_nodes(plan).items():
            existing = set(
                model.all_objects.filter(
                    pk__in=ids, deleted_at__isnull=True
                ).values_list(
                    "pk",
                    flat=True,
                )
            )
            if not existing:
                continue
            model.all_objects.filter(pk__in=existing).update(
                deleted_at=now,
                deleted_by=user,
            )
            updated_by_model[model].update(existing)

        _emit_soft_delete_signals(plan, updated_by_model, user=user)

    by_model = defaultdict(int)
    for model, ids in updated_by_model.items():
        by_model[f"{model._meta.app_label}.{model.__name__}"] += len(ids)
    for node in hard_nodes:
        model_key = (
            f"{node.instance._meta.app_label}.{node.instance.__class__.__name__}"
        )
        by_model[model_key] += 1

    total = sum(by_model.values())
    return total, dict(by_model)


def execute_restore_plan(plan: CascadePlan, *, user=None) -> tuple[int, dict]:
    """Execute a restore plan."""
    if plan.operation != OP_RESTORE:
        raise ValueError("execute_restore_plan requiere un plan de restore")

    updated_by_model: dict[type[models.Model], set[int]] = defaultdict(set)

    with transaction.atomic():
        for model, ids in _group_soft_nodes(plan).items():
            existing = set(
                model.all_objects.filter(
                    pk__in=ids, deleted_at__isnull=False
                ).values_list(
                    "pk",
                    flat=True,
                )
            )
            if not existing:
                continue
            model.all_objects.filter(pk__in=existing).update(
                deleted_at=None,
                deleted_by=None,
            )
            updated_by_model[model].update(existing)

        _emit_restore_signals(plan, updated_by_model, user=user)

    by_model = {
        f"{model._meta.app_label}.{model.__name__}": len(ids)
        for model, ids in updated_by_model.items()
    }
    total = sum(by_model.values())
    return total, by_model
