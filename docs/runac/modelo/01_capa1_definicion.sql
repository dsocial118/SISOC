-- ===========================================================================
-- Capa 1 — Definición de los archivos esperados y sus reglas
--
-- La estructura de cada archivo se VERSIONA. Un período apunta a una versión
-- por archivo; si no hay cambios, apunta a la misma que el período anterior y
-- no se duplica nada. Una versión ya usada por un período no se modifica.
--
-- Los catálogos NO se versionan: son listas vivas, con alta, baja lógica y
-- vigencia por período. Replicar el nomenclador de localidades en cada corte
-- sería inviable y no aportaría información.
-- ===========================================================================

SET NAMES utf8mb4;

-- ---------------------------------------------------------------------------
-- Archivo y versión de estructura
-- ---------------------------------------------------------------------------

CREATE TABLE `runac_c1_archivo` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT 'Identificador interno.',
  `codigo` varchar(30) UNIQUE NOT NULL COMMENT 'Código estable que identifica el tipo de archivo, por ejemplo MPI, MPE o MPJ_DAE. No cambia nunca.',
  `descripcion` text COMMENT 'Descripción funcional de la información contenida en el archivo.',
  `activo` boolean NOT NULL DEFAULT true COMMENT 'Indica si el archivo sigue formando parte de los que se solicitan.'
) COMMENT = 'La identidad del archivo. Todo lo que puede cambiar entre períodos vive en la versión.';

CREATE TABLE `runac_c1_archivo_version` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT 'Identificador interno.',
  `archivo_id` bigint NOT NULL COMMENT 'Archivo cuya estructura describe esta versión.',
  `numero` int NOT NULL COMMENT 'Número de versión, correlativo dentro del archivo.',
  `estado` ENUM('BORRADOR','VIGENTE','HISTORICA') NOT NULL DEFAULT 'BORRADOR' COMMENT 'BORRADOR: se está editando. VIGENTE: rige para el período abierto. HISTORICA: fue usada por un período anterior y no se modifica.',
  `nombre_esperado` varchar(255) NOT NULL COMMENT 'Nombre que debe tener el archivo. Puede cambiar entre versiones.',
  `titulo` varchar(255) COMMENT 'Título que encabeza la planilla, tal como aparece en la primera fila del Excel.',
  `subtitulo` varchar(255) COMMENT 'Subtítulo o segunda línea del encabezado, cuando la planilla lo tiene.',
  `orden_importacion` int NOT NULL COMMENT 'Orden en que debe procesarse respecto de los demás archivos de la misma versión de período.',
  `obligatorio` boolean NOT NULL DEFAULT true COMMENT 'Indica si la ausencia del archivo impide continuar con la importación.',
  `creada_el` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Momento en que se creó la versión.',
  `creada_por` varchar(150) COMMENT 'Usuario que la creó.',
  `copiada_de` bigint COMMENT 'Versión anterior a partir de la cual se copió para su edición.',
  `nota` text COMMENT 'Qué cambió respecto de la versión anterior.',
  UNIQUE KEY `runac_c1_archivo_version_unica` (`archivo_id`, `numero`)
) COMMENT = 'Cada versión de la estructura de un archivo. Hojas, dimensiones, campos y reglas cuelgan de la versión, no del archivo.';

-- ---------------------------------------------------------------------------
-- Estructura: hojas, dimensiones y campos
-- ---------------------------------------------------------------------------

CREATE TABLE `runac_c1_hoja` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT 'Identificador interno.',
  `archivo_version_id` bigint NOT NULL COMMENT 'Versión de archivo a la que pertenece la hoja.',
  `nombre_esperado` varchar(255) NOT NULL COMMENT 'Nombre exacto que debe tener la hoja dentro del archivo Excel.',
  `descripcion` text COMMENT 'Descripción funcional de la información contenida en la hoja.',
  `orden_procesamiento` int NOT NULL COMMENT 'Orden en que debe procesarse dentro del archivo.',
  `fila_encabezados` int NOT NULL DEFAULT 1 COMMENT 'Fila donde se encuentran los nombres de los campos. Los datos comienzan en la fila siguiente.',
  `obligatoria` boolean NOT NULL DEFAULT true COMMENT 'Indica si la ausencia de la hoja impide continuar con la importación.'
) COMMENT = 'Define las hojas que deben encontrarse dentro de cada versión de archivo.';

