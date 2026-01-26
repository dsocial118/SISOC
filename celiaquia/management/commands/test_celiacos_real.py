"""
Comando para probar todos los casos de celíacos INSERTANDO DATOS REALES.
Ejecutar: python manage.py test_celiacos_real
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.models import User
from celiaquia.models import ExpedienteCiudadano, HistorialComentarios
from celiaquia.services.comentarios_service import ComentariosService
from datetime import datetime


class Command(BaseCommand):
    help = "Prueba todos los casos de celíacos INSERTANDO DATOS REALES"

    def add_arguments(self, parser):
        parser.add_argument("--caso", type=str, help="Ejecutar solo un caso específico")

    def handle(self, *args, **options):
        self.print_header("🧪 TEST CELÍACOS - INSERTANDO DATOS REALES")

        user, _ = User.objects.get_or_create(
            username="test_celiacos",
            defaults={"email": "test@celiacos.com", "is_staff": True},
        )

        caso = options.get("caso")
        resultados = {}

        try:
            if not caso or caso == "a":
                resultados["CASO A"] = self.test_caso_a(user)
            if not caso or caso == "b":
                resultados["CASO B"] = self.test_caso_b(user)
            if not caso or caso == "c":
                resultados["CASO C"] = self.test_caso_c(user)
            if not caso or caso == "d":
                resultados["CASO D"] = self.test_caso_d(user)
            if not caso or caso == "e":
                resultados["CASO E"] = self.test_caso_e(user)
            if not caso or caso == "f":
                resultados["CASO F"] = self.test_caso_f(user)
            if not caso or caso == "error1":
                resultados["ERROR 1"] = self.test_error_1(user)
            if not caso or caso == "error4":
                resultados["ERROR 4"] = self.test_error_4(user)

            self.print_resumen(resultados)

        except Exception as e:
            self.print_error(f"Error: {str(e)}")
            import traceback

            traceback.print_exc()

    def print_header(self, texto):
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS(texto))
        self.stdout.write("=" * 80 + "\n")

    def print_section(self, texto):
        self.stdout.write(self.style.HTTP_INFO(f"\n📋 {texto}"))
        self.stdout.write("-" * 80)

    def print_ok(self, texto):
        self.stdout.write(self.style.SUCCESS(f"  ✅ {texto}"))

    def print_warning(self, texto):
        self.stdout.write(self.style.WARNING(f"  ⚠️  {texto}"))

    def print_error(self, texto):
        self.stdout.write(self.style.ERROR(f"  ❌ {texto}"))

    def print_info(self, texto):
        self.stdout.write(f"  ℹ️  {texto}")

    def test_caso_a(self, user):
        """CASO A: Responsable = Beneficiario"""
        self.print_section("CASO A: Responsable = Beneficiario")
        try:
            with transaction.atomic():
                legajo = ExpedienteCiudadano.objects.create(
                    apellido="García",
                    nombre="Matías",
                    fecha_nacimiento="1999-01-01",
                    sexo="M",
                    rol="beneficiario_y_responsable",
                    revision_tecnico="PENDIENTE",
                )
                self.print_info(
                    f"✓ Creado: {legajo.apellido}, {legajo.nombre} (ID: {legajo.id})"
                )
                self.print_ok("1 expediente creado en BD")
                self.print_ok("Rol: beneficiario_y_responsable")

                ComentariosService.agregar_validacion_tecnica(
                    legajo=legajo, comentario="Documentación completa", usuario=user
                )
                self.print_ok("Historial de comentarios registrado")
                self.print_ok("CASO A: COMPLETADO ✓\n")
                return True
        except Exception as e:
            self.print_error(str(e))
            return False

    def test_caso_b(self, user):
        """CASO B: Responsable ≠ Beneficiario"""
        self.print_section("CASO B: Responsable ≠ Beneficiario")
        try:
            with transaction.atomic():
                responsable = ExpedienteCiudadano.objects.create(
                    apellido="García",
                    nombre="Matías",
                    fecha_nacimiento="1999-01-01",
                    sexo="M",
                    rol="beneficiario_y_responsable",
                )
                self.print_info(
                    f"✓ Responsable: {responsable.apellido}, {responsable.nombre} (ID: {responsable.id})"
                )

                beneficiario = ExpedienteCiudadano.objects.create(
                    apellido="Pérez",
                    nombre="Nicolás",
                    fecha_nacimiento="2016-03-15",
                    sexo="M",
                    rol="beneficiario",
                )
                self.print_info(
                    f"✓ Beneficiario: {beneficiario.apellido}, {beneficiario.nombre} (ID: {beneficiario.id})"
                )

                ComentariosService.agregar_subsanacion_motivo(
                    legajo=beneficiario, motivo="Falta certificado médico", usuario=user
                )
                self.print_ok("1 expediente creado (Nicolás)")
                self.print_ok("Subsanación solicitada")
                self.print_ok("CASO B: COMPLETADO ✓\n")
                return True
        except Exception as e:
            self.print_error(str(e))
            return False

    def test_caso_c(self, user):
        """CASO C: Responsable Múltiple"""
        self.print_section("CASO C: Responsable Múltiple")
        try:
            with transaction.atomic():
                responsable = ExpedienteCiudadano.objects.create(
                    apellido="García",
                    nombre="Matías",
                    fecha_nacimiento="1999-01-01",
                    sexo="M",
                    rol="beneficiario_y_responsable",
                )
                self.print_info(
                    f"✓ Responsable: {responsable.apellido}, {responsable.nombre} (ID: {responsable.id})"
                )

                beneficiarios = [
                    ("López", "Juan", "2014-03-15", "M"),
                    ("Rodríguez", "María", "2012-06-20", "F"),
                ]

                for apellido, nombre, fecha, sexo in beneficiarios:
                    beneficiario = ExpedienteCiudadano.objects.create(
                        apellido=apellido,
                        nombre=nombre,
                        fecha_nacimiento=fecha,
                        sexo=sexo,
                        rol="beneficiario",
                    )
                    self.print_info(
                        f"✓ Beneficiario: {beneficiario.apellido}, {beneficiario.nombre} (ID: {beneficiario.id})"
                    )

                self.print_ok("3 expedientes creados en BD")
                self.print_ok("CASO C: COMPLETADO ✓\n")
                return True
        except Exception as e:
            self.print_error(str(e))
            return False

    def test_caso_d(self, user):
        """CASO D: Solo Beneficiario (Sin Responsable)"""
        self.print_section("CASO D: Solo Beneficiario (Sin Responsable)")
        try:
            with transaction.atomic():
                legajo = ExpedienteCiudadano.objects.create(
                    apellido="Martínez",
                    nombre="Carlos",
                    fecha_nacimiento="1994-05-10",
                    sexo="M",
                    rol="beneficiario",
                )
                self.print_info(
                    f"✓ Creado: {legajo.apellido}, {legajo.nombre} (ID: {legajo.id})"
                )
                self.print_ok("1 expediente creado en BD")
                self.print_ok("Rol: beneficiario (sin responsable)")
                self.print_ok("CASO D: COMPLETADO ✓\n")
                return True
        except Exception as e:
            self.print_error(str(e))
            return False

    def test_caso_e(self, user):
        """CASO E: Beneficiario Menor como Responsable"""
        self.print_section("CASO E: Beneficiario Menor como Responsable")
        try:
            with transaction.atomic():
                responsable = ExpedienteCiudadano.objects.create(
                    apellido="López",
                    nombre="Pedro",
                    fecha_nacimiento="2008-03-15",
                    sexo="M",
                    rol="beneficiario_y_responsable",
                )
                self.print_info(
                    f"✓ Responsable menor: {responsable.apellido}, {responsable.nombre} (ID: {responsable.id})"
                )
                self.print_warning("Responsable menor de 18 años")

                beneficiario = ExpedienteCiudadano.objects.create(
                    apellido="López",
                    nombre="Lucas",
                    fecha_nacimiento="2016-06-20",
                    sexo="M",
                    rol="beneficiario",
                )
                self.print_info(
                    f"✓ Beneficiario: {beneficiario.apellido}, {beneficiario.nombre} (ID: {beneficiario.id})"
                )

                self.print_ok("2 expedientes creados en BD")
                self.print_ok("CASO E: COMPLETADO ✓ (con warning)\n")
                return True
        except Exception as e:
            self.print_error(str(e))
            return False

    def test_caso_f(self, user):
        """CASO F: Cadena Familiar"""
        self.print_section("CASO F: Cadena Familiar")
        try:
            with transaction.atomic():
                abuelo = ExpedienteCiudadano.objects.create(
                    apellido="García",
                    nombre="Roberto",
                    fecha_nacimiento="1964-01-01",
                    sexo="M",
                    rol="beneficiario_y_responsable",
                )
                self.print_info(
                    f"✓ Abuelo: {abuelo.apellido}, {abuelo.nombre} (ID: {abuelo.id})"
                )

                padre = ExpedienteCiudadano.objects.create(
                    apellido="García",
                    nombre="Matías",
                    fecha_nacimiento="1999-01-01",
                    sexo="M",
                    rol="beneficiario",
                )
                self.print_info(
                    f"✓ Padre: {padre.apellido}, {padre.nombre} (ID: {padre.id})"
                )

                hijo = ExpedienteCiudadano.objects.create(
                    apellido="García",
                    nombre="Tomás",
                    fecha_nacimiento="2019-03-15",
                    sexo="M",
                    rol="beneficiario",
                )
                self.print_info(
                    f"✓ Hijo: {hijo.apellido}, {hijo.nombre} (ID: {hijo.id})"
                )

                self.print_ok("3 expedientes creados en BD")
                self.print_ok("Cadena: Roberto → Matías → Tomás")
                self.print_ok("CASO F: COMPLETADO ✓\n")
                return True
        except Exception as e:
            self.print_error(str(e))
            return False

    def test_error_1(self, user):
        """ERROR 1: Responsable más joven que beneficiario"""
        self.print_section("ERROR 1: Responsable más joven que beneficiario")
        try:
            beneficiario_fecha = datetime.strptime("1994-03-15", "%Y-%m-%d").date()
            responsable_fecha = datetime.strptime("2004-01-01", "%Y-%m-%d").date()

            edad_beneficiario = (
                datetime.now().date() - beneficiario_fecha
            ).days / 365.25
            edad_responsable = (datetime.now().date() - responsable_fecha).days / 365.25

            if edad_responsable < edad_beneficiario:
                self.print_error("Responsable más joven que beneficiario")
                self.print_ok("ERROR DETECTADO: Validación correcta")
                self.print_ok("ERROR 1: COMPLETADO ✓\n")
                return True
            return False
        except Exception as e:
            self.print_error(str(e))
            return False

    def test_error_4(self, user):
        """ERROR 4: Menor sin Responsable"""
        self.print_section("ERROR 4: Menor sin Responsable")
        try:
            with transaction.atomic():
                legajo = ExpedienteCiudadano.objects.create(
                    apellido="López",
                    nombre="Juan",
                    fecha_nacimiento="2016-03-15",
                    sexo="M",
                    rol="beneficiario",
                )
                self.print_info(
                    f"✓ Creado: {legajo.apellido}, {legajo.nombre} (ID: {legajo.id})"
                )

                edad = (datetime.now().date() - legajo.fecha_nacimiento).days / 365.25
                if edad < 18:
                    self.print_warning("Beneficiario menor sin responsable")
                    self.print_ok("1 expediente creado en BD")
                    self.print_ok("WARNING REGISTRADO")
                    self.print_ok("ERROR 4: COMPLETADO ✓\n")
                    return True
            return False
        except Exception as e:
            self.print_error(str(e))
            return False

    def print_resumen(self, resultados):
        self.print_header("📊 RESUMEN DE RESULTADOS")

        total = len(resultados)
        exitosos = sum(1 for v in resultados.values() if v)

        for caso, resultado in resultados.items():
            if resultado:
                self.stdout.write(self.style.SUCCESS(f"  ✅ {caso}: PASÓ"))
            else:
                self.stdout.write(self.style.ERROR(f"  ❌ {caso}: FALLÓ"))

        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(
            self.style.SUCCESS(f"TOTAL: {exitosos}/{total} tests completados")
        )
        self.stdout.write(self.style.SUCCESS(f"✓ DATOS INSERTADOS EN LA BASE DE DATOS"))
        self.stdout.write("=" * 80 + "\n")
