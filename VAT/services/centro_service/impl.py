from VAT.models import Centro


def puede_operar(centro):
    if centro.tipo == "adherido":
        return centro.faro_asociado and centro.faro_asociado.activo
    return True


def obtener_centros_adheridos_de_faro(faro):
    return Centro.objects.filter(faro_asociado=faro, activo=True)
