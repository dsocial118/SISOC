import re
from django.core.exceptions import ValidationError
import django
from django.utils.translation import gettext
django.utils.translation.ugettext = gettext
from django.utils.translation import ugettext as _


class UppercaseValidator(object):

    '''La contraseña debe tener por lo menos 1 letra mayuscula, A-Z.'''
    #  The password must contain at least 1 uppercase letter, A-Z.
    def validate(self, password, user=None):
        if not re.findall('[A-Z]', password):
            raise ValidationError(
                _("La contraseña debe tener por lo menos 1 letra mayuscula, A-Z."),
                code='password_no_upper',
            )

    def get_help_text(self):
        return _(
            "La contraseña debe tener por lo menos 1 letra mayuscula, A-Z."
        )
    

class LowercaseValidator(object):

    '''La contraseña debe tener por lo menos 1 letra minuscula, a-z.'''
    #  The password must contain at least 1 uppercase letter, A-Z.
    def validate(self, password, user=None):
        if not re.findall('[a-z]', password):
            raise ValidationError(
                _("La contraseña debe tener por lo menos 1 letra minuscula, a-z."),
                code='password_no_lower',
            )

    def get_help_text(self):
        return _(
            "La contraseña debe tener por lo menos 1 letra minuscula, a-z."
        )