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
        if not settings.DEBUG:
            self.stdout.write(
                self.style.ERROR("No se puede crear usuarios porque DEBUG=False.")
            )
            return

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
                "grupos": [
                    "Abogado Dupla",
                    "Acompanamiento Detalle",
                    "Acompanamiento Listar",
                    "Comedores",
                    "Comedores Intervencion Crear",
                    "Comedores Intervencion Editar",
                    "Comedores Intervencion Ver",
                    "Comedores Intervenciones Detalle",
                    "Comedores Listar",
                ],
            },
            {
                "username": "tecnicoqa",
                "email": "tecnicoqa@example.com",
                "password": "qa1234",
                "is_superuser": False,
                "grupos": [
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
                ],
            },
            {
                "username": "legalesqa",
                "email": "legalesqa@example.com",
                "password": "qa1234",
                "is_superuser": False,
                "grupos": [
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
                ],
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
                "username": "Ruben Arellano",
                "email": "rubenarellano@example.com",
                "password": "8392017",
                "is_superuser": False,
                "grupos": ["ReferenteCentro", "Ciudadanos"],
            },
            {
                "username": "Natasha Braga",
                "email": "natashabraga@example.com",
                "password": "5823109",
                "is_superuser": False,
                "grupos": ["ReferenteCentro", "Ciudadanos"],
            },
            {
                "username": "Rodrigo Garat",
                "email": "rodrigogarat@example.com",
                "password": "7093851",
                "is_superuser": False,
                "grupos": ["ReferenteCentro", "Ciudadanos"],
            },
            {
                "username": "Oscar Rodriguez",
                "email": "oscarrodriguez@example.com",
                "password": "6102947",
                "is_superuser": False,
                "grupos": ["ReferenteCentro", "Ciudadanos"],
            },
            {
                "username": "Andres Dalou",
                "email": "andresdalou@example.com",
                "password": "9021743",
                "is_superuser": False,
                "grupos": ["ReferenteCentro", "Ciudadanos"],
            },
            {
                "username": "Lionel Barboza",
                "email": "lionelbarboza@example.com",
                "password": "3141592",
                "is_superuser": False,
                "grupos": ["ReferenteCentro", "Ciudadanos"],
            },
            {
                "username": "Padre Cristian Arevalo",
                "email": "padrecristianarevalo@example.com",
                "password": "8273645",
                "is_superuser": False,
                "grupos": ["ReferenteCentro", "Ciudadanos"],
            },
            {
                "username": "Mariano Marfil",
                "email": "marianomarfil@example.com",
                "password": "6357284",
                "is_superuser": False,
                "grupos": ["ReferenteCentro", "Ciudadanos"],
            },
            {
                "username": "San Miguel, Analia",
                "email": "sanmiguelanalia@example.com",
                "password": "7284950",
                "is_superuser": False,
                "grupos": ["ReferenteCentro", "Ciudadanos"],
            },
            {
                "username": "Florencia Martinez",
                "email": "florenciamartinez@example.com",
                "password": "5463728",
                "is_superuser": False,
                "grupos": ["ReferenteCentro", "Ciudadanos"],
            },
            {
                "username": "Laura Balin",
                "email": "laurabalin@example.com",
                "password": "1938475",
                "is_superuser": False,
                "grupos": ["ReferenteCentro", "Ciudadanos"],
            },
            {
                "username": "Teresita Garcia de Costa",
                "email": "teresitagarciadecosta@example.com",
                "password": "3746510",
                "is_superuser": False,
                "grupos": ["ReferenteCentro", "Ciudadanos"],
            },
            {
                "username": "Pablo Valente",
                "email": "pablovalente@example.com",
                "password": "2903847",
                "is_superuser": False,
                "grupos": ["ReferenteCentro", "Ciudadanos"],
            },
            {
                "username": "Andrea Popelka",
                "email": "andreapopelka@example.com",
                "password": "8172639",
                "is_superuser": False,
                "grupos": ["ReferenteCentro", "Ciudadanos"],
            },
            {
                "username": "Gonzalez Crivelli",
                "email": "gonzalezcrivelli@example.com",
                "password": "5948372",
                "is_superuser": False,
                "grupos": ["ReferenteCentro", "Ciudadanos"],
            },
            {
                "username": "Zacarias Guillermo Nicolas",
                "email": "zacariasguillermonicolas@example.com",
                "password": "2837465",
                "is_superuser": False,
                "grupos": ["ReferenteCentro", "Ciudadanos"],
            },
            {
                "username": "Cecilia Palazzotti",
                "email": "ceciliapalazzotti@example.com",
                "password": "5321769",
                "is_superuser": False,
                "grupos": ["ReferenteCentro", "Ciudadanos"],
            },
            {
                "username": "Federico Villalta",
                "email": "federicovillalta@example.com",
                "password": "6482950",
                "is_superuser": False,
                "grupos": ["ReferenteCentro", "Ciudadanos"],
            },
            {
                "username": "Griselda Dirie",
                "email": "griseldadirie@example.com",
                "password": "8749653",
                "is_superuser": False,
                "grupos": ["ReferenteCentro", "Ciudadanos"],
            },
        ]

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
