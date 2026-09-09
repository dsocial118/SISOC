-- ===========================================================================
-- RUNAC — Capa 3: base consolidada
--
-- Una fila por cosa del mundo real: una persona, una medida, un dispositivo.
-- La Capa 2 guarda lo que presentó cada jurisdiccion en cada periodo; esta
-- capa guarda la version unica, y de cada dato se puede decir de donde salio.
--
-- Convencion de nombres: runac_<capa>_<entidad>
--
-- Las tablas runac_c3_disp_* llevan aca su clave y el comentario con los
-- grupos de campos. Sus columnas reales se generan desde la definicion de la
-- Capa 1, igual que las tablas receptoras de la Capa 2: la estructura de un
-- dispositivo es la misma que la del archivo que lo informa.
-- ===========================================================================

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `runac_c3_coincidencia`;
DROP TABLE IF EXISTS `runac_c3_precedencia`;
DROP TABLE IF EXISTS `runac_c3_cambio`;
DROP TABLE IF EXISTS `runac_c3_origen`;
DROP TABLE IF EXISTS `runac_c3_unidad_alias`;
DROP TABLE IF EXISTS `runac_c3_unidad_interviniente`;
DROP TABLE IF EXISTS `runac_c3_disp_alcance_territorial`;
DROP TABLE IF EXISTS `runac_c3_disp_guardia`;
DROP TABLE IF EXISTS `runac_c3_disp_cad`;
DROP TABLE IF EXISTS `runac_c3_disp_mpt`;
DROP TABLE IF EXISTS `runac_c3_disp_crsc`;
DROP TABLE IF EXISTS `runac_c3_disp_crc`;
DROP TABLE IF EXISTS `runac_c3_disp_residencial`;
DROP TABLE IF EXISTS `runac_c3_medida_dae`;
DROP TABLE IF EXISTS `runac_c3_medida_mpj`;
DROP TABLE IF EXISTS `runac_c3_medida_mpe`;
DROP TABLE IF EXISTS `runac_c3_medida_mpi`;
DROP TABLE IF EXISTS `runac_c3_dispositivo`;
DROP TABLE IF EXISTS `runac_c3_familia_acogimiento`;
DROP TABLE IF EXISTS `runac_c3_referente_adulto`;
DROP TABLE IF EXISTS `runac_c3_nya_id_provincial`;
DROP TABLE IF EXISTS `runac_c3_nino_adolescente`;
DROP TABLE IF EXISTS `runac_c3_persona`;
-- Tablas de la version anterior de esta capa, reemplazadas.
DROP TABLE IF EXISTS `runac_c3_persona_dato_origen`;
DROP TABLE IF EXISTS `runac_c3_familia`;
DROP TABLE IF EXISTS `runac_c3_medida`;

SET FOREIGN_KEY_CHECKS = 1;

-- ===========================================================================
-- IDENTIDAD
-- ===========================================================================

