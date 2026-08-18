# 2026-08-18 - Urgentes CDI del issue 2304

## Contexto

El issue #2304 agrupó correcciones urgentes del flujo SIMEPI/CDI: alcance
territorial de usuarios, centros y nóminas; obligatoriedad y ubicación de
campos de niños y trabajadores; un acceso visible a Grupos sin permiso; y un
comunicado interno duplicado.

El desarrollo parte de `main` y se publica en un único PR dirigido a
`homologacion`, sin pasar por `development`.

## Cambios aplicados

- Los roles EGP, Referente CDI y Trabajador CDI fallan cerrados cuando les
  falta su alcance territorial u operativo. EGP queda limitado a sus
  provincias; los roles locales, a sus CDI vinculados.
- El listado y la administración de usuarios intersectan la delegación de
  roles existente con el mismo alcance geográfico: un EGP sólo administra
  referentes vinculados a CDI de su provincia y un referente sólo administra
  trabajadores de sus CDI.
- En la nómina de niños, el CUIT del niño es obligatorio. Los CUIT de sus
  responsables continúan optativos. Lenguajes permanece obligatorio y talla,
  peso, longitud acostado y perímetro cefálico pasan a ser optativos, sin
  perder sus validaciones cuando se informan.
- La pregunta sobre apoyo al desarrollo se muestra dentro de Discapacidad en
  el alta y el detalle del niño, y deja de formar parte de Vacunación NOMIVAC.
- En el alta de trabajadores, Función es obligatoria según el subcomponente;
  Sala también es obligatoria para CDI y vuelve a enviarse al guardar. El
  correo es obligatorio únicamente al crear, para generar el usuario
  automático; una edición histórica todavía admite registros sin correo.
- El enlace lateral a Grupos sólo se renderiza con `auth.view_group`. No se
  amplían permisos y el endpoint conserva su protección ante acceso directo.
- La migración `comunicados.0010` archiva y quita de destacados los comunicados
  internos publicados cuyo título empieza con `Importación de nómina`. No
  elimina registros.

## Impacto esperado

- No debe existir lectura cruzada entre provincias o CDI para los roles
  territoriales involucrados.
- Los formularios rechazan sólo los datos que el issue define como
  obligatorios y preservan la compatibilidad de registros históricos.
- Los usuarios sin permiso dejan de encontrar un enlace que conduce a un 403,
  sin debilitar la autorización del backend.
- Los comunicados duplicados dejan de ser visibles, pero siguen disponibles
  como archivados para auditoría o recuperación manual.

## Validación

- Tests focalizados agregados para scopes de CDI y usuarios, formularios de
  niños y trabajadores, aprovisionamiento automático, sidebars y migración de
  comunicados.
- Compilación de los Python modificados y validación de sintaxis de los dos
  JavaScript del flujo.
- `git diff --check` para consistencia del diff.
- La ejecución local de pytest queda condicionada por el entorno: el Python
  global no tiene `crispy_forms` y los entornos virtuales versionados apuntan a
  un Python 3.10 inexistente. Los tests focalizados se ejecutarán en CI sin
  instalar dependencias ni modificar el entorno compartido.

## Riesgos y rollback

- La migración de comunicados usa un prefijo deliberadamente específico y
  sólo afecta internos publicados. Su reversa es un no-op para no republicar
  comunicaciones que ya estuvieran archivadas; el rollback de datos debe ser
  selectivo y manual si producto decide restaurarlas.
- Los roles CDI configurados sin vínculo dejan de heredar un alcance genérico.
  Es el comportamiento seguro esperado, pero puede visibilizar cuentas
  incompletamente configuradas que deberán corregirse asociando provincia o
  CDI.
- El rollback de código consiste en revertir este cambio. La información de
  niños, trabajadores y comunicados no se elimina.
