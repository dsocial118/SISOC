# ---------- CHOICES---------------------
CHOICE_NIVEL_EDUCATIVO = [
    (None, ''),
    ('No aplica', 'No aplica'),
    ('Educación especial', 'Educación especial'),
    ('Jardín', 'Jardín'),
    ('Primario', 'Primario'),
    ('EGB', 'EGB'),
    ('Secundario', 'Secundario'),
    ('Polimodal', 'Polimodal'),
    ('Terciario', 'Terciario'),
    ('Universitario', 'Universitario'),
]
CHOICE_ESTADO_NIVEL_EDUCATIVO = [
    (None, ''),
    ('En curso', 'En curso'),
    ('Incompleto', 'Incompleto'),
    ('Completo', 'Completo'),
]

CHOICE_ASISTE_ESCUELA = [
     ('a','Sí, asisto actualmente'),
	 ('b', 'Sí, asistí en algún momento'),
	 ('c', 'No, nunca asistí')
]

CHOICE_ESTADO_EDUCATIVO = [
    (None, ''),
    ('En curso', 'En curso'),
    ('Incompleto', 'Incompleto'),
    ('Completo', 'Completo'),
]

CHOICE_MOTIVO_NIVEL_INCOMPLETO = [
    ('El establecimiento quedaba lejos y/o no tenía cómo llegar','El establecimiento quedaba lejos y/o no tenía cómo llegar'),
    ('Necesitaba trabajar', 'Necesitaba trabajar'),
    ('No podía pagar los gastos', 'No podía pagar los gastos'),
    ('Tenía que cuidar a otras personas del hogar (niños/as, personas mayores, otras)', 'Tenía que cuidar a otras personas del hogar (niños/as, personas mayores, otras)'),
    ('Estaba embarazada', 'Estaba embarazada'),
    ('No tenía de interés', 'No tenía de interés'),
    ('Tenía dificultades para aprender o estudiar', 'Tenía dificultades para aprender o estudiar'),
    ('Tenía problemas de salud', 'Tenía problemas de salud'),
]

CHOICE_AREA_CURSO=[
    ('Albañilería','Albañilería'),
    ('Mecánica Automotor básica','Mecánica Automotor básica'),
    ('Venta en comercio', 'Venta en comercio'),
    ('Elaboración de alimentos', 'Elaboración de alimentos'),
    ('Colocación de cerámicos','Colocación de cerámicos'),
    ('Instalaciones eléctricas domiciliarias', 'Instalaciones eléctricas domiciliarias'),
    ('Instalación de gas domiciliario', 'Instalación de gas domiciliario'),
    ('Instalación de sanitarios en casas', 'Instalación de sanitarios en casas'),
    ('Jardinería y mantenimiento espacios verdes', 'Jardinería y mantenimiento espacios verdes'),
    ('Mecánica de Motos', 'Mecánica de Motos'),
    ('Atención en bares y restaurantes', 'Atención en bares y restaurantes'),
    ('Mucamo/a de hotel', 'Mucamo/a de hotel'),
    ('Confección de indumentaria', 'Confección de indumentaria'),
    ('Industrias de la carne', 'Industrias de la carne'),
    ('Tareas generales en Industrias varias', 'Tareas generales en Industrias varias'),
    ('Cuidado de personas', 'Cuidado de personas'),
    ('Servicios generales en casas particulares', 'Servicios generales en casas particulares'),
    ('Pintura de Obra', 'Pintura de Obra'),
]

CHOICE_TIPO_GESTION = [
    (None, ''),
    ('Estatal', 'Estatal'),
    ('Privada o subvencionada', 'Privada o subvencionada'),
]

CHOICE_GRADO = [
    (None, ''),
    ('1º Grado', '1º Grado'),
    ('2º Grado', '2º Grado'),
    ('3º Grado', '3º Grado'),
    ('4º Grado', '4º Grado'),
    ('5º Grado', '5º Grado'),
    ('6º Grado', '6º Grado'),
    ('1º año', '1º año'),
    ('2º año', '2º año'),
    ('3º año', '3º año'),
    ('4º año', '4º año'),
    ('5º año', '5º año'),
    ('6º año', '6º año'),
    ('Otro', 'Otro'),
]

CHOICE_TURNO = [
    (None, ''),
    ('Mañana', 'Mañana'),
    ('Tarde', 'Tarde'),
    ('Noche', 'Noche'),
    ('Jornada Completa', 'Jornada Completa'),
]
CHOICE_CantidadAmbientes = [
    ('1', '1'),
    ('2', '2'),
    ('3', '3'),
    ('4', '4'),
]

CHOICE_CondicionDe = [
   ( "Propietario del terreno y la vivienda","Propietario del terreno y la vivienda",),
   ( "Propietario de la vivienda solamente","Propietario de la vivienda solamente",),
   ( "Inquilino","Inquilino",),
   ( "beneficios laborales","beneficios laborales",),
("Préstamo o cesión (de un conocido, familiar, etc.)","Préstamo o cesión (de un conocido, familiar, etc.)",),
   ( "Ocupante de hecho","Ocupante de hecho",),
   ( "Otro","Otro"),
]

CHOICE_ContextoCasa = [
    ('En una zona inundable (en el último año)', 'En una zona inundable (en el último año)'),
    ('Cerca de basurales (a 3 cuadras o menos)', 'Cerca de basurales (a 3 cuadras o menos)'),
    ('En una cuadra con alumbrado público', 'En una cuadra con alumbrado público'),
    ('En una cuadra pavimentada o empedrada', 'En una cuadra pavimentada o empedrada'),
    ('En una cuadra con servicio regular de recolección de residuos','En una cuadra con servicio regular de recolección de residuos'),
]


PROVINCE_CHOICES = [
    ('AC', 'Córdoba'),
    ('AR', 'Buenos Aires'),
    ('BA', 'Buenos Aires (CABA)'),
    ('CA', 'Catamarca'),
    ('CH', 'Chubut'),
    ('CO', 'Córdoba'),
    ('CR', 'Corrientes'),
    ('CT', 'Entre Ríos'),
    ('ER', 'Entre Ríos'),
    ('FO', 'Formosa'),
    ('GO', 'Goiás'),
    ('JU', 'Jujuy'),
    ('LA', 'La Pampa'),
    ('LP', 'La Rioja'),
    ('MC', 'Mendoza'),
    ('MN', 'Misiones'),
    ('NE', 'Neuquén'),
    ('RN', 'Río Negro'),
    ('SA', 'Santa Cruz'),
    ('SF', 'Santa Fe'),
    ('SJ', 'San Juan'),
    ('SL', 'San Luis'),
]