CREATE TABLE `runac_c3_persona` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID SISOC. Se asigna una vez y no cambia.',
  `ciudadano_id` bigint DEFAULT NULL COMMENT 'Vinculo con ciudadanos.Ciudadano de SISOC. Definicion pendiente.',
  `tipo_documento` varchar(30) DEFAULT NULL,
  `numero_documento` varchar(20) DEFAULT NULL,
  `cuil` varchar(13) DEFAULT NULL,
  `creada_el` datetime DEFAULT CURRENT_TIMESTAMP,
  `actualizada_el` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_persona_documento` (`tipo_documento`, `numero_documento`),
  KEY `ix_persona_cuil` (`cuil`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='El mismo ser humano, y unicamente su identidad resuelta. Todo lo relevado sobre una persona vive en su caracterizacion: nino o adolescente, o referente adulto. Una misma persona puede tener las dos.';

CREATE TABLE `runac_c3_nino_adolescente` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `persona_id` bigint NOT NULL,

  `apellidos` varchar(120) DEFAULT NULL,
  `nombres` varchar(120) DEFAULT NULL,
  `situacion_documentacion` varchar(60) DEFAULT NULL,
  `fecha_nacimiento` date DEFAULT NULL,
  `edad` int DEFAULT NULL,
  `genero` varchar(30) DEFAULT NULL,
  `pais_nacimiento` varchar(120) DEFAULT NULL,

  `asiste_institucion_educativa` varchar(30) DEFAULT NULL,
  `maximo_nivel_educativo` varchar(60) DEFAULT NULL,

  `cobertura_salud` varchar(60) DEFAULT NULL,
  `enfermedad_cronica` varchar(30) DEFAULT NULL,
  `problematica_salud` varchar(255) DEFAULT NULL,
  `consumo_problematico` varchar(30) DEFAULT NULL,

  `presenta_discapacidad` varchar(30) DEFAULT NULL,
  `tipo_discapacidad` varchar(60) DEFAULT NULL,
  `posee_cud` varchar(30) DEFAULT NULL,

  `seguridad_social` varchar(60) DEFAULT NULL,
  `asignacion_universal_por_hijo` varchar(30) DEFAULT NULL,

  `pueblo_originario` varchar(30) DEFAULT NULL,
  `pueblo_originario_especificar` varchar(120) DEFAULT NULL,
  `tiene_hijos` varchar(30) DEFAULT NULL,

  `domicilio_actual` varchar(255) DEFAULT NULL COMMENT 'Solo lo releva el MPI: en proteccion integral el chico vive ahi.',
  `provincia` varchar(120) DEFAULT NULL,
  `localidad` varchar(120) DEFAULT NULL,
  `partido` varchar(120) DEFAULT NULL,
  `codigo_postal` varchar(20) DEFAULT NULL,

  `creado_el` datetime DEFAULT CURRENT_TIMESTAMP,
  `actualizado_el` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_nya_persona` (`persona_id`),
  CONSTRAINT `fk_nya_persona` FOREIGN KEY (`persona_id`)
    REFERENCES `runac_c3_persona` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='Todo lo relevado sobre el chico, con independencia del archivo que lo informo y de la medida que tenga: la medida es circunstancial y el chico no. UNA fila por chico, con el dato vigente; si una presentacion informa un valor distinto se actualiza y el cambio va a runac_c3_cambio, que es la fuente de las series historicas.';

CREATE TABLE `runac_c3_nya_id_provincial` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nino_adolescente_id` bigint NOT NULL,
  `jurisdiccion_id` bigint NOT NULL,
  `identificador` varchar(60) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_id_provincial` (`jurisdiccion_id`, `identificador`),
  KEY `ix_id_prov_nya` (`nino_adolescente_id`),
  CONSTRAINT `fk_id_prov_nya` FOREIGN KEY (`nino_adolescente_id`)
    REFERENCES `runac_c3_nino_adolescente` (`id`),
  CONSTRAINT `fk_id_prov_jur` FOREIGN KEY (`jurisdiccion_id`)
    REFERENCES `runac_c2_jurisdiccion` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='Identificador provincial del chico. Uno por jurisdiccion: un chico informado por dos provincias tiene un identificador en cada una y ambos lo designan. Debe ser obligatorio y estable en el tiempo. FALTA EN EL MPI: omision senalada a la DNPYPI.';

