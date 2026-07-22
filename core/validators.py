"""Validadores personalizados del proyecto."""

import re

from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.utils.deconstruct import deconstructible


def punycode(domain):
    """Implementación local de punycode para compatibilidad."""
    try:
        return domain.encode("idna").decode("ascii")
    except UnicodeError:
        return domain


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


CUIT_WEIGHTS = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)
CUIT_RE = re.compile(r"^\d{2}-?\d{8}-?\d$")

SOLO_LETRAS_RE = re.compile(r"^[^\W\d_]+(?:[\s'’\-][^\W\d_]+)*$", re.UNICODE)


def solo_digitos(value):
    """Devuelve únicamente los dígitos de ``value``."""

    return re.sub(r"\D", "", str(value or ""))


def _digito_verificador_cuit(base_digits):
    total = sum(int(digit) * weight for digit, weight in zip(base_digits, CUIT_WEIGHTS))
    verificador = 11 - (total % 11)
    if verificador == 11:
        return 0
    if verificador == 10:
        return 9
    return verificador


def validate_cuit(value):
    """Validar CUIT/CUIL con formato permitido y dígito verificador correcto."""

    raw_value = str(value or "").strip()
    if not CUIT_RE.fullmatch(raw_value):
        raise ValidationError("Ingrese un CUIT válido de 11 dígitos (XX-XXXXXXXX-X).")
    digits = solo_digitos(raw_value)
    if int(digits) == 0:
        raise ValidationError("El CUIT ingresado no es válido.")
    if _digito_verificador_cuit(digits[:10]) != int(digits[-1]):
        raise ValidationError("El CUIT ingresado tiene un dígito verificador inválido.")
    return digits


def validate_solo_letras(value):
    """Validar que el texto contenga solo letras, espacios, apóstrofes y guiones."""

    texto = str(value or "").strip()
    if not texto:
        return texto
    if not SOLO_LETRAS_RE.match(texto):
        raise ValidationError(
            "Ingrese solo letras (no se permiten números ni caracteres especiales)."
        )
    return texto


def validate_telefono_ar(value):
    """Validar un teléfono argentino: solo dígitos y guiones, entre 6 y 11 dígitos."""

    texto = str(value or "").strip()
    if not texto:
        return texto
    if not re.fullmatch(r"\d+(?:-\d+)*", texto):
        raise ValidationError(
            "Ingrese un teléfono válido: solo números, opcionalmente separados por guiones."
        )
    digits = solo_digitos(texto)
    if not 6 <= len(digits) <= 11:
        raise ValidationError(
            "Ingrese un teléfono válido de entre 6 y 11 dígitos "
            "(por ejemplo 4774-2015 o 011-4774-2015)."
        )
    return texto


def validate_codigo_postal_ar(value):
    """Validar un código postal argentino: 4 dígitos, entre 1000 y 9999."""

    if value in (None, ""):
        return value
    digits = solo_digitos(value)
    if len(digits) != 4 or not 1000 <= int(digits) <= 9999:
        raise ValidationError("Ingrese un código postal válido de 4 dígitos.")
    return int(digits)