TipoAyudaHogar = [
    ('Comida/vianda de comedor comunitario', 'Comida/vianda de comedor comunitario'),
    ('Merienda o desayuno de un merendero / comedor comunitario', 'Merienda o desayuno de un merendero / comedor comunitario'),
    ('Comida/ vianda de comedor escolar', 'Comida/ vianda de comedor escolar'),
    ('Merienda o desayuno de un comedor escolar', 'Merienda o desayuno de un comedor escolar'),
    ('Libros y/o útiles escolares', 'Libros y/o útiles escolares'),
    ('Comida/vianda de comedor comunitario', 'Comida/vianda de comedor comunitario'),
    ('Ropa', 'Ropa'),
    ('Medicamentos', 'Medicamentos')
]

CHOICE_INSTITUCIONES_EDUCATIVAS = [
    ('Anexo I A Escuela De Educación Secundaria N° 3 - Anexo', 'Anexo I A Escuela De Educación Secundaria N° 3 - Anexo'),
    ('C.e.pro.m', 'C.e.pro.m'),
    ('Centro De Formacion Profesional Fuce (Ex 9003),', 'Centro De Formacion Profesional Fuce (Ex 9003)'),
    ('Centro De Formación Integral N° 1', 'Centro De Formación Integral N° 1'),
    ('Centro De Formación Profesional N° 402', 'Centro De Formación Profesional N° 402'),
    ('Centro De Formación Profesional N° 403', 'Centro De Formación Profesional N° 403'),
    ('Centro Educativo De Nivel Secundario N° 453', 'Centro Educativo De Nivel Secundario N° 453'),
    ('Centro Educativo Nivel Secundaria N° 451', 'Centro Educativo Nivel Secundaria N° 451'),
    ('Centro Educativo Nivel Secundaria N° 452', 'Centro Educativo Nivel Secundaria N° 452'),
    ('Centro Educativo Nivel Secundaria N° 454', 'Centro Educativo Nivel Secundaria N° 454'),
    ('Centro Educativo Nivel Secundaria N° 455', 'Centro Educativo Nivel Secundaria N° 455'),
    ('Centro Educativo Nivel Secundaria N° 456', 'Centro Educativo Nivel Secundaria N° 456'),
    ('Centro Formación Profesional N° 401', 'Centro Formación Profesional N° 401'),
    ('Colegio Aberdare', 'Colegio Aberdare'),
    ('Colegio De La Providencia', 'Colegio De La Providencia'),
    ('Colegio De Los Santos Padres', 'Colegio De Los Santos Padres'),
    ('Colegio Divina Pastora', 'Colegio Divina Pastora'),
    ('Colegio El Tato', 'Colegio El Tato'),
    ('Colegio Glasgow', 'Colegio Glasgow'),
    ('Colegio Las Marias', 'Colegio Las Marias'),
    ('Colegio Madre Teresa', 'Colegio Madre Teresa'),
    ('Colegio Madre Tierra', 'Colegio Madre Tierra'),
    ('Colegio Monseñor Terrero', 'Colegio Monseñor Terrero'),
    ('Colegio Naciones Unidas Del Mundo', 'Colegio Naciones Unidas Del Mundo'),
    ('Colegio Parroquial Del Patriarca San Jose', 'Colegio Parroquial Del Patriarca San Jose'),
    ('Colegio Parroquial Nuestra Señora De Itati', 'Colegio Parroquial Nuestra Señora De Itati'),
    ('Colegio Parroquial Nuestra Señora De Lujan', 'Colegio Parroquial Nuestra Señora De Lujan'),
    ('Colegio Parroquial Santa Maria Del Trujui', 'Colegio Parroquial Santa Maria Del Trujui'),
    ('Colegio Parroquial Santa Teresa De Jesus', 'Colegio Parroquial Santa Teresa De Jesus'),
    ('Colegio Sagrada Familia', 'Colegio Sagrada Familia'),
    ('Colegio San Agustin', 'Colegio San Agustin'),
    ('Colegio San Jose De Oro Ocampo', 'Colegio San Jose De Oro Ocampo'),
    ('Colegio San Miguel Arcangel', 'Colegio San Miguel Arcangel'),
    ('Colegio Santa Ethnea', 'Colegio Santa Ethnea'),
    ('Colgio Tolkien', 'Colgio Tolkien'),
    ('Conservatorio De Musica N° 1', 'Conservatorio De Musica N° 1'),
    ('Ctro. Int. De Form. Para El Trabajo Mi Encuentro (Ex 9001)', 'Ctro. Int. De Form. Para El Trabajo Mi Encuentro (Ex 9001)'),
    ('Escuela Almafuerte', 'Escuela Almafuerte'),
    ('Escuela Angel D Elia', 'Escuela Angel D Elia'),
    ('Escuela Atahualpa Yupanqui', 'Escuela Atahualpa Yupanqui'),
    ('Escuela Club Atletico San Miguel', 'Escuela Club Atletico San Miguel'),
    ('Escuela De Artes Visuales N° 1', 'Escuela De Artes Visuales N° 1'),
    ('Escuela De Educacion De Adultos N° 701', 'Escuela De Educacion De Adultos N° 701'),
    ('Escuela De Educacion De Adultos N° 702', 'Escuela De Educacion De Adultos N° 702'),
    ('Escuela De Educacion De Adultos N° 703', 'Escuela De Educacion De Adultos N° 703'),
    ('Escuela De Educacion De Adultos N° 704', 'Escuela De Educacion De Adultos N° 704'),
    ('Escuela De Educacion De Adultos N° 705', 'Escuela De Educacion De Adultos N° 705'),
    ('Escuela De Educacion De Adultos N° 706', 'Escuela De Educacion De Adultos N° 706'),
    ('Escuela De Educacion De Adultos N° 707', 'Escuela De Educacion De Adultos N° 707'),
    ('Escuela De Educacion De Adultos N° 708', 'Escuela De Educacion De Adultos N° 708'),
    ('Escuela De Educacion De Adultos N° 709', 'Escuela De Educacion De Adultos N° 709'),
    ('Escuela De Educacion De Adultos N° 710', 'Escuela De Educacion De Adultos N° 710'),
    ('Escuela De Educación Especial N° 502', 'Escuela De Educación Especial N° 502'),
    ('Escuela De Educación Especial N° 503', 'Escuela De Educación Especial N° 503'),
    ('Escuela De Educación Especial N° 504', 'Escuela De Educación Especial N° 504'),
    ('Escuela De Educación Primaria N° 1 "Domingo Faustino Sarmiento"', 'Escuela De Educación Primaria N° 1 "Domingo Faustino Sarmiento"'),
    ('Escuela De Educación Primaria N° 10 "Mariano Moreno"', 'Escuela De Educación Primaria N° 10 "Mariano Moreno"'),
    ('Escuela De Educación Primaria N° 11 "Jorge Newbery"', 'Escuela De Educación Primaria N° 11 "Jorge Newbery"'),
    ('Escuela De Educación Primaria N° 12 "Gabriela Mistral"', 'Escuela De Educación Primaria N° 12 "Gabriela Mistral"'),
    ('Escuela De Educación Primaria N° 13 "Jose Gervasio Artigas"', 'Escuela De Educación Primaria N° 13 "Jose Gervasio Artigas"'),
    ('Escuela De Educación Primaria N° 14 "Dr. Francisco Javier Muñiz"', 'Escuela De Educación Primaria N° 14 "Dr. Francisco Javier Muñiz"'),
    ('Escuela De Educación Primaria N° 15 "Fray Mamerto Esquiu"', 'Escuela De Educación Primaria N° 15 "Fray Mamerto Esquiu"'),
    ('Escuela De Educación Primaria N° 16 "Justo Jose De Urquiza"', 'Escuela De Educación Primaria N° 16 "Justo Jose De Urquiza"'),
    ('Escuela De Educación Primaria N° 17 "Esteban Echeverria"', 'Escuela De Educación Primaria N° 17 "Esteban Echeverria"'),
    ('Escuela De Educación Primaria N° 18 "Maestro E Ferreyra"', 'Escuela De Educación Primaria N° 18 "Maestro E Ferreyra"'),
    ('Escuela De Educación Primaria N° 19 "Rafael Obligado"', 'Escuela De Educación Primaria N° 19 "Rafael Obligado"'),
    ('Escuela De Educación Primaria N° 2 "Bernardino Rivadavia"', 'Escuela De Educación Primaria N° 2 "Bernardino Rivadavia"'),
    ('Escuela De Educación Primaria N° 20 "Dr. Angel Gallardo"', 'Escuela De Educación Primaria N° 20 "Dr. Angel Gallardo"'),
    ('Escuela De Educación Primaria N° 21 "Ceferino Namuncura"', 'Escuela De Educación Primaria N° 21 "Ceferino Namuncura"'),
    ('Escuela De Educación Primaria N° 22 "Ejercito Argentino"', 'Escuela De Educación Primaria N° 22 "Ejercito Argentino"'),
    ('Escuela De Educación Primaria N° 23 "Alfonsina Storni"', 'Escuela De Educación Primaria N° 23 "Alfonsina Storni"'),
    ('Escuela De Educación Primaria N° 24 "Yapeyu"', 'Escuela De Educación Primaria N° 24 "Yapeyu"'),
    ('Escuela De Educación Primaria N° 25 "San Ignacio"', 'Escuela De Educación Primaria N° 25 "San Ignacio"'),
    ('Escuela De Educación Primaria N° 26 "Jose De San Martin"', 'Escuela De Educación Primaria N° 26 "Jose De San Martin"'),
    ('Escuela De Educación Primaria N° 27 "Juana Azurduy De Padilla"', 'Escuela De Educación Primaria N° 27 "Juana Azurduy De Padilla"'),
    ('Escuela De Educación Primaria N° 28', 'Escuela De Educación Primaria N° 28'),
    ('Escuela De Educación Primaria N° 29 "Dr. Jose Maria Ramos Mejia"', 'Escuela De Educación Primaria N° 29 "Dr. Jose Maria Ramos Mejia"'),
    ('Escuela De Educación Primaria N° 3 "Hipolito Yrigoyen"', 'Escuela De Educación Primaria N° 3 "Hipolito Yrigoyen"'),
    ('Escuela De Educación Primaria N° 30 "Clorinda T.b. De Munzon"', 'Escuela De Educación Primaria N° 30 "Clorinda T.b. De Munzon"'),
    ('Escuela De Educación Primaria N° 31 "Juana Paula Manso"', 'Escuela De Educación Primaria N° 31 "Juana Paula Manso"'),
    ('Escuela De Educación Primaria N° 32 "Pablo Pizzurno"', 'Escuela De Educación Primaria N° 32 "Pablo Pizzurno"'),
    ('Escuela De Educación Primaria N° 33 "Manuel Moreno"', 'Escuela De Educación Primaria N° 33 "Manuel Moreno"'),
    ('Escuela De Educación Primaria N° 34 "Mariano Acosta"', 'Escuela De Educación Primaria N° 34 "Mariano Acosta"'),
    ('Escuela De Educación Primaria N° 35 "Ricardo Güiraldes"', 'Escuela De Educación Primaria N° 35 "Ricardo Güiraldes"'),
    ('Escuela De Educación Primaria N° 36 "Crucero Gral. Belgrano"', 'Escuela De Educación Primaria N° 36 "Crucero Gral. Belgrano"'),
    ('Escuela De Educación Primaria N° 37 "Domingo Faustino Sarmiento"', 'Escuela De Educación Primaria N° 37 "Domingo Faustino Sarmiento"'),
    ('Escuela De Educación Primaria N° 38 "Manuel Belgrano"', 'Escuela De Educación Primaria N° 38 "Manuel Belgrano"'),
    ('Escuela De Educación Primaria N° 39 "Jose Hernandez"', 'Escuela De Educación Primaria N° 39 "Jose Hernandez"'),
    ('Escuela De Educación Primaria N° 4 "Nuestra Señora De Las Mercedes"', 'Escuela De Educación Primaria N° 4 "Nuestra Señora De Las Mercedes"'),
    ('Escuela De Educación Primaria N° 5 "Andres Bello"', 'Escuela De Educación Primaria N° 5 "Andres Bello"'),
    ('Escuela De Educación Primaria N° 6 "General Don Jose De San Martin"', 'Escuela De Educación Primaria N° 6 "General Don Jose De San Martin"'),
    ('Escuela De Educación Primaria N° 7 "Juan Bautista Alberdi"', 'Escuela De Educación Primaria N° 7 "Juan Bautista Alberdi"'),
    ('Escuela De Educación Primaria N° 8 "Jose Manuel Estrada"', 'Escuela De Educación Primaria N° 8 "Jose Manuel Estrada"'),
    ('Escuela De Educación Primaria N° 9 "Tambor De Tacuari"', 'Escuela De Educación Primaria N° 9 "Tambor De Tacuari"'),
    ('Escuela De Educación Secundaria N° 1 "Brigadier Gral. Juan F. Quiroga"', 'Escuela De Educación Secundaria N° 1 "Brigadier Gral. Juan F. Quiroga"'),
    ('Escuela De Educación Secundaria N° 10', 'Escuela De Educación Secundaria N° 10'),
    ('Escuela De Educación Secundaria N° 11', 'Escuela De Educación Secundaria N° 11'),
    ('Escuela De Educación Secundaria N° 12', 'Escuela De Educación Secundaria N° 12'),
    ('Escuela De Educación Secundaria N° 13', 'Escuela De Educación Secundaria N° 13'),
    ('Escuela De Educación Secundaria N° 14', 'Escuela De Educación Secundaria N° 14'),
    ('Escuela De Educación Secundaria N° 15', 'Escuela De Educación Secundaria N° 15'),
    ('Escuela De Educación Secundaria N° 16', 'Escuela De Educación Secundaria N° 16'),
    ('Escuela De Educación Secundaria N° 17', 'Escuela De Educación Secundaria N° 17'),
    ('Escuela De Educación Secundaria N° 18', 'Escuela De Educación Secundaria N° 18'),
    ('Escuela De Educación Secundaria N° 19', 'Escuela De Educación Secundaria N° 19'),
    ('Escuela De Educación Secundaria N° 2 "Ing. Adolfo Sourdeaux"', 'Escuela De Educación Secundaria N° 2 "Ing. Adolfo Sourdeaux"'),
    ('Escuela De Educación Secundaria N° 20', 'Escuela De Educación Secundaria N° 20'),
    ('Escuela De Educación Secundaria N° 21', 'Escuela De Educación Secundaria N° 21'),
    ('Escuela De Educación Secundaria N° 22', 'Escuela De Educación Secundaria N° 22'),
    ('Escuela De Educación Secundaria N° 23', 'Escuela De Educación Secundaria N° 23'),
    ('Escuela De Educación Secundaria N° 24', 'Escuela De Educación Secundaria N° 24'),
    ('Escuela De Educación Secundaria N° 25', 'Escuela De Educación Secundaria N° 25'),
    ('Escuela De Educación Secundaria N° 26', 'Escuela De Educación Secundaria N° 26'),
    ('Escuela De Educación Secundaria N° 27', 'Escuela De Educación Secundaria N° 27'),
    ('Escuela De Educación Secundaria N° 28', 'Escuela De Educación Secundaria N° 28'),
    ('Escuela De Educación Secundaria N° 29', 'Escuela De Educación Secundaria N° 29'),
    ('Escuela De Educación Secundaria N° 3 "Heroes De Malvinas"', 'Escuela De Educación Secundaria N° 3 "Heroes De Malvinas"'),
    ('Escuela De Educación Secundaria N° 30', 'Escuela De Educación Secundaria N° 30'),
    ('Escuela De Educación Secundaria N° 31', 'Escuela De Educación Secundaria N° 31'),
    ('Escuela De Educación Secundaria N° 32', 'Escuela De Educación Secundaria N° 32'),
    ('Escuela De Educación Secundaria N° 33', 'Escuela De Educación Secundaria N° 33'),
    ('Escuela De Educación Secundaria N° 34', 'Escuela De Educación Secundaria N° 34'),
    ('Escuela De Educación Secundaria N° 35', 'Escuela De Educación Secundaria N° 35'),
    ('Escuela De Educación Secundaria N° 36', 'Escuela De Educación Secundaria N° 36'),
    ('Escuela De Educación Secundaria N° 37', 'Escuela De Educación Secundaria N° 37'),
    ('Escuela De Educación Secundaria N° 38', 'Escuela De Educación Secundaria N° 38'),
    ('Escuela De Educación Secundaria N° 4 "Raul Scalabrini Ortiz"', 'Escuela De Educación Secundaria N° 4 "Raul Scalabrini Ortiz"'),
    ('Escuela De Educación Secundaria N° 4 - Anexo', 'Escuela De Educación Secundaria N° 4 - Anexo'),
    ('Escuela De Educación Secundaria N° 5 "Belgrano Educador"', 'Escuela De Educación Secundaria N° 5 "Belgrano Educador"'),
    ('Escuela De Educación Secundaria N° 6 "Juana Manso"', 'Escuela De Educación Secundaria N° 6 "Juana Manso"'),
    ('Escuela De Educación Secundaria N° 7 "Domingo F. Sarmiento"', 'Escuela De Educación Secundaria N° 7 "Domingo F. Sarmiento"'),
    ('Escuela De Educación Secundaria N° 8', 'Escuela De Educación Secundaria N° 8'),
    ('Escuela De Educación Secundaria N° 9', 'Escuela De Educación Secundaria N° 9'),
    ('Escuela De Educación Secundaria Técnica N° 1 "Nuestra Señora Del Valle"', 'Escuela De Educación Secundaria Técnica N° 1 "Nuestra Señora Del Valle"'),
    ('Escuela De Educación Secundaria Técnica N° 2 "República Argentina"', 'Escuela De Educación Secundaria Técnica N° 2 "República Argentina"'),
    ('Escuela De Educación Secundaria Técnica N° 3 "Japón"', 'Escuela De Educación Secundaria Técnica N° 3 "Japón"'),
    ('Escuela De Teatro N° 1', 'Escuela De Teatro N° 1'),
    ('Escuela Especial Buscando El Sol', 'Escuela Especial Buscando El Sol'),
    ('Escuela Especial Mi Encuentro', 'Escuela Especial Mi Encuentro'),
    ('Escuela Integral Jorge Luis Borges', 'Escuela Integral Jorge Luis Borges'),
    ('Escuela Jorge Luis Borges', 'Escuela Jorge Luis Borges'),
    ('Escuela La Inmaculada', 'Escuela La Inmaculada'),
    ('Escuela Malvinas Argentinas', 'Escuela Malvinas Argentinas'),
    ('Escuela Maria Rosa Mistica', 'Escuela Maria Rosa Mistica'),
    ('Escuela Martin Fierro', 'Escuela Martin Fierro'),
    ('Escuela Mi Jardin', 'Escuela Mi Jardin'),
    ('Escuela Modelo Bella Vista', 'Escuela Modelo Bella Vista'),
    ('Escuela Nuestra Señora Del Valle', 'Escuela Nuestra Señora Del Valle'),
    ('Escuelita Fundacion Suzuki', 'Escuelita Fundacion Suzuki'),
    ('Extension I De Escuela De Educación Secundaria N° 28', 'Extension I De Escuela De Educación Secundaria N° 28'),
    ('Extension Nº1 De Esc. Secundaria N° 9', 'Extension Nº1 De Esc. Secundaria N° 9'),
    ('Fundacion Ser', 'Fundacion Ser'),
    ('Hogar Escuela Ezpeleta', 'Hogar Escuela Ezpeleta'),
    ('Hogar Escuela La Inmaculada', 'Hogar Escuela La Inmaculada'),
    ('Hogar Escuela San Jose', 'Hogar Escuela San Jose'),
    ('Instituto Aberdare (Ex 025),', 'Instituto Aberdare (Ex 025)'),
    ('Instituto Alejandro Bunge', 'Instituto Alejandro Bunge'),
    ('Instituto Angel D Elia', 'Instituto Angel D Elia'),
    ('Instituto Club Atletico San Miguel', 'Instituto Club Atletico San Miguel'),
    ('Instituto De Educación Dr. Luis F. Leloir', 'Instituto De Educación Dr. Luis F. Leloir'),
    ('Instituto De Enseñanza Secundaria Almafuerte', 'Instituto De Enseñanza Secundaria Almafuerte'),
    ('Instituto De Los Padres Redentoristas', 'Instituto De Los Padres Redentoristas'),
    ('Instituto Del Bicentenario', 'Instituto Del Bicentenario'),
    ('Instituto Don Jose De San Martin', 'Instituto Don Jose De San Martin'),
    ('Instituto Don Jose De San Martin (Ex 9003)', 'Instituto Don Jose De San Martin (Ex 9003)'),
    ('Instituto Educacional Buenos Aires', 'Instituto Educacional Buenos Aires'),
    ('Instituto Educacional Dr. Luis F. Leloir', 'Instituto Educacional Dr. Luis F. Leloir'),
    ('Instituto Educacional Maria Rosa Mistica', 'Instituto Educacional Maria Rosa Mistica'),
    ('Instituto Educacional San Miguel', 'Instituto Educacional San Miguel'),
    ('Instituto Futuro Argentino', 'Instituto Futuro Argentino'),
    ('Instituto Gaspar Campos', 'Instituto Gaspar Campos'),
    ('Instituto Independencia', 'Instituto Independencia'),
    ('Instituto Jesus Maria', 'Instituto Jesus Maria'),
    ('Instituto Jorge Newbery (Ex 9011),', 'Instituto Jorge Newbery (Ex 9011),'),
    ('Instituto Jose De San Martin', 'Instituto Jose De San Martin'),
    ('Instituto Luigi Pirandello', 'Instituto Luigi Pirandello'),
    ('Instituto Luis Federico Leloir', 'Instituto Luis Federico Leloir'),
    ('Instituto Manuel Dorrego', 'Instituto Manuel Dorrego'),
    ('Instituto Mariano Moreno', 'Instituto Mariano Moreno'),
    ('Instituto Modelo De Bellla Vista', 'Instituto Modelo De Bellla Vista'),
    ('Instituto Naciones Unidas', 'Instituto Naciones Unidas'),
    ('Instituto Naciones Unidas Del Mundo', 'Instituto Naciones Unidas Del Mundo'),
    ('Instituto Nuestra Señora De Itati (Ex 9027)', 'Instituto Nuestra Señora De Itati (Ex 9027)'),
    ('Instituto Nuestra Señora De La Asuncion', 'Instituto Nuestra Señora De La Asuncion'),
    ('Instituto Nuestra Señora De La Compasion', 'Instituto Nuestra Señora De La Compasion'),
    ('Instituto Nuestra Señora De Lujan', 'Instituto Nuestra Señora De Lujan'),
    ('Instituto Nuestra Señora Del Valle', 'Instituto Nuestra Señora Del Valle'),
    ('Instituto Parroquial Nuestra Señora De La Asuncion', 'Instituto Parroquial Nuestra Señora De La Asuncion'),
    ('Instituto Patriarca San Jose', 'Instituto Patriarca San Jose'),
    ('Instituto Polimodal Culturas Unidas Del Mundo (Ex 9021)', 'Instituto Polimodal Culturas Unidas Del Mundo (Ex 9021)'),
    ('Instituto Privado Leon Gallardo', 'Instituto Privado Leon Gallardo'),
    ('Instituto San Alfonso', 'Instituto San Alfonso'),
    ('Instituto San Miguel', 'Instituto San Miguel'),
    ('Instituto San Pio X', 'Instituto San Pio X'),
    ('Instituto Santa Ethnea', 'Instituto Santa Ethnea'),
    ('Instituto Santa Maria Del Trujui', 'Instituto Santa Maria Del Trujui'),
    ('Instituto Superior Cultural Britanico', 'Instituto Superior Cultural Britanico'),
    ('Instituto Superior De Carreras Paramedicas', 'Instituto Superior De Carreras Paramedicas'),
    ('Instituto Superior De Ciencias Sagradas San Miguel Arcangel', 'Instituto Superior De Ciencias Sagradas San Miguel Arcangel'),
    ('Instituto Superior De Formacion Docente N° 112', 'Instituto Superior De Formacion Docente N° 112'),
    ('Instituto Superior De Formacion Docente N° 42', 'Instituto Superior De Formacion Docente N° 42'),
    ('Instituto Superior De Formación Docente Y Técnica N° 182', 'Instituto Superior De Formación Docente Y Técnica N° 182'),
    ('Instituto Superior De Formación Docente Y Técnica N° 42', 'Instituto Superior De Formación Docente Y Técnica N° 42'),
    ('Instituto Tato Hermano Pequeño (Ex 9013)', 'Instituto Tato Hermano Pequeño (Ex 9013)'),
    ('Jesus Maria', 'Jesus Maria'),
    ('Lirios Del Sol', 'Lirios Del Sol'),
    ('Monseñor Terrero', 'Monseñor Terrero'),
    ('Nuestra Señora De La Paz', 'Nuestra Señora De La Paz'),
    ('Nuestra Señora Del Valle', 'Nuestra Señora Del Valle'),
    ('Opción 149', 'Opción 149'),
    ('Opción 194', 'Opción 194'),
    ('Otra', 'Otra'),
]

