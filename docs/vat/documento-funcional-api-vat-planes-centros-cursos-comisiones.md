# Documento funcional - API VAT operativa para planes, centros, cursos y comisiones

Fecha: 2026-04-08

## Objetivo

Describir, desde una mirada funcional, qué información de negocio queda disponible consumiendo la API operativa de VAT asociada al flujo de:

1. ubicación,
2. planes curriculares,
3. centros,
4. cursos,
5. comisiones.

Este documento no explica la colección de Postman como artefacto técnico. El foco está en qué datos puede obtener un consumidor de API y para qué sirven en un flujo funcional.

Colección de referencia:

- `postman/VAT - Planes Centros Cursos Comisiones.postman_collection.json`

## Base URL y autenticación

Base:

- `/api/vat/`

Autenticación:

- `Authorization: Api-Key <clave>`

Permiso aplicado en estos endpoints:

- `HasAPIKey`

## Paginación de respuestas

Los endpoints listados en este flujo se consumen con paginación basada en páginas.

En términos funcionales, esto significa que la API separa:

- el total de registros existentes,
- el subconjunto de registros devueltos en la página actual,
- la navegación hacia la página siguiente o anterior.

La estructura de respuesta esperable para endpoints listados incluye:

- `count`: total de registros disponibles para ese endpoint y esos filtros,
- `next`: URL de la próxima página, si existe,
- `previous`: URL de la página anterior, si existe,
- `results`: registros concretos devueltos en la página actual.

Ejemplo funcional:

- si `count` devuelve `2041`, eso significa que el universo total de centros disponibles para esa consulta es de 2041,
- si `results` trae 10 elementos, eso no significa que existan solo 10 centros, sino que la API está mostrando una sola página,
- para seguir recorriendo la información se debe usar `next` o pedir explícitamente `?page=2`, `?page=3`, etc.

Implicancias para consumo:

- para conocer el total no hace falta recorrer todas las páginas: alcanza con leer `count`,
- para obtener todos los registros sí hace falta iterar por páginas,
- la API admite `page_size` como query param opcional en endpoints paginados de este flujo,
- `page_size` acepta enteros positivos hasta un máximo de `200`,
- si `page_size` es inválido (texto, `0`, negativo o mayor al máximo), la API aplica silenciosamente el tamaño por defecto.

Uso funcional de la paginación:

- mostrar totales globales sin descargar toda la colección,
- construir tablas o selectores paginados,
- recorrer progresivamente grandes volúmenes de centros, cursos o comisiones,
- evitar respuestas demasiado pesadas en integraciones o frontends.

## Qué datos habilita esta API

Consumir esta API permite construir un recorrido operativo sobre la oferta formativa de VAT con cuatro niveles principales:

1. identificar una ubicación administrativa,
2. conocer qué planes curriculares están vigentes,
3. ubicar qué centros existen dentro de una jurisdicción,
4. listar qué cursos ofrece un centro,
5. listar qué comisiones concretas tiene cada curso.

En términos funcionales, la API permite responder preguntas como:

- qué provincias y municipios están disponibles para filtrar la oferta,
- qué planes curriculares activos existen y a qué sector o subsector pertenecen,
- qué centros operativos existen en una zona,
- qué cursos dicta un centro determinado,
- qué comisiones concretas se pueden abrir, consultar o mostrar para un curso.

## Endpoints funcionales y datos disponibles

### 1. Ubicación administrativa

Endpoints:

- `GET /api/vat/provincias/`
- `GET /api/vat/municipios/?provincia_id=<id>`

Datos funcionales disponibles:

- catálogo de provincias,
- catálogo de municipios asociados a una provincia,
- base geográfica mínima para segmentar centros, cursos y comisiones.

Campos relevantes:

#### Provincias

- `id`
- `nombre`

#### Municipios

- `id`
- `nombre`
- `provincia`
- `provincia_nombre`

Uso funcional:

- poblar filtros de jurisdicción,
- acotar búsquedas por territorio,
- construir navegación provincia -> municipio antes de consultar centros u oferta.

### 2. Planes curriculares

Endpoint principal:

- `GET /api/vat/planes-curriculares/`

Filtros relevantes:

- `activo=true|false`
- `sector_id`
- `subsector_id`
- `titulo_referencia_id`
- `modalidad_cursada_id`

Datos funcionales disponibles:

- planes curriculares vigentes o inactivos,
- nombre del plan,
- sector y subsector al que pertenece,
- modalidad de cursada,
- carga horaria,
- normativa,
- niveles requeridos y certificados.

Campos relevantes:

- `id`
- `nombre`
- `titulo_referencia`
- `titulo_referencia_nombre`
- `sector`
- `sector_nombre`
- `subsector`
- `subsector_nombre`
- `modalidad_cursada`
- `modalidad_cursada_nombre`
- `normativa`
- `horas_reloj`
- `nivel_requerido`
- `nivel_certifica`
- `activo`

Uso funcional:

- identificar la oferta académica disponible,
- filtrar planes por sector o subsector,
- mostrar metadatos académicos antes de llegar al centro o al curso,
- validar qué planes están operativos para una jurisdicción o programa.

### 3. Centros

Endpoint principal:

- `GET /api/vat/centros/`

Filtros relevantes:

- `activo=true|false`
- `provincia_id`
- `municipio_id`
- `localidad_id`

Datos funcionales disponibles:

- listado de centros de formación,
- ubicación administrativa del centro,
- datos de contacto básicos,
- estado operativo del centro,
- referencia institucional y de referente.

Campos relevantes:

