from io import BytesIO

from PIL import Image


def recortar_imagen(imagen):
    imagen = Image.open(imagen)
    tamano_minimo = min(imagen.width, imagen.height)
    area = (0, 0, tamano_minimo, tamano_minimo)
    imagen_recortada = imagen.crop(area)

    buffer = BytesIO()
    imagen_recortada.save(buffer, format="PNG")
    return buffer
