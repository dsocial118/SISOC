from centrodefamilia.models import Centro

def puede_operar(centro):
    """
    Verifica si un centro puede operar:
    - Si es tipo 'adherido', debe tener un centro faro activo asociado.
    - Si es tipo 'faro', puede operar por defecto.
    """
    if centro.tipo == 'adherido':
        return centro.faro_asociado and centro.faro_asociado.activo
    return True

def obtener_centros_adheridos_de_faro(faro):
    """
    Retorna todos los centros adheridos vinculados a un centro faro específico.
    Solo devuelve los que estén activos.
    """
    return Centro.objects.filter(faro_asociado=faro, activo=True)

def validar_cuit(cuit):
    """
    Verifica que el CUIT sea numérico y tenga entre 10 y 11 dígitos.
    """
    return cuit.isdigit() and len(cuit) in [10, 11]