CHOICE_SINO = [
    (None, ''),
    ('True', 'SI'),
    ('False', 'NO'),
]

CHOICE_ESTADO_CIVIL = [
    (None, ''),
    ('Soltero', 'Soltero'),
    ('Casado', 'Casado'),
    ('Divorciado/Separado', 'Divorciado/Separado'),
    ('Viudo', 'Viudo'),
    ('Conviviendo', 'Conviviendo'),
    ('En pareja', 'En pareja'),
    ('Otro', 'Otro'),
]

CHOICE_SEXO = [
    (None, ''),
    ('Femenino', 'Femenino'),
    ('Masculino', 'Masculino'),
    ('X', 'X'),
]

CHOICE_GENERO = [
    (None, ''),
    ('Cisgénero', 'Cisgénero'),
    ('Transgénero', 'Transgénero'),
    ('Intergénero', 'Intergénero'),
    ('Género Fluido', 'Género Fluido'),
    ('Bigénero', 'Bigénero'),
    ('Queer', 'Queer'),
    ('Otro', 'Otro'),
]

CHOICE_GENERO_PRONOMBRE = [
    (None, ''),
    ('ELLA', 'ELLA'),
    ('ÉL', 'ÉL'),
    ('NEUTRO', 'NEUTRO'),
]

