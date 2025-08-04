from collections import Counter
from num2words import num2words  # pip install num2words


def generar_texto_comidas(anexo):
    resultado = {}

    comidas = {
        "Desayunos": [
            anexo.desayuno_lunes,
            anexo.desayuno_martes,
            anexo.desayuno_miercoles,
            anexo.desayuno_jueves,
            anexo.desayuno_viernes,
            anexo.desayuno_sabado,
            anexo.desayuno_domingo,
        ],
        "Almuerzos": [
            anexo.almuerzo_lunes,
            anexo.almuerzo_martes,
            anexo.almuerzo_miercoles,
            anexo.almuerzo_jueves,
            anexo.almuerzo_viernes,
            anexo.almuerzo_sabado,
            anexo.almuerzo_domingo,
        ],
        "Meriendas": [
            anexo.merienda_lunes,
            anexo.merienda_martes,
            anexo.merienda_miercoles,
            anexo.merienda_jueves,
            anexo.merienda_viernes,
            anexo.merienda_sabado,
            anexo.merienda_domingo,
        ],
        "Cenas": [
            anexo.cena_lunes,
            anexo.cena_martes,
            anexo.cena_miercoles,
            anexo.cena_jueves,
            anexo.cena_viernes,
            anexo.cena_sabado,
            anexo.cena_domingo,
        ],
    }

    for tipo, valores in comidas.items():
        contador = Counter(valores)
        lineas = []
        for cantidad, veces in sorted(contador.items(), key=lambda x: -x[1]):
            if cantidad is not None:
                linea = (
                    f"<li>Por la cantidad de {cantidad} &lt;{num2words(cantidad, lang='es')}&gt; prestaciones, "
                    f"&lt;{num2words(veces, lang='es')}&gt; {veces} veces por semana.</li>"
                )
                lineas.append(linea)
        resultado[tipo] = f"<ul>{''.join(lineas)}</ul>"

    return resultado
