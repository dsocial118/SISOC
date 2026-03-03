# Usuarios de testing

Este listado se crea automaticamente por el comando:

```bash
python manage.py create_test_users
```

Solo se ejecuta si `DEBUG=True`.

## QA por persona y rol
Se crean usuarios para Juan, Agustina, Facundo y Camilo con los roles:
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

### Usuarios generados
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

## Superadmins
Usuarios con permisos de superadmin:
- `asampaulo`
- `fsuarez`
- `jalfonso`
- `cparra`

Password para todos: `1`
Email: `<username>@example.com`

## Notas
- Si el usuario ya existe, el comando actualiza email y password.
- El resto de usuarios de testing definidos en el comando se mantienen sin cambios.
