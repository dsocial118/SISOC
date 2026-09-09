-- ===========================================================================
-- Capa 2 — Parte fija: control de la importación y del circuito
--
-- Estas tablas NO dependen de la estructura de ningún archivo: son siempre las
-- mismas, para cualquier planilla y para cualquier proyecto de importación.
--
-- Las tablas que SÍ dependen de la estructura (las que reciben los datos) se
-- generan a partir de la Capa 1: una por hoja y versión de estructura. Su
-- nombre se deduce por convención: runac_c2_<archivo>_v<n>_<hoja>.
--
-- Circuito de 9 pasos: carga -> control de admisión -> validación de datos ->
-- corrección -> cierre de carga -> revisión nacional -> subsanación ->
-- presentación -> consolidación.
-- ===========================================================================

SET NAMES utf8mb4;

-- ---------------------------------------------------------------------------
-- Jurisdicción y período
-- ---------------------------------------------------------------------------

CREATE TABLE `runac_c2_jurisdiccion` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT 'Identificador interno.',
  `codigo` varchar(20) UNIQUE NOT NULL COMMENT 'Código estable de la jurisdicción.',
  `nombre` varchar(120) NOT NULL COMMENT 'Denominación de la jurisdicción.',
  `modalidad` ENUM('PRESENTACION_PERIODICA','GESTION_CONTINUA') NOT NULL DEFAULT 'PRESENTACION_PERIODICA' COMMENT 'PRESENTACION_PERIODICA: aporta archivos en cada corte, y una nueva importación reemplaza a la anterior. GESTION_CONTINUA: registra novedades dentro del sistema, y la importación incorpora sin descartar lo existente.',
  `activa` boolean NOT NULL DEFAULT true COMMENT 'Baja lógica.'
) COMMENT = 'Unidad que presenta. Es una entidad y no un texto, para que el mismo mecanismo sirva a provincias, municipios u organismos.';

CREATE TABLE `runac_c2_periodo` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT 'Identificador interno.',
  `codigo` varchar(30) UNIQUE NOT NULL COMMENT 'Código del período, por ejemplo 2026_T1.',
  `anio` smallint NOT NULL COMMENT 'Año del corte.',
  `numero` tinyint NOT NULL COMMENT 'Número de corte dentro del año. Con periodicidad trimestral va de 1 a 4.',
  `fecha_desde` date NOT NULL COMMENT 'Primer día del período de referencia.',
  `fecha_hasta` date NOT NULL COMMENT 'Último día del período de referencia. Es la fecha de corte: la fotografía se toma a ese día.',
  `estado` ENUM('PREPARACION','ABIERTO','CERRADO') NOT NULL DEFAULT 'PREPARACION' COMMENT 'PREPARACION: se está definiendo la estructura y la Capa 1 todavía puede cambiar. ABIERTO: las jurisdicciones importan y la estructura queda congelada. CERRADO: no se admiten más cargas.',
  `declaro_cambios` boolean NOT NULL DEFAULT false COMMENT 'El administrador declaró, al abrir el período, si había cambios de estructura respecto del anterior.',
  `usuario_declara` varchar(150) COMMENT 'Usuario que realizó la declaración.',
  `declarado_el` datetime COMMENT 'Momento de la declaración.',
  `abierto_el` datetime COMMENT 'Momento en que se habilitó la carga.',
  `cerrado_el` datetime COMMENT 'Momento en que se cerró la carga.',
  UNIQUE KEY `runac_c2_periodo_anio_numero` (`anio`, `numero`)
) COMMENT = 'Períodos de corte. Mientras un período está ABIERTO la estructura que utiliza no puede modificarse: alguna jurisdicción ya pudo haber importado.';

CREATE TABLE `runac_c2_periodo_archivo` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT 'Identificador interno.',
  `periodo_id` bigint NOT NULL COMMENT 'Período.',
  `archivo_version_id` bigint NOT NULL COMMENT 'Versión de estructura que rige para ese archivo en ese período.',
  UNIQUE KEY `runac_c2_periodo_archivo_unica` (`periodo_id`, `archivo_version_id`)
) COMMENT = 'Qué versión de cada archivo rige en cada período. Si no hubo cambios, dos períodos apuntan a la misma versión y no se duplica ninguna definición. El nombre de la tabla receptora se deduce por convención del archivo y la versión.';

