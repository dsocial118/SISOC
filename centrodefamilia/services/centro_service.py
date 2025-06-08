from centrodefamilia.models import Centro

def puede_operar(centro):
    """
    Verifica si un centro puede operar:
    - Si es tipo 'adherido', debe tener un centro faro activo.
    - Si es tipo 'faro', puede operar directamente.
    """
    if centro.tipo == 'adherido':
        return centro.faro_asociado and centro.faro_asociado.activo
    return True

def obtener_centros_adheridos_de_faro(faro):
    """
    Retorna todos los centros adheridos activos vinculados a un faro dado.
    """
    return Centro.objects.filter(faro_asociado=faro, activo=True)
