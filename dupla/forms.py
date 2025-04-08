from django import forms

from dupla.models import Dupla
from django.forms import ValidationError


class DuplaForm(forms.ModelForm):

    class Meta:
        model = Dupla
        fields = "__all__"