-- ---------------------------------------------------------------------------
-- Presentación
-- ---------------------------------------------------------------------------

CREATE TABLE `runac_c2_presentacion` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT 'Identificador interno.',
  `periodo_id` bigint NOT NULL COMMENT 'Período al que corresponde la presentación.',
  `jurisdiccion_id` bigint NOT NULL COMMENT 'Jurisdicción que presenta.',
  `version` int NOT NULL DEFAULT 1 COMMENT 'Número de versión. Una subsanación genera una versión nueva; la anterior se conserva con sus observaciones.',
  `estado` ENUM(
    'EN_CARGA','CERRADA','EN_REVISION','OBSERVADA','SUBSANADA',
    'HABILITADA','PRESENTADA','CONSOLIDADA'
  ) NOT NULL DEFAULT 'EN_CARGA' COMMENT 'Estado del circuito jurisdicción-Nación. No se mezcla con el estado de cada importación: una presentación puede tener importaciones anuladas y estar igual en condiciones de cerrarse.',
  `cerrada_el` datetime COMMENT 'Cierre de carga: el responsable provincial declaró terminada la carga y la envió a revisión.',
  `habilitada_el` datetime COMMENT 'Momento en que el revisor técnico nacional habilitó la presentación formal.',
  `presentada_el` datetime COMMENT 'Presentación formal. Se generó el comprobante.',
  `consolidada_el` datetime COMMENT 'Momento en que los datos se incorporaron a la Capa 3.',
  `expediente` varchar(100) COMMENT 'Número GDE, incorporado por el responsable provincial tras remitir el comprobante. Su ausencia no impide la consolidación: es un resguardo documental de la jurisdicción.',
  `usuario_cierra` varchar(150) COMMENT 'Responsable provincial que cerró la carga.',
  `usuario_habilita` varchar(150) COMMENT 'Revisor técnico nacional que habilitó la presentación.',
  `usuario_presenta` varchar(150) COMMENT 'Responsable provincial que presentó formalmente.',
  `reemplaza_a` bigint COMMENT 'Presentación anterior que esta versión subsana.',
  UNIQUE KEY `runac_c2_presentacion_unica` (`periodo_id`, `jurisdiccion_id`, `version`)
) COMMENT = 'Presentación de una jurisdicción para un período. Agrupa las importaciones de los distintos archivos.';

-- ---------------------------------------------------------------------------
-- Importación
-- ---------------------------------------------------------------------------

CREATE TABLE `runac_c2_importacion` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT 'Identificador interno.',
  `presentacion_id` bigint NOT NULL COMMENT 'Presentación a la que pertenece este intento.',
  `archivo_id` bigint NOT NULL COMMENT 'Archivo que el operador declaró estar cargando. El operador elige el archivo: el nombre del fichero no lo determina.',
  `archivo_version_id` bigint COMMENT 'Versión contra la que se validó. Queda vacío cuando el archivo no se pudo identificar.',
  `nombre_archivo` varchar(255) NOT NULL COMMENT 'Nombre del archivo tal como lo subió el usuario.',
  `sha1` char(40) COMMENT 'Huella del archivo subido. Permite detectar que se volvió a subir el mismo.',
  `bytes` bigint COMMENT 'Tamaño del archivo.',
  `ruta_archivo` varchar(500) COMMENT 'Ubicación del archivo recibido, tal como llegó. Es lo que permite devolver al operador su propio Excel con las celdas marcadas, y el respaldo documental de lo presentado.',
  `estado` ENUM('VALIDA','ANULADA','FALLIDA') NOT NULL COMMENT 'VALIDA: admitida e incorporada. ANULADA: reemplazada por una importación posterior del mismo archivo. FALLIDA: rechazada en el control de admisión o interrumpida por un error técnico. Dado que la importación es restrictiva, un archivo con bloqueantes no genera una importación válida.',
  `filas_leidas` int NOT NULL DEFAULT 0 COMMENT 'Filas de datos leídas del archivo.',
  `filas_incorporadas` int NOT NULL DEFAULT 0 COMMENT 'Filas efectivamente incorporadas.',
  `bloqueantes` int NOT NULL DEFAULT 0 COMMENT 'Cantidad de reglas incumplidas con severidad bloqueante.',
  `advertencias` int NOT NULL DEFAULT 0 COMMENT 'Cantidad de reglas incumplidas con severidad advertencia.',
  `iniciada_el` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Momento en que se recibió el archivo.',
  `terminada_el` datetime COMMENT 'Momento en que terminó el procesamiento.',
  `duracion_ms` int COMMENT 'Duración del procesamiento, en milisegundos.',
  `usuario` varchar(150) COMMENT 'Usuario que subió el archivo.',
  `anulada_por` bigint COMMENT 'Importación posterior que dejó sin efecto a esta. Conserva el historial de intentos.'
) COMMENT = 'Cada intento de importación de un archivo, incluidos los que fallaron. Nunca se borra: es la trazabilidad. Permite distinguir a quien no cargó de quien intentó cargar y no pudo.';