CHOICE_TIPO_DOC = [(None, ''), ('DNI', 'DNI'), ('DOCUMENTO EXTRANJERO', 'DOCUMENTO EXTRANJERO'), ('PASAPORTE', 'PASAPORTE'), ('SIN DOCUMENTO', 'SIN DOCUMENTO')]

CHOICE_NACIONALIDAD = [
    (None, ''),
    ('Argentina', 'Argentina'),
    ('Boliviana', 'Boliviana'),
    ('Brasilera', 'Brasilera'),
    ('Chilena', 'Chilena'),
    ('Colombiana', 'Colombiana'),
    ('Paraguaya', 'Paraguaya'),
    ('Peruana', 'Peruana'),
    ('Uruguaya', 'Uruguaya'),
    ('Venezolana', 'Venezolana'),
    ('Otra', 'Otra'),
]
# Diccionario con emojis de banderitas
EMOJIS_BANDERAS = {
    'Argentina': 'flag-icon-ar',
    'Boliviana': 'flag-icon-bo',
    'Brasilera': 'flag-icon-br',
    'Chilena': 'flag-icon-cl',
    'Colombiana': 'flag-icon-co',
    'Paraguaya': 'flag-icon-py',
    'Peruana': 'flag-icon-pe',
    'Uruguaya': 'flag-icon-uy',
    'Venezolana': 'flag-icon-ve',
    'Otra': '',
}

