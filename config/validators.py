import re

import django
from django.core.exceptions import ValidationError
from django.utils.translation import gettext
from django.utils.translation import ugettext as _

django.utils.translation.ugettext = gettext


class UppercaseValidator:
    """La contraseña debe tener por lo menos 1 letra mayuscula, A-Z."""

    #  The password must contain at least 1 uppercase letter, A-Z.
    def validate(self, password, user=None):
        if not re.findall("[A-Z]", password):
            raise ValidationError(
                _("La contraseña debe tener por lo menos 1 letra mayuscula, A-Z."),
                code="password_no_upper",
            )

    def get_help_text(self):
        return _("La contraseña debe tener por lo menos 1 letra mayuscula, A-Z.")


class LowercaseValidator:
    """La contraseña debe tener por lo menos 1 letra minuscula, a-z."""

    #  The password must contain at least 1 uppercase letter, A-Z.
    def validate(self, password, user=None):
        if not re.findall("[a-z]", password):
            raise ValidationError(
                _("La contraseña debe tener por lo menos 1 letra minuscula, a-z."),
                code="password_no_lower",
            )

    def get_help_text(self):
        return _("La contraseña debe tener por lo menos 1 letra minuscula, a-z.")
