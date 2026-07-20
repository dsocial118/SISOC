# Guía de testeo — Nuevos roles SIMEPI / CDI (issue #2038, PR #2078)

> Para perfil QA / funcional. Sin tecnicismos: hablamos de roles, pantallas, botones y resultados esperados.

> **Aclaración importante antes de empezar.** El pedido original mencionaba solo "fases 1 a 3".
> En la práctica el PR #2078 ya está **fusionado (merged)** e incluye **las 7 fases completas**.
> Es decir: lo que en el pedido figuraba como "todavía no está" (alta automática del referente,
> alta automática de trabajadores, sincronización de email, y el recorte de qué ve cada rol)
> **sí está implementado** en este PR. Por eso esta guía cubre **todo lo entregado**, y al final
> aclara lo que sí quedó genuinamente afuera.

---

## 1. Qué se pidió

El sistema **SIMEPI** administra los **CDI** (Centros de Desarrollo Infantil). Hasta ahora no había
roles propios para este programa: se necesitaba un conjunto de roles nuevos y una forma **ordenada**
de que cada rol pueda dar de alta usuarios de los niveles de abajo, sin saltarse escalones. A esa
lógica de "quién puede crear a quién" la llamamos **cascada de altas**.

> Nota: el título del issue dice "Centros de Familia", pero el módulo real es **CDI**
> (Centros de Desarrollo Infantil) del programa **SIMEPI**.

### Los 7 roles

| Rol | Para qué sirve |
|---|---|
| **Administrador SISOC** | Administra todo el sistema (rol técnico general, por encima de SIMEPI). |
| **Administrador SIMEPI** | Máximo responsable del programa SIMEPI. Da de alta al Equipo Nacional. |
| **Equipo Nacional** | Coordina a nivel país. Da de alta a los referentes provinciales (EGP), analistas y auditores. |
| **Analista de datos** | Consulta y trabaja los datos de CDI a nivel nacional. No da de alta usuarios. |
| **Auditoría** | Mira todo a nivel nacional, pero **solo lectura**: no puede modificar nada. |
| **EGP (Referente provincial)** | Responsable de una **provincia**. Da de alta a los referentes de centro de su provincia. Solo ve su provincia. |
| **Referente de centro** | Responsable de un **CDI puntual**. Da de alta a los trabajadores de su centro. Solo ve su centro. |
| **Trabajador** | Personal del CDI. Acceso de consulta a su centro. |

### La cascada de altas (quién puede crear a quién)

```
Administrador SIMEPI
      └── crea → Equipo Nacional
                      └── crea → EGP (referente provincial)
                      └── crea → Analista de datos
                      └── crea → Auditoría
                                   
EGP (referente provincial)
      └── crea → Referente de centro

Referente de centro
      └── crea → Trabajador
```

Regla de oro: **cada rol solo puede asignar los roles inmediatamente por debajo suyo.** No puede
"saltar" niveles (por ejemplo, el Equipo Nacional no puede crear directamente un Referente de centro
ni un Administrador).

---

## 2. Qué se resolvió en este PR

- **Se crearon los 7 roles** con sus permisos correspondientes.
- **La cascada funciona en vivo**: cuando un usuario va a crear a otro, la lista de roles que puede
  asignar se arma automáticamente según su propio rol. No aparecen roles que no le corresponden.
- **Pantalla nueva para dar de alta un Referente Provincial (EGP)**: obliga a **elegir una provincia**.
  Ese usuario quedará atado a esa provincia y solo verá esa provincia. Se accede desde la barra lateral
  izquierda en **Legajos → Centro de Infancia → Alta de referente EGP**.
- **Los roles nacionales** (Equipo Nacional, Analista de datos, Auditoría) se crean desde la pantalla
  de usuarios de siempre (Administración → Usuarios).
- **Alta automática del referente de centro**: al guardar un CDI con nombre, apellido y email de
  referente completos, se crea automáticamente su usuario Referente de centro.
- **Alta automática de trabajadores**: al cargar la nómina del CDI, cada trabajador con email recibe
  su propia cuenta de Trabajador.
- **Sincronización de email**: si se cambia el email del referente o de un trabajador y se guarda,
  la cuenta se actualiza sola.
- **Recorte de alcances (qué ve cada rol)**:
  - EGP ve **solo su provincia**.
  - Referente de centro ve **solo su centro**.
  - Trabajador ve **solo su centro**.
  - Auditoría ve todo a nivel nacional, pero **no puede modificar nada** (solo lectura).
  - Administrador SIMEPI, Equipo Nacional y Analista tienen alcance nacional.

