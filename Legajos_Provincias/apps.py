from django.apps import AppConfig


class LegajosProvinciasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Legajos_Provincias'

class LegajosProvinciasConfig(AppConfig):
    name = 'Legajos_Provincias'
    verbose_name = 'Legajos y Provincias'

    def ready(self):
        import Legajos_Provincias.signals