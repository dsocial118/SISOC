# services/importacion_service.py
import pandas as pd
from io import BytesIO
from django.db import transaction
from django.core.exceptions import ValidationError

from celiaquia.models import EstadoLegajo, ExpedienteCiudadano
from celiaquia.services.ciudadano_service import CiudadanoService

class ImportacionService:
    @staticmethod
    def preview_excel(archivo_excel, max_rows=5):
        """
        Lee un Excel completo con pandas y devuelve:
         - headers: lista de nombres normalizados
         - rows: hasta max_rows filas como dicts (clave=columna)
        """
        archivo_excel.open()
        archivo_excel.seek(0)
        data = archivo_excel.read()

        try:
            df = pd.read_excel(BytesIO(data), engine='openpyxl')
        except Exception as e:
            raise ValidationError(f"Error al leer Excel con pandas: {e}")

        # Normalizar encabezados
        df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]

        # Evitar NaN y convertir timestamps
        df = df.fillna('')
        if 'fecha_nacimiento' in df.columns:
            df['fecha_nacimiento'] = df['fecha_nacimiento'].apply(
                lambda x: x.date() if hasattr(x, 'date') else x
            )

        # Aquí volvemos a dicts
        sample = df.head(max_rows).to_dict(orient='records')
        return {
            'headers': list(df.columns),
            'rows': sample
        }

    @staticmethod
    @transaction.atomic
    def importar_legajos_desde_excel(expediente, archivo_excel, batch_size=500):
        """
        Importa todos los legajos desde el Excel usando pandas:
          - Valida encabezados (tolerando orden distinto)
          - Bulk-create en lotes
          - Registra detalles de errores
        Devuelve dict con 'validos', 'errores' y 'detalles_errores'.
        """
        # Leer datos
        archivo_excel.open()
        archivo_excel.seek(0)
        data = archivo_excel.read()
        try:
            df = pd.read_excel(BytesIO(data), engine='openpyxl')
        except Exception as e:
            raise ValidationError(f"No se pudo leer Excel: {e}")

        # Normalizar encabezados
        df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
        expected = ['nombre', 'apellido', 'documento', 'fecha_nacimiento', 'tipo_documento', 'sexo']
        if set(df.columns) != set(expected):
            raise ValidationError(
                f"Encabezados inválidos: {list(df.columns)} – se esperaban: {expected}"
            )

        # Reordenar columnas según expected
        df = df[[col for col in expected if col in df.columns]]
        df = df.fillna('')
        if 'fecha_nacimiento' in df.columns:
            df['fecha_nacimiento'] = df['fecha_nacimiento'].apply(
                lambda x: x.date() if hasattr(x, 'date') else x
            )

        estado_inicial = EstadoLegajo.objects.get(nombre='DOCUMENTO_PENDIENTE')
        validos = errores = 0
        detalles_errores = []
        batch = []

        # Iterar filas con índice en hoja
        for offset, row in enumerate(df.to_dict(orient='records'), start=2):
            try:
                ciudadano = CiudadanoService.get_or_create_ciudadano(row)
                batch.append(
                    ExpedienteCiudadano(
                        expediente=expediente,
                        ciudadano=ciudadano,
                        estado=estado_inicial
                    )
                )
                validos += 1
            except Exception as e:
                errores += 1
                detalles_errores.append({'fila': offset, 'error': str(e)})

            if len(batch) >= batch_size:
                ExpedienteCiudadano.objects.bulk_create(batch)
                batch.clear()

        # Procesar resto de batch
        if batch:
            ExpedienteCiudadano.objects.bulk_create(batch)

        return {
            'validos': validos,
            'errores': errores,
            'detalles_errores': detalles_errores
        }