CHOICE_TIPO_DISCAPACIDAD = [
    (None, ''),
    ('Discapacidad física', 'Discapacidad física'),
    ('Discapacidad mental', 'Discapacidad mental'),
    ('Discapacidad sensorial', 'Discapacidad sensorial'),
    ('Discapacidad intelectual', 'Discapacidad intelectual'),
    ('Discapacidad múltiple', 'Discapacidad múltiple'),
    ('Otra', 'Otra'),
]

CHOICE_TIPO_ENFERMEDAD = [
    (None, ''),
    ('Metabólica', 'Metabólica'),
    ('Cardíaca', 'Cardíaca'),
    ('Respiratoria', 'Respiratoria'),
    ('Cerebro Vascular', 'Cerebro Vascular'),
    ('Tumoral', 'Tumoral'),
    ('Otra', 'Otra'),
]

CHOICE_TIPO_VIVIENDA = [
    (None, ''),
    ('Casa', 'Casa'),
    ('Rancho', 'Rancho'),
    ('Casilla', 'Casilla'),
    ('Vivienda móvil', 'Vivienda móvil'),
    ('Situación de calle', 'Situación de calle'),
    ('Departamento', 'Departamento'),
    ('Pieza en hotel familiar o pensión', 'Pieza en hotel familiar o pensión'),
    ('Pieza en hotel/Pensón', 'Pieza en hotel/Pensón'),
    ('Sitio no construido para vivienda', 'Sitio no construido para vivienda'),
    ('Otro', 'Otro'),
]

