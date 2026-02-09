"""Validadores personalizados del proyecto."""

import re

from django.core.validators import EmailValidator
from django.utils.deconstruct import deconstructible


UNICODE_USER_REGEX = re.compile(
    r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z\u00C0-\u00FF]+"
    r"(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z\u00C0-\u00FF]+)*\Z"
    r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]'
    r'|\\[\001-\011\013\014\016-\177])*"\Z)',
    re.IGNORECASE,
)


@deconstructible
class UnicodeEmailValidator(EmailValidator):
    """EmailValidator que permite tildes en la parte local."""

    user_regex = UNICODE_USER_REGEX


def validate_unicode_email(value):
    """Validar email permitiendo tildes en la parte local."""

    return UnicodeEmailValidator()(value)