---

## 3. Cómo probarlo, paso a paso

### 3.1 Preparación del entorno

Levantar el sistema y dejar los roles disponibles (copiar/pegar):

```bash
docker compose up
docker compose exec django python manage.py migrate
docker compose exec django python manage.py sync_group_permissions_from_registry
```

Después, crear los usuarios de prueba. Podés hacerlo desde el **panel de administración** o desde la
pantalla **Administración → Usuarios**. Creá al menos uno de cada rol para poder probar:

- 1 usuario **Administrador SIMEPI**
- 1 usuario **Equipo Nacional**
- 1 usuario **Analista de datos**
- 1 usuario **Auditoría**
- 1 usuario **EGP** atado a una provincia (o crealo con la prueba B de abajo)

> Tip: para probar la cascada real conviene que cada usuario tenga **exactamente un** rol asignado.

Anotá el usuario y contraseña de cada uno para ir entrando y saliendo.

---

### 3.2 Casos de prueba

#### Caso A — El Equipo Nacional ve la opción de alta de EGP

- **Entrar como:** Equipo Nacional.
- **Ir a:** barra lateral izquierda → **Legajos → Centro de Infancia**.
- **Qué hacer:** desplegar el submenú **"Centro de Infancia"**.
- **Resultado esperado:** dentro aparece la opción **"Alta de referente EGP"** (además de "Ver Centros de Infancia").

---

#### Caso B — Crear un EGP eligiendo provincia

- **Entrar como:** Equipo Nacional.
- **Ir a:** **Legajos → Centro de Infancia → Alta de referente EGP**.
- **Qué hacer:** completar Nombre, Apellido, Email y **elegir una Provincia**. Guardar.
- **Resultado esperado:**
  - Aparece una pantalla de confirmación con la **contraseña temporal** del nuevo usuario
    (y el aviso de si se le envió el email con las credenciales).
  - El usuario nuevo queda con rol **EGP**.
  - El usuario nuevo queda **atado a la provincia elegida**.
- **Dónde verificar:** en el listado de usuarios (Administración → Usuarios) el usuario nuevo figura
  con el grupo "SIMEPI - EGP" y su provincia asignada.

---

#### Caso C — Crear un EGP SIN elegir provincia (debe fallar)

- **Entrar como:** Equipo Nacional.
- **Ir a:** **Legajos → Centro de Infancia → Alta de referente EGP**.
- **Qué hacer:** completar Nombre, Apellido y Email, pero **dejar la Provincia vacía**. Intentar guardar.
- **Resultado esperado:** el formulario **no deja continuar**, marca la provincia como obligatoria y
  **no se crea ningún usuario**.

---

#### Caso D — El Equipo Nacional solo puede asignar EGP / Analista / Auditoría

- **Entrar como:** Equipo Nacional.
- **Ir a:** Administración → Usuarios → crear/editar un usuario.
- **Qué hacer:** mirar la lista de roles disponibles para asignar.
- **Resultado esperado:** solo aparecen **EGP, Analista de datos y Auditoría**.
  **No** aparecen Administrador (ni SISOC ni SIMEPI) ni Referente de centro ni Trabajador.

---

#### Caso E — El Administrador SIMEPI solo puede crear Equipo Nacional

- **Entrar como:** Administrador SIMEPI.
- **Ir a:** Administración → Usuarios → crear/editar un usuario.
- **Qué hacer:** mirar la lista de roles disponibles para asignar.
- **Resultado esperado:** solo aparece **Equipo Nacional**. No puede crear EGP directamente
  (eso lo hace el Equipo Nacional).

---

#### Caso F — EGP y Analista NO ven la opción "Alta de referente EGP" (ni entrando por URL)

- **Entrar como:** EGP (y repetir con Analista de datos).
- **Ir a:** barra lateral izquierda → **Legajos → Centro de Infancia**.
- **Resultado esperado:** el submenú "Centro de Infancia" puede verse (tienen permiso de consulta),
  pero **no aparece** la opción **"Alta de referente EGP"**.
- **Prueba extra (por URL):** pegar en el navegador la dirección de la pantalla de alta de EGP
  (`.../simepi/egp/generar-usuario/`).
- **Resultado esperado:** el sistema responde **"acceso denegado"** (no deja entrar).

---

#### Caso G — Alta automática del referente al guardar el CDI

