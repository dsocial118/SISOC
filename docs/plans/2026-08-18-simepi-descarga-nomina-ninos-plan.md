# Plan de implementacion: descarga provincial de nomina SIMEPI

Fecha: 2026-08-18

Diseno: `docs/plans/2026-08-18-simepi-descarga-nomina-ninos-design.md`

Rama: `codex/simepi-descarga-nomina-ninos`

Base: `main`

## Criterio de finalizacion

La tarea esta implementada cuando un usuario EGP puede descargar desde el
listado de CDI un PDF rasterizado con solo la nomina activa y unica de su
provincia, mientras todos los demas roles y alcances quedan bloqueados en el
servidor. La suite focalizada, los checks de formato y una inspeccion visual del
PDF deben pasar antes de abrir el PR a `homologacion`.

La integracion a HML no equivale a publicacion en produccion. El segundo PR a
`main`, su gate de release y el deploy productivo son estados separados.

## Fase 1: contrato y autorizacion

### Archivos

- `centrodeinfancia/access.py`
- `centrodeinfancia/views_export.py`
- `centrodeinfancia/urls.py`
- `centrodeinfancia/tests/test_nomina_ninos_pdf.py`

### Trabajo

1. Agregar un helper pequeno y reutilizable para detectar el rol exacto
   `SIMEPI - EGP`.
2. Implementar una view autenticada de descarga que haga el control del grupo
   antes de construir cualquier queryset.
3. Resolver la unica provincia completa mediante el alcance territorial
   explicito; rechazar cero, multiples o alcances parciales.
4. Agregar una ruta con nombre estable, sin aceptar provincia o CDI desde el
   cliente.
5. Configurar attachment, nombre de archivo seguro y headers anti-cache.

### Pruebas

- anonimo redirigido al login;
- EGP con una provincia obtiene 200;
- EGP sin alcance, con multiples provincias o alcance parcial obtiene 403;
- Administrador, Analista, Equipo Nacional, Auditoria, Referente y Trabajador
  no pueden acceder;
- no se consulta el servicio de render si falla la autorizacion.

## Fase 2: consulta y normalizacion de datos

### Archivos

- nuevo `centrodeinfancia/services_nomina_ninos_pdf.py`
- `centrodeinfancia/tests/test_nomina_ninos_pdf.py`

### Trabajo

1. Definir dataclasses inmutables para usuario, CDI, nino, adulto y pagina.
2. Construir un queryset de fichas activas y no eliminadas, acotado por la
   provincia antes de evaluar resultados.
3. Usar `select_related` para CDI, provincia, ciudadano, sexo y perfil del
   actor.
4. Resolver accesos de referentes y validaciones RENAPER de adultos con
   consultas masivas, sin N+1.
5. Aplicar fallbacks de campos de nomina a ciudadano.
6. Calcular edad usando una unica fecha/hora de descarga compartida por todo el
   documento.
7. Normalizar la clave de identidad, deduplicar y conservar la ficha activa mas
   reciente.
8. Ordenar y agrupar por CDI; omitir CDI vacios.
9. No loggear valores de identidad.

### Pruebas

- otra provincia nunca llega al DTO;
- baja y soft-delete quedan fuera;
- duplicado historico produce una sola fila;
- desempate estable por fecha e id;
- orden completo por medida, edad, apellido, nombre y DNI;
- datos faltantes producen `-`;
- validacion RENAPER del nino y adulto respeta el contrato `Si`/`No`;
- referente ambiguo no expone un CUIL arbitrario;
- cantidad de queries acotada al aumentar el numero de filas.

## Fase 3: render vectorial

### Archivos

- `centrodeinfancia/services_nomina_ninos_pdf.py`
- `centrodeinfancia/tests/test_nomina_ninos_pdf.py`

### Trabajo

1. Definir pagina A4 horizontal y margenes.
2. Registrar Liberation Sans o mapearla de manera explicita como fuente
   compatible; no depender de una Arial presente por casualidad.
3. Crear encabezado provincial, encabezado CDI, tabla de trece columnas y pie.
4. Repetir encabezados mediante `PageTemplate`/callbacks de ReportLab.
5. Implementar marca de agua y numeracion `X de Y` con una pasada que conozca
   el total.
6. Agregar una pagina final de resumen provincial.
7. Mantener anchos de columna y wrapping en constantes testeables.

### Pruebas

- el PDF intermedio abre con `pypdf`;
- pagina A4 horizontal;
- encabezados repetidos al forzar mas de una pagina;
- total provincial y metadatos de pagina reciben el numero correcto;
- documento de cero filas sigue siendo valido.

## Fase 4: rasterizacion y PDF final

### Archivos

- `centrodeinfancia/services_nomina_ninos_pdf.py`
- `centrodeinfancia/tests/test_nomina_ninos_pdf.py`

### Trabajo