CREATE TABLE `runac_c3_referente_adulto` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `persona_id` bigint NOT NULL,

  `apellidos` varchar(120) DEFAULT NULL,
  `nombres` varchar(120) DEFAULT NULL,
  `fecha_nacimiento` date DEFAULT NULL,
  `genero` varchar(30) DEFAULT NULL,
  `nacionalidad` varchar(120) DEFAULT NULL,

  `domicilio_actual` varchar(255) DEFAULT NULL,
  `provincia` varchar(120) DEFAULT NULL,
  `localidad` varchar(120) DEFAULT NULL,
  `partido` varchar(120) DEFAULT NULL,
  `codigo_postal` varchar(20) DEFAULT NULL,
  `telefono` varchar(60) DEFAULT NULL,
  `mail` varchar(120) DEFAULT NULL,

  `nivel_escolar` varchar(60) DEFAULT NULL,
  `situacion_laboral` varchar(60) DEFAULT NULL,

  `creado_el` datetime DEFAULT CURRENT_TIMESTAMP,
  `actualizado_el` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_referente_persona` (`persona_id`),
  CONSTRAINT `fk_referente_persona` FOREIGN KEY (`persona_id`)
    REFERENCES `runac_c3_persona` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='18 campos, informados unicamente en el MPI. Limitacion: la planilla no preve identificador propio del referente; sin documento, cada presentacion lo registra como un adulto distinto.';

CREATE TABLE `runac_c3_familia_acogimiento` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `jurisdiccion_id` bigint NOT NULL,
  `modalidad` ENUM('FORMAL','AMPLIADA') NOT NULL,
  `id_provincial` varchar(60) DEFAULT NULL,
  `denominacion` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_familia` (`jurisdiccion_id`, `modalidad`, `id_provincial`),
  CONSTRAINT `fk_familia_jur` FOREIGN KEY (`jurisdiccion_id`)
    REFERENCES `runac_c2_jurisdiccion` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='La planilla MPE informa dos modalidades en columnas paralelas, y hoy reune identificador y apellido de los cuidadores en un mismo campo. La separacion fue solicitada a la DNPYPI.';

-- ===========================================================================
-- DISPOSITIVOS — identificacion comun y un registro por tipo
-- ===========================================================================

CREATE TABLE `runac_c3_dispositivo` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID SISOC del dispositivo. Las plantillas siguientes deben traerlo.',
  `jurisdiccion_id` bigint NOT NULL,
  `tipo` ENUM('RESIDENCIAL','CRC','CRSC','MPT','CAD','GUARDIA') NOT NULL,
  `denominacion` varchar(255) NOT NULL,
  `dependencia_institucional` varchar(255) DEFAULT NULL,
  `localidad` varchar(120) DEFAULT NULL,
  `direccion` varchar(255) DEFAULT NULL,
  `telefono` varchar(60) DEFAULT NULL,
  `estado` ENUM('ACTIVO','BAJA_TEMPORAL','BAJA_DEFINITIVA') NOT NULL DEFAULT 'ACTIVO',
  `creado_el` datetime DEFAULT CURRENT_TIMESTAMP,
  `actualizado_el` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_dispositivo` (`jurisdiccion_id`, `denominacion`, `tipo`),
  CONSTRAINT `fk_dispositivo_jur` FOREIGN KEY (`jurisdiccion_id`)
    REFERENCES `runac_c2_jurisdiccion` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='El lugar donde se lleva a cabo la medida. Identificacion comun a los seis tipos: un identificador unico que el resto del sistema referencia sin conocer el tipo. Son los cinco campos que efectivamente aparecen en las seis hojas. Localidad y direccion faltan en la hoja Guardia Comisaria: omision senalada a la DNPYPI.';

CREATE TABLE `runac_c3_disp_residencial` (
  `dispositivo_id` bigint NOT NULL,
  PRIMARY KEY (`dispositivo_id`),
  CONSTRAINT `fk_disp_resid` FOREIGN KEY (`dispositivo_id`)
    REFERENCES `runac_c3_dispositivo` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='61 campos. Grupos: datos institucionales, gestion y convenio con el OPN, el establecimiento cuenta con..., protocolos, capacidad y cobertura, perfiles poblacionales admitidos, personal por funcion, 14 capacitaciones, proyecto de restitucion de derechos, insercion familiar y comunitaria. Comparte con los penales solo 5 de sus 61 campos, los de identificacion: son instrumentos distintos.';

CREATE TABLE `runac_c3_disp_crc` (
  `dispositivo_id` bigint NOT NULL,
  PRIMARY KEY (`dispositivo_id`),
  CONSTRAINT `fk_disp_crc` FOREIGN KEY (`dispositivo_id`)
    REFERENCES `runac_c3_dispositivo` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='36 campos. Grupos: capacidad por genero, proyecto institucional y normativa convivencial, personal por funcion, 6 protocolos, contacto socioafectivo, educacion obligatoria por nivel y horas, formacion profesional y talleres, espacios, condiciones de las celdas.';

CREATE TABLE `runac_c3_disp_crsc` (
  `dispositivo_id` bigint NOT NULL,
  PRIMARY KEY (`dispositivo_id`),
  CONSTRAINT `fk_disp_crsc` FOREIGN KEY (`dispositivo_id`)
    REFERENCES `runac_c3_dispositivo` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='36 campos IDENTICOS a los de CRC: mismos nombres, misma cantidad. Se mantiene como registro propio porque son regimenes distintos y sus cuestionarios pueden diferenciarse. Consulta abierta a la DNPYPI: corresponde relevar lo mismo?';

CREATE TABLE `runac_c3_disp_mpt` (
  `dispositivo_id` bigint NOT NULL,
  PRIMARY KEY (`dispositivo_id`),
  CONSTRAINT `fk_disp_mpt` FOREIGN KEY (`dispositivo_id`)
    REFERENCES `runac_c3_dispositivo` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='10 campos, 8 de ellos tambien en CRC. Propios: espacio de grupalidad y alcance territorial. Es un programa en territorio, no un lugar de alojamiento.';

CREATE TABLE `runac_c3_disp_cad` (
  `dispositivo_id` bigint NOT NULL,
  PRIMARY KEY (`dispositivo_id`),
  CONSTRAINT `fk_disp_cad` FOREIGN KEY (`dispositivo_id`)
    REFERENCES `runac_c3_dispositivo` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='27 campos, 22 compartidos con CRC. Propios: resolucion de creacion, articulacion interministerial, alcance territorial y tiempo maximo de permanencia en horas.';

CREATE TABLE `runac_c3_disp_guardia` (
  `dispositivo_id` bigint NOT NULL,
  PRIMARY KEY (`dispositivo_id`),
  CONSTRAINT `fk_disp_guardia` FOREIGN KEY (`dispositivo_id`)
    REFERENCES `runac_c3_dispositivo` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='9 campos, todos contenidos en CAD: es un subconjunto exacto. Consulta abierta a la DNPYPI: faltan campos propios de la guardia?';

CREATE TABLE `runac_c3_disp_alcance_territorial` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `dispositivo_id` bigint NOT NULL,
  `jurisdiccion_alcanzada` varchar(120) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_alcance` (`dispositivo_id`, `jurisdiccion_alcanzada`),
  CONSTRAINT `fk_alcance_disp` FOREIGN KEY (`dispositivo_id`)
    REFERENCES `runac_c3_dispositivo` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='MPT, CAD y guardia informan VARIAS jurisdicciones de alcance. Por eso es una relacion y no un campo de texto: permite responder que dispositivos alcanzan a un municipio determinado.';

