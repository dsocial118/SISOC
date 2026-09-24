# Encuestas: rondas, privacidad y resultados

## Alcance

`encuestas` permite crear encuestas periódicas para usuarios autenticados de
SISOC. Una encuesta se publica en rondas; cada ronda abre y cierra en fechas
propias y conserva el resultado histórico de esa versión.

El módulo admite preguntas de texto, opciones, escala, Sí/No, número y fecha.
Las preguntas pueden ser obligatorias, depender de una respuesta anterior y,
cuando tienen un conjunto cerrado de respuestas, participar de un puntaje
ponderado. El puntaje se calcula al consultar resultados; no se persiste como
un dato independiente.

## Ciclo y segmentación

- Las encuestas pueden ser únicas o recurrentes. El worker ejecuta
  `process_encuestas_rondas` para abrir y cerrar rondas por fecha.
- La segmentación puede ser todos los usuarios o un listado de documentos. Los
  cambios de destinatarios se aplican a la ronda abierta.
- Editar una encuesta con respuestas crea una nueva versión; no se permite
  editarla mientras tenga una ronda abierta.
- Modalidades de respuesta:
  - **Obligatoria:** bloquea la navegación hasta responder.
  - **Postergable:** permite responder más tarde y exige un intervalo de
    recordatorio mayor a cero.
  - **Opcional:** permite elegir «Prefiero no responder». El descarte aplica
    al usuario y a la ronda actual; no cuenta como respuesta ni cumplimiento.
    Una ronda recurrente posterior vuelve a ofrecerse.
- El selector del editor deriva `es_obligatoria` y `es_opcional`. El intervalo
  de recordatorio se muestra y conserva solo para postergables. Ambas banderas
  no pueden estar activas a la vez. Las solicitudes anteriores sin selector
  siguen admitiendo las banderas originales.
- El descarte se guarda en `RecordatorioUsuario.descartada`. Se comprueba que
  la ronda esté abierta y vigente, el usuario sea destinatario y no haya
  respondido. El cierre visual del modal no equivale a descartar la ronda.

## Exportación e importación de configuración

- Desde edición, **Exportar JSON** ofrece **Solo encuesta** o **Con segmentación**.
  Descarga los datos guardados; los cambios sin guardar no se incluyen.
- El archivo usa `formato: "sisoc.encuesta"` y `version_formato: 3`. Incluye
  título, descripción, anonimato, modalidad, recurrencia, plazos y preguntas
  con opciones, puntajes y condiciones referenciadas por orden.
- La segmentación es optativa: tipo «todos los usuarios» o documentos de los
  destinatarios. No se incluyen archivos de origen, cuentas de usuario,
  respuestas, rondas, identificadores ni historial de versiones.
- Desde el listado, **Importar** abre el selector y envía el archivo al elegirlo,
  mostrando un spinner. Admite `.json` UTF-8 (con o sin BOM), hasta 5 MB.
- La importación siempre crea una encuesta nueva en borrador, versión 1 y
  atribuida al usuario importador. No sobrescribe encuestas existentes.
  Si el archivo incluye segmentación, la restaura; si no, queda pendiente.
  Después vuelve al listado y muestra el mensaje correspondiente. El flujo
  continúa con revisión/configuración de segmentación y publicación manual.
- Se admiten versiones 1 y 2 del JSON; sin `es_opcional`, se conserva el
  comportamiento anterior (obligatoria o postergable). Los consumidores
  antiguos deben actualizarse para importar el formato 3.
- Formato, tipos, reglas de preguntas y documentos se validan en el servidor.
  Los errores revierten la operación completa y se muestran en un toast rojo.

## Presentación

El botón «Agregar pregunta» permanece al pie del listado, a la derecha.
Crear/editar, segmentación y el modal de respuesta comparten tokens y botones
Poncho. El modal agrupa preguntas, resalta opciones seleccionadas e informa la
modalidad y el anonimato. Conserva preguntas condicionales y dispone de scroll
interno y adaptación a pantallas pequeñas.

## Permisos y privacidad

`Gestor de Encuestas` administra encuestas, preguntas, segmentación y rondas.
`Encuestas Resultados` accede al listado y al permiso específico
`encuestas.ver_resultados`, sin adquirir acciones de gestión.

En encuestas anónimas, el sistema conserva el cumplimiento necesario para no
volver a mostrar la ronda, pero resultados y exportaciones no deben asociar el
contenido de una respuesta con una identidad. Los resultados son agregados y
la exportación sigue la política común de CSV/Excel.

La exportación **de configuración JSON** requiere `encuestas.change_encuesta`;
la importación requiere `encuestas.add_encuesta`. Ambas exigen autenticación;
importar y descartar son POST con protección CSRF. Exportar con segmentación
incluye documentos personales por elección explícita del gestor, incluso si
las respuestas de la encuesta son anónimas. No se registran esos documentos
en logs de importación/exportación.

## Despliegue

Aplicar `python manage.py migrate encuestas` (migración
`0003_encuesta_opcional`) antes de servir las nuevas versiones del módulo y
reiniciar el proceso web y `encuestas_worker`. Las banderas nuevas tienen
valor inicial `False`, preservando encuestas y recordatorios existentes.
No revertir esta migración sin considerar la pérdida de la modalidad opcional
y de los descartes almacenados.

## Puntos de entrada

- Dominio y reglas: `encuestas/models.py`, `encuestas/services.py` y
  `encuestas/services_resultados.py`.
- Portabilidad: `exportar_encuesta` / `importar_encuesta` en `services.py`;
  `/encuestas/<pk>/exportar/` y `/encuestas/importar/`.
- Descarte: `/encuestas/responder/<pk>/descartar/` (identificador de ronda).
- Presentación: `static/custom/css/encuestaForm.css`,
  `static/custom/css/encuestaResponder.css` y templates en `encuestas/templates/`.
- Regresiones de portabilidad/modalidad: `encuestas/tests/test_encuestas_portabilidad.py`
  y `encuestas/tests/test_encuestas_opcionales.py`.
- Bloqueo transversal: `encuestas/middleware.py`.
- Operación de rondas: `encuestas/management/commands/process_encuestas_rondas.py`
  y el servicio `encuestas_worker`.
- Diseño y decisiones históricas: `docs/registro/analisis/2026-08-28-modulo-encuestas.md`.
