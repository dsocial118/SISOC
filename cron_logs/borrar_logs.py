import os
import datetime
import shutil


def borrar_carpetas_logs_viejas(logs_dir):
    """
    Borra las carpetas de logs que tienen más de 30 días de antigüedad.

    :param logs_dir: Ruta del directorio donde se encuentran las carpetas de logs.
    """
    if not os.path.exists(logs_dir):
        print(f"La ruta especificada no existe: {logs_dir}")
        return

    limite_fecha = datetime.datetime.now() - datetime.timedelta(days=30)
    for carpeta in os.listdir(logs_dir):
        carpeta_path = os.path.join(logs_dir, carpeta)

        # Verificar si es una carpeta
        if os.path.isdir(carpeta_path):
            try:
                # Intentar convertir el nombre de la carpeta en una fecha (formato año-mes-dia)
                fecha_carpeta = datetime.datetime.strptime(carpeta, "%Y-%m-%d")

                # Si la carpeta es más antigua que la fecha límite, eliminarla
                if fecha_carpeta < limite_fecha:
                    print(f"Borrando carpeta: {carpeta_path}")
                    shutil.rmtree(carpeta_path)  # Eliminar la carpeta y su contenido
            except ValueError:
                print(f"Formato inválido para la carpeta: {carpeta}")
        else:
            print(f"'{carpeta}' no es una carpeta válida en {logs_dir}")


if __name__ == "__main__":
    # Ruta del directorio donde se encuentran las carpetas de logs
    logs_dir = "C:/Users/nehue/Documents/SISOC-Backoffice/logs/"  # Cambia esto por la ruta real de tus logs

    borrar_carpetas_logs_viejas(logs_dir)
