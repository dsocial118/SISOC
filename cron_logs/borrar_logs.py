import os
import datetime
import shutil


def borrar_carpetas_logs_viejas(directory):
    """
    Borra las carpetas de logs que tienen más de 30 días de antigüedad.

    :param directory: Ruta del directorio donde se encuentran las carpetas de logs.
    """
    if not os.path.exists(directory):
        print(f"La ruta especificada no existe: {directory}")
        return

    limite_fecha = datetime.datetime.now() - datetime.timedelta(days=7
    for carpeta in os.listdir(directory):
        carpeta_path = os.path.join(directory, carpeta)

        if os.path.isdir(carpeta_path):
            try:
                fecha_carpeta = datetime.datetime.strptime(carpeta, "%Y-%m-%d")

                if fecha_carpeta < limite_fecha:
                    print(f"Borrando carpeta: {carpeta_path}")
                    shutil.rmtree(carpeta_path)  # Eliminar la carpeta y su contenido
            except ValueError:
                print(f"Formato inválido para la carpeta: {carpeta}")
        else:
            print(f"'{carpeta}' no es una carpeta válida en {directory}")


if __name__ == "__main__":
    # Ruta del directorio donde se encuentran las carpetas de logs
    LOGS_DIR = "/home/admin-ssies/SISOC-Backoffice/logs/"

    borrar_carpetas_logs_viejas(LOGS_DIR)