-- ===========================================================================
-- NORMALIZACION DE CAMPOS ABIERTOS
-- ===========================================================================

CREATE TABLE `runac_c3_unidad_interviniente` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `jurisdiccion_id` bigint NOT NULL,
  `denominacion_normalizada` varchar(255) NOT NULL,
  `dependencia` varchar(255) DEFAULT NULL,
  `tipo_espacio` varchar(60) DEFAULT NULL COMMENT 'Recomendado a la DNPYPI: servicio local, programa municipal, programa provincial, hogar o residencia, centro de dia, otro.',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_unidad` (`jurisdiccion_id`, `denominacion_normalizada`),
  CONSTRAINT `fk_unidad_jur` FOREIGN KEY (`jurisdiccion_id`)
    REFERENCES `runac_c2_jurisdiccion` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='Tabla referencial de servicios, equipos y programas de proteccion integral. No es un padron que las jurisdicciones completen: se construye con lo que efectivamente se informa. El universo es abierto y por eso no admite un padron cerrado.';

CREATE TABLE `runac_c3_unidad_alias` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `jurisdiccion_id` bigint NOT NULL,
  `denominacion_informada` varchar(255) NOT NULL,
  `unidad_interviniente_id` bigint DEFAULT NULL COMMENT 'Vacio mientras esta pendiente de normalizar.',
  `estado` ENUM('RESUELTA','PENDIENTE') NOT NULL DEFAULT 'PENDIENTE',
  `resuelta_por` varchar(150) DEFAULT NULL,
  `resuelta_el` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_alias` (`jurisdiccion_id`, `denominacion_informada`),
  KEY `ix_alias_unidad` (`unidad_interviniente_id`),
  CONSTRAINT `fk_alias_jur` FOREIGN KEY (`jurisdiccion_id`)
    REFERENCES `runac_c2_jurisdiccion` (`id`),
  CONSTRAINT `fk_alias_unidad` FOREIGN KEY (`unidad_interviniente_id`)
    REFERENCES `runac_c3_unidad_interviniente` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='El diccionario. Opera en la importacion (Capa 2) y se perfecciona en cada iteracion: lo ya conocido se resuelve solo, lo nuevo queda pendiente y su resolucion incorpora una entrada para la proxima vez. Su mejora se puede aplicar a lo ya consolidado; ese reproceso queda en runac_c3_cambio.';

