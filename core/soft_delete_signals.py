"""Domain signals emitted for soft-delete lifecycle events."""

from django.dispatch import Signal

# Sent after a model instance was soft-deleted.
# kwargs: user, cascade, root
post_soft_delete = Signal()

# Sent after a model instance was restored.
# kwargs: user, cascade, root
post_restore = Signal()

