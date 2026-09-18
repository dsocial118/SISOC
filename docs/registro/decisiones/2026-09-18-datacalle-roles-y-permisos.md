# 2026-09-18 - DataCalle: tres roles explícitos, provincia única y acceso a la app para coordinadores

## Estado
- aceptada (implementada en `fix/datacalle-qa-2026-09`, 2026-09-18)

## Contexto

El área definió por escrito el esquema de roles de DataCalle/SISOC ("Definición
funcional de roles y permisos", 2026-09-18): **Administrador Nacional >
Coordinador Provincial > Relevador**, jerárquicos y decrecientes, con provincia
única para los dos roles provinciales y acceso a la app para los tres.

Buena parte ya está construida y verificada por QA: alcance provincial en
servidor (RN08), relevadores de la misma provincia que el operativo (RN04,
QA-0013), cierre sólo desde SISOC (RN06, QA-0020), operativo cerrado que no
admite casos (RN07), relevador sin acceso al backoffice (RN05), provincia
heredada al crear relevador (QA-0016), estados `planificado → en_curso →
finalizado` (8.4), y `creado_por` / `cerrado_por` con fechas (8.6 parcial).

Lo que **no** cuadra con el documento:

1. **El Administrador Nacional no existe como rol.** Hoy es "coordinador sin
   alcance provincial": mismo grupo `Coordinador DataCalle`, sin
   `territorial_scopes`. El flujo "Crear usuario → Rol → Provincia" y la regla
   "sólo el Admin crea coordinadores y elige provincia" necesitan un rol
   explícito.
2. **Coordinador y Admin no entran a la app.** `EsRelevadorCalle` exige
   `Profile.es_relevador_calle`, que sólo tiene el entrevistador. Y si se les
   pusiera el flag, el gate de login del backoffice
   (`BackofficeAuthenticationForm.confirm_login_allowed`) los echaría de SISOC,
   porque hoy "tiene el flag" significa "usuario sólo-app".
3. **Provincia única (RN01) no está en el modelo.** `RelevadorCalleProvincia`
   permite N provincias por relevador (`unique(profile, provincia)`); el
   coordinador usa `ProfileTerritorialScope`, también N. Dos tablas para la
   misma idea, ninguna con tope de una.
4. **Un coordinador podría crear coordinadores** si un admin le delega el grupo
   por `grupos_asignables`. El documento lo prohíbe de forma absoluta.
5. **Nadie provincial debe poder cambiar su propia provincia** (RN02). No hay
   regla para la auto-edición.
6. **8.6: no se registran las modificaciones del operativo ni quién las hizo.**
   `django-auditlog` está instalado y con middleware, pero `datacalle` no
   registra modelos.

## Decision

### D1. Una sola fuente de verdad para el rol: `Profile.datacalle_rol`

`Profile.DataCalleRol` pasa de un valor a tres:

| Código | Etiqueta | SISOC | App |
|---|---|---|---|
| `administrador` | Administrador Nacional | sí, todo el país | sí, todo el país |
| `coordinador` | Coordinador Provincial | sí, su provincia | sí, su provincia |
| `entrevistador` | Relevador | **no** | sí, sus operativos |

- `datacalle_rol` es **el** rol DataCalle del usuario, para los tres. Vacío =
  no es usuario DataCalle.
- `Profile.es_relevador_calle` **se conserva como columna** pero cambia de
  semántica: deja de significar "usuario sólo-app" y pasa a significar
  "tiene acceso a DataCalle" (los tres roles lo tienen en `True`). Se mantiene
  para no romper el contrato D1 (`/api/users/me/` lo expone) ni la migración;
  los lectores dejan de usarlo para decidir *qué* puede hacer el usuario.
- Los permisos del backoffice siguen siendo **grupos Django**: se agrega el
  grupo `Administrador DataCalle` a la semilla (mismos permisos de datacalle y
  auth que el coordinador; el alcance nacional sale de no tener
  `territorial_scopes`). El formulario de usuarios, al elegir el rol, asigna el
  grupo y el alcance solo: el operador elige un rol, el sistema arma el resto.
- **Migración de datos** para los usuarios que ya existen: quien tenga el grupo
  `Coordinador DataCalle` pasa a `datacalle_rol = "coordinador"` si tiene
  `territorial_scopes`, o `"administrador"` si no tiene ninguno; ambos con
  `es_relevador_calle = True`. Los entrevistadores actuales no cambian. Es
  reversible (la reversa vacía el rol y el flag sólo a los que la migración
  tocó).
- Helpers nuevos en `users/services_datacalle.py`, que reemplazan a los
  actuales en todos los lectores: `get_datacalle_rol(user)`,
  `tiene_acceso_datacalle(user)`, `es_administrador_datacalle(user)`,
  `es_coordinador_datacalle(user)` (rol `coordinador` **o** `administrador`,
  porque la jerarquía es decreciente), `es_solo_app(user)` (rol
  `entrevistador`). `es_coordinador_calle()` se conserva como alias del
  segundo hasta que no quede ningún uso.

### D2. Acceso a SISOC y a la app según el rol, no según el flag

- **Login backoffice** (`confirm_login_allowed`): rechaza sólo a
  `es_solo_app(user)`. Coordinador y administrador entran.
- **Login API** (`UserLoginViewSet`): habilita a `tiene_acceso_datacalle(user)`
  (los tres roles), además de los accesos PWA que ya existen.
- **API de DataCalle**: `EsRelevadorCalle` pasa a `TieneAccesoDataCalle`.
- **Tareas (`GET /relevamientos/`)**: `mis_relevamientos(user)` se vuelve
  jerárquico: entrevistador → operativos donde está en `equipo`
  (comportamiento actual, 8.1 se mantiene: **asignados expresamente**);
  coordinador → todos los operativos de su provincia; administrador → todos.
  Cargar un caso sigue exigiendo que el operativo esté en esa lista, así que
  un coordinador puede relevar en su provincia sin estar en el equipo.
- **Cierre por API** (`POST …/cerrar/`): la guardia de QA-0020 pasa a usar
  `es_coordinador_datacalle(user)` **y** a exigir que el operativo esté en su
  alcance (`RelevamientoViewSet.get_object()` ya lo garantiza vía
  `mis_relevamientos`). Sigue devolviendo 403 `cierre_no_autorizado` al
  entrevistador.

### D3. Provincia única (RN01), incremental

- `RelevadorCalleProvincia`: nueva constraint `UniqueConstraint(fields=["profile"])`.
  La migración **verifica antes** que no haya perfiles con más de una fila y
  aborta con mensaje claro si los hay (en la base local hay cero; en
  producción se corre el mismo chequeo antes de desplegar).
- Coordinador: su alcance vive en `ProfileTerritorialScope`, tabla compartida
  con otros roles del backoffice que sí admiten varias provincias, así que
  **no se constrainea**: se valida en el formulario y en el servicio que un
  usuario con rol `coordinador` tenga exactamente un scope de provincia
  completa.
- Lector único `get_datacalle_provincia(user) -> Provincia | None` que
  reemplaza a `get_relevador_calle_provincia_ids` y a las lecturas directas de
  `get_full_province_scope_ids` en `datacalle/`. Devuelve `None` para el
  administrador (alcance nacional).
- `/api/users/me/` sigue exponiendo `datacalle_provincias` como lista (contrato
  D1.2); pasa a ser una lista de un elemento o vacía. **No se rompe la app.**
- Colapsar las dos tablas en un FK único queda **fuera de esta decisión**: es
  refactor y se hará aparte cuando esto esté estable.

### D4. Jerarquía dura en el servidor (RN02, RN03, RN08)

Todo en `clean()` del formulario **y** en el servicio de guardado, nunca sólo
en el template:

- Sólo `es_administrador_datacalle(actor)` o superusuario puede fijar rol
  `coordinador` o `administrador`, y elegir provincia libremente.
- Un coordinador sólo puede crear/editar usuarios con rol `entrevistador`, y la
  provincia se hereda de la suya (QA-0016, que ya existe, pasa a ser regla y
  no ajuste de pantalla). No ve selector de provincia ni de rol superior.
- Un usuario provincial que edita su propio perfil no puede cambiar su
  provincia (el campo llega `disabled` y el servicio ignora el valor).
- Esta regla es **más angosta y prioritaria** que la delegación genérica
  (`grupos_asignables`): aunque un admin delegue el grupo `Coordinador
  DataCalle` a un coordinador, el servicio rechaza la asignación.

### D5. Trazabilidad (8.6)

`auditlog.register(Relevamiento)` y `auditlog.register(Encuesta)` en
`datacalle/apps.py`. Con eso queda quién modificó qué y cuándo, además de lo
que ya existe (`creado_por`, `created_at`, `cerrado_por`, `fecha_cierre`).

### D6. Fuera de alcance, a propósito

- **8.3 Reapertura**: el documento la deja "a definir". No se implementa nada;
  hoy un operativo `finalizado` no vuelve atrás salvo edición manual del
  estado por un superusuario.
- **8.2 Visibilidad de casos dentro de la app**: es de la app; SISOC ya
  devuelve `relevador_id` en cada caso para que la app decida.
- **QA-0015 (taxonomía)** queda resuelto de raíz por D1: el selector "Rol en
  DataCalle" pasa a tener los tres roles del documento, y "Tipo de usuario"
  deja de competir con él.

## Consecuencias

**Positivas**
- El documento funcional y el código dicen lo mismo: tres roles con nombre,
  una provincia, jerarquía decreciente aplicada en servidor.
- Coordinador y administrador pueden relevar en campo sin un segundo usuario.
- QA-0015 se cierra de verdad, no con texto de ayuda.

**Costos y riesgos**
- **Migración con constraint** sobre `RelevadorCalleProvincia`: si producción
  tiene relevadores con más de una provincia, hay que resolverlos a mano antes
  de desplegar. El chequeo previo está en la migración para que falle
  temprano y con mensaje.
- **Cambio de semántica de `es_relevador_calle`**: todo lector que lo usara
  como "es sólo-app" (login backoffice, `RelevadorCalleFormMixin`) tiene que
  pasar por los helpers nuevos. Se buscan y se cambian todos en esta rama; los
  tests de `test_datacalle_qa_usuarios.py` cubren los caminos.
- **Contrato D1**: `datacalle_rol` en `/api/users/me/` puede valer ahora
  `coordinador` o `administrador`. Es aditivo (la app hoy sólo mira si es
  truthy), pero se avisa en el canal de coordinación.
- El PR de la rama crece: pasa de fixes de QA a fixes + roles. Decisión del
  responsable del módulo (2026-09-18), para desplegar todo junto.

## Referencias
- Documento funcional del área: "Definición funcional de roles y permisos
  DataCalle / SISOC" (2026-09-18), recibido por el canal de coordinación.
- `docs/registro/cambios/2026-09-16-datacalle-qa-alcance-provincial.md`
- `docs/registro/cambios/2026-09-17-datacalle-qa-segundo-bloque.md`
- Canal: `Desktop/COORDINACION-DATACALLE-SISOC.md`, §D2.1 (roles y alcance).
- Código de partida: `users/models.py` (`DataCalleRol`, `RelevadorCalleProvincia`),
  `users/services_datacalle.py`, `users/forms.py` (`RelevadorCalleFormMixin`,
  `confirm_login_allowed`), `datacalle/api_permissions.py`,
  `datacalle/api_views.py` (`mis_relevamientos`), `users/bootstrap/groups_seed.py`.
