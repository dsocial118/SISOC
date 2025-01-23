from django import forms

from comedores.models.comedor import Observacion


class ObservacionForm(forms.ModelForm):

    class Meta:
        model = Observacion
        fields = "__all__"
