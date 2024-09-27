from django import forms

from comedores.models import Observacion


class ObservacionForm(forms.ModelForm):

    class Meta:
        model = Observacion
        fields = "__all__"
