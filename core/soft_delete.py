"""Core soft-delete primitives: model mixin, manager and queryset."""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

from core.soft_delete_cascade import (
    build_delete_plan,
    build_restore_plan,
    execute_delete_plan,
    execute_restore_plan,
)
from core.soft_delete_signals import post_restore, post_soft_delete


class SoftDeleteQuerySet(models.QuerySet):
    """QuerySet that defaults to logical delete/restore semantics."""

    def alive(self):
        return self.filter(deleted_at__isnull=True)

    def deleted(self):
        return self.filter(deleted_at__isnull=False)

    def hard_delete(self):
        return super().delete()

    def delete(self, user=None, cascade=True):  # pylint: disable=arguments-differ
        total = 0
        details = {}
        for instance in self:
            deleted_count, deleted_details = instance.delete(user=user, cascade=cascade)
            total += deleted_count
            for model_key, value in (deleted_details or {}).items():
                details[model_key] = details.get(model_key, 0) + value
        return total, details

    def restore(self, user=None, cascade=True):
        total = 0
        details = {}
        for instance in self:
            restored_count, restored_details = instance.restore(
                user=user, cascade=cascade
            )
            total += restored_count
            for model_key, value in (restored_details or {}).items():
                details[model_key] = details.get(model_key, 0) + value
        return total, details


class SoftDeleteManager(models.Manager):
    """Manager with optional inclusion of deleted rows."""

    use_in_migrations = True

    def __init__(self, *args, include_deleted=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.include_deleted = include_deleted

    def get_queryset(self):
        queryset = SoftDeleteQuerySet(self.model, using=self._db)
        if self.include_deleted:
            return queryset
        return queryset.alive()


class SoftDeleteModelMixin(models.Model):
    """Abstract model with logical delete/restore support."""

    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
    )
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    objects = SoftDeleteManager()
    all_objects = SoftDeleteManager(include_deleted=True)

    class Meta:
        abstract = True

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def _soft_delete_single(self, *, user=None, cascade=False):
        if self.pk is None or self.deleted_at is not None:
            return 0, {}
        now = timezone.now()
        updated = self.__class__.all_objects.filter(
            pk=self.pk,
            deleted_at__isnull=True,
        ).update(
            deleted_at=now,
            deleted_by=user,
        )
        if updated:
            self.deleted_at = now
            self.deleted_by = user
            post_soft_delete.send(
                sender=self.__class__,
                instance=self,
                user=user,
                cascade=cascade,
                root=self,
            )
        model_key = f"{self._meta.app_label}.{self.__class__.__name__}"
        return updated, {model_key: updated} if updated else {}

    def _restore_single(self, *, user=None, cascade=False):
        if self.pk is None or self.deleted_at is None:
            return 0, {}
        updated = self.__class__.all_objects.filter(
            pk=self.pk,
            deleted_at__isnull=False,
        ).update(
            deleted_at=None,
            deleted_by=None,
        )
        if updated:
            self.deleted_at = None
            self.deleted_by = None
            post_restore.send(
                sender=self.__class__,
                instance=self,
                user=user,
                cascade=cascade,
                root=self,
            )
        model_key = f"{self._meta.app_label}.{self.__class__.__name__}"
        return updated, {model_key: updated} if updated else {}

    def delete(  # pylint: disable=arguments-differ
        self,
        using=None,
        keep_parents=False,
        *,
        user=None,
        cascade=True,
    ):
        del using, keep_parents
        if self.pk is None:
            return 0, {}
        if not cascade:
            return self._soft_delete_single(user=user, cascade=False)

        plan = build_delete_plan(self)
        return execute_delete_plan(plan, user=user)

    def restore(self, *, user=None, cascade=True):
        if self.pk is None:
            return 0, {}
        if not cascade:
            return self._restore_single(user=user, cascade=False)
        plan = build_restore_plan(self)
        return execute_restore_plan(plan, user=user)

    def hard_delete(self, using=None, keep_parents=False):
        return super().delete(using=using, keep_parents=keep_parents)