CREATE TABLE `runac_c1_dimension` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT 'Identificador interno.',
  `hoja_id` bigint NOT NULL COMMENT 'Hoja a la que pertenece la dimensión.',
  `nombre_esperado` varchar(255) NOT NULL COMMENT 'Texto que debe aparecer en la celda combinada ubicada sobre los títulos de las columnas.',
  `descripcion` text COMMENT 'Descripción funcional del grupo de campos representado por la dimensión.',
  `orden` int NOT NULL COMMENT 'Orden en que aparece la dimensión dentro de la hoja.'
) COMMENT = 'Define los encabezados que agrupan conjuntos de campos dentro de una hoja.';

CREATE TABLE `runac_c1_campo` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT 'Identificador interno.',
  `hoja_id` bigint NOT NULL COMMENT 'Hoja a la que pertenece el campo.',
  `dimension_id` bigint COMMENT 'Dimensión que agrupa el campo. Puede quedar vacío cuando el campo no pertenece a una dimensión.',
  `catalogo_id` bigint COMMENT 'Catálogo que contiene los valores permitidos para el campo. Puede quedar vacío cuando el campo no utiliza una lista cerrada.',
  `nombre` varchar(100) NOT NULL COMMENT 'Nombre técnico y estable del campo, escrito en snake_case y sin tildes ni caracteres especiales.',
  `titulo_esperado` varchar(255) NOT NULL COMMENT 'Título exacto que debe aparecer en la columna del archivo Excel.',
  `orden` int NOT NULL COMMENT 'Posición esperada de la columna dentro de la hoja.',
  `tipo_dato` ENUM ('TEXTO', 'ENTERO', 'DECIMAL', 'FECHA') NOT NULL COMMENT 'Tipo de dato esperado para el campo.',
  `longitud_maxima` int COMMENT 'Cantidad máxima de caracteres admitidos para campos de tipo TEXTO. Si queda vacío, la columna receptora se creará como TEXT.',
  `obligatorio` boolean NOT NULL DEFAULT false COMMENT 'Indica si el campo debe contener un valor. Las obligatoriedades condicionales se definen mediante reglas.',
  `ayuda` text COMMENT 'Texto explicativo para la confección o validación del campo.'
) COMMENT = 'Define los campos o columnas esperados dentro de cada hoja.';

-- ---------------------------------------------------------------------------
-- Catálogos — NO se versionan: alta, baja lógica y vigencia por período
-- ---------------------------------------------------------------------------

CREATE TABLE `runac_c1_catalogo` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT 'Identificador interno.',
  `codigo` varchar(100) UNIQUE NOT NULL COMMENT 'Código técnico y estable del catálogo, escrito en snake_case.',
  `nombre` varchar(255) NOT NULL COMMENT 'Nombre descriptivo del catálogo.',
  `descripcion` text COMMENT 'Explicación funcional de los valores contenidos en el catálogo.'
) COMMENT = 'Define un conjunto cerrado de valores admitidos para uno o más campos. Una lista que reaparece en varios archivos se define una sola vez.';

