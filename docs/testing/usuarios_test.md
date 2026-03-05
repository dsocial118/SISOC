# Politica de usuarios de testing y grupos

Este documento describe **exactamente** lo que ejecutan los comandos:

- `users/management/commands/create_test_users.py`
- `users/management/commands/create_groups.py`

## Comando: create_groups

Ejecuta:

```bash
python manage.py create_groups
```

Comportamiento:
- Crea (si no existen) los grupos listados en `core.constants.UserGroups.CREATE_GROUPS_SEED`.
- No modifica ni elimina grupos existentes.

La lista completa de grupos se mantiene en `core/constants.py`.

## Comando: create_test_users

Ejecuta:

```bash
python manage.py create_test_users
```

Comportamiento:
- **Solo corre si `DEBUG=True`**.
- Si el usuario **no existe**, lo crea.
- Si el usuario **ya existe**, actualiza **email** y **password** y mantiene el usuario.
- Si se indican grupos, los crea si no existen y los asigna al usuario.

### Usuarios fijos

#### Superusuario base
- `1` (email `1@gmail.com`, password `1`, `is_superuser=True`)

#### QA historicos
- `abogadoqa` (password `qa1234`)
- `tecnicoqa` (password `qa1234`)
- `legalesqa` (password `qa1234`)
- `contableqa` (password `qa1234`)

#### Centro de Familia / Ciudadanos
- `CDF SSE` (password `8392017`)
- `FARO` (password `5823109`)
- `AD` (password `5823109`)

#### Celiaquia
- `TecnicoCeliaquia` (password `1`)
- `TecnicoCeliaquia2` (password `1`)
- `TecnicoCeliaquia3` (password `1`)
- `CoordinadorCeliaquia` (password `1`)
- `ProvinciaCeliaquia` (password `1`)

### Usuarios QA por persona y rol

Se crean usuarios para Juan, Agustina, Facundo y Camilo con estos roles:
- `legales`
- `abogado`
- `tec`
- `coordinador`
- `operador`
- `auditor`

Formato de usuario: `<nombre><rol>` en minusculas.
Ejemplos: `facundotec`, `juanabogado`, `agustinacoordinador`.

Password para todos: `1`
Email: `<username>@example.com`

Usuarios generados:
- `juanlegales`
- `juanabogado`
- `juantec`
- `juancoordinador`
- `juanoperador`
- `juanauditor`
- `agustinalegales`
- `agustinaabogado`
- `agustinatec`
- `agustinacoordinador`
- `agustinaoperador`
- `agustinaauditor`
- `facundolegales`
- `facundoabogado`
- `facundotec`
- `facundocoordinador`
- `facundooperador`
- `facundoauditor`
- `camilolegales`
- `camiloabogado`
- `camilotec`
- `camilocoordinador`
- `camilooperador`
- `camiloauditor`

### Superadmins QA

Usuarios con permisos de superadmin:
- `asampaulo`
- `fsuarez`
- `jalfonso`
- `cparra`

Password para todos: `1`
Email: `<username>@example.com`

## Grupos asignados por rol

### Abogado (`abogadoqa` y `*abogado`)
- `Abogado Dupla`
- `Acompanamiento Detalle`
- `Acompanamiento Listar`
- `Comedores`
- `Comedores Intervencion Crear`
- `Comedores Intervencion Editar`
- `Comedores Intervencion Ver`
- `Comedores Intervenciones Detalle`
- `Comedores Listar`

### Tecnico (`tecnicoqa` y `*tec`)
- `Acompanamiento Detalle`
- `Acompanamiento Listar`
- `Comedores`
- `Comedores Editar`
- `Comedores Intervencion Crear`
- `Comedores Intervencion Editar`
- `Comedores Intervencion Ver`
- `Comedores Intervenciones Detalle`
- `Comedores Listar`
- `Comedores Observaciones Crear`
- `Comedores Observaciones Detalle`
- `Comedores Observaciones Editar`
- `Comedores Observaciones Eliminar`
- `Comedores Relevamiento Detalle`
- `Comedores Ver`
- `Tecnico Comedor`

### Legales (`legalesqa` y `*legales`)
- `Comedores`
- `Area Legales`
- `Comedores Relevamiento Ver`
- `Comedores Relevamiento Detalle`
- `Comedores Observaciones Detalle`
- `Comedores Intervencion Ver`
- `Comedores Intervenciones Detalle`
- `Comedores Nomina Ver`
- `Acompanamiento Detalle`
- `Acompanamiento Listar`

### Contable (`contableqa`)
- `Comedores`
- `Area Contable`
- `Comedores Relevamiento Ver`
- `Comedores Relevamiento Detalle`
- `Comedores Observaciones Detalle`
- `Comedores Intervencion Ver`
- `Comedores Intervenciones Detalle`
- `Comedores Nomina Ver`
- `Acompanamiento Detalle`
- `Acompanamiento Listar`

### Coordinador (`*coordinador`)
- `Coordinador Equipo Tecnico`
- `Comedores`
- `Comedores Listar`
- `Comedores Ver`
- `Comedores Editar`
- `Comedores Relevamiento Ver`
- `Comedores Relevamiento Detalle`
- `Comedores Observaciones Crear`
- `Comedores Observaciones Detalle`
- `Comedores Observaciones Editar`
- `Comedores Observaciones Eliminar`
- `Comedores Intervencion Ver`
- `Comedores Intervencion Crear`
- `Comedores Intervencion Editar`
- `Comedores Intervenciones Detalle`
- `Comedores Nomina Ver`
- `Acompanamiento Detalle`
- `Acompanamiento Listar`

### Operador (`*operador`)
- `Comedores`
- `Comedores Listar`
- `Comedores Ver`
- `Comedores Relevamiento Ver`
- `Comedores Relevamiento Detalle`
- `Comedores Observaciones Crear`
- `Comedores Observaciones Detalle`
- `Comedores Observaciones Editar`
- `Comedores Intervencion Ver`
- `Comedores Intervencion Crear`
- `Comedores Intervencion Editar`
- `Comedores Intervenciones Detalle`
- `Comedores Nomina Ver`
- `Acompanamiento Detalle`
- `Acompanamiento Listar`

### Auditor (`*auditor`)
- `Comedores`
- `Comedores Listar`
- `Comedores Ver`
- `Comedores Relevamiento Ver`
- `Comedores Relevamiento Detalle`
- `Comedores Observaciones Detalle`
- `Comedores Intervencion Ver`
- `Comedores Intervenciones Detalle`
- `Comedores Nomina Ver`
- `Acompanamiento Detalle`
- `Acompanamiento Listar`

### Centro de Familia / Ciudadanos
- `CDF SSE`: `CDF SSE`, `Ciudadanos`
- `FARO`: `ReferenteCentro`, `Ciudadanos`
- `AD`: `ReferenteCentro`, `Ciudadanos`

### Celiaquia
- `TecnicoCeliaquia*`: `TecnicoCeliaquia`, `Ciudadanos`
- `CoordinadorCeliaquia`: `CoordinadorCeliaquia`, `Ciudadanos`
- `ProvinciaCeliaquia`: `ProvinciaCeliaquia`, `Ciudadanos`
