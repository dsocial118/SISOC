# Generated by Django 4.0.2 on 2024-07-22 18:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('Usuarios', '0001_initial'),
        ('Legajos', '0010_dimensiontrabajo_legajos_dim_fk_lega_bd11d0_idx'),
        ('Configuraciones', '0003_alter_alertas_gravedad_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CDIF_Admision',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado_vacante', models.CharField(blank=True, max_length=150, null=True)),
                ('estado', models.CharField(blank=True, default='Activa', max_length=150, null=True)),
                ('creado', models.DateField(auto_now_add=True, null=True)),
                ('modificado', models.DateField(auto_now=True, null=True)),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='Admision_creado_por', to='Usuarios.usuarios')),
            ],
        ),
        migrations.CreateModel(
            name='CDIF_PreAdmision',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('menores_a_cargo_1', models.CharField(blank=True, choices=[(None, ''), ('0', '0'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('Más de 5', 'Más de 5')], max_length=50, null=True)),
                ('control_gine_1', models.CharField(blank=True, choices=[(None, ''), ('True', 'SI'), ('False', 'NO')], max_length=50, null=True)),
                ('hijos_1', models.CharField(blank=True, choices=[(None, ''), ('0', '0'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('Más de 5', 'Más de 5')], max_length=50, null=True)),
                ('embarazos_1', models.CharField(blank=True, choices=[(None, ''), ('0', '0'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('Más de 5', 'Más de 5')], max_length=50, null=True)),
                ('abortos_esp_1', models.CharField(blank=True, choices=[(None, ''), ('0', '0'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('Más de 5', 'Más de 5')], max_length=50, null=True)),
                ('abortos_prov_1', models.CharField(blank=True, choices=[(None, ''), ('0', '0'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('Más de 5', 'Más de 5')], max_length=50, null=True)),
                ('emb_no_control_1', models.BooleanField(blank=True, null=True, verbose_name='Embarazo NO controlado')),
                ('emb_adolescente_1', models.BooleanField(blank=True, null=True, verbose_name='Embarazo adolescente')),
                ('emb_riesgo_1', models.BooleanField(blank=True, null=True, verbose_name='Embarazo de riesgo')),
                ('cesareas_multip_1', models.BooleanField(blank=True, null=True, verbose_name='Cesáreas múltiples')),
                ('partos_multip_1', models.BooleanField(blank=True, null=True, verbose_name='Partos múltiples')),
                ('partos_premat_1', models.BooleanField(blank=True, null=True, verbose_name='Partos prematuros')),
                ('partos_menos18meses_1', models.BooleanField(blank=True, null=True, verbose_name='Partos con menos de 18 meses de intervalo')),
                ('emb_actualmente_1', models.CharField(blank=True, choices=[(None, ''), ('True', 'SI'), ('False', 'NO')], max_length=50, null=True)),
                ('controles_1', models.CharField(blank=True, choices=[(None, ''), ('True', 'SI'), ('False', 'NO')], max_length=50, null=True)),
                ('emb_actual_1', models.CharField(blank=True, choices=[(None, ''), ('Normal', 'Normal'), ('Adolescente', 'Adolescente'), ('De riesgo (Diabetes, Hipertension, Sífilis, etc.)', 'De riesgo (Diabetes, Hipertension, Sífilis, etc.)')], max_length=150, null=True)),
                ('educ_maximo_1', models.CharField(blank=True, choices=[(None, ''), ('Primario', 'Primario'), ('Secundario', 'Secundario'), ('Terciario', 'Terciario'), ('Universitario', 'Universitario')], max_length=150, null=True)),
                ('educ_estado_1', models.CharField(blank=True, choices=[(None, ''), ('Completo', 'Completo'), ('Incompleto', 'Incompleto'), ('En curso', 'En curso'), ('No aplica', 'No aplica')], max_length=150, null=True)),
                ('leer_1', models.BooleanField(blank=True, null=True, verbose_name='Sabe leer')),
                ('escribir_1', models.BooleanField(blank=True, null=True, verbose_name='Sabe escribir')),
                ('retomar_estudios_1', models.BooleanField(blank=True, null=True, verbose_name='Quiere retomar estudios')),
                ('aprender_oficio_1', models.BooleanField(blank=True, null=True, verbose_name='Quiere aprender un oficio')),
                ('trabajo_actual_1', models.CharField(blank=True, choices=[(None, ''), ('True', 'SI'), ('False', 'NO')], max_length=50, null=True)),
                ('ocupacion_1', models.CharField(blank=True, max_length=100, null=True, verbose_name='Ocupación')),
                ('modo_contrat_1', models.CharField(blank=True, choices=[(None, ''), ('Relación de dependencia', 'Relación de dependencia'), ('Monotributista / Contratado', 'Monotributista / Contratado'), ('Informal con cobro mensual', 'Informal con cobro mensual'), ('Jornal', 'Jornal'), ('Changarín', 'Changarín'), ('Otro', 'Otro')], max_length=150, null=True)),
                ('educ_maximo_2', models.CharField(blank=True, choices=[(None, ''), ('Primario', 'Primario'), ('Secundario', 'Secundario'), ('Terciario', 'Terciario'), ('Universitario', 'Universitario')], max_length=150, null=True)),
                ('educ_estado_2', models.CharField(blank=True, choices=[(None, ''), ('Completo', 'Completo'), ('Incompleto', 'Incompleto'), ('En curso', 'En curso'), ('No aplica', 'No aplica')], max_length=150, null=True)),
                ('leer_2', models.BooleanField(blank=True, null=True, verbose_name='Sabe leer')),
                ('escribir_2', models.BooleanField(blank=True, null=True, verbose_name='Sabe escribir')),
                ('retomar_estudios_2', models.BooleanField(blank=True, null=True, verbose_name='Quiere retomar estudios')),
                ('aprender_oficio_2', models.BooleanField(blank=True, null=True, verbose_name='Quiere aprender un oficio')),
                ('programa_Pilares_2', models.BooleanField(blank=True, null=True, verbose_name='Quiere participar del Programa Pilares')),
                ('trabajo_actual_2', models.CharField(blank=True, choices=[(None, ''), ('True', 'SI'), ('False', 'NO')], max_length=50, null=True)),
                ('ocupacion_2', models.CharField(blank=True, max_length=100, null=True, verbose_name='Ocupación')),
                ('modo_contrat_2', models.CharField(blank=True, choices=[(None, ''), ('Relación de dependencia', 'Relación de dependencia'), ('Monotributista / Contratado', 'Monotributista / Contratado'), ('Informal con cobro mensual', 'Informal con cobro mensual'), ('Jornal', 'Jornal'), ('Changarín', 'Changarín'), ('Otro', 'Otro')], max_length=150, null=True)),
                ('educ_maximo_3', models.CharField(blank=True, choices=[(None, ''), ('Primario', 'Primario'), ('Secundario', 'Secundario'), ('Terciario', 'Terciario'), ('Universitario', 'Universitario')], max_length=150, null=True)),
                ('educ_estado_3', models.CharField(blank=True, choices=[(None, ''), ('Completo', 'Completo'), ('Incompleto', 'Incompleto'), ('En curso', 'En curso'), ('No aplica', 'No aplica')], max_length=150, null=True)),
                ('leer_3', models.BooleanField(blank=True, null=True, verbose_name='Sabe leer')),
                ('escribir_3', models.BooleanField(blank=True, null=True, verbose_name='Sabe escribir')),
                ('retomar_estudios_3', models.BooleanField(blank=True, null=True, verbose_name='Quiere retomar estudios')),
                ('aprender_oficio_3', models.BooleanField(blank=True, null=True, verbose_name='Quiere aprender un oficio')),
                ('programa_Pilares_3', models.BooleanField(blank=True, null=True, verbose_name='Quiere participar del Programa Pilares')),
                ('educ_maximo_4', models.CharField(blank=True, choices=[(None, ''), ('Primario', 'Primario'), ('Secundario', 'Secundario'), ('Terciario', 'Terciario'), ('Universitario', 'Universitario')], max_length=150, null=True)),
                ('educ_estado_4', models.CharField(blank=True, choices=[(None, ''), ('Completo', 'Completo'), ('Incompleto', 'Incompleto'), ('En curso', 'En curso'), ('No aplica', 'No aplica')], max_length=150, null=True)),
                ('leer_4', models.BooleanField(blank=True, null=True, verbose_name='Sabe leer')),
                ('escribir_4', models.BooleanField(blank=True, null=True, verbose_name='Sabe escribir')),
                ('retomar_estudios_4', models.BooleanField(blank=True, null=True, verbose_name='Quiere retomar estudios')),
                ('aprender_oficio_4', models.BooleanField(blank=True, null=True, verbose_name='Quiere aprender un oficio')),
                ('programa_Pilares_4', models.BooleanField(blank=True, null=True, verbose_name='Quiere participar del Programa Pilares')),
                ('educ_maximo_5', models.CharField(blank=True, choices=[(None, ''), ('Primario', 'Primario'), ('Secundario', 'Secundario'), ('Terciario', 'Terciario'), ('Universitario', 'Universitario')], max_length=150, null=True)),
                ('educ_estado_5', models.CharField(blank=True, choices=[(None, ''), ('Completo', 'Completo'), ('Incompleto', 'Incompleto'), ('En curso', 'En curso'), ('No aplica', 'No aplica')], max_length=150, null=True)),
                ('leer_5', models.BooleanField(blank=True, null=True, verbose_name='Sabe leer')),
                ('escribir_5', models.BooleanField(blank=True, null=True, verbose_name='Sabe escribir')),
                ('retomar_estudios_5', models.BooleanField(blank=True, null=True, verbose_name='Quiere retomar estudios')),
                ('aprender_oficio_5', models.BooleanField(blank=True, null=True, verbose_name='Quiere aprender un oficio')),
                ('programa_Pilares_5', models.BooleanField(blank=True, null=True, verbose_name='Quiere participar del Programa Pilares')),
                ('sala_postula', models.CharField(choices=[(None, ''), ('Bebés', 'Bebés'), ('Sala de 2', 'Sala de 2'), ('Sala de 3', 'Sala de 3')], max_length=150)),
                ('turno_postula', models.CharField(choices=[(None, ''), ('Mañana', 'Mañana'), ('Tarde', 'Tarde')], max_length=150)),
                ('sala_short', models.CharField(blank=True, max_length=150, null=True)),
                ('vinculo1', models.CharField(blank=True, max_length=150, null=True)),
                ('vinculo2', models.CharField(blank=True, max_length=150, null=True)),
                ('vinculo3', models.CharField(blank=True, max_length=150, null=True)),
                ('vinculo4', models.CharField(blank=True, max_length=150, null=True)),
                ('vinculo5', models.CharField(blank=True, max_length=150, null=True)),
                ('ivi', models.CharField(blank=True, max_length=150, null=True)),
                ('admitido', models.CharField(blank=True, max_length=150, null=True)),
                ('creado', models.DateField(auto_now_add=True, null=True)),
                ('modificado', models.DateField(auto_now=True, null=True)),
                ('estado', models.CharField(blank=True, max_length=100, null=True)),
                ('tipo', models.CharField(blank=True, max_length=100, null=True)),
                ('centro_postula', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Configuraciones.vacantes')),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='PreAdm_creado_por', to='Usuarios.usuarios')),
                ('fk_derivacion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Legajos.legajosderivaciones')),
                ('fk_legajo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='fk_legajo', to='Legajos.legajos')),
                ('fk_legajo_1', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='fk_legajo_1', to='Legajos.legajos')),
                ('fk_legajo_2', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='fk_legajo_2', to='Legajos.legajos')),
                ('fk_legajo_3', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='fk_legajo_3', to='Legajos.legajos')),
                ('fk_legajo_4', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='fk_legajo_4', to='Legajos.legajos')),
                ('fk_legajo_5', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='fk_legajo_5', to='Legajos.legajos')),
                ('modificado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='PreAdm_modificado_por', to='Usuarios.usuarios')),
                ('planes_sociales_1', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='planes_sociales_1', to='Configuraciones.planessociales')),
                ('planes_sociales_2', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='planes_sociales_2', to='Configuraciones.planessociales')),
            ],
        ),
        migrations.CreateModel(
            name='Criterios_IVI',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('criterio', models.CharField(max_length=250)),
                ('tipo', models.CharField(choices=[(None, ''), ('Madre o Cuidador principal', 'Madre o Cuidador principal'), ('Bebé, niño o niña', 'Bebé, niño o niña'), ('Familia', 'Familia'), ('Ajustes', 'Ajustes')], max_length=250)),
                ('puntaje', models.SmallIntegerField()),
                ('modificable', models.CharField(choices=[(None, ''), ('SI', 'SI'), ('NO', 'NO')], max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='OpcionesResponsables',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=250, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='CDIF_VacantesOtorgadas',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sala', models.CharField(max_length=150)),
                ('salashort', models.CharField(blank=True, max_length=150, null=True)),
                ('turno', models.CharField(max_length=150)),
                ('educador', models.CharField(blank=True, max_length=150, null=True)),
                ('estado_vacante', models.CharField(blank=True, default='Asignada', max_length=150, null=True)),
                ('fecha_ingreso', models.DateField()),
                ('fecha_egreso', models.DateField(blank=True, null=True)),
                ('motivo', models.CharField(blank=True, max_length=100, null=True)),
                ('detalles', models.CharField(blank=True, max_length=350, null=True)),
                ('evento', models.CharField(blank=True, max_length=100, null=True)),
                ('creado', models.DateField(auto_now_add=True, null=True)),
                ('modificado', models.DateField(auto_now=True, null=True)),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='VacanteOtorgada_creado_por', to='Usuarios.usuarios')),
                ('fk_admision', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='SIF_CDIF.cdif_admision')),
                ('fk_organismo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Configuraciones.vacantes')),
                ('modificado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='VacanteOtorgada_modificada_por', to='Usuarios.usuarios')),
            ],
        ),
        migrations.CreateModel(
            name='CDIF_Vacantes',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('organizacion', models.CharField(max_length=100)),
                ('sala', models.CharField(max_length=100)),
                ('estado', models.CharField(max_length=100)),
                ('creado', models.DateField(auto_now_add=True, null=True)),
                ('modificado', models.DateField(auto_now=True, null=True)),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='Vacante_creado_por', to='Usuarios.usuarios')),
                ('fk_derivacion', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='SIF_CDIF.cdif_preadmision')),
                ('fk_legajo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Legajos.legajos')),
                ('fk_organismo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Configuraciones.organismos')),
                ('fk_vacantes', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Configuraciones.vacantes')),
                ('modificado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='Vacante_modificada_por', to='Usuarios.usuarios')),
            ],
        ),
        migrations.CreateModel(
            name='CDIF_Intervenciones',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('accion', models.CharField(choices=[('Se realizan entrevistas de acompañamiento/ seguimiento', 'Se realizan entrevistas de acompañamiento/ seguimiento'), ('Se la acompaño a realizar el tramite', 'Se la acompaño a realizar el tramite'), ('Se articulo con CDLE', 'Se articulo con CDLE'), ('Se articulo con 1000 dias', 'Se articulo con 1000 dias'), ('Se articulo con PDV', 'Se articulo con PDV'), ('Se articulo con asistencia critica/ Desarrollo social', 'Se articulo con asistencia critica/ Desarrollo social'), ('Se articulo con Salud por un turno', 'Se articulo con Salud por un turno'), ('Se articula con salud', 'Se articula con salud'), ('Se articulo con Salud Mental', 'Se articulo con Salud Mental'), ('Se artiulo con Servicio Local', 'Se artiulo con Servicio Local'), ('Se articulo con Politicas de genero', 'Se articulo con Politicas de genero'), ('Se realizo denuncia por violencia', 'Se realizo denuncia por violencia'), ('Se oriento para realizar la denuncia', 'Se oriento para realizar la denuncia'), ('Se articulo con educación/ FINES', 'Se articulo con educación/ FINES'), ('Se articulo con Potenciar trabajo', 'Se articulo con Potenciar trabajo'), ('Se brindo información', 'Se brindo información'), ('Se realizo un control del niño sano', 'Se realizo un control del niño sano'), ('Se articulo con una institución no municipal', 'Se articulo con una institución no municipal')], max_length=250)),
                ('impacto', models.CharField(choices=[('Trabajado', 'Trabajado'), ('Revertido', 'Revertido')], max_length=250)),
                ('detalle', models.CharField(blank=True, max_length=350, null=True)),
                ('creado', models.DateField(auto_now_add=True, null=True)),
                ('modificado', models.DateField(auto_now=True, null=True)),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='Intervenciones_creado_por', to='Usuarios.usuarios')),
                ('criterio_modificable', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='SIF_CDIF.criterios_ivi')),
                ('fk_admision', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='SIF_CDIF.cdif_admision')),
                ('modificado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='Intervenciones_modificada_por', to='Usuarios.usuarios')),
                ('responsable', models.ManyToManyField(to='SIF_CDIF.OpcionesResponsables')),
            ],
        ),
        migrations.CreateModel(
            name='CDIF_IndiceIVI',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('presencia', models.BooleanField(blank=True, default=False, null=True)),
                ('tipo', models.CharField(blank=True, max_length=350, null=True)),
                ('programa', models.CharField(blank=True, choices=[(None, ''), ('SI', 'SI'), ('NO', 'NO')], max_length=150, null=True)),
                ('clave', models.CharField(blank=True, max_length=350, null=True)),
                ('creado', models.DateField(auto_now_add=True, null=True)),
                ('modificado', models.DateField(auto_now=True, null=True)),
                ('fk_criterios_ivi', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='SIF_CDIF.criterios_ivi')),
                ('fk_legajo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Legajos.legajos')),
                ('fk_preadmi', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='SIF_CDIF.cdif_preadmision')),
            ],
        ),
        migrations.CreateModel(
            name='CDIF_HistorialVacantes',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado', models.CharField(blank=True, max_length=150, null=True)),
                ('sala', models.CharField(blank=True, max_length=150, null=True)),
                ('creado', models.DateField(auto_now_add=True, null=True)),
                ('modificado', models.DateField(auto_now=True, null=True)),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='HistorialVacantes_creado_por', to='Usuarios.usuarios')),
                ('fk_admision', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='SIF_CDIF.cdif_admision')),
                ('fk_organismo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Configuraciones.vacantes')),
                ('modificado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='HistorialVacantes_modificada_por', to='Usuarios.usuarios')),
            ],
        ),
        migrations.CreateModel(
            name='CDIF_Historial',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('movimiento', models.CharField(blank=True, max_length=150, null=True)),
                ('creado', models.DateField(auto_now_add=True, null=True)),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Usuarios.usuarios')),
                ('fk_admision', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='SIF_CDIF.cdif_admision')),
                ('fk_legajo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Legajos.legajos')),
                ('fk_legajo_derivacion', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Legajos.legajosderivaciones')),
                ('fk_preadmi', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='SIF_CDIF.cdif_preadmision')),
            ],
        ),
        migrations.CreateModel(
            name='CDIF_Foto_IVI',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('puntaje', models.SmallIntegerField(blank=True, null=True)),
                ('puntaje_max', models.SmallIntegerField(blank=True, null=True)),
                ('crit_modificables', models.SmallIntegerField(blank=True, null=True)),
                ('crit_presentes', models.SmallIntegerField(blank=True, null=True)),
                ('observaciones', models.CharField(blank=True, max_length=350, null=True)),
                ('tipo', models.CharField(blank=True, max_length=350, null=True)),
                ('clave', models.CharField(blank=True, max_length=350, null=True)),
                ('creado', models.DateField(auto_now_add=True, null=True)),
                ('modificado', models.DateField(auto_now=True, null=True)),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='IVI_creado_por', to='Usuarios.usuarios')),
                ('fk_legajo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Legajos.legajos')),
                ('fk_preadmi', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='SIF_CDIF.cdif_preadmision')),
                ('modificado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='IVI_modificado_por', to='Usuarios.usuarios')),
            ],
        ),
        migrations.AddField(
            model_name='cdif_admision',
            name='fk_preadmi',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='SIF_CDIF.cdif_preadmision'),
        ),
        migrations.AddField(
            model_name='cdif_admision',
            name='modificado_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='Admision_modificada_por', to='Usuarios.usuarios'),
        ),
    ]
