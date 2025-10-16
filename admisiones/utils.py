from collections import Counter
import logging

logger = logging.getLogger(__name__)

try:
    from num2words import num2words
except ImportError:

    def num2words(num, lang="es"):
        return str(num)


def generar_texto_comidas(informe):
    try:
        resultado = {}

        comidas = {
            "Desayunos": [
                informe.solicitudes_desayuno_lunes,
                informe.solicitudes_desayuno_martes,
                informe.solicitudes_desayuno_miercoles,
                informe.solicitudes_desayuno_jueves,
                informe.solicitudes_desayuno_viernes,
                informe.solicitudes_desayuno_sabado,
                informe.solicitudes_desayuno_domingo,
            ],
            "Almuerzos": [
                informe.solicitudes_almuerzo_lunes,
                informe.solicitudes_almuerzo_martes,
                informe.solicitudes_almuerzo_miercoles,
                informe.solicitudes_almuerzo_jueves,
                informe.solicitudes_almuerzo_viernes,
                informe.solicitudes_almuerzo_sabado,
                informe.solicitudes_almuerzo_domingo,
            ],
            "Meriendas": [
                informe.solicitudes_merienda_lunes,
                informe.solicitudes_merienda_martes,
                informe.solicitudes_merienda_miercoles,
                informe.solicitudes_merienda_jueves,
                informe.solicitudes_merienda_viernes,
                informe.solicitudes_merienda_sabado,
                informe.solicitudes_merienda_domingo,
            ],
            "Cenas": [
                informe.solicitudes_cena_lunes,
                informe.solicitudes_cena_martes,
                informe.solicitudes_cena_miercoles,
                informe.solicitudes_cena_jueves,
                informe.solicitudes_cena_viernes,
                informe.solicitudes_cena_sabado,
                informe.solicitudes_cena_domingo,
            ],
        }

        for tipo, valores in comidas.items():
            contador = Counter(valores)
            lineas = []
            for cantidad, veces in sorted(contador.items(), key=lambda x: -x[1]):
                if cantidad is not None and cantidad > 0:
                    linea = (
                        f"<li>Por la cantidad de {cantidad} &lt;{num2words(cantidad, lang='es')}&gt; prestaciones, "
                        f"&lt;{num2words(veces, lang='es')}&gt; {veces} veces por semana.</li>"
                    )
                    lineas.append(linea)
            resultado[tipo] = (
                f"<ul>{''.join(lineas)}</ul>"
                if lineas
                else "<ul><li>No se solicitan.</li></ul>"
            )

        return resultado
    except Exception:
        logger.exception(
            "Error generando texto de comidas",
            extra={"informe_id": getattr(informe, "id", None)},
        )
        return {
            "Desayunos": "<ul><li>Error al procesar datos</li></ul>",
            "Almuerzos": "<ul><li>Error al procesar datos</li></ul>",
            "Meriendas": "<ul><li>Error al procesar datos</li></ul>",
            "Cenas": "<ul><li>Error al procesar datos</li></ul>",
        }