- `id`
- `nombre`
- `referente`
- `referente_nombre`
- `codigo`
- `activo`
- `provincia`
- `provincia_nombre`
- `municipio`
- `municipio_nombre`
- `localidad`
- `localidad_nombre`
- `domicilio_actividad`
- `telefono`
- `celular`
- `correo`
- `nombre_referente`
- `apellido_referente`
- `tipo_gestion`
- `clase_institucion`
- `situacion`

Uso funcional:

- obtener el padrón de centros activos,
- encontrar centros por zona geográfica,
- mostrar ficha básica del centro,
- seleccionar un centro para consultar su oferta de cursos.

Consideraciones de paginación para centros:

- `GET /api/vat/centros/` no devuelve todos los centros en un único bloque,
- el total del padrón filtrado se obtiene desde `count`,
- los centros concretos de la página actual vienen en `results`,
- para recorrer el padrón completo se debe avanzar con `next` o con `?page=<n>`.

### 4. Cursos

Endpoint principal:

- `GET /api/vat/cursos/`

Filtros relevantes:

- `centro_id`
- `provincia_id`
- `municipio_id`
- `modalidad_id`
- `programa_id`
- `estado`

Datos funcionales disponibles:

- cursos asociados a un centro,
- relación entre curso y plan de estudio,
- modalidad de dictado,
- programa asociado,
- si usa voucher,
- costo en créditos,
- parametrías de voucher vinculadas,
- estado general del curso.

Campos relevantes:

- `id`
- `centro`
- `centro_nombre`
- `plan_estudio`
- `plan_estudio_nombre`
- `nombre`
- `modalidad`
- `modalidad_nombre`
- `programa`
- `programa_nombre`
- `estado`
- `usa_voucher`
- `voucher_parametrias`
- `costo_creditos`
- `observaciones`
- `fecha_creacion`
- `fecha_modificacion`

Uso funcional:

- consultar toda la oferta de cursos de un centro,
- filtrar cursos por programa o modalidad,
- distinguir cursos activos,
- saber si una oferta requiere o consume vouchers,
- preparar la navegación hacia el nivel de comisión.

### 5. Comisiones de curso

Endpoint principal:

- `GET /api/vat/comisiones-curso/`

Filtros relevantes:

- `curso_id`
- `centro_id`
- `provincia_id`
- `municipio_id`
- `estado`

Datos funcionales disponibles:

- comisiones concretas asociadas a un curso,
- identificación de la comisión,
- sede o ubicación de dictado,
- cupo total,
- fechas de inicio y fin,
- estado de la comisión.

Campos relevantes:

- `id`
- `curso`
- `curso_nombre`
- `curso_centro_id`
- `ubicacion`
- `ubicacion_nombre`
- `codigo_comision`
- `nombre`
- `cupo_total`
- `fecha_inicio`
- `fecha_fin`
- `estado`
- `observaciones`
- `fecha_creacion`
- `fecha_modificacion`

Uso funcional:

- conocer la oferta concreta abierta al público o a la operatoria interna,
- diferenciar múltiples comisiones de un mismo curso,
- mostrar calendario básico y capacidad disponible a nivel comisión,
- habilitar selección de comisión para inscripción, seguimiento o consulta operativa.

## Relación funcional entre los datos

El valor principal de esta API no está en cada endpoint aislado sino en el encadenamiento de datos:

1. con `provincias` y `municipios` se define la jurisdicción de trabajo,
2. con `planes-curriculares` se identifica la oferta académica disponible,
3. con `centros` se localizan instituciones dentro de esa jurisdicción,
4. con `cursos` se obtiene la oferta concreta de cada centro,
5. con `comisiones-curso` se baja al nivel operativo final donde existe una edición específica del curso.

Eso permite construir pantallas, reportes o integraciones que respondan preguntas del tipo:

- qué centros de una provincia tienen oferta activa,
- qué cursos vinculados a determinado programa se dictan en un municipio,
- qué comisiones tiene un curso puntual,
- qué cursos requieren vouchers y cuáles no,
- qué planes curriculares terminan materializándose en cursos y comisiones dentro de los centros.

## Casos de uso funcionales posibles

### Mapa de oferta por territorio

Consumir `provincias`, `municipios`, `centros` y `cursos` permite armar una vista de oferta formativa por jurisdicción.

### Navegación institucional de la oferta

Consumir `centros`, luego `cursos` por `centro_id` y finalmente `comisiones-curso` por `curso_id` permite mostrar la estructura completa de un centro: institución -> curso -> comisión.

### Consulta de cursos financiados con voucher

Consumir `cursos` permite distinguir si una oferta usa vouchers, qué programa tiene asociado y qué costo en créditos presenta.

### Consulta operativa de aperturas

Consumir `comisiones-curso` permite identificar aperturas concretas, su período y su cupo total, que es el nivel más cercano a la ejecución real del dictado.

## Alcance funcional del flujo

Con esta API se obtiene principalmente información de consulta y navegación operativa.

El flujo cubre:

- catálogos geográficos mínimos,
- estructura académica base,
- instituciones que dictan oferta,
- cursos disponibles,
- comisiones concretas.

El flujo no está orientado en este documento a:

- explicar alta, edición o borrado de registros,
- explicar la colección Postman paso a paso,
- documentar la API web pública `/api/vat/web/`.

## Resumen ejecutivo

Consumir la API operativa de VAT en este flujo permite obtener una visión completa de la cadena:

- dónde se dicta la oferta,
- qué planes la estructuran,
- qué centros la sostienen,
- qué cursos se ofrecen,
- y en qué comisiones concretas se materializa.

Es una API útil para tableros operativos, integraciones internas, navegación administrativa y consultas de oferta formativa con segmentación territorial.

Además, su paginación permite distinguir con claridad entre el total disponible y el subconjunto actualmente descargado, algo clave cuando se consumen padrones grandes como el de centros.