-- ===========================================================================
-- MEDIDAS — una entidad por tipo, con su nomenclatura
-- ===========================================================================

CREATE TABLE `runac_c3_medida_mpi` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nino_adolescente_id` bigint NOT NULL,
  `jurisdiccion_id` bigint NOT NULL,
  `fecha_inicio` date DEFAULT NULL,
  `fecha_cese` date DEFAULT NULL,
  `estado` ENUM('VIGENTE','CESADA','NO_INFORMADA') DEFAULT NULL,
  `motivo_cese` varchar(255) DEFAULT NULL,

  `origen_demanda` varchar(120) DEFAULT NULL,
  `causas` varchar(255) DEFAULT NULL,
  `destinatario` varchar(120) DEFAULT NULL COMMENT 'La planilla lo agrupa entre los datos del chico, pero describe la medida.',
  `linea_de_accion` varchar(120) DEFAULT NULL COMMENT 'Idem.',
  `plazo_previsto` varchar(120) DEFAULT NULL,

  `referente_adulto_id` bigint DEFAULT NULL,
  `relacion_vincular` varchar(60) DEFAULT NULL COMMENT 'Vinculo del referente con este chico.',

  `unidad_interviniente_id` bigint DEFAULT NULL COMMENT 'Referencia normalizada.',
  `unidad_denominacion_informada` varchar(255) DEFAULT NULL COMMENT 'Tal como la informo la jurisdiccion. Sostiene la trazabilidad.',
  `unidad_dependencia` varchar(255) DEFAULT NULL,
  `unidad_localidad` varchar(120) DEFAULT NULL,
  `unidad_domicilio` varchar(255) DEFAULT NULL,
  `unidad_equipo` varchar(255) DEFAULT NULL,
  `unidad_responsable` varchar(255) DEFAULT NULL,
  `unidad_telefono` varchar(60) DEFAULT NULL,
  `unidad_mail` varchar(120) DEFAULT NULL,

  `presentacion_alta_id` bigint DEFAULT NULL,
  `presentacion_actualizacion_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_mpi` (`nino_adolescente_id`, `jurisdiccion_id`, `fecha_inicio`),
  KEY `ix_mpi_estado` (`estado`),
  CONSTRAINT `fk_mpi_nya` FOREIGN KEY (`nino_adolescente_id`)
    REFERENCES `runac_c3_nino_adolescente` (`id`),
  CONSTRAINT `fk_mpi_jur` FOREIGN KEY (`jurisdiccion_id`)
    REFERENCES `runac_c2_jurisdiccion` (`id`),
  CONSTRAINT `fk_mpi_referente` FOREIGN KEY (`referente_adulto_id`)
    REFERENCES `runac_c3_referente_adulto` (`id`),
  CONSTRAINT `fk_mpi_unidad` FOREIGN KEY (`unidad_interviniente_id`)
    REFERENCES `runac_c3_unidad_interviniente` (`id`),
  CONSTRAINT `fk_mpi_pres_alta` FOREIGN KEY (`presentacion_alta_id`)
    REFERENCES `runac_c2_presentacion` (`id`),
  CONSTRAINT `fk_mpi_pres_act` FOREIGN KEY (`presentacion_actualizacion_id`)
    REFERENCES `runac_c2_presentacion` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='Medida de Proteccion Integral. Se actualiza cuando presenta novedades.';

CREATE TABLE `runac_c3_medida_mpe` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nino_adolescente_id` bigint NOT NULL,
  `jurisdiccion_id` bigint NOT NULL,
  `fecha_inicio` date DEFAULT NULL,
  `fecha_cese` date DEFAULT NULL,
  `estado` ENUM('VIGENTE','CESADA','NO_INFORMADA') DEFAULT NULL,
  `motivo_cese` varchar(255) DEFAULT NULL,

  `modalidad_cuidado` ENUM('RESIDENCIAL','FAMILIAR_FORMAL','FAMILIA_AMPLIADA') DEFAULT NULL,
  `dispositivo_id` bigint DEFAULT NULL COMMENT 'Solo cuando la modalidad es residencial.',
  `familia_id` bigint DEFAULT NULL COMMENT 'Familia de acogimiento formal.',
  `familia_ampliada_id` bigint DEFAULT NULL COMMENT 'Familia ampliada.',

  `motivo` varchar(255) DEFAULT NULL,
  `proyecto_restitucion` varchar(120) DEFAULT NULL,
  `participa_nya_en_per` varchar(30) DEFAULT NULL,
  `articulacion_per_plan_estadia` varchar(30) DEFAULT NULL,
  `intervencion_judicial` varchar(120) DEFAULT NULL,
  `control_legalidad_juzgado_familia` varchar(30) DEFAULT NULL,
  `adoptabilidad` varchar(60) DEFAULT NULL,
  `autonomia` varchar(60) DEFAULT NULL,
  `pae` varchar(30) DEFAULT NULL COMMENT 'Programa de Acompanamiento para el Egreso.',

  `presentacion_alta_id` bigint DEFAULT NULL,
  `presentacion_actualizacion_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_mpe` (`nino_adolescente_id`, `jurisdiccion_id`, `fecha_inicio`),
  KEY `ix_mpe_estado` (`estado`),
  CONSTRAINT `fk_mpe_nya` FOREIGN KEY (`nino_adolescente_id`)
    REFERENCES `runac_c3_nino_adolescente` (`id`),
  CONSTRAINT `fk_mpe_jur` FOREIGN KEY (`jurisdiccion_id`)
    REFERENCES `runac_c2_jurisdiccion` (`id`),
  CONSTRAINT `fk_mpe_disp` FOREIGN KEY (`dispositivo_id`)
    REFERENCES `runac_c3_dispositivo` (`id`),
  CONSTRAINT `fk_mpe_familia` FOREIGN KEY (`familia_id`)
    REFERENCES `runac_c3_familia_acogimiento` (`id`),
  CONSTRAINT `fk_mpe_familia_amp` FOREIGN KEY (`familia_ampliada_id`)
    REFERENCES `runac_c3_familia_acogimiento` (`id`),
  CONSTRAINT `fk_mpe_pres_alta` FOREIGN KEY (`presentacion_alta_id`)
    REFERENCES `runac_c2_presentacion` (`id`),
  CONSTRAINT `fk_mpe_pres_act` FOREIGN KEY (`presentacion_actualizacion_id`)
    REFERENCES `runac_c2_presentacion` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='Medida de Proteccion Excepcional. La modalidad determina si se enlaza a un dispositivo residencial o a una familia.';

