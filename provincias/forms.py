from django import forms
from .models import AnexoSocioProductivo, TipoPersonaJuridica, Proyecto, PersonaJuridica, PersonaFisica, AbstractPersoneria

class ProyectoForm(forms.ModelForm):
    class Meta:
        model = Proyecto
        fields = ['tipo_anexo', 'nombre']

class PersonaJuridicaForm(forms.ModelForm):
    class Meta:
        model = PersonaJuridica
        fields = [
            'direccion',
            'localidad',
            'codigo_postal',
            'provincia',
            'nombre',
            'tipo',
            'fecha_creacion',
            'numero_personeria_juridica',
            'fecha_otorgamiento',
            'cuit',
            'domicilio_legal',
            'autoridad_nombre_completo',
            'autoridad_dni',
            'autoridad_cuit',
            'autoridad_rol',
            'proyecto_tipo_actividad',
        ]
        widgets = {
            'direccion': forms.TextInput(attrs={'required': False}),
            'localidad': forms.TextInput(attrs={'required': False}),
            'codigo_postal': forms.NumberInput(attrs={'required': False}),
            'provincia': forms.Select(attrs={'required': False}),
            'nombre': forms.TextInput(attrs={'required': False}),
            'tipo': forms.Select(attrs={'required': False}),
            'fecha_creacion': forms.DateInput(attrs={'required': False}),
            'numero_personeria_juridica': forms.TextInput(attrs={'required': False}),
            'fecha_otorgamiento': forms.DateInput(attrs={'required': False}),
            'cuit': forms.NumberInput(attrs={'required': False}),
            'domicilio_legal': forms.TextInput(attrs={'required': False}),
            'autoridad_nombre_completo': forms.TextInput(attrs={'required': False}),
            'autoridad_dni': forms.NumberInput(attrs={'required': False}),
            'autoridad_cuit': forms.NumberInput(attrs={'required': False}),
            'autoridad_rol': forms.TextInput(attrs={'required': False}),
        }

class PersonaFisicaForm(forms.ModelForm):
    class Meta:
        model = PersonaFisica
        fields = [
            'direccion',
            'localidad',
            'codigo_postal',
            'provincia',
            'nombre_completo',
            'dni',
            'fecha_nacimiento',
            'cuil',
            'domicilio_real',
            'mail',
            'telefono'
        ]
        widgets = {
            'direccion': forms.TextInput(attrs={'required': False}),
            'localidad': forms.TextInput(attrs={'required': False}),
            'codigo_postal': forms.NumberInput(attrs={'required': False}),
            'provincia': forms.Select(attrs={'required': False}),
            'nombre_completo': forms.TextInput(attrs={'required': False}),
            'dni': forms.NumberInput(attrs={'required': False}),
            'fecha_nacimiento': forms.DateInput(attrs={'required': False}),
            'cuil': forms.NumberInput(attrs={'required': False}),
            'domicilio_real': forms.TextInput(attrs={'required': False}),
            'mail': forms.EmailInput(attrs={'required': False}),
            'telefono': forms.TextInput(attrs={'required': False}),
        }

class AnexoSocioProductivoForm(forms.ModelForm):
    TIPO_PERSONA_CHOICES = [
        ('juridica', 'Persona Jurídica'),
        ('humana', 'Persona Humana'),
    ]

    tipo_persona = forms.ChoiceField(choices=TIPO_PERSONA_CHOICES, widget=forms.RadioSelect)

    class Meta:
        model = AnexoSocioProductivo
        fields = ['proyecto', 'personeria', 'linea_de_accion', 'acta_constitutiva', 'estatuto', 'personeria_juridica', 'designacion_autoridades', 'autorizacion_gestionar', 'designacion_intendente', 'media']

class DatosProyectoForm(forms.ModelForm):
    class Meta:
        model = AbstractPersoneria
        fields = [
            'direccion',
            'localidad',
            'codigo_postal',
            'provincia',
            'proyecto_nombre',
            'proyecto_tipo_actividad',
            'proyecto_rubro',
            'proyecto_objetivo',
            'proyecto_costo',
            'proyecto_pertenece_comunidad_indigena',
            'proyecto_comunidad_indigena',
            'proyecto_practicas_regenerativas'
        ]    