CREATE TABLE `runac_c1_catalogo_opcion` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT 'Identificador interno.',
  `catalogo_id` bigint NOT NULL COMMENT 'Catálogo al que pertenece la opción.',
  `codigo` varchar(100) NOT NULL COMMENT 'Código técnico y estable de la opción. NO cambia aunque cambie el texto: es lo que permite comparar series históricas.',
  `valor_esperado` varchar(255) NOT NULL COMMENT 'Texto que debe encontrarse en el archivo Excel. Puede cambiar sin que cambie el código.',
  `descripcion` text COMMENT 'Explicación funcional de la opción.',
  `orden` int NOT NULL COMMENT 'Orden de presentación de la opción dentro del catálogo.',
  `activo` boolean NOT NULL DEFAULT true COMMENT 'Baja lógica. Una opción inactiva no se admite en nuevas importaciones, pero el registro se conserva para que los datos anteriores sigan siendo legibles.',
  `vigente_desde_periodo` varchar(30) COMMENT 'Código del primer período en que la opción se admite. Vacío significa que rige desde el inicio. Se guarda el código y no el id para que la Capa 1 no dependa de la Capa 2.',
  `vigente_hasta_periodo` varchar(30) COMMENT 'Código del último período en que la opción se admite. Vacío significa que sigue vigente.'
) COMMENT = 'Cada valor permitido dentro de un catálogo, con su vigencia. Permite validar cada archivo contra las opciones que regían en su período.';

-- ---------------------------------------------------------------------------
-- Reglas de validación
-- ---------------------------------------------------------------------------

CREATE TABLE `runac_c1_tipo_regla` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT 'Identificador interno.',
  `nombre` varchar(100) UNIQUE NOT NULL COMMENT 'Nombre técnico y estable del tipo de regla, por ejemplo RANGO, OBLIGATORIO_SI, EXISTE_EN o EJECUTAR_FUNCION.',
  `descripcion` text COMMENT 'Explica el comportamiento general de la validación.'
) COMMENT = 'Vocabulario genérico de validaciones. Los mismos tipos sirven para cualquier relevamiento; cambian los parámetros.';

CREATE TABLE `runac_c1_tipo_regla_parametro` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT 'Identificador interno.',
  `tipo_regla_id` bigint NOT NULL COMMENT 'Tipo de regla al que pertenece el parámetro.',
  `nombre` varchar(100) NOT NULL COMMENT 'Nombre técnico del parámetro dentro del JSON, por ejemplo minimo, maximo, operador o campo_condicion.',
  `tipo_parametro` ENUM ('TEXTO', 'ENTERO', 'DECIMAL', 'FECHA', 'HORA', 'BOOLEANO', 'CAMPO', 'LISTA') NOT NULL COMMENT 'Tipo de valor que debe contener el parámetro.',
  `obligatorio` boolean NOT NULL DEFAULT true COMMENT 'Indica si el parámetro debe estar presente para configurar la regla.',
  `orden` int NOT NULL COMMENT 'Orden de presentación del parámetro.',
  `descripcion` text COMMENT 'Explica el significado y uso del parámetro.'
) COMMENT = 'Define los parámetros esperados por cada tipo de regla.';

CREATE TABLE `runac_c1_regla` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT 'Identificador interno.',
  `tipo_regla_id` bigint NOT NULL COMMENT 'Tipo de validación que debe ejecutar el importador.',
  `nombre` varchar(255) UNIQUE NOT NULL COMMENT 'Nombre técnico y estable que identifica la regla concreta.',
  `descripcion` text COMMENT 'Explicación funcional de la validación.',
  `parametros` json COMMENT 'Valores necesarios para ejecutar la regla, de acuerdo con los parámetros definidos para su tipo.'
) COMMENT = 'Una validación concreta, reutilizable en distintos campos.';

CREATE TABLE `runac_c1_campo_regla` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT 'Identificador interno.',
  `campo_id` bigint NOT NULL COMMENT 'Campo sobre el que se aplica la regla.',
  `regla_id` bigint NOT NULL COMMENT 'Regla que debe aplicarse.',
  `severidad` ENUM ('BLOQUEANTE', 'ADVERTENCIA') NOT NULL COMMENT 'Atributo de la regla APLICADA, no del tipo: un mismo tipo puede ser bloqueante en un campo y advertencia en otro.',
  `mensaje` text COMMENT 'Mensaje al usuario, en lenguaje claro. Vive en la definición y no en el código, de modo que pueda mejorarse sin desarrollo.'
) COMMENT = 'Relaciona los campos con las reglas que deben aplicarse, con su severidad y su mensaje.';

-- ---------------------------------------------------------------------------
-- Índices
-- ---------------------------------------------------------------------------

