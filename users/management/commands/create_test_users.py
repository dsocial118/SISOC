from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


def crear_usuario_con_grupos(
    username, email, password, grupos=None, is_superuser=False
):
    user_model = get_user_model()
    user_qs = user_model.objects.filter(username=username)
    if user_qs.exists():
        user = user_qs.first()
        user.email = email  # actualiza email por si cambió
        user.set_password(password)
        user.save()
        creado = False
    else:
        if is_superuser:
            user = user_model.objects.create_superuser(
                username=username, email=email, password=password
            )
        else:
            user = user_model.objects.create_user(
                username=username, email=email, password=password
            )
        creado = True
    # Asignar grupos si es necesario
    if grupos:
        for group_name in grupos:
            group, _ = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)
    return user, creado


class Command(BaseCommand):
    help = "Crea usuarios de testing y sus grupos solo si DEBUG=True"

    def handle(self, *args, **kwargs):
        if settings.DEBUG:
            self.stdout.write("👥 Creando usuarios para test...")

            grupos_abogado = [
                "Abogado Dupla",
                "Acompanamiento Detalle",
                "Acompanamiento Listar",
                "Comedores",
                "Comedores Intervencion Crear",
                "Comedores Intervencion Editar",
                "Comedores Intervencion Ver",
                "Comedores Intervenciones Detalle",
                "Comedores Listar",
            ]
            grupos_tecnico = [
                "Acompanamiento Detalle",
                "Acompanamiento Listar",
                "Comedores",
                "Comedores Editar",
                "Comedores Intervencion Crear",
                "Comedores Intervencion Editar",
                "Comedores Intervencion Ver",
                "Comedores Intervenciones Detalle",
                "Comedores Listar",
                "Comedores Observaciones Crear",
                "Comedores Observaciones Detalle",
                "Comedores Observaciones Editar",
                "Comedores Observaciones Eliminar",
                "Comedores Relevamiento Detalle",
                "Comedores Ver",
                "Tecnico Comedor",
            ]
            grupos_legales = [
                "Comedores",
                "Area Legales",
                "Comedores Relevamiento Ver",
                "Comedores Relevamiento Detalle",
                "Comedores Observaciones Detalle",
                "Comedores Intervencion Ver",
                "Comedores Intervenciones Detalle",
                "Comedores Nomina Ver",
                "Acompanamiento Detalle",
                "Acompanamiento Listar",
            ]
            grupos_coordinador = [
                "Coordinador Equipo Tecnico",
                "Comedores",
                "Comedores Listar",
                "Comedores Ver",
                "Comedores Editar",
                "Comedores Relevamiento Ver",
                "Comedores Relevamiento Detalle",
                "Comedores Observaciones Crear",
                "Comedores Observaciones Detalle",
                "Comedores Observaciones Editar",
                "Comedores Observaciones Eliminar",
                "Comedores Intervencion Ver",
                "Comedores Intervencion Crear",
                "Comedores Intervencion Editar",
                "Comedores Intervenciones Detalle",
                "Comedores Nomina Ver",
                "Acompanamiento Detalle",
                "Acompanamiento Listar",
            ]
            grupos_operador = [
                "Comedores",
                "Comedores Listar",
                "Comedores Ver",
                "Comedores Relevamiento Ver",
                "Comedores Relevamiento Detalle",
                "Comedores Observaciones Crear",
                "Comedores Observaciones Detalle",
                "Comedores Observaciones Editar",
                "Comedores Intervencion Ver",
                "Comedores Intervencion Crear",
                "Comedores Intervencion Editar",
                "Comedores Intervenciones Detalle",
                "Comedores Nomina Ver",
                "Acompanamiento Detalle",
                "Acompanamiento Listar",
            ]
            grupos_auditor = [
                "Comedores",
                "Comedores Listar",
                "Comedores Ver",
                "Comedores Relevamiento Ver",
                "Comedores Relevamiento Detalle",
                "Comedores Observaciones Detalle",
                "Comedores Intervencion Ver",
                "Comedores Intervenciones Detalle",
                "Comedores Nomina Ver",
                "Acompanamiento Detalle",
                "Acompanamiento Listar",
            ]

            usuarios = [
                {
                    "username": "1",
                    "email": "1@gmail.com",
                    "password": "1",
                    "is_superuser": True,
                    "grupos": [],
                },
                {
                    "username": "abogadoqa",
                    "email": "abogadoqa@example.com",
                    "password": "qa1234",
                    "is_superuser": False,
                    "grupos": grupos_abogado,
                },
                {
                    "username": "tecnicoqa",
                    "email": "tecnicoqa@example.com",
                    "password": "qa1234",
                    "is_superuser": False,
                    "grupos": grupos_tecnico,
                },
                {
                    "username": "legalesqa",
                    "email": "legalesqa@example.com",
                    "password": "qa1234",
                    "is_superuser": False,
                    "grupos": grupos_legales,
                },
                {
                    "username": "contableqa",
                    "email": "contableqa@example.com",
                    "password": "qa1234",
                    "is_superuser": False,
                    "grupos": [
                        "Comedores",
                        "Area Contable",
                        "Comedores Relevamiento Ver",
                        "Comedores Relevamiento Detalle",
                        "Comedores Observaciones Detalle",
                        "Comedores Intervencion Ver",
                        "Comedores Intervenciones Detalle",
                        "Comedores Nomina Ver",
                        "Acompanamiento Detalle",
                        "Acompanamiento Listar",
                    ],
                },
                # Usuarios de Centro de Familia (ReferenteCentro + Ciudadanos):
                {
                    "username": "CDF SSE",
                    "email": "rubenarellano@example.com",
                    "password": "8392017",
                    "is_superuser": False,
                    "grupos": ["CDF SSE", "Ciudadanos"],
                },
                {
                    "username": "FARO",
                    "email": "natashabraga@example.com",
                    "password": "5823109",
                    "is_superuser": False,
                    "grupos": ["ReferenteCentro", "Ciudadanos"],
                },
                {
                    "username": "AD",
                    "email": "natashabraga@example.com",
                    "password": "5823109",
                    "is_superuser": False,
                    "grupos": ["ReferenteCentro", "Ciudadanos"],
                },
                {
                    "username": "TecnicoCeliaquia",
                    "email": "natashabraga@example.com",
                    "password": "1",
                    "is_superuser": False,
                    "grupos": ["TecnicoCeliaquia", "Ciudadanos"],
                },
                {
                    "username": "TecnicoCeliaquia2",
                    "email": "natashabraga@example.com",
                    "password": "1",
                    "is_superuser": False,
                    "grupos": ["TecnicoCeliaquia", "Ciudadanos"],
                },
                {
                    "username": "TecnicoCeliaquia3",
                    "email": "natashabraga@example.com",
                    "password": "1",
                    "is_superuser": False,
                    "grupos": ["TecnicoCeliaquia", "Ciudadanos"],
                },
                {
                    "username": "CoordinadorCeliaquia",
                    "email": "natashabraga@example.com",
                    "password": "1",
                    "is_superuser": False,
                    "grupos": ["CoordinadorCeliaquia", "Ciudadanos"],
                },
                {
                    "username": "ProvinciaCeliaquia",
                    "email": "natashabraga@example.com",
                    "password": "1",
                    "is_superuser": False,
                    "grupos": ["ProvinciaCeliaquia", "Ciudadanos"],
                },
            ]

            qa_personas = ["Juan", "Agustina", "Facundo", "Camilo"]
            qa_roles = {
                "legales": grupos_legales,
                "abogado": grupos_abogado,
                "tec": grupos_tecnico,
                "coordinador": grupos_coordinador,
                "operador": grupos_operador,
                "auditor": grupos_auditor,
            }
            for nombre in qa_personas:
                for rol, grupos in qa_roles.items():
                    username = f"{nombre.lower()}{rol}"
                    usuarios.append(
                        {
                            "username": username,
                            "email": f"{username}@example.com",
                            "password": "1",
                            "is_superuser": False,
                            "grupos": grupos,
                        }
                    )

            superadmins = ["asampaulo", "fsuarez", "jalfonso", "cparra"]
            for username in superadmins:
                usuarios.append(
                    {
                        "username": username,
                        "email": f"{username}@example.com",
                        "password": "1",
                        "is_superuser": True,
                        "grupos": [],
                    }
                )

            for conf in usuarios:
                user, creado = crear_usuario_con_grupos(
                    username=conf["username"],
                    email=conf["email"],
                    password=conf["password"],
                    grupos=conf.get("grupos"),
                    is_superuser=conf.get("is_superuser", False),
                )
                tipo = "Superusuario" if conf.get("is_superuser") else "Usuario"
                if creado:
                    self.stdout.write(
                        self.style.SUCCESS(f"{tipo} '{conf['username']}' creado.")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"{tipo} '{conf['username']}' ya existe (actualizado)."
                        )
                    )

            self.stdout.write(self.style.SUCCESS("Proceso completado."))
