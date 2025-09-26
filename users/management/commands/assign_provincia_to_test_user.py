from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import Profile

User = get_user_model()


class Command(BaseCommand):
    help = "Asigna provincia_id = 1 al usuario ProvinciaCeliaquia"

    def handle(self, *args, **options):
        try:
            user = User.objects.get(username="ProvinciaCeliaquia")
            profile, created = Profile.objects.get_or_create(user=user)
            
            profile.es_usuario_provincial = True
            profile.provincia_id = 1
            profile.save()
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Perfil creado para usuario '{user.username}' con provincia_id = 1"
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Perfil actualizado para usuario '{user.username}' con provincia_id = 1"
                    )
                )
                
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR("Usuario 'ProvinciaCeliaquia' no encontrado")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error: {str(e)}")
            )