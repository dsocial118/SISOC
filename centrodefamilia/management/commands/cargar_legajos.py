import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from centrodefamilia.services.participante_service import ParticipanteService
from ciudadanos.models import TipoDocumento, Sexo, Ciudadano
from datetime import datetime

class Command(BaseCommand):
    help = 'Crea ciudadanos con sus dimensiones desde un archivo Excel'

    def add_arguments(self, parser):
        parser.add_argument('archivo_excel', type=str, help='Ruta al archivo .xlsx')

    def handle(self, *args, **kwargs):
        archivo_excel = kwargs['archivo_excel']

        try:
            df = pd.read_excel(archivo_excel)
        except Exception as e:
            raise CommandError(f"No se pudo leer el archivo: {e}")

        exitosos = 0
        errores = []
        duplicados = 0

        for i, row in df.iterrows():
            try:
                data = {
                    "nombre": str(row["nombre"]).strip(),
                    "apellido": str(row["apellido"]).strip(),
                    "dni": str(row["dni"]).strip(),
                    "fecha_nacimiento": self.parse_fecha(row["fecha_nacimiento"]),
                    "tipo_documento": self.get_tipo_documento(row.get("tipo_documento")),
                    "genero": self.get_sexo(row.get("genero")),
                }

                if not self.ciudadano_ya_existe(data["tipo_documento"], data["dni"]):
                    ParticipanteService.crear_ciudadano_con_dimensiones(data)
                    exitosos += 1
                else:
                    self.stdout.write(self.style.NOTICE(f"Fila {i + 2}: Ciudadano duplicado (omitido)"))
                    duplicados += 1

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error en fila {i + 2}: {e}"))
                errores.append(i + 2)

        self.stdout.write(self.style.SUCCESS(f"{exitosos} ciudadanos creados correctamente."))
        self.stdout.write(self.style.WARNING(f"{duplicados} ciudadanos omitidos por duplicado."))
        if errores:
            self.stdout.write(self.style.ERROR(f"Errores en filas: {errores}"))

    def parse_fecha(self, valor):
        if isinstance(valor, datetime):
            return valor.date()
        try:
            return datetime.strptime(str(valor), "%Y-%m-%d").date()
        except:
            return None

    def get_tipo_documento(self, valor):
        try:
            if isinstance(valor, int) or str(valor).isdigit():
                return TipoDocumento.objects.get(id=int(valor))
            return TipoDocumento.objects.get(nombre__iexact=str(valor).strip())
        except TipoDocumento.DoesNotExist:
            raise ValueError(f"TipoDocumento no encontrado: {valor}")

    def get_sexo(self, valor):
        try:
            if isinstance(valor, int) or str(valor).isdigit():
                return Sexo.objects.get(id=int(valor))
            return Sexo.objects.get(nombre__iexact=str(valor).strip())
        except Sexo.DoesNotExist:
            raise ValueError(f"Sexo no encontrado: {valor}")

    def ciudadano_ya_existe(self, tipo_documento, dni):
        return Ciudadano.objects.filter(tipo_documento=tipo_documento, documento=dni).exists()
