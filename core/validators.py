"""Validadores personalizados del proyecto."""

import re

from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, punycode
from django.utils.deconstruct import deconstructible


UNICODE_USER_REGEX = re.compile(
    r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z\u00C0-\u00FF]+"
    r"(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z\u00C0-\u00FF]+)*\Z)",
    re.IGNORECASE,
)

# Rango permitido para quoted-string (RFC 5322 + obs-qtext) sin backtracking.
_QUOTED_TEXT_ALLOWED = (
    (1, 8),
    (11, 12),
    (14, 31),
    (33, 91),
    (93, 127),
)
_QUOTED_ESCAPED_ALLOWED = (
    (1, 9),
    (11, 12),
    (14, 127),
)


def _is_quoted_local_part(value):
    if len(value) < 2 or value[0] != '"' or value[-1] != '"':
        return False

    inner = value[1:-1]
    idx = 0
    while idx < len(inner):
        ch = inner[idx]
        if ch == "\\":
            idx += 1
            if idx >= len(inner):
                return False
            code = ord(inner[idx])
            if not any(start <= code <= end for start, end in _QUOTED_ESCAPED_ALLOWED):
                return False
            idx += 1
            continue

        code = ord(ch)
        if not any(start <= code <= end for start, end in _QUOTED_TEXT_ALLOWED):
            return False
        idx += 1

    return True


@deconstructible
class UnicodeEmailValidator(EmailValidator):
    """EmailValidator que permite tildes en la parte local."""

    user_regex = UNICODE_USER_REGEX

    def __call__(self, value):
        # Mantener la misma logica base de EmailValidator, pero evitando
        # un regex con backtracking para quoted-string.
        if not value or "@" not in value or len(value) > 320:
            raise ValidationError(self.message, code=self.code, params={"value": value})

        user_part, domain_part = value.rsplit("@", 1)

        if not (self.user_regex.match(user_part) or _is_quoted_local_part(user_part)):
            raise ValidationError(self.message, code=self.code, params={"value": value})

        if domain_part not in self.domain_allowlist and not self.validate_domain_part(
            domain_part
        ):
            try:
                domain_part = punycode(domain_part)
            except UnicodeError:
                pass
            else:
                if self.validate_domain_part(domain_part):
                    return
            raise ValidationError(self.message, code=self.code, params={"value": value})


def validate_unicode_email(value):
    """Validar email permitiendo tildes en la parte local."""

    return UnicodeEmailValidator()(value)
