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

        if os.path.isdir(carpeta_path):
            try:
                fecha_carpeta = datetime.datetime.strptime(carpeta, "%Y-%m-%d")

                if fecha_carpeta < limite_fecha:
                    print(f"Borrando carpeta: {carpeta_path}")
                    shutil.rmtree(carpeta_path)  # Eliminar la carpeta y su contenido
            except ValueError:
                print(f"Formato inválido para la carpeta: {carpeta}")
        else:
            print(f"'{carpeta}' no es una carpeta válida en {logs_dir}")


if __name__ == "__main__":
    # Ruta del directorio donde se encuentran las carpetas de logs
    logs_dir = ""  # Cambia esto por la ruta real de tus logs

    borrar_carpetas_logs_viejas(logs_dir)
