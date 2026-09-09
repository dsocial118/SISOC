# Celiaquía: un menor no puede quedar sin adulto responsable

## Problema

Al dar de baja el legajo del adulto responsable antes de enviar el expediente, el
legajo del menor seguía adentro y el envío se confirmaba sin ninguna alerta. El
expediente llegaba a Nación con un menor sin responsable asociado.

La regla "todo beneficiario menor de 18 debe tener un responsable" ya existía en
`ValidacionEdadService.validar_beneficiario_menor_con_responsable`, pero sólo se
aplicaba durante la importación (carga del Excel masivo y reproceso de
`RegistroErroneo`). Después de importar no volvía a ejecutarse nunca.

El agujero es doble:

- `ExpedienteService.confirmar_envio` sólo validaba estado `EN_ESPERA` y
  documentación completa (`all_legajos_loaded`); la vista sumaba registros
  erróneos pendientes y archivos faltantes. Ninguna miraba la relación familiar.
- La validación de archivos tampoco lo tapaba por accidente: los archivos
  requeridos de un beneficiario menor (Biopsia + Foto DNI) no dependen del
  responsable, así que el legajo del menor quedaba con `archivos_ok=True`.

La causa de fondo es dónde vive el vínculo. `ciudadanos.GrupoFamiliar` cuelga del
**ciudadano**, no del legajo, y el borrado del legajo es un soft delete en
cascada que no lo toca. El menor no queda "sin vínculo": queda con un responsable
que ya no tiene legajo vivo en el expediente. Por eso ninguna consulta lo
detectaba.

## Solución

Un método nuevo, `ValidacionEdadService.menores_sin_responsable(expediente)`,
devuelve los legajos de menores de 18 cuyo responsable no tiene legajo vivo en
ese expediente. El corte es "el responsable tiene legajo vivo acá", no "existe el
vínculo". Acepta `excluir_legajo_ids` para simular una baja antes de ejecutarla.

Se aplica en tres puntos:

1. **Bloqueo al enviar**, en `ExpedienteConfirmView` (mensaje con los afectados y
   `menores_sin_responsable_ids` en el JSON) y también en
   `ExpedienteService.confirmar_envio`, para que ningún otro llamador pueda
   saltear la regla. El texto lo arma `mensaje_menores_sin_responsable`, único
   para los dos.
2. **Aviso al eliminar**, en el preview de baja que el front ya pedía antes de
   confirmar. `advertencia_por_eliminacion` devuelve sólo el **delta**: los
   menores que quedan huérfanos *por esta baja*, sin atribuirle los que ya lo
   estaban.
3. **Badge en el detalle** del expediente, sobre la fila del menor afectado,
   reutilizando el estilo `alerta-intermitente` que ya usan los avisos de edad.

## Decisiones

**La eliminación avisa, no bloquea.** El ticket era ambiguo entre las dos cosas.
Bloquear la baja dejaría trabada a la provincia que quiere dar de baja al grupo
familiar completo: no podría borrar al responsable por tener un menor a cargo, y
tendría que borrar primero al menor y reintentar. Además es coherente con cómo ya
funciona la documentación faltante en la misma pantalla: se avisa, y frena recién
en el envío.

**Sin fecha de nacimiento se asume mayor de edad**, en línea con
`validar_beneficiario_menor_con_responsable` y con el cálculo de archivos
requeridos de `LegajoService`. Un dato faltante no debe bloquear un expediente.

**Cuenta como responsable válido cualquier ciudadano vinculado como cuidador
principal con legajo vivo en el expediente**, sin exigir un rol determinado. La
validación bloquea el envío, y un falso positivo frenaría un expediente legítimo.

**El endpoint `legajo_eliminar` también quedó cubierto.** `LegajoEliminarView`
está montada en `urls.py` pero ningún template ni JS la usa: el borrado real de
la UI va por `RevisarLegajoView` con `accion=ELIMINAR`. Se le agregó el mismo
aviso para que no quede como bypass silencioso si alguien la vuelve a enganchar.

## Efecto colateral: `calcular_edad`

`ValidacionEdadService.calcular_edad` calculaba la edad como `días // 365`, que
por los bisiestos acumulados adelantaba el cumpleaños hasta 4 días: una persona
de 17 años y 362 días daba 18. Justo el borde que le importa a esta regla. Pasó a
comparar `(mes, día)`, igual que el filtro `edad` de los templates y que
`LegajoService.get_archivos_requeridos_por_legajo`.

Esto también corrige, en esos 4 días de borde, la validación de importación que
rechaza responsables menores de 18.

## Alcance de datos: medido en producción (2026-09-09)

La validación corre sólo en el paso `EN_ESPERA → envío`, así que no afecta
expedientes ya enviados ni requiere migración. Se midió el impacto en producción
antes de mergear, con consultas de sólo lectura sobre
`celiaquia_expedienteciudadano`, `celiaquia_expediente` y
`ciudadanos_grupofamiliar`.

Resultado: **cero expedientes bloqueados**.

- Expedientes vivos por estado: 68 `CRUCE_FINALIZADO`, 26 `ASIGNADO` y **1 solo
  en `EN_ESPERA`**. La validación tiene hoy un único expediente donde puede
  actuar, así que el riesgo de rollout es nulo.
- Ese expediente tiene 4 legajos, los 4 con fecha de nacimiento cargada y
  ninguno menor de 18. No hay `sin_fecha_nacimiento`, así que la puerta de
  escape (sin fecha se asume mayor) no está tapando nada.
- `ciudadanos_grupofamiliar`: 679 vínculos vivos, **los 679 con
  `cuidador_principal = 1`**, ninguno en 0.

Ese último número era el riesgo real y quedó descartado. La app entiende por
responsable una fila con `cuidador_principal = 1` — criterio de toda
`FamiliaService`, y `crear_relacion_responsable_hijo` (la que usa la importación)
siempre lo deja en 1. Si en producción hubiera vínculos con el flag en 0, la
validación habría bloqueado expedientes que sí tienen adulto (falso positivo) o,
peor, no habría detectado nada cuando el caso ocurriera (falso negativo
silencioso). No hay ninguno: el criterio describe bien los datos reales.

La base local es el caso opuesto — los hijos del expediente QA-1947 tienen el
vínculo con la madre en 0 — pero es dato de prueba cargado a mano, no
representativo de producción.

## Pendiente de producto

El caso inverso quedó fuera: si se da de baja al menor, el responsable puro queda
solo en el expediente sin ocupar cupo ni entrar al padrón, es decir un legajo
inútil. No estaba en el ticket. Hay que definir si también merece aviso.
