"""Campos personalizados reutilizables."""

from django.db import models

from core.validators import UnicodeEmailValidator


class UnicodeEmailField(models.EmailField):
    """EmailField que permite tildes en la parte local."""

    default_validators = [UnicodeEmailValidator()]