CHOICE_TIPO_POSESION_VIVIENDA = [
    (None, ''),
    ('Propia', 'Propia'),
    ('Alquilada', 'Alquilada'),
    ('Cedida', 'Cedida'),
    ('Posesión de Hecho', 'Posesión de Hecho'),
    ('Otro', 'Otro'),
]

CHOICE_TIPO_PISOS_VIVIENDA = [
    (None, ''),
    ('Mosaico / baldosa / madera / cerámica', 'Mosaico / baldosa / madera / cerámica'),
    ('Cemento / ladrillo fijo', 'Cemento / ladrillo fijo'),
    ('Ladrillo suelto / tierra', 'Ladrillo suelto / tierra'),
    ('Otro', 'Otro'),
]

CHOICE_TIPO_TECHO_VIVIENDA = [
    ('Cubierta asfáltica o membrana', 'Cubierta asfáltica o membrana'),
	('Baldosa o losa (sin cubierta)', 'Baldosa o losa (sin cubierta)'),
	('Pizarra o teja', 'Pizarra o teja'),
	('Chapa de metal (sin cubierta)', 'Chapa de metal (sin cubierta)'),
	('Chapa de fibrocemento o plástico', 'Chapa de fibrocemento o plástico'),
	('Chapa de cartón', 'Chapa de cartón'),
	('Caña, palma, tabla o paja con o sin barro', 'Caña, palma, tabla o paja con o sin barro'),
	('Otro', 'Otro'),
	('Ns/Nc', 'Ns/Nc')
]

CHOICE_AGUA = [
	('Red pública', 'Red pública'),
	('Perforación bomba a motor', 'Perforación bomba a motor'),
	('Perforación bomba manual', 'Perforación bomba manual'),
    ('Pozo', 'Pozo'),
	('Transporte con cisterna', 'Transporte con cisterna'),
	('Agua de lluvia, canal, río, arroyo o acequia', 'Agua de lluvia, canal, río, arroyo o acequia'),
	('Otro', 'Otro')
]