CREATE TABLE `runac_c2_errores_de_importacion` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT 'Identificador interno.',
  `importacion_id` bigint NOT NULL COMMENT 'Intento en el que se detectó.',
  `tipo` ENUM(
    'HOJA_FALTANTE','HOJA_NOMBRE_DISTINTO','COLUMNA_FALTANTE',
    'COLUMNA_NO_ESPERADA','COLUMNA_FUERA_DE_ORDEN',
    'FILA_VACIA_INTERCALADA','ARCHIVO_ILEGIBLE','ERROR_TECNICO'
  ) NOT NULL COMMENT 'Los cinco primeros son discrepancias con la estructura esperada. FILA_VACIA_INTERCALADA es una fila en blanco en el medio de los datos, que el requerimiento pide corregir antes de importar. ARCHIVO_ILEGIBLE y ERROR_TECNICO no dependen del contenido: formato no reconocido, archivo dañado, interrupción del proceso o pérdida de conexión.',
  `hoja` varchar(255) COMMENT 'Hoja donde se detectó, cuando corresponde.',
  `numero_fila` int COMMENT 'Fila del Excel, cuando el problema tiene una ubicación puntual.',
  `esperado` varchar(255) COMMENT 'Nombre de hoja, título de columna o posición que se esperaba encontrar.',
  `encontrado` varchar(255) COMMENT 'Qué se encontró en su lugar.',
  `descripcion` text NOT NULL COMMENT 'Mensaje en lenguaje claro para el operador.',
  `detalle_tecnico` text COMMENT 'Traza del error, para soporte. No se muestra al usuario.'
) COMMENT = 'Motivos por los que un archivo no pudo importarse. Un archivo equivocado suele fallar por varias razones a la vez: se informan todas juntas para que el operador corrija una sola vez.';