CREATE TABLE `runac_c3_medida_mpj` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nino_adolescente_id` bigint NOT NULL,
  `jurisdiccion_id` bigint NOT NULL,
  `fecha_inicio` date DEFAULT NULL,
  `fecha_cese` date DEFAULT NULL,
  `estado` ENUM('VIGENTE','CESADA','NO_INFORMADA') DEFAULT NULL,

  `descripcion_causa_penal` varchar(500) DEFAULT NULL,
  `dependencia_judicial` varchar(255) DEFAULT NULL,
  `situacion_procesal` varchar(120) DEFAULT NULL,
  `monto_de_la_pena` decimal(10,2) DEFAULT NULL,

  `dispositivo_id` bigint DEFAULT NULL COMMENT 'Dispositivo penal donde se encuentra el adolescente.',
  `fecha_ingreso_dispositivo` date DEFAULT NULL,
  `edad_al_ingreso` int DEFAULT NULL,
  `procedencia` varchar(120) DEFAULT NULL,
  `procedencia_dispositivo_id` bigint DEFAULT NULL COMMENT 'Cuando la procedencia es otro dispositivo del padron.',
  `fecha_egreso_dispositivo` date DEFAULT NULL,
  `destino_al_egreso` varchar(120) DEFAULT NULL,
  `destino_dispositivo_id` bigint DEFAULT NULL COMMENT 'Cuando el egreso es hacia otro dispositivo penal.',

  `presentacion_alta_id` bigint DEFAULT NULL,
  `presentacion_actualizacion_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_mpj` (`nino_adolescente_id`, `jurisdiccion_id`, `fecha_inicio`),
  KEY `ix_mpj_estado` (`estado`),
  CONSTRAINT `fk_mpj_nya` FOREIGN KEY (`nino_adolescente_id`)
    REFERENCES `runac_c3_nino_adolescente` (`id`),
  CONSTRAINT `fk_mpj_jur` FOREIGN KEY (`jurisdiccion_id`)
    REFERENCES `runac_c2_jurisdiccion` (`id`),
  CONSTRAINT `fk_mpj_disp` FOREIGN KEY (`dispositivo_id`)
    REFERENCES `runac_c3_dispositivo` (`id`),
  CONSTRAINT `fk_mpj_disp_proc` FOREIGN KEY (`procedencia_dispositivo_id`)
    REFERENCES `runac_c3_dispositivo` (`id`),
  CONSTRAINT `fk_mpj_disp_dest` FOREIGN KEY (`destino_dispositivo_id`)
    REFERENCES `runac_c3_dispositivo` (`id`),
  CONSTRAINT `fk_mpj_pres_alta` FOREIGN KEY (`presentacion_alta_id`)
    REFERENCES `runac_c2_presentacion` (`id`),
  CONSTRAINT `fk_mpj_pres_act` FOREIGN KEY (`presentacion_actualizacion_id`)
    REFERENCES `runac_c2_presentacion` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='Medida Penal Juvenil. Referencia hasta tres dispositivos: el actual, la procedencia y el destino al egreso. DEFINICION PENDIENTE: como informan las jurisdicciones el traslado de un adolescente entre dispositivos por la misma causa penal.';

CREATE TABLE `runac_c3_medida_dae` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nino_adolescente_id` bigint NOT NULL,
  `jurisdiccion_id` bigint NOT NULL,

  `dispositivo_id` bigint DEFAULT NULL COMMENT 'CAD o guardia especializada.',
  `fecha_hora_ingreso` datetime DEFAULT NULL,
  `fecha_hora_egreso` datetime DEFAULT NULL,
  `fuerza_interviniente` varchar(120) DEFAULT NULL,
  `dependencia` varchar(255) DEFAULT NULL,
  `tiempo_permanencia` varchar(60) DEFAULT NULL,
  `destino` varchar(120) DEFAULT NULL,
  `denuncia_por_apremios` varchar(30) DEFAULT NULL,

  `presentacion_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_dae` (`nino_adolescente_id`, `dispositivo_id`, `fecha_hora_ingreso`),
  CONSTRAINT `fk_dae_nya` FOREIGN KEY (`nino_adolescente_id`)
    REFERENCES `runac_c3_nino_adolescente` (`id`),
  CONSTRAINT `fk_dae_jur` FOREIGN KEY (`jurisdiccion_id`)
    REFERENCES `runac_c2_jurisdiccion` (`id`),
  CONSTRAINT `fk_dae_disp` FOREIGN KEY (`dispositivo_id`)
    REFERENCES `runac_c3_dispositivo` (`id`),
  CONSTRAINT `fk_dae_pres` FOREIGN KEY (`presentacion_id`)
    REFERENCES `runac_c2_presentacion` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='Ingreso y egreso de CAD o permanencia en dependencia policial. A diferencia de las otras tres, describe un HECHO ya ocurrido: se acumula, no se actualiza. Puede haber varios por chico. El requerimiento advierte que no debe confundirse con una medida penal prolongada.';

