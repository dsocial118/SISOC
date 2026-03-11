from pwa.catalogo_seed import bootstrap_catalogo_actividades


def seed_catalogo_actividades(sender, **kwargs):
    bootstrap_catalogo_actividades(using=kwargs.get("using", "default"))
