# Flujo: Derivación de beneficiarios entre centros

## Objetivo
Permitir transferir un beneficiario activo de la nómina de un centro hacia otro,
preservando el histórico en origen (estado `Baja`) y creando un nuevo registro
pendiente de validación en destino. Aplica tanto a `comedores.Nomina` como a
`centrodeinfancia.NominaCentroInfancia`.

## Entrada / Salida
- Entrada: POST AJAX a `nomina_derivar` (comedores) o `centrodeinfancia_nomina_derivar`,
  con `centro_destino_id` y `motivo` opcional. Evidencia: comedores/views/nomina.py,
  centrodeinfancia/views.py (función `nomina_centrodeinfancia_derivar`).
- Salida: respuesta JSON `{success, message}`. Para `success=True`, lado servidor:
  - `Nomina/NominaCentroInfancia` origen → `ESTADO_BAJA`.
  - Nuevo `Nomina` destino en `ESTADO_ESPERA` (comedores) / nuevo
    `NominaCentroInfancia` en `ESTADO_PENDIENTE` (CDI).
  - Auditoría: `NominaDerivacion` / `NominaCentroInfanciaDerivacion` con
    `nomina_origen`, `nomina_destino`, `comedor_origen`/`comedor_destino` (FK
    PROTECT), `usuario`, `fecha`, `motivo`. Evidencia: comedores/models.py,
    centrodeinfancia/models.py.

## Pasos
1. La vista valida que el usuario tiene acceso al origen vía
   `_get_nomina_scoped_or_404` / `_nomina_cdi_queryset_scoped`.
2. Parsea `centro_destino_id` (entero). Si no es válido devuelve 400 con `message`.
3. Llama al servicio:
   - Comedores: `ComedorService.transferir_ciudadano_entre_centros`.
   - CDI: `CentroDeInfanciaService.transferir_ciudadano_entre_centros`.
4. El servicio valida que el destino esté **dentro del scope del usuario**
   (`get_scoped_comedor_queryset` / `aplicar_scope_centros_cdi`). Si no, retorna
   `False` con mensaje neutro (no expone existencia del centro fuera de scope).
5. Si el comedor destino usa admisión, busca la última admisión activa; si no
   hay, rechaza con mensaje claro.
6. Verifica que la persona no tenga ya un registro `Activo`/`Espera` o
   `Activo`/`Pendiente` en destino.
7. Abre una transacción atómica:
   - Bloquea origen con `select_for_update()` y revalida estado y duplicado.
   - Marca origen como `BAJA`.
   - Crea destino con estado `ESPERA`/`PENDIENTE`. En CDI copia campos ricos
     desde el origen (`_CAMPOS_COPIABLES`: identidad, salud, domicilio,
     responsables, observaciones).
   - Registra la derivación.
8. Devuelve `(True, "Derivación realizada correctamente.")`.

## Validaciones y reglas
- Solo se puede derivar registros con estado `ESTADO_ACTIVO`.
- El destino debe ser distinto al origen.
- El usuario debe tener scope tanto sobre origen como sobre destino.
- Comedor destino con `programa.usa_admision_para_nomina=True` exige al menos
  una `Admision.activa=True`.
- Permisos requeridos en URL (ambos a la vez, `permissions_all_required`):
  - Comedores: `comedores.change_nomina` + `comedores.add_nomina`.
  - CDI: `centrodeinfancia.change_nominacentroinfancia` +
    `centrodeinfancia.add_nominacentroinfancia`.

## Side effects
- Cambio de estado del origen y creación del registro destino, todo bajo
  `transaction.atomic` con bloqueo de fila origen.
- Registro de auditoría inmutable (admin define `has_add_permission=False` y
  `has_change_permission=False`).
- FKs `comedor_origen`/`comedor_destino` con `on_delete=PROTECT` para impedir
  hard delete de centros con derivaciones asociadas (preservar trazabilidad).

## Errores comunes y debug
- `Centro destino no existe o no está dentro de tu alcance`: el centro no
  existe o el usuario no tiene scope sobre él.
- `El centro «X» no tiene una admisión activa`: el destino exige admisión y no
  hay ninguna activa.
- `La persona ya tiene un registro activo o en espera en «X»`: hay duplicado.
- `El registro fue modificado antes de completar la derivación`: TOCTOU
  detectado por la revalidación bajo lock.

## Selector del modal
- `comedores_para_derivar` se construye con `get_scoped_comedor_queryset(user)`
  más un filtro que excluye comedores con admisión sin ninguna admisión activa.
  Evidencia: comedores/views/nomina.py — helper `_comedores_destino_para_derivar`.
- `centros_para_derivar` se construye con `aplicar_scope_centros_cdi`.

## UI
- Templates: `comedores/templates/comedor/nomina_detail.html` y
  `centrodeinfancia/templates/centrodeinfancia/nomina_detail.html`.
- JS común: `static/custom/js/nomina_derivar.js` (ambos templates incluyen el
  mismo script). El payload POST usa la clave `centro_destino_id`.

## Decisiones de diseño
- Se eligió FK + PROTECT sobre IntegerField para los centros origen/destino del
  modelo de auditoría: priorizar integridad referencial sin perder histórico.
- El estado destino difiere entre módulos por nomenclatura propia del modelo:
  `ESTADO_ESPERA` en comedores, `ESTADO_PENDIENTE` en CDI. Semánticamente
  equivalente (pendiente de validación por el centro destino).
- La validación del scope del destino se hace **en la capa de servicio** para
  cerrar el flujo a usos no-HTTP (comandos, tareas async).

## Tests
- `comedores/test_derivar_service.py`: casos servicio (camino feliz directo,
  con admisión, fallas por estado/duplicado/admisión inexistente) + vistas
  AJAX (405 sin POST, 302/403 sin auth, 400 entrada inválida, 200 OK).
- `centrodeinfancia/tests/test_derivar_service.py`: análogos para CDI,
  incluyendo verificación de copia de campos ricos (incluye FK a Provincia).