1. Rasterizar el PDF intermedio con `pdf2image` a JPEG dentro de un
   `TemporaryDirectory`.
2. Usar timeout, un worker y resolucion fija suficiente para texto de 9 puntos.
3. Crear un PDF final A4 horizontal que coloque una unica imagen por pagina.
4. Eliminar temporales incluso ante excepciones.
5. Traducir fallos de Poppler/render a una excepcion de servicio sin PII.

### Pruebas

- cada pagina final contiene un unico XObject de imagen;
- el filtro del objeto es JPEG (`DCTDecode`);
- el PDF final no contiene una capa de texto con DNI o nombres;
- cantidad de paginas igual al intermedio;
- falla de rasterizacion produce respuesta 503 y limpia temporales.

## Fase 5: interfaz

### Archivos

- `centrodeinfancia/views.py`
- `centrodeinfancia/templates/centrodeinfancia/centrodeinfancia_list.html`
- `centrodeinfancia/tests/test_nomina_ninos_pdf.py`

### Trabajo

1. Exponer en el contexto un boton adicional solo para EGP.
2. Reutilizar `components/search_bar.html`.
3. Usar el texto literal `Descargar nomina de ninos` y un titulo accesible.
4. No reutilizar el helper JavaScript de CSV si una descarga normal por enlace
   es suficiente.

### Pruebas

- boton visible para EGP;
- boton ausente para todos los demas roles;
- el enlace apunta al endpoint nuevo;
- la ausencia visual no reemplaza las pruebas de acceso directo.

## Fase 6: documentacion y mapa

### Archivos

- `docs/registro/cambios/2026-08-18-simepi-descarga-nomina-ninos.md`
- `AGENT_REPO_MAP.md`
- este diseno y plan

### Trabajo

1. Documentar contrato funcional, alcance, privacidad y rollback.
2. Agregar el nuevo servicio y endpoint al mapa del repositorio.
3. Registrar que no se crean archivos persistentes ni migraciones.
4. Documentar la dependencia operativa de Poppler ya presente en la imagen.

## Validacion focalizada

Ejecutar primero:

```powershell
docker compose run --build --rm --no-deps -T django pytest -q centrodeinfancia/tests/test_nomina_ninos_pdf.py
```

Luego, sobre los archivos tocados:

```powershell
docker compose run --build --rm --no-deps -T django black --check centrodeinfancia
docker compose run --build --rm --no-deps -T django pylint centrodeinfancia
docker compose run --build --rm --no-deps -T django djlint --check centrodeinfancia/templates/centrodeinfancia/centrodeinfancia_list.html
git diff --check
```

La suite completa y el build quedan a cargo de CI salvo que un fallo focalizado
indique acoplamiento adicional.

## Verificacion visual y HML

1. Generar un PDF local con datos sinteticos que cubran textos largos, valores
   faltantes y mas de una pagina.
2. Inspeccionar todas las paginas renderizadas: legibilidad, columnas, marca de
   agua, encabezados, pie y resumen final.
3. Comparar el diff de la rama contra `origin/main`.
4. Verificar integrabilidad sin conflictos contra `origin/homologacion`.
5. Abrir PR hacia `homologacion` y esperar CI completa.
6. Despues del merge, verificar SHA desplegado y repetir la descarga con un EGP
   de prueba en HML sin usar PII real.

## Promocion selectiva a main

1. Conservar la rama despues del primer merge.
2. Confirmar que `git diff origin/main...codex/simepi-descarga-nomina-ninos`
   contiene solamente esta funcionalidad.
3. Revalidar que la rama sigue actualizada con `main`; incorporar `main` por un
   merge normal si avanzo, sin rebase ni force-push.
4. Abrir el segundo PR desde la misma rama hacia `main`.
5. Revalidar rulesets y `release_baseline` en vivo.
6. Si el baseline no admite este origen, detener el release y pedir un camino
   formal; no quitar checks ni usar bypass.
7. Tras merge autorizado, esperar aprobacion del Environment `production`,
   verificar el SHA desplegado y ejecutar smoke de descarga.

## Riesgos y mitigaciones

- **PII fuera de provincia:** alcance aplicado antes de evaluar el queryset y
  pruebas negativas con dos provincias.
- **Permiso solo visual:** control de grupo duplicado en servidor.
- **N+1 y descarga lenta:** precarga y consultas masivas, prueba de query count.
- **Consumo de memoria:** temporales en disco, un worker y no conservar todas
  las imagenes decodificadas simultaneamente.
- **Datos faltantes:** `-` explicito; no inferir CUIL ni unidad de edad.
- **Duplicados legacy:** desempate determinista y log agregado sin PII.
- **Salida vectorial accidental:** inspeccionar objetos PDF y exigir JPEG por
  pagina.
- **Arrastre de HML a produccion:** rama nacida de `main` y diff del segundo PR
  calculado contra `main`.
- **Gate de release incompatible:** detenerse; no degradar la proteccion.
