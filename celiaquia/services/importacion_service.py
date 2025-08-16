# services/importacion_service.py
import logging
from io import BytesIO

import pandas as pd
from django.core.exceptions import ValidationError
from django.db import transaction

from celiaquia.models import EstadoLegajo, ExpedienteCiudadano

logger = logging.getLogger(__name__)


class ImportacionService:
    @staticmethod
    def preview_excel(archivo_excel, max_rows=5):
        """
        Lee el Excel subido y devuelve:
          - headers: lista de columnas normalizadas
          - rows: primeras N filas (N = max_rows)
          - total_rows: cantidad total de filas en el archivo
          - shown_rows: cuántas filas se están mostrando en 'rows'

        Notas:
        - Si max_rows es None o "none", se devuelven todas las filas (¡ojo con archivos grandes!).
        - Mantiene la conversión de fechas de 'fecha_nacimiento' si existe.
        """
        # Asegurar lectura desde el inicio
        try:
            archivo_excel.open()
        except Exception:
            pass
        archivo_excel.seek(0)
        data = archivo_excel.read()

        # Leer como Excel (openpyxl), igual que en tu versión estable
        try:
            df = pd.read_excel(BytesIO(data), engine="openpyxl")
        except Exception as e:
            raise ValidationError(f"Error al leer Excel: {e}")

        # Normalizar encabezados
        df.columns = [str(col).strip().lower().replace(" ", "_") for col in df.columns]
        df = df.fillna("")

        # Convertir fechas si aplica
        if "fecha_nacimiento" in df.columns:
            df["fecha_nacimiento"] = df["fecha_nacimiento"].apply(
                lambda x: x.date() if hasattr(x, "date") else x
            )

        total_rows = len(df)

        # Determinar límite
        show_all = max_rows is None or (isinstance(max_rows, str) and str(max_rows).lower() == "none")
        if show_all:
            sample_df = df
        else:
            try:
                n = int(max_rows)
            except (TypeError, ValueError):
                n = 5  # default
            if n <= 0:
                n = 5
            sample_df = df.head(n)

        sample = sample_df.to_dict(orient="records")
        return {
            "headers": list(df.columns),
            "rows": sample,
            "total_rows": total_rows,
            "shown_rows": len(sample),
        }

    @staticmethod
    @transaction.atomic
    def importar_legajos_desde_excel(expediente, archivo_excel, usuario, batch_size=500):
        """
        Importa legajos desde el Excel subido:
        - Normaliza encabezados y campos.
        - Crea Ciudadano (vía CiudadanoService) y ExpedienteCiudadano en batches.
        - Valida encabezados esperados (misma lógica que tu versión estable).
        - Requiere que luego cada legajo tenga su archivo (validación existente).
        """
        # Import local para evitar circularidad
        from celiaquia.services.ciudadano_service import CiudadanoService

        # Asegurar lectura desde el inicio
        try:
            archivo_excel.open()
        except Exception:
            pass
        archivo_excel.seek(0)
        data = archivo_excel.read()

        try:
            df = pd.read_excel(BytesIO(data), engine="openpyxl")
        except Exception as e:
            raise ValidationError(f"No se pudo leer Excel: {e}")

        # Normalizar encabezados
        df.columns = [str(col).strip().lower().replace(" ", "_") for col in df.columns]
        expected = [
            "nombre",
            "apellido",
            "documento",
            "fecha_nacimiento",
            "tipo_documento",
            "sexo",
        ]
        if set(df.columns) != set(expected):
            raise ValidationError(
                f"Encabezados inválidos: {list(df.columns)} — esperados: {expected}"
            )

        # Reordenar y limpiar
        df = df[expected]
        df = df.fillna("")
        if "fecha_nacimiento" in df.columns:
            df["fecha_nacimiento"] = df["fecha_nacimiento"].apply(
                lambda x: x.date() if hasattr(x, "date") else x
            )

        estado_inicial = EstadoLegajo.objects.get(nombre="DOCUMENTO_PENDIENTE")
        validos = errores = 0
        detalles_errores = []
        batch = []

        # Empezamos en 2 para reflejar fila real de Excel (1 = encabezados)
        for offset, row in enumerate(df.to_dict(orient="records"), start=2):
            logger.debug(f"Fila {offset}: {row}")
            try:
                ciudadano = CiudadanoService.get_or_create_ciudadano(row, usuario)
                batch.append(
                    ExpedienteCiudadano(
                        expediente=expediente,
                        ciudadano=ciudadano,
                        estado=estado_inicial,
                    )
                )
                validos += 1
            except Exception as e:
                errores += 1
                detalles_errores.append({"fila": offset, "error": str(e)})
                logger.error(f"Error fila {offset}: {e}")

            if len(batch) >= batch_size:
                ExpedienteCiudadano.objects.bulk_create(batch)
                batch.clear()

        if batch:
            ExpedienteCiudadano.objects.bulk_create(batch)

        logger.info(f"Import completo: {validos} válidos, {errores} errores")

        # Validación: todos los legajos con archivo antes de continuar
        faltantes = ExpedienteCiudadano.objects.filter(
            expediente=expediente, archivo__isnull=True
        ).exists()
        if faltantes:
            raise ValidationError(
                "Debe subir un archivo para cada legajo antes de continuar."
            )

        return {
            "validos": validos,
            "errores": errores,
            "detalles_errores": detalles_errores,
        }
