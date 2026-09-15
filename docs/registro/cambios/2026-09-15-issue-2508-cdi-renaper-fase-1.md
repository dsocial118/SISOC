# Issue #2508 — Validación RENAPER de nómina CDI, Fase 1

## Resultado

El alta de nómina registra validación solo desde una precarga firmada, con
coincidencia de identidad y una reconsulta a RENAPER resuelta en el servidor.
El PDF reutiliza un único cálculo para niño/a y responsables. El comando de
revalidación conserva la identidad cargada y confirma por lotes.

No se cambió el modelo, no hacen falta migraciones, no se crean responsables
legales y no se implementó la Fase 2.

## Archivos

| Archivo | Cambio |
| --- | --- |
| ciudadanos/services_renaper_validacion.py | Payload extraído y comparación de identidad completa. |
| ciudadanos/services_importacion_masiva.py | Consume el helper manteniendo fecha, origen, datos crudos y tipo de registro. |
| centrodeinfancia/services_renaper_estado.py | Indicador para niño/a y ambos responsables, con mapa por lote. |
| centrodeinfancia/services_nomina_ninos_pdf.py | Delega el indicador y conserva etiquetas y coincidencia única. |
| centrodeinfancia/views.py | Token por CDI/usuario de 15 minutos con identidad mínima, reconsulta RENAPER en servidor y origen resuelto ahí. |
| centrodeinfancia/templates/centrodeinfancia/destinatario_form.html | Transporta el token en lugar de confiar en origen_dato. |
| centrodeinfancia/management/commands/validar_renaper_nominas_cdi.py | Dry-run, límite, contadores y confirmación por lote de --batch-size. |
| core/services/text_encoding.py | Expone normalize_text, la normalización NFKD que ya usaba el PDF. |
| centrodeinfancia/tests/test_nomina_renaper_validacion.py | Token válido, falsificación, CDI/usuario ajenos, vencimiento, datos alterados, ciudadano local y reenvío inválido. |
| centrodeinfancia/tests/test_validar_renaper_nominas_cdi.py | Coincidencia, discrepancias, no_match, dry-run, fallo tardío, reintento por sexo, universo, límites, idempotencia, cambios concurrentes y rollback. |
| centrodeinfancia/tests/test_renaper_estado.py | Paridad contra reglas previas y salida de build_export_data; ambos adultos, ausencias, duplicados y borrados. |
| tests/test_ciudadanos_renaper_validacion.py | Contrato del payload y su uso por importación masiva. |
| docs/implementaciones/centrodeinfancia_nomina_renaper.md | Contrato, operación y límites. |
| AGENT_REPO_MAP.md | Ubicación de servicios y comando, con advertencia de llamadas reales. |
| Este registro | Evidencia y continuación. |

## Validación y límites de la evidencia

Se leyeron AGENTS.md, el plan completo y los patrones existentes antes de editar.
Se inspeccionó el código y se escribieron los tests, pero **no se ejecutaron**.
La terminal falla al crear procesos con CreateProcessAsUserW (-1073283067).
Black, pylint y makemigrations se intentaron y no llegaron a iniciar; pytest
queda pendiente, con el stack detenido y sin .env. Tampoco se pudo obtener git
status/diff: los cambios se aplicaron sobre el contenido leído, con reemplazos
acotados y conservación de finales de línea existentes.

No se levantó Docker ni la base y no se ejecutó el comando contra RENAPER real.
Los tests del comando sustituyen consultar_datos_renaper por mocks.

**Ejecutados después, con el stack Docker levantado:** `pytest` sobre los cuatro
archivos nuevos más las regresiones de nómina, PDF provincial, destinatarios e
importación masiva; `black`, `pylint` y `makemigrations --check --dry-run`.
Resultado: 731 tests en verde (1 skip), pylint 10.00/10 sobre el comando y sin
migraciones detectadas.

Dos correcciones surgieron de esa corrida:

- `test_adulto_borrado_no_cuenta_como_coincidencia` afirmaba el contrato viejo
  del mapa de adultos (`== {}`). Con el mapa que responde por cada documento
  pedido, lo correcto es `{"30111111": "No"}`; la intención del test —que un
  borrado lógico nunca afirme "Sí"— se mantiene.
- `handle` del comando quedó con demasiadas ramas y anidamiento. Se extrajeron
  `_universo`, `_procesar_ciudadano` y `_procesar_lote`, sin cambiar el
  comportamiento.

Sigue sin ejecutarse el comando contra RENAPER real: eso requiere ventana
autorizada.

