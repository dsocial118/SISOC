from django.db.models.signals import post_migrate
from django.dispatch import receiver
from Legajos_Provincias.models import Provincias

@receiver(post_migrate)
def load_provincias(sender, **kwargs):
    if sender.name == 'Legajos_Provincias':
        provincias = [
            "Buenos Aires", "CABA", "Catamarca", "Chaco",
            "Chubut", "Córdoba", "Corrientes", "Entre Ríos", "Formosa", "Jujuy",
            "La Pampa", "La Rioja", "Mendoza", "Misiones", "Neuquen", "Río Negro",
            "Salta", "San Juan", "San Luís", "Santa Cruz", "Santa Fe",
            "Santiago del Estero", "Tierra del Fuego", "Tucumán"
        ]
        for nombre in provincias:
            Provincias.objects.get_or_create(nombre=nombre)
