# Generated migration to assign provincia_id = 1 to ProvinciaCeliaquia user

from django.db import migrations
from django.contrib.auth import get_user_model


def assign_provincia_to_test_user(apps, schema_editor):
    """
    Asignar provincia_id = 1 al usuario ProvinciaCeliaquia si existe
    """
    User = get_user_model()
    Profile = apps.get_model('users', 'Profile')
    
    try:
        user = User.objects.get(username="ProvinciaCeliaquia")
        profile, created = Profile.objects.get_or_create(user=user)
        
        profile.es_usuario_provincial = True
        profile.provincia_id = 1
        profile.save()
        
        print(f"✅ Usuario ProvinciaCeliaquia configurado con provincia_id = 1")
        
    except User.DoesNotExist:
        print("⚠️  Usuario ProvinciaCeliaquia no encontrado, se omite la asignación")
    except Exception as e:
        print(f"❌ Error al asignar provincia: {e}")


def reverse_assign_provincia(apps, schema_editor):
    """
    Revertir la asignación de provincia
    """
    User = get_user_model()
    Profile = apps.get_model('users', 'Profile')
    
    try:
        user = User.objects.get(username="ProvinciaCeliaquia")
        profile = Profile.objects.get(user=user)
        
        profile.es_usuario_provincial = False
        profile.provincia_id = None
        profile.save()
        
        print(f"✅ Provincia removida del usuario ProvinciaCeliaquia")
        
    except (User.DoesNotExist, Profile.DoesNotExist):
        print("⚠️  Usuario o perfil no encontrado")


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_profile_es_usuario_provincial_profile_provincia'),
    ]

    operations = [
        migrations.RunPython(
            assign_provincia_to_test_user,
            reverse_assign_provincia,
        ),
    ]