import tempfile
import pandas as pd
from io import BytesIO
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from celiaquia.models import Expediente, EstadoExpediente, ExpedienteCiudadano
from celiaquia.services.importacion_service_optimized import ImportacionServiceOptimized
from ciudadanos.models import TipoDocumento
from core.models import Provincia

User = get_user_model()


class ImportacionOptimizadaTest(TestCase):
    def setUp(self):
        # Crear datos de prueba
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='testpass123'
        )
        
        # Crear provincia
        self.provincia = Provincia.objects.create(nombre='Test Provincia')
        
        # Crear tipo de documento CUIT
        self.tipo_doc_cuit = TipoDocumento.objects.create(
            tipo='CUIT',
            codigo='CUIT'
        )
        
        # Crear estado de expediente
        self.estado_expediente = EstadoExpediente.objects.create(
            nombre='CREADO'
        )
        
        # Crear expediente
        self.expediente = Expediente.objects.create(
            usuario_provincia=self.user,
            estado=self.estado_expediente
        )

    def create_test_excel(self, num_rows=150):
        """Crea un archivo Excel de prueba con el número especificado de filas"""
        data = []
        for i in range(num_rows):
            data.append({
                'apellido': f'Apellido{i}',
                'nombre': f'Nombre{i}',
                'documento': f'2012345678{i:02d}',  # CUIT format
                'fecha_nacimiento': '1990-01-01',
                'sexo': 'Masculino',
                'email': f'test{i}@example.com',
                'telefono': f'11234567{i:02d}',
            })
        
        df = pd.DataFrame(data)
        
        # Crear archivo en memoria
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        
        return SimpleUploadedFile(
            "test_legajos.xlsx",
            output.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    def test_importacion_optimizada_funciona(self):
        """Test básico de que la importación optimizada funciona"""
        # Crear archivo de prueba
        excel_file = self.create_test_excel(150)
        
        try:
            # Ejecutar importación optimizada
            result = ImportacionServiceOptimized.importar_legajos_desde_excel_optimized(
                self.expediente, excel_file, self.user
            )
            
            # Verificar resultados
            self.assertIsInstance(result, dict)
            self.assertIn('validos', result)
            self.assertIn('errores', result)
            self.assertIn('excluidos_count', result)
            
            # Verificar que se crearon legajos
            legajos_count = ExpedienteCiudadano.objects.filter(
                expediente=self.expediente
            ).count()
            
            self.assertGreater(legajos_count, 0)
            self.assertEqual(legajos_count, result['validos'])
            
        except Exception as e:
            self.fail(f"La importación optimizada falló: {e}")

    def test_manejo_errores_datos_invalidos(self):
        """Test de manejo de errores con datos inválidos"""
        # Crear datos con errores
        data = [
            {
                'apellido': '',  # Apellido vacío
                'nombre': 'Nombre1',
                'documento': '20123456781',
                'fecha_nacimiento': '1990-01-01',
            },
            {
                'apellido': 'Apellido2',
                'nombre': 'Nombre2',
                'documento': 'INVALID',  # Documento inválido
                'fecha_nacimiento': '1990-01-01',
            }
        ]
        
        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        
        excel_file = SimpleUploadedFile(
            "test_errores.xlsx",
            output.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        try:
            result = ImportacionServiceOptimized.importar_legajos_desde_excel_optimized(
                self.expediente, excel_file, self.user
            )
            
            # Debe manejar errores sin fallar completamente
            self.assertIsInstance(result, dict)
            self.assertGreaterEqual(result['errores'], 1)
            
        except Exception as e:
            self.fail(f"El manejo de errores falló: {e}")

    def test_compatibilidad_con_version_original(self):
        """Test de que los resultados son compatibles con la versión original"""
        excel_file = self.create_test_excel(50)  # Archivo pequeño
        
        try:
            result = ImportacionServiceOptimized.importar_legajos_desde_excel_optimized(
                self.expediente, excel_file, self.user
            )
            
            # Verificar estructura de respuesta compatible
            required_keys = ['validos', 'errores', 'detalles_errores', 'excluidos_count', 'excluidos', 'warnings']
            for key in required_keys:
                self.assertIn(key, result, f"Falta clave requerida: {key}")
                
        except Exception as e:
            self.fail(f"Test de compatibilidad falló: {e}")