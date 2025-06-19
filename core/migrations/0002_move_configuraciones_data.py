from django.db import migrations

def transfer_configuraciones_data(apps, schema_editor):
    """Transferir datos de configuraciones a core"""
    db_alias = schema_editor.connection.alias
    
    # Obtener modelos de ambas apps (solo los que existen)
    # Configuraciones (old)
    OldProvincia = apps.get_model('configuraciones', 'Provincia')
    OldMes = apps.get_model('configuraciones', 'Mes')
    OldDia = apps.get_model('configuraciones', 'Dia')
    OldTurno = apps.get_model('configuraciones', 'Turno')
    OldMunicipio = apps.get_model('configuraciones', 'Municipio')
    OldLocalidad = apps.get_model('configuraciones', 'Localidad')
    OldSexo = apps.get_model('configuraciones', 'Sexo')
    
    # Core (new)
    NewProvincia = apps.get_model('core', 'Provincia')
    NewMes = apps.get_model('core', 'Mes')
    NewDia = apps.get_model('core', 'Dia')
    NewTurno = apps.get_model('core', 'Turno')
    NewMunicipio = apps.get_model('core', 'Municipio')
    NewLocalidad = apps.get_model('core', 'Localidad')
    NewSexo = apps.get_model('core', 'Sexo')
    
    # Transferir modelos sin relaciones primero
    simple_models = [
        (OldProvincia, NewProvincia, 'Provincia'),
        (OldMes, NewMes, 'Mes'),
        (OldDia, NewDia, 'Dia'),
        (OldTurno, NewTurno, 'Turno'),
        (OldSexo, NewSexo, 'Sexo'),
    ]
    
    for old_model, new_model, model_name in simple_models:
        print(f"Transfiriendo datos de {model_name}...")
        
        # Verificar si ya existen datos en el nuevo modelo
        existing_count = new_model.objects.using(db_alias).count()
        if existing_count > 0:
            print(f"  {model_name} ya tiene {existing_count} registros, omitiendo...")
            continue
        
        # Obtener todos los registros del modelo antiguo
        old_objects = old_model.objects.using(db_alias).all()
        
        if not old_objects:
            print(f"  No hay datos para transferir en {model_name}")
            continue
        
        # Crear registros en el nuevo modelo
        new_objects = []
        for old_obj in old_objects:
            # Obtener todos los campos del objeto (sin relaciones)
            field_data = {}
            for field in old_obj._meta.fields:
                if not field.is_relation:
                    field_data[field.name] = getattr(old_obj, field.name)
                else:
                    # Para campos de relación, solo copiar el ID
                    field_data[field.name] = field_data.get('id', old_obj.id)
            
            new_objects.append(new_model(**field_data))
        
        # Insertar en lote para mejor performance
        if new_objects:
            new_model.objects.using(db_alias).bulk_create(new_objects)
            print(f"  Transferidos {len(new_objects)} registros de {model_name}")
    
    # Ahora transferir Municipio con referencias correctas
    print("Transfiriendo datos de Municipio...")
    existing_count = NewMunicipio.objects.using(db_alias).count()
    if existing_count == 0:
        old_municipios = OldMunicipio.objects.using(db_alias).all()
        if old_municipios:
            new_municipios = []
            for old_municipio in old_municipios:
                # Obtener la provincia correspondiente en core
                provincia_id = old_municipio.provincia_id if old_municipio.provincia_id else None
                
                new_municipios.append(NewMunicipio(
                    id=old_municipio.id,
                    nombre=old_municipio.nombre,
                    provincia_id=provincia_id
                ))
            
            NewMunicipio.objects.using(db_alias).bulk_create(new_municipios)
            print(f"  Transferidos {len(new_municipios)} registros de Municipio")
    else:
        print(f"  Municipio ya tiene {existing_count} registros, omitiendo...")
    
    # Finalmente transferir Localidad con referencias correctas
    print("Transfiriendo datos de Localidad...")
    existing_count = NewLocalidad.objects.using(db_alias).count()
    if existing_count == 0:
        old_localidades = OldLocalidad.objects.using(db_alias).all()
        if old_localidades:
            new_localidades = []
            for old_localidad in old_localidades:
                # Obtener el municipio correspondiente en core
                municipio_id = old_localidad.municipio_id if old_localidad.municipio_id else None
                
                new_localidades.append(NewLocalidad(
                    id=old_localidad.id,
                    nombre=old_localidad.nombre,
                    municipio_id=municipio_id
                ))
            
            NewLocalidad.objects.using(db_alias).bulk_create(new_localidades)
            print(f"  Transferidos {len(new_localidades)} registros de Localidad")
    else:
        print(f"  Localidad ya tiene {existing_count} registros, omitiendo...")

def reverse_transfer(apps, schema_editor):
    """Reversar la transferencia (eliminar datos de core)"""
    # En caso de rollback, eliminar los datos transferidos
    models_to_clean = [
        'Localidad', 'Municipio', 'Provincia', 'Mes', 'Dia', 'Turno', 'Sexo'
    ]
    
    for model_name in models_to_clean:
        try:
            Model = apps.get_model('core', model_name)
            Model.objects.all().delete()
            print(f"Limpiados datos de {model_name}")
        except:
            pass

class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            transfer_configuraciones_data,
            reverse_transfer,
        ),
    ]