CHOICE_DESAGUE = [
	('A red pública', 'A red pública'),
	('A cámara séptica', 'A cámara séptica') ,
	('A pozo ciego', 'A pozo ciego'),
	('A hoyo, excavación en la tierra, etc', 'A hoyo, excavación en la tierra, etc'),
    ('Otro', 'Otro'),
	('Ns/Nc', 'Ns/Nc')
]

CHOICE_INODORO = [
    ('Inodoro con botón o cadena', 'Inodoro con botón o cadena') ,
	('Inodoro sin botón o cadena', 'Inodoro sin botón o cadena'),
	('No tiene inodoro', 'No tiene inodoro'),
	('No tiene baño', 'No tiene baño')
]

CHOICE_GAS = [
    ('Gas de red', 'Gas de red'),
	('Gas a granel', 'Gas a granel'),
	('Gas en tubo', 'Gas en tubo'),
	('Gas en garrafa sin subsidio', 'Gas en garrafa sin subsidio'),
	('Gas en garrafa con subsidio estatal', 'Gas en garrafa con subsidio estatal'),
	('Electricidad', 'Electricidad'),
	('Leña o carbón', 'Leña o carbón'),
	('Otro', 'Otro')
]

CHOICE_TIPO_CONSTRUCCION_VIVIENDA = [
    (None, ''),
    ('Material', 'Material'),
    ('Mixta (chapa y madera)', 'Mixta (chapa y madera)'),
    ('Casilla (otros materiales)', 'Casilla (otros materiales)'),
    ('Otro', 'Otro'),
]

CHOICE_TIPO_ESTADO_VIVIENDA = [
    (None, ''),
    ('Bueno', 'Bueno'),
    ('Malo', 'Malo'),
    ('Muy malo', 'Muy malo'),
]

CHOICE_CENTROS_SALUD = [
    (None, ''),
    ('20 de Julio', '20 de Julio'),
    ('29 de Septiembre', '29 de Septiembre'),
    ('Ana Teresa Barthalot', 'Ana Teresa Barthalot'),
    ('C.I.C Maria Lobato', 'C.I.C Maria Lobato'),
    ('Camila Rolón', 'Camila Rolón'),
    ('Cándido Castello', 'Cándido Castello'),
    ('Rodolfo Podestá', 'Rodolfo Podestá'),
    ('Cura Brochero', 'Cura Brochero'),
    ('Alberto Sabin', 'Alberto Sabin'),
    ('Federico Leloir', 'Federico Leloir'),
    ('Suárez París', 'Suárez París'),
    ('Raúl Matera', 'Raúl Matera'),
    ('René Favaloro', 'René Favaloro'),
    ('Marta Antoniazzi', 'Marta Antoniazzi'),
    ('Padre Mora', 'Padre Mora'),
    ('Pte. Perón', 'Pte. Perón'),
    ('Ramón Castillo', 'Ramón Castillo'),
    ('San Miguel Oeste', 'San Miguel Oeste'),
    ('U.F.O /Manuelita', 'U.F.O /Manuelita'),
    ('Hospital Público', 'Hospital Público'),
    ('Clínica Privada o Sanatorio', 'Clínica Privada o Sanatorio'),
    ('No asiste a instituciones de salud ', 'No asiste a instituciones de salud'),
]

CHOICE_FRECUENCIA = [
    (None, ''),
    ('6 meses o menos', '6 meses o menos'),
    ('1 año', '1 año'),
    ('5 años', '5 años'),
    ('Solo ante afecciones', 'Solo ante afecciones'),
    ('No realiza controles', 'No realiza controles'),
]

CHOICE_MODO_CONTRATACION = [
    (None, ''),
    ('Relación de dependencia', 'Relación de dependencia'),
    ('Monotributista / Contratado', 'Monotributista / Contratado'),
    ('Informal con cobro mensual', 'Informal con cobro mensual'),
    ('Jornal', 'Jornal'),
    ('Changarín', 'Changarín'),
    ('Otro', 'Otro'),
]

CHOICE_ACTIVIDAD_REALIZADA = [
    ('Patrón o empleador', 'Patrón o empleador'),
    ('Trabajador por cuenta propia solo', 'Trabajador por cuenta propia solo'),
    ('Trabajador por cuenta propia asociado (en cooperativa, en emprendimiento familiar, etc.)', 'Trabajador por cuenta propia asociado (en cooperativa, en emprendimiento familiar, etc.)'),
    ('Obrero o empleado del sector privado (asalariado)', 'Obrero o empleado del sector privado (asalariado)'),
    ('Obrero o empleado del sector público (asalariado)', 'Obrero o empleado del sector público (asalariado)'),
    ('Servicio doméstico', 'Servicio doméstico'),
    ('Trabajador sin remuneración', 'Trabajador sin remuneración'),
    ('Cuenta con un programa de empleo o comunitario', 'Cuenta con un programa de empleo o comunitario')
]

CHOICE_DURACION_TRABAJO = [
    ('Permanente', 'Permanente'),
    ('Temporario (plazo fijo/ obra) por más de un mes', 'Temporario (plazo fijo/ obra) por más de un mes'),
    ('Changa (1 mes o menos)', 'Changa (1 mes o menos)'),
    ('Duración desconocida (inestable)', 'Duración desconocida (inestable)')
]

CHOICE_APORTES_JUBILACION= [
    ('Me descuentan', 'Me descuentan'),
    ('Soy monotributista o autónomo', 'Soy monotributista o autónomo'),
    ('Soy monotributista social', 'Soy monotributista social'),
    ('Ni me descuentan ni aporto', 'Ni me descuentan ni aporto')
]

CHOICE_TIEMPO_BUSQUEDA_LABORAL = [
    ('Menos de un mes', 'Menos de un mes'),
    ('De 1 a 3 meses', 'De 1 a 3 meses'),
    (' Más de 3 a 6 meses', ' Más de 3 a 6 meses'),
    ('Más de 6 meses a 1 año', 'Más de 6 meses a 1 año'),
    ('Más de 1 año', 'Más de 1 año')
    
]

