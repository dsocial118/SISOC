# Generated by Django 4.0.2 on 2024-07-01 15:41

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('Usuarios', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Acciones',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=70, unique=True)),
                ('dimension', models.CharField(choices=[(None, ''), ('Familia', 'Familia'), ('Vivienda', 'Vivienda'), ('Salud', 'Salud'), ('Economía', 'Economía'), ('Educación', 'Educación'), ('Trabajo', 'Trabajo')], default='Desconocida', max_length=12)),
                ('observaciones', models.CharField(blank=True, max_length=500, null=True)),
            ],
            options={
                'verbose_name': 'Acciones',
                'verbose_name_plural': 'Acciones',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='AgentesExternos',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('apellido', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('telefono', models.PositiveIntegerField(blank=True, null=True)),
                ('rol', models.CharField(blank=True, max_length=30, null=True)),
                ('estado', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Agente Externo',
                'verbose_name_plural': 'Agentes Externos',
                'ordering': ['apellido'],
            },
        ),
        migrations.CreateModel(
            name='CategoriaAlertas',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, unique=True)),
                ('dimension', models.CharField(blank=True, choices=[(None, ''), ('Familia', 'Familia'), ('Vivienda', 'Vivienda'), ('Salud', 'Salud'), ('Economía', 'Economía'), ('Educación', 'Educación'), ('Trabajo', 'Trabajo')], max_length=20, null=True)),
                ('estado', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'CategoriaAlertas',
                'verbose_name_plural': 'CategoriasAlertas',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='Criterios',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=250, unique=True)),
                ('dimension', models.CharField(choices=[(None, ''), ('Familia', 'Familia'), ('Vivienda', 'Vivienda'), ('Salud', 'Salud'), ('Economía', 'Economía'), ('Educación', 'Educación'), ('Trabajo', 'Trabajo')], default='Desconocida', max_length=12)),
                ('permite_potencial', models.BooleanField(default=False)),
                ('estado', models.BooleanField(default=True)),
                ('observaciones', models.CharField(blank=True, max_length=500, null=True)),
            ],
            options={
                'verbose_name': 'Criterio',
                'verbose_name_plural': 'Criterios',
                'ordering': ['fk_sujeto'],
            },
        ),
        migrations.CreateModel(
            name='IndiceCriterios',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('puntaje_base', models.PositiveSmallIntegerField(help_text='Permite valores entre 0 y 10.', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)])),
                ('fk_criterio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fkcriterio', to='Configuraciones.criterios')),
            ],
            options={
                'verbose_name': 'IndiceCriterios',
                'verbose_name_plural': 'IndicesCriterios',
            },
        ),
        migrations.CreateModel(
            name='Organismos',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=250, unique=True)),
                ('tipo', models.CharField(choices=[(None, ''), ('Hospital', 'Hospital'), ('CAP', 'CAP'), ('Escuela', 'Escuela'), ('Club Barrial', 'Club Barrial'), ('ONG/Agrupación Comunitaria', 'ONG/Agrupación Comunitaria'), ('Organismo Municipal', 'Organismo Municipal'), ('Organismo Provincial', 'Organismo Provincial'), ('Organismo Nacional', 'Organismo Nacional')], max_length=50)),
                ('calle', models.CharField(blank=True, max_length=250, null=True)),
                ('altura', models.IntegerField(blank=True, null=True)),
                ('piso', models.CharField(blank=True, max_length=100)),
                ('barrio', models.CharField(blank=True, choices=[(None, ''), ('Altos de San José', 'Altos de San José'), ('Bello Horizonte', 'Bello Horizonte'), ('Colegio Máximo', 'Colegio Máximo'), ('Colibrí', 'Colibrí'), ('Constantini', 'Constantini'), ('Cuartel Segundo Cc.', 'Cuartel Segundo Cc.'), ('Don Alfonso', 'Don Alfonso'), ('La Gloria', 'La Gloria'), ('La Estrella', 'La Estrella'), ('La Guarida', 'La Guarida'), ('La Manuelita', 'La Manuelita'), ('Lomas de Mariló', 'Lomas de Mariló'), ('Los Paraísos', 'Los Paraísos'), ('Los Plátanos', 'Los Plátanos'), ('Macabi', 'Macabi'), ('María Rosa Mística', 'María Rosa Mística'), ('Mitre', 'Mitre'), ('Parque San Miguel', 'Parque San Miguel'), ('Parque San Ignacio', 'Parque San Ignacio'), ('Santa Brígida', 'Santa Brígida'), ('Sarmiento', 'Sarmiento'), ('Trujui', 'Trujui'), ('Santa María', 'Santa María'), ('San Antonio', 'San Antonio'), ('San Ignacio', 'San Ignacio')], max_length=250, null=True)),
                ('localidad', models.CharField(blank=True, choices=[(None, ''), ('San Miguel', 'San Miguel'), ('Bella Vista', 'Bella Vista'), ('Muñiz', 'Muñiz'), ('Santa María', 'Santa María')], max_length=250, null=True)),
                ('telefono', models.IntegerField(blank=True, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('estado', models.BooleanField(default=True)),
                ('observaciones', models.CharField(blank=True, max_length=300, null=True)),
            ],
            options={
                'verbose_name': 'Organismo',
                'verbose_name_plural': 'Organismos',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='PlanesSociales',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=250, unique=True)),
                ('jurisdiccion', models.CharField(choices=[(None, ''), ('Nacional', 'Nacional'), ('Provincial', 'Provincial'), ('Municipal', 'Municipal')], max_length=50)),
                ('estado', models.BooleanField(default=True)),
                ('observaciones', models.CharField(blank=True, max_length=500, null=True)),
            ],
            options={
                'verbose_name': 'PlanSocial',
                'verbose_name_plural': 'PlanesSociales',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='Programas',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, unique=True)),
                ('estado', models.BooleanField(default=True)),
                ('observaciones', models.CharField(blank=True, max_length=300, null=True)),
            ],
            options={
                'verbose_name': 'Programa',
                'verbose_name_plural': 'Programas',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='Secretarias',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=40, unique=True)),
                ('observaciones', models.CharField(blank=True, max_length=300, null=True)),
                ('estado', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Secretaría',
                'verbose_name_plural': 'Secretarías',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='Sujetos',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=70, unique=True)),
            ],
            options={
                'verbose_name': 'Sujetos',
                'verbose_name_plural': 'Sujetos',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='Vacantes',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('observaciones', models.CharField(blank=True, max_length=300, null=True)),
                ('manianabb', models.PositiveIntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Turno Mañana')),
                ('tardebb', models.PositiveIntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Turno Tarde')),
                ('maniana2', models.PositiveIntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Turno Mañana')),
                ('tarde2', models.PositiveIntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Turno Tarde')),
                ('maniana3', models.PositiveIntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Turno Mañana')),
                ('tarde3', models.PositiveIntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Turno Tarde')),
                ('maniana4', models.PositiveIntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Turno Mañana')),
                ('tarde4', models.PositiveIntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Turno Tarde')),
                ('estado', models.BooleanField(default=True)),
                ('fk_organismo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Configuraciones.organismos')),
                ('fk_programa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Configuraciones.programas')),
            ],
            options={
                'verbose_name': 'Vacante',
                'verbose_name_plural': 'Vacantes',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='Subsecretarias',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=40, unique=True)),
                ('observaciones', models.CharField(blank=True, max_length=300, null=True)),
                ('estado', models.BooleanField(default=True)),
                ('fk_secretaria', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Configuraciones.secretarias')),
            ],
            options={
                'verbose_name': 'Subsecretaría',
                'verbose_name_plural': 'Subecretarías',
                'ordering': ['nombre'],
            },
        ),
        migrations.AddField(
            model_name='programas',
            name='fk_subsecretaria',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Configuraciones.subsecretarias'),
        ),
        migrations.CreateModel(
            name='Indices',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=250, unique=True)),
                ('observaciones', models.CharField(blank=True, max_length=500, null=True)),
                ('estado', models.BooleanField(default=True)),
                ('m2m_criterios', models.ManyToManyField(through='Configuraciones.IndiceCriterios', to='Configuraciones.Criterios')),
                ('m2m_programas', models.ManyToManyField(to='Configuraciones.Programas')),
            ],
            options={
                'verbose_name': 'Indice',
                'verbose_name_plural': 'Indices',
            },
        ),
        migrations.AddField(
            model_name='indicecriterios',
            name='fk_indice',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fkindice', to='Configuraciones.indices'),
        ),
        migrations.CreateModel(
            name='GruposDestinatarios',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=250)),
                ('observaciones', models.CharField(blank=True, max_length=500, null=True)),
                ('estado', models.BooleanField(default=True)),
                ('m2m_agentes_externos', models.ManyToManyField(blank=True, to='Configuraciones.AgentesExternos')),
                ('m2m_usuarios', models.ManyToManyField(blank=True, to='Usuarios.Usuarios')),
            ],
            options={
                'verbose_name': 'GrupoDestinatarios',
                'verbose_name_plural': 'GruposDestinatarios',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='Equipos',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=250)),
                ('observaciones', models.CharField(blank=True, max_length=500, null=True)),
                ('estado', models.BooleanField(default=True)),
                ('fk_coordinador', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='fkcoordinador', to='Usuarios.usuarios')),
                ('fk_programa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Configuraciones.programas')),
                ('m2m_usuarios', models.ManyToManyField(to='Usuarios.Usuarios')),
            ],
            options={
                'verbose_name': 'Equipo',
                'verbose_name_plural': 'Equipos',
                'ordering': ['nombre'],
            },
        ),
        migrations.AddField(
            model_name='criterios',
            name='fk_sujeto',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Configuraciones.sujetos'),
        ),
        migrations.AddField(
            model_name='criterios',
            name='m2m_acciones',
            field=models.ManyToManyField(blank=True, to='Configuraciones.Acciones'),
        ),
        migrations.AddField(
            model_name='criterios',
            name='m2m_alertas',
            field=models.ManyToManyField(blank=True, to='Configuraciones.CategoriaAlertas'),
        ),
        migrations.CreateModel(
            name='Alertas',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, unique=True)),
                ('estado', models.BooleanField(default=True)),
                ('gravedad', models.CharField(max_length=500)),
                ('fk_categoria', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Configuraciones.categoriaalertas')),
            ],
            options={
                'verbose_name': 'Alerta',
                'verbose_name_plural': 'Alertas',
                'ordering': ['nombre'],
            },
        ),
        migrations.AddField(
            model_name='agentesexternos',
            name='fk_organismo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Configuraciones.organismos'),
        ),
    ]