CREATE UNIQUE INDEX `runac_c1_hoja_index_0` ON `runac_c1_hoja` (`archivo_version_id`, `nombre_esperado`);
CREATE UNIQUE INDEX `runac_c1_hoja_index_1` ON `runac_c1_hoja` (`archivo_version_id`, `orden_procesamiento`);
CREATE UNIQUE INDEX `runac_c1_dimension_index_2` ON `runac_c1_dimension` (`hoja_id`, `orden`);
CREATE UNIQUE INDEX `runac_c1_campo_index_3` ON `runac_c1_campo` (`hoja_id`, `nombre`);
CREATE UNIQUE INDEX `runac_c1_campo_index_4` ON `runac_c1_campo` (`hoja_id`, `orden`);
CREATE UNIQUE INDEX `runac_c1_catalogo_opcion_index_5` ON `runac_c1_catalogo_opcion` (`catalogo_id`, `codigo`);
CREATE UNIQUE INDEX `runac_c1_catalogo_opcion_index_6` ON `runac_c1_catalogo_opcion` (`catalogo_id`, `valor_esperado`);
CREATE UNIQUE INDEX `runac_c1_catalogo_opcion_index_7` ON `runac_c1_catalogo_opcion` (`catalogo_id`, `orden`);
CREATE UNIQUE INDEX `runac_c1_tipo_regla_parametro_index_8` ON `runac_c1_tipo_regla_parametro` (`tipo_regla_id`, `nombre`);
CREATE UNIQUE INDEX `runac_c1_tipo_regla_parametro_index_9` ON `runac_c1_tipo_regla_parametro` (`tipo_regla_id`, `orden`);
CREATE UNIQUE INDEX `runac_c1_campo_regla_index_10` ON `runac_c1_campo_regla` (`campo_id`, `regla_id`);
CREATE INDEX `runac_c1_archivo_version_estado` ON `runac_c1_archivo_version` (`archivo_id`, `estado`);

-- ---------------------------------------------------------------------------
-- Claves foráneas
-- ---------------------------------------------------------------------------

ALTER TABLE `runac_c1_archivo_version` ADD FOREIGN KEY (`archivo_id`) REFERENCES `runac_c1_archivo` (`id`);
ALTER TABLE `runac_c1_archivo_version` ADD FOREIGN KEY (`copiada_de`) REFERENCES `runac_c1_archivo_version` (`id`);
ALTER TABLE `runac_c1_hoja` ADD FOREIGN KEY (`archivo_version_id`) REFERENCES `runac_c1_archivo_version` (`id`);
ALTER TABLE `runac_c1_dimension` ADD FOREIGN KEY (`hoja_id`) REFERENCES `runac_c1_hoja` (`id`);
ALTER TABLE `runac_c1_campo` ADD FOREIGN KEY (`hoja_id`) REFERENCES `runac_c1_hoja` (`id`);
ALTER TABLE `runac_c1_campo` ADD FOREIGN KEY (`dimension_id`) REFERENCES `runac_c1_dimension` (`id`);
ALTER TABLE `runac_c1_campo` ADD FOREIGN KEY (`catalogo_id`) REFERENCES `runac_c1_catalogo` (`id`);
ALTER TABLE `runac_c1_catalogo_opcion` ADD FOREIGN KEY (`catalogo_id`) REFERENCES `runac_c1_catalogo` (`id`);
ALTER TABLE `runac_c1_tipo_regla_parametro` ADD FOREIGN KEY (`tipo_regla_id`) REFERENCES `runac_c1_tipo_regla` (`id`);
ALTER TABLE `runac_c1_regla` ADD FOREIGN KEY (`tipo_regla_id`) REFERENCES `runac_c1_tipo_regla` (`id`);
ALTER TABLE `runac_c1_campo_regla` ADD FOREIGN KEY (`campo_id`) REFERENCES `runac_c1_campo` (`id`);
ALTER TABLE `runac_c1_campo_regla` ADD FOREIGN KEY (`regla_id`) REFERENCES `runac_c1_regla` (`id`);