CHOICE_NO_BUSQUEDA_LABORAL = [
    ('Espero respuesta de un empleador', 'Espero respuesta de un empleador'),
    ('Espero comienzo de un nuevo trabajo (trabajo estacional)', 'Espero comienzo de un nuevo trabajo (trabajo estacional)'),
    ('Soy estudiante/ me estoy capacitando', 'Soy estudiante/ me estoy capacitando'),
    ('Por motivos de edad (menor o anciano)', 'Por motivos de edad (menor o anciano)'),
    ('Me dedico a quehaceres del hogar/ cuido personas en el hogar', 'Me dedico a quehaceres del hogar/ cuido personas en el hogar'),
    ('Soy pensionado/ jubilado', 'Soy pensionado/ jubilado'),
    ('Soy rentista', 'Soy rentista'),
    ('Soy discapacitado', 'Soy discapacitado'),
    ('Estoy enfermo', 'Estoy enfermo'),
    ('Creo no poder encontrarlo/ no hay', 'Creo no poder encontrarlo/ no hay'),
    ('No tengo dinero para viajar', 'No tengo dinero para viajar'),
    ('Otro motivo', 'Otro motivo')
]


CHOICE_NIVEL = [
    (None, ''),
    ('Bajo', 'Bajo'),
    ('Medio', 'Medio'),
    ('Alto', 'Alto'),
    ('Muy alto', 'Muy alto'),
]

CHOICE_ACCION = [
    (None, ''),
    ('ALTA', 'ALTA'),
    ('BAJA', 'BAJA'),
]

CHOICE_ESTADO_RELACION = [
    (None, ''),
    ('Buena', 'Buena'),
    ('Mala', 'Mala'),
    ('Indiferente', 'Indiferente'),
    ('Sin Datos', 'Sin Datos'),
]
CHOICE_ESTADO_DERIVACION = [
    (None, ''),
    ('Pendiente', 'Pendiente'),
    ('En análisis', 'En análisis'),
    ('Aceptada', 'Aceptada'),
    ('Asesoramiento', 'Asesoramiento'),
    ('finalizada', 'finalizada'),
]

CHOICE_VINCULO_FAMILIAR = [
    (None, ''),
    ('Padre', 'Padre'),
    ('Madre', 'Madre'),
    ('Hijo/a', 'Hijo/a'),
    ('Hermano/a', 'Hermano/a'),
    ('Abuelo/a', 'Abuelo/a'),
    ('Nieto/a', 'Nieta/a'),
    ('Tío/a', 'Tío/a'),
    ('Sobrino/a', 'Sobrino/a'),
    ('Pareja', 'Pareja'),
    ('Otro', 'Otro'),
]

CHOICE_CIRCUITOS = [
    (None, ''),
    ('0397A', '0397A'),
    ('0397B', '0397B'),
    ('0397C', '0397C'),
    ('0397', '0397'),
    ('0400', '0400'),
    ('0401A', '0401A'),
    ('0401', '0401'),
    ('0402', '0402'),
]

CHOICE_LOCALIDAD = [
    (None, ''),
    ('San Miguel', 'San Miguel'),
    ('Bella Vista', 'Bella Vista'),
    ('Muñiz', 'Muñiz'),
    ('Santa María', 'Santa María'),
]

CHOICE_BARRIOS = [
    (None, ''),
    ('Altos de San José', 'Altos de San José'),
    ('Bello Horizonte', 'Bello Horizonte'),
    ('Colegio Máximo', 'Colegio Máximo'),
    ('Colibrí', 'Colibrí'),
    ('Constantini', 'Constantini'),
    ('Cuartel Segundo Cc.', 'Cuartel Segundo Cc.'),
    ('Don Alfonso', 'Don Alfonso'),
    ('La Gloria', 'La Gloria'),
    ('La Estrella', 'La Estrella'),
    ('La Guarida', 'La Guarida'),
    ('La Manuelita', 'La Manuelita'),
    ('Lomas de Mariló', 'Lomas de Mariló'),
    ('Los Paraísos', 'Los Paraísos'),
    ('Los Plátanos', 'Los Plátanos'),
    ('Macabi', 'Macabi'),
    ('María Rosa Mística', 'María Rosa Mística'),
    ('Mitre', 'Mitre'),
    ('Parque San Miguel', 'Parque San Miguel'),
    ('Parque San Ignacio', 'Parque San Ignacio'),
    ('Santa Brígida', 'Santa Brígida'),
    ('Sarmiento', 'Sarmiento'),
    ('Trujui', 'Trujui'),
    ('Santa María', 'Santa María'),
    ('San Antonio', 'San Antonio'),
    ('San Ignacio', 'San Ignacio'),
]

CHOICE_IMPORTANCIA = [
    (None, ''),
    ('Alta', 'Alta'),
    ('Urgente', 'Urgente'),
    ('Muy urgente', 'Muy urgente'),
]

VINCULO_MAP = {
    "Padre": {"vinculo": "Padre", "vinculo_inverso": "Hijo/a"},
    "Madre": {"vinculo": "Madre", "vinculo_inverso": "Hijo/a"},
    "Hijo/a": {"vinculo": "Hijo/a", "vinculo_inverso": "Padre/Madre"},
    "Abuelo/a": {"vinculo": "Abuelo/a", "vinculo_inverso": "Nieto/a"},
    "Nieto/a": {"vinculo": "Nieto/a", "vinculo_inverso": "Abuelo/a"},
    "Pareja": {"vinculo": "Pareja", "vinculo_inverso": "Pareja"},
    "Hermano/a": {"vinculo": "Hermano/a", "vinculo_inverso": "Hermano/a"},
    "Tío/a": {"vinculo": "Tío/a", "vinculo_inverso": "Sobrino/a"},
    "Sobrino/a": {"vinculo": "Sobrino/a", "vinculo_inverso": "Tío/a"},
    "Otro": {"vinculo": "Otro", "vinculo_inverso": "Otro"},
}
DIMENSIONES_RIESGO_MAP = {
    'Familia':  'Riesgo familiar',
    'Vivienda':  'Riesgo habitacional',
    'Salud':  'Riesgo Salud',
    'Economía':  'Riesgo económico',
    'Educación':  'Riesgo educacional',
    'Trabajo':  'Riesgo laboral',
}
NOMBRES_MESES_MAP = {
    1: 'Enero',
    2: 'Febrero',
    3: 'Marzo',
    4: 'Abril',
    5: 'Mayo',
    6: 'Junio',
    7: 'Julio',
    8: 'Agosto',
    9: 'Septiembre',
    10: 'Octubre',
    11: 'Noviembre',
    12: 'Diciembre',
}
CHOICE_RECHAZO = [
    (None, ''),
    ('No corresponde',  'No corresponde'),
    ('Fuera de edad requerida',  'Fuera de edad requerida'),
]