CREATE TABLE `runac_c2_reglas_incumplidas` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT 'Identificador interno.',
  `importacion_id` bigint NOT NULL COMMENT 'Importación en la que se detectó.',
  `campo_id` bigint NOT NULL COMMENT 'Campo de Capa 1 afectado. Siempre presente: un incumplimiento sin campo es un problema del archivo y va a runac_c2_errores_de_importacion.',
  `regla_id` bigint COMMENT 'Regla de Capa 1 que no se cumplió. Queda vacío cuando el incumplimiento es de una validación intrínseca del campo —tipo de dato, obligatoriedad, valor de catálogo o longitud máxima—, que se define en runac_c1_campo y no en runac_c1_regla. El código indica de cuál se trata.',
  `codigo` varchar(50) NOT NULL COMMENT 'Código estable del incumplimiento, para contarlos y agruparlos: qué regla se incumple con más frecuencia, si se repite entre períodos.',
  `severidad` ENUM('BLOQUEANTE','ADVERTENCIA') NOT NULL COMMENT 'Tomada de la regla aplicada al campo.',
  `nombre_hoja` varchar(255) NOT NULL COMMENT 'Hoja del Excel donde está el problema.',
  `numero_fila` int NOT NULL COMMENT 'Fila del Excel, tal como la ve el usuario.',
  `columna` varchar(10) COMMENT 'Letra de la columna en el Excel.',
  `nombre_campo` varchar(255) COMMENT 'Título de la columna, para que el informe se entienda sin unir tablas.',
  `identificador_registro` varchar(100) COMMENT 'Identificador provincial de la fila afectada.',
  `valor_encontrado` text COMMENT 'El valor que provocó el incumplimiento, tal como vino.',
  `descripcion` text NOT NULL COMMENT 'Mensaje en lenguaje claro, tomado de la definición de la regla.',
  `resuelta` boolean NOT NULL DEFAULT false COMMENT 'Indica si la advertencia fue corregida o justificada dentro del sistema.'
) COMMENT = 'Validaciones no superadas en un archivo que SÍ fue admitido. Una fila por incumplimiento, con su ubicación exacta.';

-- ---------------------------------------------------------------------------
-- Revisión y corrección
-- ---------------------------------------------------------------------------

CREATE TABLE `runac_c2_observacion` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT 'Identificador interno.',
  `presentacion_id` bigint NOT NULL COMMENT 'Presentación observada.',
  `importacion_id` bigint COMMENT 'Importación puntual observada.',
  `numero_fila` int COMMENT 'Fila puntual observada.',
  `campo_id` bigint COMMENT 'Campo puntual observado.',
  `identificador_registro` varchar(100) COMMENT 'Identificador provincial del registro observado.',
  `texto` text NOT NULL COMMENT 'La observación, escrita por el revisor técnico nacional.',
  `estado` ENUM('ABIERTA','RESPONDIDA','SUBSANADA','DESESTIMADA') NOT NULL DEFAULT 'ABIERTA' COMMENT 'Seguimiento de la observación.',
  `respuesta` text COMMENT 'Respuesta de la jurisdicción.',
  `creada_el` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Momento en que se formuló.',
  `usuario_observa` varchar(150) NOT NULL COMMENT 'Revisor que la formuló.',
  `respondida_el` datetime COMMENT 'Momento de la respuesta.',
  `usuario_responde` varchar(150) COMMENT 'Usuario provincial que respondió.'
) COMMENT = 'Observaciones del revisor nacional. El revisor no modifica datos provinciales: observa. El ciclo de observación y subsanación no tiene límite de rondas.';

CREATE TABLE `runac_c2_historial_cambios` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT 'Identificador interno.',
  `importacion_id` bigint NOT NULL COMMENT 'Importación cuyos datos se editaron.',
  `numero_fila` int NOT NULL COMMENT 'Fila editada.',
  `campo_id` bigint NOT NULL COMMENT 'Campo editado.',
  `identificador_registro` varchar(100) COMMENT 'Identificador provincial del registro editado.',
  `observacion_id` bigint COMMENT 'Observación que motivó el cambio, cuando corresponde.',
  `valor_anterior` text COMMENT 'Contenido previo al cambio.',
  `valor_nuevo` text COMMENT 'Contenido posterior al cambio.',
  `motivo` text COMMENT 'Justificación del cambio.',
  `fecha` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Momento del cambio.',
  `usuario` varchar(150) NOT NULL COMMENT 'Usuario que realizó el cambio.'
) COMMENT = 'Correcciones sobre los datos importados, con usuario, fecha, valor anterior y valor nuevo. Responde a la pregunta: el Excel decía X y el operador puso Y. No confundir con el historial de la Capa 3, que registra la evolución del dato consolidado entre períodos.';

-- ---------------------------------------------------------------------------
-- Índices
-- ---------------------------------------------------------------------------

