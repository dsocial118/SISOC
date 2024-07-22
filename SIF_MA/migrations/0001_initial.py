# Generated by Django 4.0.2 on 2024-07-22 18:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('Configuraciones', '0003_alter_alertas_gravedad_and_more'),
        ('Legajos', '0010_dimensiontrabajo_legajos_dim_fk_lega_bd11d0_idx'),
        ('Usuarios', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Criterios_Ingreso',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('criterio', models.CharField(max_length=250)),
                ('tipo', models.CharField(choices=[(None, ''), ('Criteros autónomos de ingreso', 'Criteros autónomos de ingreso'), ('Motivo de falta de control o control insuficiente', 'Motivo de falta de control o control insuficiente'), ('Criterios combinables de ingreso', 'Criterios combinables de ingreso'), ('Criterios sociales para el ingreso', 'Criterios sociales para el ingreso')], max_length=250)),
                ('puntaje', models.SmallIntegerField()),
                ('modificable', models.CharField(choices=[(None, ''), ('SI', 'SI'), ('NO', 'NO')], max_length=50)),
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
            name='MA_Admision',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado', models.CharField(blank=True, default='Activa', max_length=150, null=True)),
                ('creado', models.DateField(auto_now_add=True, null=True)),
                ('modificado', models.DateField(auto_now=True, null=True)),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='MA_Admision_creado_por', to='Usuarios.usuarios')),
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
            name='MA_PreAdmision',
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
                ('test_embarazo', models.BooleanField(blank=True, null=True, verbose_name='¿Te hiciste test de embarazo?')),
                ('fum', models.DateField(blank=True, null=True, verbose_name='Fecha última mestruación')),
                ('sem_embarazo', models.IntegerField(blank=True, choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'), (6, '6'), (7, '7'), (8, '8'), (9, '9'), (10, '10'), (11, '11'), (12, '12'), (13, '13'), (14, '14'), (15, '15'), (16, '16'), (17, '17'), (18, '18'), (19, '19'), (20, '20'), (21, '21'), (22, '22'), (23, '23'), (24, '24'), (25, '25'), (26, '26'), (27, '27'), (28, '28'), (29, '29'), (30, '30'), (31, '31'), (32, '32'), (33, '33'), (34, '34'), (35, '35'), (36, '36'), (37, '37'), (38, '38'), (39, '39'), (40, '40')], null=True, verbose_name='Semanas de embarazo')),
                ('fpp', models.DateField(blank=True, null=True, verbose_name='FPP')),
                ('centro_controla', models.CharField(blank=True, choices=[('20_de_Julio', '20 de Julio'), ('29_de_Septiembre', '29 de Septiembre'), ('Ana_Teresa_Barthalot', 'Ana Teresa Barthalot'), ('C_1_C_Maria_Lobato', 'C.1.C. «Maria Lobato»'), ('Camila_Rolen', 'Camila Rolén'), ('Candido_Castello', 'Candido Castello'), ('Rodolfo_Podesta', 'Rodolfo Podesta'), ('Cura_Brochero', 'Cura Brochero'), ('Alberto_Sabin', 'Alberto Sabin'), ('Federico_Leloir', 'Federico Leloir'), ('Suarez_Paris', 'Suarez Paris'), ('Ratil_Matera', 'Ratil Matera'), ('Rene_Favaloro', 'René Favaloro'), ('Marta_Antoniazzi', 'Marta Antoniazzi'), ('Padre_Mora', 'Padre Mora'), ('Pte_Peren', 'Pte. Perén'), ('Ramen_Carrillo', 'Ramén Carrillo'), ('San_Miguel_Oeste', 'San Miguel Oeste'), ('UF0_Manuelita', 'U.F.0 (Manuelita)'), ('Hospital_Larcade', 'Hospital Larcade'), ('Privado', 'Privado'), ('Extrapartidario', 'Extrapartidario')], max_length=250, null=True, verbose_name='Centro de salud que se controla o controlará')),
                ('primer_control', models.IntegerField(blank=True, choices=[(4, '4'), (5, '5'), (6, '6'), (7, '7'), (8, '8'), (9, '9'), (10, '10'), (11, '11'), (12, '12'), (13, '13'), (14, '14'), (15, '15'), (16, '16'), (17, '17'), (18, '18'), (19, '19'), (20, '20'), (21, '21'), (22, '22'), (23, '23'), (24, '24'), (25, '25'), (26, '26'), (27, '27'), (28, '28'), (29, '29'), (30, '30'), (31, '31'), (32, '32'), (33, '33'), (34, '34'), (35, '35'), (36, '36'), (37, '37'), (38, '38'), (39, '39'), (40, '40')], null=True, verbose_name='¿Semana del primer control?')),
                ('primer_embarazo', models.BooleanField(blank=True, null=True, verbose_name='¿Es tu primer embarazo?')),
                ('libreta_sanitaria', models.BooleanField(blank=True, null=True, verbose_name='¿Tiene libreta sanitaria?')),
                ('metodos_anticonceptivos', models.BooleanField(blank=True, null=True, verbose_name='¿Conoces los métodos anticonceptivos?')),
                ('cuales_met_anticon_conoces', models.CharField(blank=True, choices=[('Preservativo', 'Preservativo'), ('Inyectable', 'Inyectable'), ('Implante_Anticonceptivo', 'Implante Anticonceptivo'), ('DIU', 'DIU'), ('Parche_Anticonceptivo', 'Parche Anticonceptivo'), ('Anticonceptivo_Oral', 'Anticonceptivo Oral'), ('Ligadura_Tubaria', 'Ligadura Tubaria'), ('Ninguno', 'Ninguno')], max_length=250, null=True, verbose_name='¿Cuáles conoces?')),
                ('utilizabas_alguno', models.BooleanField(blank=True, null=True, verbose_name='¿Utilizabas alguno cuando quedaste embarazada?')),
                ('cual_usabas', models.CharField(blank=True, choices=[('Preservativo', 'Preservativo'), ('Inyectable', 'Inyectable'), ('Implante_Anticonceptivo', 'Implante Anticonceptivo'), ('DIU', 'DIU'), ('Parche_Anticonceptivo', 'Parche Anticonceptivo'), ('Anticonceptivo_Oral', 'Anticonceptivo Oral'), ('Ligadura_Tubaria', 'Ligadura Tubaria'), ('Ninguno', 'Ninguno')], max_length=250, null=True, verbose_name='¿Cual usabas?')),
                ('sifilis_anterior', models.BooleanField(blank=True, null=True, verbose_name='¿Tuviste sifilis en embarazos anteriores?')),
                ('sifilis_ahora', models.BooleanField(blank=True, null=True, verbose_name='¿Tenes sifilis actualmente?')),
                ('sifilis_tratamiento_pareja', models.BooleanField(blank=True, null=True, verbose_name='En caso de haber tenido o tener sifilis: ¿Tu pareja hizo el tratamiento?')),
                ('consumio_drogas', models.BooleanField(blank=True, null=True, verbose_name='¿Alguna vez consumió drogas?')),
                ('drogas_ahora', models.BooleanField(blank=True, null=True, verbose_name='¿Consume drogas actualmente?')),
                ('alcohol_ahora', models.BooleanField(blank=True, null=True, verbose_name='¿Consume alcohol actualmente?')),
                ('sospecha_consumo', models.BooleanField(blank=True, null=True, verbose_name='Sospecha de consumo')),
                ('embarazo_controlado', models.CharField(blank=True, choices=[('Si', 'Si'), ('No', 'No'), ('Insuficiente', 'Insuficiente')], max_length=250, null=True, verbose_name='Embarazo controlado')),
                ('comienza_control', models.BooleanField(blank=True, null=True, verbose_name='¿Comienza control en operativo?')),
                ('prim_trim_control_obstetra', models.BooleanField(blank=True, null=True, verbose_name='Al menos 1 control con la obstetra')),
                ('prim_trim_estudios_labo', models.BooleanField(blank=True, null=True, verbose_name='Laboratorio- Rutina 1er trimestre')),
                ('prim_trim_estudios_eco', models.BooleanField(blank=True, null=True, verbose_name='Ecografía')),
                ('prim_trim_estudios_pap', models.BooleanField(blank=True, null=True, verbose_name='PAP')),
                ('prim_trim_estudios_grupo_factor', models.BooleanField(blank=True, null=True, verbose_name='Grupo y Factor')),
                ('prim_trim_control_odonto', models.BooleanField(blank=True, null=True, verbose_name='Control odontologico')),
                ('seg_trim_control_obsetra', models.BooleanField(blank=True, null=True, verbose_name='Al menos 2 controles con la obstetra')),
                ('seg_trim_control_fetal', models.BooleanField(blank=True, null=True, verbose_name='Scan fetal')),
                ('seg_trim_p75', models.BooleanField(blank=True, null=True, verbose_name='P75')),
                ('ter_trim_control_rutina', models.BooleanField(blank=True, null=True, verbose_name='Ecografía, hisopado vaginal y laboratorio')),
                ('ter_trim_monitoreo_fetal', models.BooleanField(blank=True, null=True, verbose_name='Monitoreo fetal')),
                ('ter_trim_electro_cardio', models.BooleanField(blank=True, null=True, verbose_name='Electro cardiograma')),
                ('vinculo1', models.CharField(blank=True, max_length=150, null=True)),
                ('vinculo2', models.CharField(blank=True, max_length=150, null=True)),
                ('vinculo3', models.CharField(blank=True, max_length=150, null=True)),
                ('vinculo4', models.CharField(blank=True, max_length=150, null=True)),
                ('vinculo5', models.CharField(blank=True, max_length=150, null=True)),
                ('ivi', models.CharField(blank=True, max_length=150, null=True)),
                ('indice_ingreso', models.CharField(blank=True, max_length=150, null=True)),
                ('admitido', models.CharField(blank=True, max_length=150, null=True)),
                ('creado', models.DateField(auto_now_add=True, null=True)),
                ('modificado', models.DateField(auto_now=True, null=True)),
                ('estado', models.CharField(blank=True, max_length=100, null=True)),
                ('tipo', models.CharField(blank=True, max_length=100, null=True)),
                ('acompaniante', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='MA_Acompaniante', to='Usuarios.usuarios')),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='MA_PreAdm_creado_por', to='Usuarios.usuarios')),
                ('fk_derivacion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Legajos.legajosderivaciones')),
                ('fk_legajo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='MA_fk_legajo', to='Legajos.legajos')),
                ('fk_legajo_1', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='MA_fk_legajo_1', to='Legajos.legajos')),
                ('fk_legajo_2', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='MA_fk_legajo_2', to='Legajos.legajos')),
                ('fk_legajo_3', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='MA_fk_legajo_3', to='Legajos.legajos')),
                ('fk_legajo_4', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='MA_fk_legajo_4', to='Legajos.legajos')),
                ('fk_legajo_5', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='MA_fk_legajo_5', to='Legajos.legajos')),
                ('madrina', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='MA_Madrina', to='Configuraciones.agentesexternos')),
                ('modificado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='MA_PreAdm_modificado_por', to='Usuarios.usuarios')),
                ('planes_sociales_1', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='MA_planes_sociales_1', to='Configuraciones.planessociales')),
                ('planes_sociales_2', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='MA_planes_sociales_2', to='Configuraciones.planessociales')),
            ],
        ),
        migrations.CreateModel(
            name='MA_Intervenciones',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('accion', models.CharField(choices=[('Se realizan entrevistas de acompañamiento/ seguimiento', 'Se realizan entrevistas de acompañamiento/ seguimiento'), ('Se la acompaño a realizar el tramite', 'Se la acompaño a realizar el tramite'), ('Se articulo con MA', 'Se articulo con MA'), ('Se articulo con 1000 dias', 'Se articulo con 1000 dias'), ('Se articulo con PDV', 'Se articulo con PDV'), ('Se articulo con asistencia critica/ Desarrollo social', 'Se articulo con asistencia critica/ Desarrollo social'), ('Se articulo con Salud por un turno', 'Se articulo con Salud por un turno'), ('Se articula con salud', 'Se articula con salud'), ('Se articulo con Salud Mental', 'Se articulo con Salud Mental'), ('Se artiulo con Servicio Local', 'Se artiulo con Servicio Local'), ('Se articulo con Politicas de genero', 'Se articulo con Politicas de genero'), ('Se realizo denuncia por violencia', 'Se realizo denuncia por violencia'), ('Se oriento para realizar la denuncia', 'Se oriento para realizar la denuncia'), ('Se articulo con educación/ FINES', 'Se articulo con educación/ FINES'), ('Se articulo con Potenciar trabajo', 'Se articulo con Potenciar trabajo'), ('Se brindo información', 'Se brindo información'), ('Se realizo un control del niño sano', 'Se realizo un control del niño sano'), ('Se articulo con una institución no municipal', 'Se articulo con una institución no municipal')], max_length=250)),
                ('impacto', models.CharField(choices=[('Trabajado', 'Trabajado'), ('Revertido', 'Revertido')], max_length=250)),
                ('detalle', models.CharField(blank=True, max_length=350, null=True)),
                ('creado', models.DateField(auto_now_add=True, null=True)),
                ('modificado', models.DateField(auto_now=True, null=True)),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='MA_Intervenciones_creado_por', to='Usuarios.usuarios')),
                ('criterio_modificable', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='SIF_MA.criterios_ivi')),
                ('fk_admision', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='SIF_MA.ma_admision')),
                ('modificado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='MA_Intervenciones_modificada_por', to='Usuarios.usuarios')),
                ('responsable', models.ManyToManyField(to='SIF_MA.OpcionesResponsables')),
            ],
        ),
        migrations.CreateModel(
            name='MA_IndiceIVI',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('presencia', models.BooleanField(blank=True, default=False, null=True)),
                ('tipo', models.CharField(blank=True, max_length=350, null=True)),
                ('programa', models.CharField(blank=True, choices=[(None, ''), ('SI', 'SI'), ('NO', 'NO')], max_length=150, null=True)),
                ('clave', models.CharField(blank=True, max_length=350, null=True)),
                ('creado', models.DateField(auto_now_add=True, null=True)),
                ('modificado', models.DateField(auto_now=True, null=True)),
                ('fk_criterios_ivi', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='SIF_MA.criterios_ivi')),
                ('fk_legajo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Legajos.legajos')),
                ('fk_preadmi', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='SIF_MA.ma_preadmision')),
            ],
        ),
        migrations.CreateModel(
            name='MA_IndiceIngreso',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('presencia', models.BooleanField(blank=True, default=False, null=True)),
                ('tipo', models.CharField(blank=True, max_length=350, null=True)),
                ('programa', models.CharField(blank=True, choices=[(None, ''), ('SI', 'SI'), ('NO', 'NO')], max_length=150, null=True)),
                ('clave', models.CharField(blank=True, max_length=350, null=True)),
                ('creado', models.DateField(auto_now_add=True, null=True)),
                ('modificado', models.DateField(auto_now=True, null=True)),
                ('fk_criterios_ingreso', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='SIF_MA.criterios_ingreso')),
                ('fk_legajo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Legajos.legajos')),
                ('fk_preadmi', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='SIF_MA.ma_preadmision')),
            ],
        ),
        migrations.CreateModel(
            name='MA_Historial',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('movimiento', models.CharField(blank=True, max_length=150, null=True)),
                ('creado', models.DateField(auto_now_add=True, null=True)),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Usuarios.usuarios')),
                ('fk_admision', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='SIF_MA.ma_admision')),
                ('fk_legajo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Legajos.legajos')),
                ('fk_legajo_derivacion', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Legajos.legajosderivaciones')),
                ('fk_preadmi', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='SIF_MA.ma_preadmision')),
            ],
        ),
        migrations.CreateModel(
            name='MA_Foto_IVI',
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
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='MA_IVI_creado_por', to='Usuarios.usuarios')),
                ('fk_legajo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Legajos.legajos')),
                ('fk_preadmi', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='SIF_MA.ma_preadmision')),
                ('modificado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='MA_IVI_modificado_por', to='Usuarios.usuarios')),
            ],
        ),
        migrations.CreateModel(
            name='MA_Foto_Ingreso',
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
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='MA_Ingreso_creado_por', to='Usuarios.usuarios')),
                ('fk_legajo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Legajos.legajos')),
                ('fk_preadmi', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='SIF_MA.ma_preadmision')),
                ('modificado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='MA_Ingreso_modificado_por', to='Usuarios.usuarios')),
            ],
        ),
        migrations.AddField(
            model_name='ma_admision',
            name='fk_preadmi',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='SIF_MA.ma_preadmision'),
        ),
        migrations.AddField(
            model_name='ma_admision',
            name='modificado_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='MA_Admision_modificada_por', to='Usuarios.usuarios'),
        ),
    ]