-- ===========================================================================
-- TRAZABILIDAD
-- ===========================================================================

CREATE TABLE `runac_c3_origen` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `entidad` varchar(40) NOT NULL COMMENT 'Tabla de Capa 3 a la que pertenece el registro.',
  `entidad_id` bigint NOT NULL,
  `presentacion_id` bigint NOT NULL,
  `importacion_id` bigint NOT NULL,
  `numero_fila` int DEFAULT NULL,
  `accion` ENUM('ALTA','ACTUALIZACION','SIN_CAMBIOS') DEFAULT NULL,
  `fecha` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_origen_entidad` (`entidad`, `entidad_id`),
  CONSTRAINT `fk_origen_pres` FOREIGN KEY (`presentacion_id`)
    REFERENCES `runac_c2_presentacion` (`id`),
  CONSTRAINT `fk_origen_imp` FOREIGN KEY (`importacion_id`)
    REFERENCES `runac_c2_importacion` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='Responde de donde salio cada dato: provincia, periodo, archivo, hoja, fila y version.';

CREATE TABLE `runac_c3_cambio` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `entidad` varchar(40) NOT NULL,
  `entidad_id` bigint NOT NULL,
  `campo` varchar(100) NOT NULL,
  `valor_anterior` text,
  `valor_nuevo` text,
  `presentacion_id` bigint DEFAULT NULL,
  `usuario` varchar(150) DEFAULT NULL,
  `motivo` ENUM('CONSOLIDACION','PRECEDENCIA','NORMALIZACION','REPROCESO') DEFAULT NULL,
  `justificacion` text,
  `fecha` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_cambio_entidad` (`entidad`, `entidad_id`, `campo`),
  CONSTRAINT `fk_cambio_pres` FOREIGN KEY (`presentacion_id`)
    REFERENCES `runac_c2_presentacion` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='El historial campo a campo. No es un accesorio de auditoria: es la fuente de las series historicas, porque la base guarda una sola fila por chico con el dato vigente. Por eso registra el valor ANTERIOR y la presentacion que produjo el cambio.';