- **Entrar como:** EGP (de la provincia del CDI) o superusuario.
- **Ir a:** el detalle/edición de un CDI.
- **Qué hacer:** completar los datos del referente del CDI (**nombre, apellido y email**) y guardar.
- **Resultado esperado:** se crea automáticamente un usuario **Referente de centro** vinculado a ese CDI.
- **Verificar además:**
  - Si se guarda de nuevo, **no se duplica** el usuario ni el acceso.
  - Si falta el email, el CDI **igual se guarda** y se muestra un mensaje explicando que no se pudo crear la cuenta.

---

#### Caso H — Alta automática de trabajadores al cargar la nómina

- **Entrar como:** Referente de centro (o quien cargue la nómina).
- **Ir a:** la nómina del CDI.
- **Qué hacer:** cargar trabajadores **con email**.
- **Resultado esperado:** cada trabajador con email recibe **su propia cuenta** de Trabajador,
  aunque dos compartan la misma dirección de correo (cada uno tiene su cuenta).

---

#### Caso I — Sincronización de email

- **Entrar como:** quien edite el CDI o la nómina.
- **Qué hacer:** cambiar el email del referente (o de un trabajador) y guardar.
- **Resultado esperado:** la cuenta correspondiente queda actualizada con el nuevo email.
  Si el email se deja vacío, se limpia. (La sincronización solo corre cuando efectivamente **cambió**
  el email en ese guardado.)

---

#### Caso J — Alcances: cada rol ve solo lo suyo

- **EGP:** entra a los listados de Centros de Infancia → ve **solo los CDI de su provincia**.
- **Referente de centro:** ve **solo su centro**.
- **Trabajador:** ve **solo su centro**.
- **Auditoría:** ve todo a nivel nacional pero, al intentar **modificar** un CDI, trabajador, nómina o
  formulario, **el sistema no se lo permite** (solo lectura). Probar tocando un botón de editar/guardar
  y confirmar que no puede.
- **Administrador SIMEPI / Analista / Equipo Nacional:** ven a nivel **nacional**.

---

### 3.3 Dónde ver los resultados

- **Listado de usuarios:** Administración → Usuarios (rol/grupo asignado y provincia).
- **Grupo asignado:** en el detalle de cada usuario.
- **Provincia / centro:** en el detalle del usuario y en el vínculo con el CDI.
- **Contraseña temporal:** se muestra en la pantalla de confirmación al crear el usuario.

---

## 4. Lo que quedó genuinamente afuera / a mirar con cuidado

> Recordatorio: a diferencia del pedido original, la alta automática de referente y trabajadores, la
> sincronización de email y el recorte de alcances **SÍ están** en este PR (ver casos G, H, I y J).
> Lo que sigue son los límites reales que conviene tener presentes al testear:

- **Robustez del "no rompe nada":** el diseño garantiza que guardar un CDI **nunca falle** aunque no se
  pueda crear la cuenta (falta email, email repetido, sin permisos). Vale la pena verificar estos
  bordes: sin email, email ya usado por otra cuenta, y guardar dos veces (no debe duplicar).
- **Auditoría solo lectura:** confirmar que Auditoría no pueda modificar por **ningún camino**
  (ni botones ni pantallas), no solo en el listado principal.
- **Alcance provincial estricto del EGP:** verificar que un EGP no vea ni pueda tocar CDI de **otra**
  provincia (probar entrando por URL a un CDI de otra provincia → debe dar no encontrado / acceso denegado).
- **Roles fuera de SIMEPI:** el "Administrador SISOC" es un rol técnico general del sistema, previo a
  este trabajo; no forma parte de la cascada SIMEPI y no se testea acá.

---

### Resumen de resultados esperados (checklist rápido)

| # | Caso | Resultado esperado |
|---|---|---|
| A | Equipo Nacional → sidebar | Ve "Alta de referente EGP" en Legajos → Centro de Infancia |
| B | Crear EGP con provincia | Usuario EGP + provincia + contraseña temporal |
| C | Crear EGP sin provincia | No deja / no crea |
| D | Equipo Nacional asigna roles | Solo EGP / Analista / Auditoría |
| E | Admin SIMEPI asigna roles | Solo Equipo Nacional |
| F | EGP/Analista y "Alta de referente EGP" | No la ven; por URL → acceso denegado |
| G | Guardar CDI con referente | Crea Referente de centro (no duplica) |
| H | Cargar nómina con email | Crea cuenta por trabajador |
| I | Cambiar email y guardar | Sincroniza la cuenta |
| J | Alcances por rol | EGP=provincia, Referente/Trabajador=centro, Auditoría=solo lectura |
