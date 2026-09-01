# PAS: Declaración Jurada versionada

Fecha: 2026-08-06

## Alcance

- Se incorpora un formulario público responsive, accesible mediante token aleatorio
  de un solo uso.
- Cada presentación genera una versión nueva e inmutable y conserva las anteriores.
- La última versión actualiza provincia, municipio, domicilio, correo electrónico y
  teléfono celular del titular PAS.
- Cada versión conserva una fotografía de respuestas, el texto legal aceptado y un
  PDF descargable mediante un endpoint interno protegido.

## Decisiones

- Las declaraciones finalizadas no admiten edición ni borrado desde modelo o admin.
- Los PDF y el historial requieren permisos internos de PAS. El formulario es el
  único endpoint público y no permite consultar el padrón.
- El criterio monetario se guarda como aceptación respecto de un SMVM, no como el
  monto fijo del documento fuente, para evitar que una cifra normativa cambiante
  quede incorporada a la lógica.
- Las periodicidades trimestral, semestral y anual quedan fuera de esta primera
  entrega hasta definir qué preguntas pertenecen a cada ciclo y cómo se emitirán
  las invitaciones.

## Validación

- Pruebas de creación del PDF, impacto en datos actuales, versionado, inmutabilidad,
  token de un solo uso y permisos de descarga.

## Ajustes de presentación

- El formulario adopta el flujo móvil de siete pasos provisto por UX: actualización
  de datos, situación familiar, controles condicionales, consumos, confirmación de
  contacto y revisión/firma. El stepper conserva la numeración funcional aunque
  omita los controles de embarazo o menores cuando no corresponden.
- Se incorporan la consulta de términos legales, el modal amarillo previo al envío
  y la tarjeta verde de confirmación con los textos y proporciones del diseño UX.
- El formulario público usa una hoja de estilos propia basada en la guía PONCHO:
  Lora/Montserrat, azul `#232D4F`, foco amarillo `#E7BA61`, verde de éxito
  `#2E7D33`, tarjetas blancas y botones redondeados.
- La confirmación final informa el éxito sin exponer datos del titular ni destinos
  internos.
- El PDF replica la estructura legal del documento fuente y muestra únicamente la
  alternativa elegida en respuestas binarias.
- La pestaña Declaración Jurada permite consultar la última versión o seleccionar
  una presentación anterior, mostrando su fotografía completa de respuestas.
- La línea de tiempo de Historial de estados incorpora las presentaciones DDJJ
  ordenadas junto con los cambios de estado.
- La primera pantalla muestra la fotografía de datos vigentes del registro PAS. Si
  se confirman, solo se solicitan campos faltantes; si se rechazan, todos los datos
  editables se presentan juntos, excluyendo DNI y CUIL.
- Las preguntas dependientes se responden en la misma pantalla que su pregunta
  principal. Al cambiar la respuesta principal se descartan los valores que hayan
  quedado ocultos, tanto en el navegador como en la validación del servidor.
- Los controles binarios se presentan como tarjetas seleccionables y las preguntas
  dependientes dentro de un bloque visual asociado. Los municipios se filtran por
  la provincia elegida mediante el mismo token público vigente de la declaración.
- Las alternativas Sí/No se disponen verticalmente y la navegación queda fija al
  pie en pantallas móviles para facilitar el uso desde Android e iOS.
- El resumen final identifica cada respuesta por el texto de su pregunta, incluidas
  las preguntas dependientes, en lugar de repetir la etiqueta de la opción elegida.
- El enlace distribuible no se persiste con dominio: la invitación conserva el token
  y lo combina con `DOMINIO`, configurado por ambiente. `PasPersona` permite obtener
  su invitación vigente mediante la relación histórica existente.
- Una migración crea una invitación vigente para cada titular existente que no la
  tenga. Los registros incorporados por alta o importación también reciben token.
- El admin de Personas PAS permite regenerar tokens: revoca la invitación vigente y
  crea otra, sin registrar falsamente el token anterior como utilizado.
- El Buscador PAS reemplaza «Nuevo titular» por una importación CSV incremental. Se
  aceptan Apellidos, Nombres, DNI, CUIT/CUIL, Provincia y Municipio; una coincidencia
  por DNI o CUIT se omite sin modificar datos existentes.
- El padrón de distribución se descarga como XLSX con las columnas `CUIL` y `TOKEN`,
  limitado a invitaciones vigentes y protegido por el permiso de consulta de PAS.

## Endurecimiento de distribución y cierre del formulario

- La columna `TOKEN` del Excel contiene el enlace completo al formulario,
  compuesto con `DOMINIO`, y no solamente el UUID.
- La exportación requiere el permiso específico `pas.export_ddjj_tokens`. Cada
  descarga registra usuario, fecha y cantidad de enlaces en
  `PasExportacionTokens`, sin copiar los tokens al registro de auditoría.
- La confirmación posterior al envío es genérica, no lleva un `pk`, no redirige
  al Panel PAS y muestra solamente un botón visual «OK».
- El resumen 7/7 incluye todas las respuestas Sí/No visibles, incluidas las
  preguntas condicionales que correspondan. El contenedor crece con el contenido
  y mantiene las acciones debajo del resumen en escritorio y móvil; CSS y JS se
  versionan en el template para evitar que el navegador reutilice esa lógica
  anterior desde caché.
- Los PDF sólo se sirven mediante la vista autenticada con
  `pas.view_paspersona`. Django y las configuraciones operativas de NGINX
  bloquean el acceso directo a `/media/pas/ddjj/`.

## Ampliación del padrón

- La importación incremental acepta `Nombre`/`Apellido` además de
  `Nombres`/`Apellidos` y suma las columnas opcionales `Calle`, `Altura`,
  `Email`, `UltimoEstadoPas` y `AvisoLiquidacion`.
- Calle y Altura se combinan en el domicilio. Los opcionales ausentes o vacíos
  se conservan sin dato.
- El estado se resuelve contra el catálogo PAS. El aviso se busca únicamente
  entre los compatibles con ese estado y tolera texto variable agregado, como
  una fecha de liquidación. Una etiqueta inexistente o ambigua se informa como
  error de fila para evitar asociaciones incorrectas.
- El estado y aviso iniciales también quedan registrados en el historial. Se
  mantienen la omisión sin cambios de duplicados por DNI/CUIT, la carga por
  lotes y la creación del token DDJJ.
