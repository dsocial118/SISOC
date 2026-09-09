# Circuito de nueve pasos, informes de errores y tooling de calidad

**Fecha:** 2026-09-07
**Alcance:** prototipo de RUNAC (fuera del repositorio de SISOC)

Registro con la convención de `docs/registro/` de SISOC. El prototipo está fuera
del repositorio, pero se documenta igual: al integrarse, este archivo es el que
explica por qué las cosas están como están.

---

## 1. El circuito vive en un servicio, no en las vistas

**Decisión.** Las transiciones de estado de una presentación se concentran en
`runac/services/circuito_service.py`. Las vistas piden una acción; el servicio
valida el estado de origen y el rol, y levanta `TransicionInvalida` si no
corresponde.

**Por qué.** `AGENTS.md` establece que la lógica de negocio vive en `services/` y
que las vistas son delgadas. Además, tener la tabla de transiciones en un solo
lugar permite testearla sin base de datos, que es lo que hacen los tests.

**Trade-off.** Las vistas quedan casi vacías y la pantalla no puede inventar
acciones: sólo muestra las que el servicio declara disponibles. Es más rígido, y
es deliberado.

---

## 2. La carga es de a un archivo

**Decisión.** Se eliminó la selección de carpeta. El operador declara qué archivo
sube, y el sistema controla el orden de importación.

**Por qué.** Lo define el análisis funcional para la primera versión: si el
operador declara el archivo, el nombre del fichero deja de condicionar la
importación y se elimina una causa de rechazo que no aporta al control de la
información. Además, la selección de carpeta depende de una función no estándar
de los navegadores, restringida en equipos de organismos públicos.

**Pendiente conocido.** La dependencia entre archivos se deriva hoy del orden de
importación, y eso encadena todo con todo: `DISP_SCP` queda bloqueado por
`DISP_PENAL` aunque sean independientes entre sí. Las dependencias reales son
MPE → dispositivos residenciales y MPJ/DAE → dispositivos penales, y deberían
declararse en la Capa 1 en lugar de inferirse.

---

## 3. Dos informes de errores, y el que importa es el segundo

**Decisión.** Ante una importación con errores, el operador puede descargar:

1. una **planilla de errores**: un Excel nuevo, una hoja por cada hoja del
   archivo, una fila por error;
2. **su propio archivo con las celdas marcadas**: el mismo Excel que subió, con
   las celdas problemáticas pintadas y un comentario en cada una.

**Por qué.** El operador corrige *en el Excel*, no en la pantalla. Una lista en
la web lo obliga a ir y venir entre dos ventanas contando filas. El archivo
marcado se abre, se ve qué está mal y dónde, se corrige y se vuelve a importar.

**Consecuencia en el modelo.** Para poder devolver el archivo hizo falta
conservar dónde quedó: se agregó `runac_c2_importacion.ruta_archivo`. Ese campo
cubre además la definición pendiente sobre el respaldo documental del Excel
recibido.

**Consecuencia en el motor.** Cada regla incumplida ahora guarda la **letra de
columna** del Excel, derivada del orden del campo en la Capa 1. Sin eso no se
puede señalar la celda.

---

## 4. Tooling de calidad: el mismo que SISOC

**Decisión.** Se incorporaron `black 24.8.0`, `pylint 3.2.6` con
`pylint-django 2.7.0`, `djlint 1.34.2` y `pytest 8.3.5` —las versiones de
`requirements/dev.txt`, `lint.txt` y `test.txt` de SISOC—, y se copiaron sin
cambios `.pylintrc`, `.djlintrc` y `pyproject.toml`.

**Por qué.** `AGENTS.md` define ese tooling como el real del repositorio. Si el
prototipo se valida con otras herramientas o con otra configuración, al
integrarlo aparecen diferencias de formato que no son decisiones de nadie.

**Estado.** `black` y `djlint` limpios. `pylint` en 9.58/10.

**Supresiones.** Una sola, y acotada: `runac/models.py` está generado por
`inspectdb` y sus comentarios de campo vienen de la base, así que se suprimen
`line-too-long` y `too-many-lines` en ese archivo. La guía de estilo pide usar la
supresión más chica posible y dejar constancia; es esto.

**Lo que queda.** Los avisos de complejidad (`too-many-locals`,
`too-many-statements`) están en `services/motor/`, que son scripts nacidos como
herramientas de línea de comandos. Corregirlos sería el refactor amplio que
`AGENTS.md` pide evitar mezclar con una feature. Queda anotado para cuando el
motor se integre.

---

## 5. Tests sin base de datos

**Decisión.** Los tests cubren la tabla de transiciones del circuito, los
permisos por rol y la convención de nombres de las tablas receptoras. No crean
base de datos.

**Por qué.** Los modelos del prototipo son `managed = False`: la estructura la
genera la Capa 1 y no Django, así que `pytest-django` no puede crearla. Lo que sí
se puede testear sin base es la lógica, que es justamente donde están las reglas
que no pueden romperse.

**Cobertura actual.** 29 tests. Los que necesiten datos reales deberían marcarse
`mysql_compat` y correr contra la base de trabajo, el mismo criterio de SISOC.

---

## 6. La estética no sigue a SISOC, y es a propósito

**Situación.** SISOC usa AdminLTE sobre Bootstrap 4, con una biblioteca de
componentes propios en `templates/components/`. El prototipo usa Bootstrap 5 con
estilos propios.

**Por qué.** El prototipo existe para mostrar el circuito y destrabar
definiciones, no para parecerse al sistema. Adoptar AdminLTE ahora sumaría
trabajo sin cambiar ninguna de las decisiones que hay que tomar.

**Consecuencia.** Al integrar el módulo hay que rehacer las plantillas con los
componentes de SISOC. Es trabajo previsible y conviene tenerlo en la estimación.