CREATE TABLE `runac_c3_precedencia` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `entidad` varchar(40) NOT NULL,
  `entidad_id` bigint DEFAULT NULL,
  `campo` varchar(100) NOT NULL,
  `valor_elegido` text,
  `regla` varchar(120) DEFAULT NULL COMMENT 'Jerarquia por archivo, ultimo informado, fuente externa, o decision manual.',
  `usuario` varchar(150) DEFAULT NULL,
  `fecha` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_precedencia_entidad` (`entidad`, `entidad_id`, `campo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='La decision sobre que valor prevalece, conservada para las presentaciones siguientes: la misma discrepancia no se resuelve dos veces.';

CREATE TABLE `runac_c3_coincidencia` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `importacion_id` bigint NOT NULL,
  `numero_fila` int DEFAULT NULL,
  `persona_candidata_id` bigint DEFAULT NULL,
  `motivo` varchar(255) NOT NULL,
  `puntaje` decimal(5,2) DEFAULT NULL,
  `estado` ENUM('PENDIENTE','CONFIRMADA','DESCARTADA') NOT NULL DEFAULT 'PENDIENTE',
  `resuelta_por` varchar(150) DEFAULT NULL,
  `resuelta_el` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_coincidencia_estado` (`estado`),
  CONSTRAINT `fk_coincidencia_imp` FOREIGN KEY (`importacion_id`)
    REFERENCES `runac_c2_importacion` (`id`),
  CONSTRAINT `fk_coincidencia_persona` FOREIGN KEY (`persona_candidata_id`)
    REFERENCES `runac_c3_persona` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='Coincidencias de identidad que no se pueden decidir solas: documento y nombre que coinciden parcialmente, o nombre y fecha de nacimiento sin documento.';
