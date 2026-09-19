# Cambio: DataCalle — tres roles explícitos, provincia única y acceso a la app para coordinadores

## Alcance

Implementación de la decisión `2026-09-18-datacalle-roles-y-permisos.md`, que
alinea el módulo con el documento funcional del área ("Definición funcional de
roles y permisos DataCalle / SISOC", 2026-09-18). Cierra en esta misma rama el
segundo bloque de QA (`2026-09-17-datacalle-qa-segundo-bloque.md`).

## Comportamiento

- **Tres roles explícitos.** `Profile.datacalle_rol` distingue ahora
  Administrador Nacional, Coordinador Provincial y Relevador. Es la única
  fuente de verdad sobre qué puede hacer un usuario en DataCalle; los grupos
  Django y el alcance territorial se derivan de él, no al revés.
- **`Profile.es_relevador_calle` cambia de semántica.** Antes marcaba "usuario
  sólo-app"; ahora marca "tiene acceso a DataCalle", y lo llevan los tres
  roles en `True`. Ningún lector debe seguir interpretándolo como "es
  entrevistador exclusivamente".
- **Coordinador y administrador entran al backoffice y a la app.** El gate de
  login de SISOC sólo rechaza al relevador (RN05, que se mantiene sin
  backoffice). Ambos roles provinciales/nacionales pueden además operar la
  app en campo.
- **La API sirve a los tres roles con alcance propio.** El relevador ve los
  operativos donde está asignado al equipo (8.1, sin cambios); el coordinador
  ve todos los operativos de su provincia aunque no esté en el equipo; el
  administrador ve todos, sin recorte territorial.
- **Provincia única por usuario (RN01).** El relevador tiene constraint en la
  base que le impide tener más de una provincia. El coordinador la tiene por
  regla de negocio (un único `ProfileTerritorialScope` de provincia completa),
  validada en formulario y servicio.
- **Sólo el administrador crea coordinadores y elige provincia (RN02).** La
  regla se aplica en servidor —formulario y servicio de guardado—, no sólo
  ocultando el selector en la plantilla (RN08). El selector de rol siempre
  incluye el rol que el perfil editado **ya tiene**, para que reenviarlo sin
  cambios no sea una escalada; y la validación RN08 rechaza sólo cuando el rol
  *cambia* a uno que el actor no puede asignar.
- **El formulario arma el alcance a partir del rol (D1).** Al guardar un
  usuario con rol `coordinador`, el sistema fuerza `es_usuario_provincial` y
  crea el `ProfileTerritorialScope` de provincia completa de la provincia
  elegida; con rol `administrador` no escribe alcance alguno (nacional);
  `RelevadorCalleProvincia` se escribe sólo para el `entrevistador`. En ambos
  casos el sistema asigna además el grupo Django que corresponde al rol.
- **Convertir en usuario de DataCalle a alguien que ya tiene alcance
  territorial cargado se rechaza en pantalla (2026-09-19).**
  `es_usuario_provincial` y `ProfileTerritorialScope` son el panel territorial
  genérico del backoffice, compartido con comedores, admisiones y SIMEPI. La
  derivación del punto anterior los reescribe, así que asignar un rol de
  DataCalle a un usuario que ya tenía alcance propio le cambiaba el acceso en
  esos módulos sin avisar. Ahora el formulario no guarda: muestra un error en
  el selector de rol que dice cuántas provincias tiene hoy, qué le pasaría y
  que hay que resolver ese alcance antes. Los casos son:
  - rol `coordinador` con una sola provincia completa, la misma que la elegida
    en DataCalle: **sin conflicto**, se deriva como hasta ahora (es el
    coordinador que se reedita);
  - rol `coordinador` con dos o más provincias, o con una distinta a la
    elegida: **se rechaza** (perdería el acceso a las demás);
  - rol `coordinador` con alcance sólo municipal: **se rechaza** (derivarlo a
    provincia completa se lo ensancharía);
  - rol `administrador` con cualquier alcance cargado: **se rechaza** (quitarle
    el alcance lo dejaría irrestricto en todo el backoffice, no sólo en
    DataCalle);
  - usuario sin alcance cargado: **sin conflicto**, se deriva. Es el caso común
    del alta.
- **El grupo de DataCalle se sincroniza en los dos sentidos (2026-09-19).** La
  automatización sólo agregaba el grupo del rol: bajar a un coordinador a
  relevador le dejaba puesto `Coordinador DataCalle`, y destildar el acceso a
  DataCalle lo dejaba con el grupo y sin rol, o sea viendo y editando
  operativos en el backoffice. Ahora también se quita el grupo de DataCalle que
  no corresponde al rol actual. No se tocan otros grupos.
- **Nadie provincial puede cambiar su propia provincia (RN02).** En la
  autoedición, `territorial_scopes` y `es_usuario_provincial` llegan
  `disabled`, así que Django ignora lo que llegue por POST.
- **Nuevo grupo `Administrador DataCalle` en la semilla**, con el mismo
  conjunto de permisos de datacalle y auth que el coordinador; el alcance
  nacional surge de no tener `territorial_scopes`, no de un permiso especial.
- **Cambios de operativos y casos quedan en auditoría (8.6)**, registrados vía
  `audittrail` en lugar de un log ad hoc.
- **`/api/users/me/` deja de mentir al coordinador y al administrador.** Antes
  devolvía una lista de provincias vacía para ambos roles aunque sí tuvieran
  alcance; ahora refleja la provincia real del coordinador y la ausencia de
  recorte territorial del administrador. El rol que expone sale de
  `get_datacalle_rol`: ya no queda gateado detrás de `es_relevador_calle`, que
  con la semántica nueva no decide nada.

- **El Administrador Nacional ve y administra a todos los usuarios de
  DataCalle del país** (coordinadores, relevadores y otros administradores, sin
  superusuarios). Sin esto no tenía alcance en el listado —no tiene scopes
  provinciales— y se veía sólo a sí mismo, con lo que el flujo "Administrador →
  Crear usuario → Rol Coordinador" que RN02 le reserva no arrancaba sin una
  delegación aparte. Es el análogo un nivel arriba de la regla del coordinador.

## Decisiones

1. **`es_relevador_calle` cambia de significado en vez de renombrarse.** Un
   rename hubiera obligado a tocar el contrato D1.2 que la app ya consume
   (expone ese campo por nombre); reinterpretar el valor existente —de
   "sólo-app" a "tiene acceso a DataCalle"— evita romper a un cliente que no
   controlamos.

2. **La provincia única se impone con constraint sólo para el relevador.**
   `RelevadorCalleProvincia` es una tabla exclusiva de DataCalle, así que
   puede llevar el `UniqueConstraint` sin afectar a nadie más. El coordinador
   usa `ProfileTerritorialScope`, tabla compartida con otros roles del
   backoffice que sí necesitan varias provincias; ahí no se puede constrainear
   a nivel de base sin romper esos otros usos, así que la unicidad se valida
   en el formulario y en el servicio.

3. **El mecanismo `union`/`fijas` del formulario de usuarios se eliminó.**
   Existía para que un coordinador de una provincia, al editar a un relevador,
   no le borrara la provincia que ya tenía asignada de otra provincia: el
   formulario unía la provincia nueva con la vieja en vez de reemplazarla. Con
   RN01 (provincia única) esa unión producía dos provincias sobre una tabla
   que ahora las prohíbe, y el guardado se rechazaba con un error que parecía
   un bug. El caso que el mecanismo protegía —un coordinador tocando la
   provincia de un relevador ajeno a la suya— ya lo prohíbe RN03 y ya lo
   bloquea el filtro de alcance del propio formulario, así que el mecanismo
   quedó redundante y se sacó en lugar de parchearlo.

4. **La migración de datos no tiene reversa.** Clasifica a los coordinadores
   existentes en administrador o coordinador según si tienen alcance
   territorial. No hay forma de distinguir, después de correrla, un rol que
   quedó así por la migración de uno que se dio de alta legítimamente con
   posterioridad; revertir la migración borraría roles que nadie pidió
   borrar. El forward es idempotente, así que puede correrse más de una vez
   sin efecto adicional.

5. **La clasificación de la migración pregunta por la restricción
   territorial, no por la forma del alcance.** Pasó por tres versiones. La
   primera miraba `territorial_scopes.exists()`: un perfil con scopes pero sin
   `es_usuario_provincial` quedaba `coordinador` mientras los lectores en
   runtime lo trataban como nacional. La segunda replicó
   `get_full_province_scope_ids`, el predicado de los lectores, y arregló ese
   caso pero introdujo otro peor: ese predicado devuelve `False` tanto para
   quien no tiene la restricción activa —hoy irrestricto en el backoffice—
   como para quien la tiene con alcance **sólo municipal**, que hoy no ve nada
   (`apply_relevamientos_scope` le devuelve `.none()`). Al segundo lo ascendía
   a Administrador Nacional, o sea le regalaba el país entero en la app y el
   cierre de cualquier operativo. La versión actual separa los dos casos:
   `administrador` sólo para quien **no** tiene `es_usuario_provincial`;
   cualquier perfil con la restricción activa queda `coordinador`, tenga
   provincia completa o un único municipio. Para decidir un rol, "sin
   restricción" y "restricción municipal" no son lo mismo, y el predicado de
   alcance efectivo no los distingue.

6. **La migración `0053` también migra a los relevadores.** Un perfil con
   `es_relevador_calle=True` y `datacalle_rol=""` no es "relevador" con la
   semántica nueva sino "nadie": pierde el acceso a la app, deja de ser
   `es_solo_app` (o sea que gana el backoffice), desaparece del selector de
   equipo —que filtra por `datacalle_rol="entrevistador"`— y bloquea la
   edición de cualquier operativo que lo tenga en el equipo. El backfill les
   asigna `entrevistador` salvo que estén en el grupo `Coordinador DataCalle`,
   que ya clasificó el paso anterior. Es idempotente como el resto de `0053`.

7. **La auditoría de casos excluye todo lo que identifica o ubica a la
   persona:** `respuestas`, `lat`, `lon`, `codigo_entrevistado`,
   `persona_entrevistada` y `es_menor_de_edad` quedan fuera del log. El log de
   auditoría es exportable y sobrevive al borrado del caso, así que copiar ahí
   el instrumento completo o las coordenadas sería una fuga de datos
   sensibles por una puerta distinta a la que se cuida en el resto del
   sistema. Lo que sí queda —estado, operativo, origen, variante, grupo y
   timestamps— alcanza para lo que pide el punto 8.6 del documento funcional.

8. **El mismo criterio se aplicó al operativo y a `object_repr`.** Excluir los
   campos del caso no alcanzaba, por dos puertas que quedaban abiertas. La
   primera: `Relevamiento` guarda en cada cierre `lat`, `lon`,
   `observacion_asentamiento` y `otra_observacion`, que describen la ubicación
   exacta y las condiciones de vida de un grupo entero —más sensible que un
   caso individual—, así que también se excluyen. `area_operativa` **sí** se
   audita: es dato de planificación que escribe el coordinador, es la
   identidad del operativo, y sus cambios son justamente los que interesa
   rastrear. La segunda: `LogEntry.object_repr` sale de `str(instancia)` y
   **no pasa por la lista de exclusión**, así que el `__str__` de `Encuesta`
   —que devolvía el código del entrevistado— grababa ese identificador en cada
   entrada, además visible en `/admin/auditlog/logentry/`, que gatea con el
   permiso estándar de Django y no con el de `audittrail`. `__str__` pasa a
   devolver sólo el id; las dos pantallas que mostraban el código lo piden
   ahora de forma explícita, así que la UI no cambia.

9. **Ante un alcance territorial preexistente se rechaza, no se pisa.** La
   alternativa era derivar igual y avisar, o fusionar el alcance del rol con el
   que el usuario ya tenía. Las dos dejan al operador que asigna un rol de
   DataCalle decidiendo —sin saberlo— el acceso de ese usuario a comedores,
   admisiones y SIMEPI. Rechazar cuesta un guardado más (resolver el alcance
   aparte, a la vista) y no puede producir una ampliación ni una baja de
   acceso silenciosa en módulos ajenos.

10. **La validación de SIMEPI - EGP pasó a correr al final del `clean()`.**
    Corría antes que la de DataCalle, así que miraba los scopes del panel y no
    los que el rol deriva: a un coordinador nuevo con el grupo SIMEPI le
    reclamaba una provincia completa que la derivación iba a darle en el mismo
    guardado. Con el orden nuevo valida el alcance efectivo, que es el que se
    guarda.

## Pendiente

1. **El borrado lógico no queda auditado.** `SoftDeleteModelMixin` hace el
   borrado con `QuerySet.update()`, que no dispara las señales que usa
   `django-auditlog` para registrar cambios. Arreglarlo de raíz implica tocar
   `core/soft_delete/`, compartido por todas las apps del sistema, y por lo
   tanto excede esta rama. No hay pérdida de dato: la fila borrada conserva
   `deleted_by` y `deleted_at`.

~~2. `_roles_datacalle_para_el_actor` es fail-open cuando no hay actor.~~
**Resuelto en la revisión final de la rama (2026-09-19):** sin actor ofrece
sólo `entrevistador`. El superusuario y el administrador siguen viendo los
tres roles.

3. **La migración `0054` puede fallar en producción** si existe algún
   relevador con más de una provincia cargada. Falla temprano, antes de
   aplicar la constraint, y nombra los perfiles en conflicto en el mensaje de
   error; hay que resolverlos a mano antes de desplegar.

4. **En un entorno donde `0053` ya se aplicó, la reclasificación no vuelve a
   correr.** El forward es idempotente por diseño: saltea los perfiles que ya
   tienen rol. Un perfil provincial con alcance municipal que la versión
   anterior de la migración dejó como `administrador` sigue así hasta que
   alguien le vacíe el rol o se lo corrija a mano. En la base local hay un
   perfil en esa situación (`coord.nacional`, provincial y sin ningún scope
   cargado); en producción, donde la rama todavía no se desplegó, la migración
   corre por primera vez con el criterio corregido.

La reapertura de operativos (punto 8.3 del documento funcional) no se
implementó: el propio documento la deja "a definir".