Comandos exactos para un entorno de validación preparado (black/pylint solo
sobre los Python modificados; el último comando incluye regresiones existentes):

~~~powershell
python -m black --check centrodeinfancia/management/commands/validar_renaper_nominas_cdi.py centrodeinfancia/services_nomina_ninos_pdf.py centrodeinfancia/services_renaper_estado.py centrodeinfancia/tests/test_nomina_renaper_validacion.py centrodeinfancia/tests/test_renaper_estado.py centrodeinfancia/tests/test_validar_renaper_nominas_cdi.py centrodeinfancia/views.py ciudadanos/services_importacion_masiva.py ciudadanos/services_renaper_validacion.py tests/test_ciudadanos_renaper_validacion.py

python -m pylint centrodeinfancia/management/commands/validar_renaper_nominas_cdi.py centrodeinfancia/services_nomina_ninos_pdf.py centrodeinfancia/services_renaper_estado.py centrodeinfancia/tests/test_nomina_renaper_validacion.py centrodeinfancia/tests/test_renaper_estado.py centrodeinfancia/tests/test_validar_renaper_nominas_cdi.py centrodeinfancia/views.py ciudadanos/services_importacion_masiva.py ciudadanos/services_renaper_validacion.py tests/test_ciudadanos_renaper_validacion.py

python manage.py makemigrations --check --dry-run

python -m pytest centrodeinfancia/tests/test_nomina_renaper_validacion.py centrodeinfancia/tests/test_validar_renaper_nominas_cdi.py centrodeinfancia/tests/test_renaper_estado.py tests/test_ciudadanos_renaper_validacion.py centrodeinfancia/tests/test_destinatario_views.py centrodeinfancia/tests/test_nomina_ninos_pdf.py tests/test_ciudadanos_importacion_masiva.py -v
~~~

## Decisiones y riesgos de implementación

- Los nombres se comparan reparando mojibake y normalizando diacríticos, espacios
  y mayúsculas, con `repair_utf8_mojibake` y `normalize_text`. Sin esto, los
  198.688 ciudadanos candidatos a mojibake que documenta
  `docs/plans/2026-09-01-reparacion-mojibake-datos-design.md` habrían quedado
  marcados NO_VALIDADO contra una respuesta de RENAPER que ya viene reparada en
  `core/integrations/renaper.py`. Una fecha faltante nunca es coincidencia.
- El comando confirma cada lote de `--batch-size` en su propia transacción. Una
  falla descarta solo el lote en curso y conserva los anteriores; como el universo
  filtra NO_CONSULTADO, reejecutarlo retoma donde quedó. `--limit` acota consultas
  y memoria.
- Se reutilizan is_systemic_renaper_error y el orden M/F/X de importación. Un sexo
  local conocido se consulta directamente. Un error sistémico corta la corrida; un
  `fallecido` marca NO_VALIDADO con su propia descripción y no interrumpe; el resto
  de los errores no sistémicos omite la ficha sin escribir, con corte de seguridad
  a los 20 errores inesperados consecutivos.
- El token firmado no transporta el payload de RENAPER: `signing.dumps` firma pero
  no cifra, así que el crudo habría quedado legible en el HTML. Lleva solo la
  identidad mínima y el `datos_renaper` que se persiste sale de una reconsulta
  server-side hecha antes de abrir la transacción del alta. Si esa reconsulta falla
  o devuelve otra identidad, el alta queda como manual. No se usó la cache de
  Django para esto porque `config/settings.py` usa LocMemCache, que es por proceso.
- La escritura bloquea y relee ciudadano/vínculo; omite cambios de identidad,
  estado o pérdida del vínculo. Los tests simulan cambios entre lectura y escritura:
  sigue pendiente comprobar concurrencia real y locks en MySQL.
- Motivo OTRO más descripción evita inventar una causa de la discrepancia.
  Se usa update acotado: Ciudadano.save limpia los motivos en registros ESTANDAR.
  Un guardado posterior por otro circuito todavía puede borrarlos; no cambia el
  indicador, que lee estado_validacion_renaper. No se alteró esa regla del modelo.
- Revertir código no restaura marcas ya confirmadas. Una corrida real requiere
  respaldo autorizado de los campos afectados para poder restaurarlos selectivamente.
- No se validó comprensión/aceptación humana ni se recomienda incorporación
  basándose en tests no ejecutados.

## Skill

Se usó systematic-debugging para contrastar la causa descrita con el flujo real,
comparar el token de trabajadores y escribir regresiones contra la falsificación
y errores externos. El diseño aprobado se tomó del plan; no se abrió otro diseño.
