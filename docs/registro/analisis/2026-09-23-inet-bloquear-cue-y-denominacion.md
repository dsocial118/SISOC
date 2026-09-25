# REQ — Bloquear la edición de CUE y Denominación de la institución

| | |
|---|---|
| **Tipo** | Control de acceso / integridad de datos |
| **Sistema / Módulo** | SISOC — INET/VAT, edición del legajo de Centro |
| **Estado** | Implementado |

## Situación actual

En *Editar Centro de Formación Profesional* → **Datos de la institución**, los
campos **Denominación de la institución** (`nombre`) y **Clave Única de
Establecimiento (CUE)** (`codigo`) son editables por los perfiles de CFP.

Son datos identificatorios del establecimiento: modificarlos por error rompe la
trazabilidad y puede duplicar o desviar el legajo.

Hoy existe un bloqueo **parcial**: `CentroForm` ya deja el CUE de solo lectura,
pero únicamente para el perfil INET_PROVINCIA y sobre legajos existentes
(`VAT/forms.py:901-903`):

```python
if _is_inet_provincia_actor(actor) and self.instance and self.instance.pk:
    _lock_fields_readonly(self, ["codigo", "provincia"])
```

La denominación no está bloqueada para ningún perfil.

## Objetivo

Que ambos campos queden **visibles pero no editables** para los perfiles de CFP,
conservando la edición para los perfiles de administración.

## Roles alcanzados

El bloqueo aplica a los usuarios que pertenezcan a estos grupos:

| Grupo | Perfil |
|---|---|
| `CFP` | Referente del centro |
| `CFPJuridicccion` | Jurisdicción |
| `CFPRevisor` | Revisor del centro |

> ⚠️ **Atención al nombre del grupo.** En el sistema está escrito
> **`CFPJuridicccion`** (así, con "Juridic" y tres "c"), no `CFPJurisdiccion`.
> Es el nombre canónico en `core/permissions/registry.py:145` y el que usa el
> comando que crea los grupos. Si se escribe corregido, el bloqueo **no aplica
> y falla en silencio**, porque no coincide con ningún grupo existente.

Los demás grupos con permiso de edición de centro (`CFPINET`, `Provincia VAT`,
`VAT SSE`) **conservan** la edición. Conviene confirmar que sea lo esperado.

## Cómo extender el bloqueo a otros roles

La lista se define como una constante a nivel de módulo en `VAT/forms.py`, junto
a las que ya existen (`REFERENTE_GROUP_NAMES`, `REVISOR_GROUP_NAMES`):

```python
# Grupos que NO pueden editar la identificación del centro (nombre y CUE).
IDENTIFICACION_CENTRO_BLOQUEADA_GROUP_NAMES = (
    "CFP",
    "CFPJuridicccion",
    "CFPRevisor",
)
```

**Para sumar otro rol al bloqueo alcanza con agregar el nombre de su grupo a esa
tupla.** No hay que tocar nada más.

Si más adelante se prefiere administrarlo sin tocar código, la alternativa es
crear un permiso (por ejemplo `auth.role_editar_identificacion_centro`),
otorgarlo a quienes sí deban editar y evaluarlo con `user_has_permission_code()`,
como ya se hace con `ROLE_INET_PROVINCIA_PERMISSION`. Queda como opción, no
como parte de este requerimiento.

## Alcance

| Capa | A modificar |
|---|---|
| `VAT/forms.py` | `CentroForm.__init__`: bloquear `nombre` y `codigo` según el grupo del actor |

La infraestructura ya está disponible y **debe reutilizarse**:

- `_lock_fields_readonly()` (`VAT/forms.py:285`) deshabilita campos dejándolos
  visibles.
- `CentroForm.__init__` ya recibe `actor` vía `kwargs.pop("actor", None)`.

**No incluye** cambios de modelo, migraciones ni la validación de CUE (unicidad,
formato numérico y prefijo provincial siguen igual).

## Requerimiento funcional

1. En la **edición** de un centro existente, `nombre` y `codigo` se muestran
   deshabilitados si el usuario pertenece a alguno de los grupos alcanzados.
2. Los campos siguen **visibles**: se usa `_lock_fields_readonly()`, no
   `_hide_and_lock_fields()` ni la eliminación del campo.
3. El bloqueo aplica **solo a la edición**. En el alta de un centro ambos campos
   deben poder cargarse, o no se podría crear un legajo. La condición
   `self.instance and self.instance.pk` que ya usa el código cubre este caso.
4. El bloqueo existente del CUE para INET_PROVINCIA **se mantiene**: ese perfil
   no está en los grupos alcanzados, así que si se lo quitara perdería una
   restricción que hoy tiene.
5. Para los perfiles no alcanzados, ambos campos siguen siendo editables con las
   validaciones actuales.

## Criterios de aceptación

- [ ] Un usuario de `CFP`, `CFPJuridicccion` o `CFPRevisor` ve ambos campos pero
      no puede editarlos.
- [ ] Un usuario de administración (p. ej. `CFPINET`) puede editarlos y guardar.
- [ ] El alta de un centro sigue permitiendo cargar denominación y CUE.
- [ ] Un POST manipulado que intente cambiar esos campos desde un perfil
      bloqueado **no** modifica los valores guardados.
- [ ] El CUE sigue bloqueado para INET_PROVINCIA, como hasta ahora.
- [ ] Las validaciones de CUE (unicidad, 9 dígitos, prefijo provincial) siguen
      funcionando para quien sí puede editar.

## Riesgos

- **El bloqueo no puede ser solo visual.** `field.disabled = True` ya lo
  resuelve en servidor: Django ignora el valor que venga en el POST y conserva
  el inicial. Un `readonly` de HTML sería evadible.
- **Nombre de grupo mal escrito.** Ver la advertencia sobre `CFPJuridicccion`:
  un error de tipeo desactiva el bloqueo sin dar ningún error.
- El bloqueo es a nivel de formulario. Si existen otras vías de modificación
  (importación masiva por Excel `import_vat_centros_excel`, endpoints de API,
  admin de Django), hay que definir si también deben restringirse.
