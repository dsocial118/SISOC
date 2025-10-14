from django import template

register = template.Library()


@register.filter
def numero_a_palabra(value):
    """Convierte un número a su representación en palabras"""
    numeros = {
        0: "cero",
        1: "uno",
        2: "dos",
        3: "tres",
        4: "cuatro",
        5: "cinco",
        6: "seis",
        7: "siete",
        8: "ocho",
        9: "nueve",
        10: "diez",
        11: "once",
        12: "doce",
        13: "trece",
        14: "catorce",
        15: "quince",
        16: "dieciséis",
        17: "diecisiete",
        18: "dieciocho",
        19: "diecinueve",
        20: "veinte",
        21: "veintiuno",
        22: "veintidós",
        23: "veintitrés",
        24: "veinticuatro",
        25: "veinticinco",
        26: "veintiséis",
        27: "veintisiete",
        28: "veintiocho",
        29: "veintinueve",
        30: "treinta",
        40: "cuarenta",
        50: "cincuenta",
        60: "sesenta",
        70: "setenta",
        80: "ochenta",
        90: "noventa",
    }

    try:
        num = int(value)
        if num in numeros:
            return numeros[num]
        elif 30 < num < 40:
            return f"treinta y {numeros[num - 30]}"
        elif 40 < num < 50:
            return f"cuarenta y {numeros[num - 40]}"
        elif 50 < num < 60:
            return f"cincuenta y {numeros[num - 50]}"
        elif 60 < num < 70:
            return f"sesenta y {numeros[num - 60]}"
        elif 70 < num < 80:
            return f"setenta y {numeros[num - 70]}"
        elif 80 < num < 90:
            return f"ochenta y {numeros[num - 80]}"
        elif 90 < num < 100:
            return f"noventa y {numeros[num - 90]}"
        else:
            return str(num)
    except (ValueError, TypeError):
        return str(value)


@register.filter
def agrupar_comidas(informe, tipo_comida):
    """Agrupa las comidas por cantidad y cuenta los días"""
    dias = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
    cantidades = {}

    for dia in dias:
        campo = f"solicitudes_{tipo_comida}_{dia}"
        cantidad = getattr(informe, campo, 0)
        if cantidad > 0:
            if cantidad not in cantidades:
                cantidades[cantidad] = 0
            cantidades[cantidad] += 1

    return cantidades