CREATE INDEX `runac_c2_importacion_presentacion` ON `runac_c2_importacion` (`presentacion_id`, `archivo_id`, `estado`);
CREATE INDEX `runac_c2_errores_importacion` ON `runac_c2_errores_de_importacion` (`importacion_id`, `tipo`);
CREATE INDEX `runac_c2_reglas_incumplidas_sev` ON `runac_c2_reglas_incumplidas` (`importacion_id`, `severidad`);
CREATE INDEX `runac_c2_reglas_incumplidas_ubic` ON `runac_c2_reglas_incumplidas` (`importacion_id`, `numero_fila`);
CREATE INDEX `runac_c2_reglas_incumplidas_codigo` ON `runac_c2_reglas_incumplidas` (`codigo`);
CREATE INDEX `runac_c2_observacion_presentacion` ON `runac_c2_observacion` (`presentacion_id`, `estado`);
CREATE INDEX `runac_c2_historial_ubicacion` ON `runac_c2_historial_cambios` (`importacion_id`, `numero_fila`);

-- ---------------------------------------------------------------------------
-- Claves foráneas
-- ---------------------------------------------------------------------------

ALTER TABLE `runac_c2_periodo_archivo` ADD FOREIGN KEY (`periodo_id`) REFERENCES `runac_c2_periodo` (`id`);
ALTER TABLE `runac_c2_periodo_archivo` ADD FOREIGN KEY (`archivo_version_id`) REFERENCES `runac_c1_archivo_version` (`id`);

ALTER TABLE `runac_c2_presentacion` ADD FOREIGN KEY (`periodo_id`) REFERENCES `runac_c2_periodo` (`id`);
ALTER TABLE `runac_c2_presentacion` ADD FOREIGN KEY (`jurisdiccion_id`) REFERENCES `runac_c2_jurisdiccion` (`id`);
ALTER TABLE `runac_c2_presentacion` ADD FOREIGN KEY (`reemplaza_a`) REFERENCES `runac_c2_presentacion` (`id`);

ALTER TABLE `runac_c2_importacion` ADD FOREIGN KEY (`presentacion_id`) REFERENCES `runac_c2_presentacion` (`id`);
ALTER TABLE `runac_c2_importacion` ADD FOREIGN KEY (`archivo_id`) REFERENCES `runac_c1_archivo` (`id`);
ALTER TABLE `runac_c2_importacion` ADD FOREIGN KEY (`archivo_version_id`) REFERENCES `runac_c1_archivo_version` (`id`);
ALTER TABLE `runac_c2_importacion` ADD FOREIGN KEY (`anulada_por`) REFERENCES `runac_c2_importacion` (`id`);

ALTER TABLE `runac_c2_errores_de_importacion` ADD FOREIGN KEY (`importacion_id`) REFERENCES `runac_c2_importacion` (`id`);

ALTER TABLE `runac_c2_reglas_incumplidas` ADD FOREIGN KEY (`importacion_id`) REFERENCES `runac_c2_importacion` (`id`);
ALTER TABLE `runac_c2_reglas_incumplidas` ADD FOREIGN KEY (`campo_id`) REFERENCES `runac_c1_campo` (`id`);
ALTER TABLE `runac_c2_reglas_incumplidas` ADD FOREIGN KEY (`regla_id`) REFERENCES `runac_c1_regla` (`id`);

ALTER TABLE `runac_c2_observacion` ADD FOREIGN KEY (`presentacion_id`) REFERENCES `runac_c2_presentacion` (`id`);
ALTER TABLE `runac_c2_observacion` ADD FOREIGN KEY (`importacion_id`) REFERENCES `runac_c2_importacion` (`id`);
ALTER TABLE `runac_c2_observacion` ADD FOREIGN KEY (`campo_id`) REFERENCES `runac_c1_campo` (`id`);

ALTER TABLE `runac_c2_historial_cambios` ADD FOREIGN KEY (`importacion_id`) REFERENCES `runac_c2_importacion` (`id`);
ALTER TABLE `runac_c2_historial_cambios` ADD FOREIGN KEY (`campo_id`) REFERENCES `runac_c1_campo` (`id`);
ALTER TABLE `runac_c2_historial_cambios` ADD FOREIGN KEY (`observacion_id`) REFERENCES `runac_c2_observacion` (`id`);
