# 2026-03-10 - Integridad nómina por admisión en comedores

## Contexto
Se ajustó el flujo de nómina migrado de `comedor` a `admision` para corregir tres riesgos detectados en revisión de PR:
- importación desde convenio incorrecto,
- cruce inconsistente `comedor/admisión` en URLs web,
- migración que podía dejar registros de nómina sin vínculo funcional.

## Cambios aplicados

### 1) Validación de pertenencia `admision_pk` al `pk` de comedor
- Archivo: `comedores/views/nomina.py`
- Se agregó helper `_get_admision_del_comedor_or_404` y se usa en:
  - `NominaDetailView`
  - `NominaCreateView`
  - `NominaImportarView`
- Se acotó `NominaDeleteView.get_queryset()` para permitir borrar sólo registros de la admisión/comedor de la URL.

Resultado: ante URL cruzada entre comedor y admisión, la respuesta ahora es `404`.

### 2) Importar desde admisión anterior real
- Archivo: `comedores/services/comedor_service/impl.py`
- `importar_nomina_ultimo_convenio` ahora:
  - valida que la admisión destino pertenezca al comedor recibido,
  - busca origen con `id__lt=admision_destino.id` (anterior real),
  - mantiene deduplicación por `ciudadano_id` y carga en estado `pendiente`.

Resultado: evita copiar desde admisiones posteriores cuando se opera sobre convenios intermedios.

### 3) Data migration con fallback seguro
- Archivo: `comedores/migrations/0024_nomina_switch_comedor_to_admision.py`
- La asignación de admisión para datos existentes ahora:
  - prioriza admisión activa más reciente,
  - y si no existe, usa la admisión más reciente del comedor.

Resultado: reduce casos de nómina huérfana (`admision=NULL`) al migrar.

## Tests agregados/actualizados
- Archivo: `comedores/tests.py`
- Nuevos casos:
  - importación toma admisión anterior y no una posterior,
  - importación falla si la admisión no pertenece al comedor,
  - `NominaDetailView` devuelve `404` para `admision_pk` cruzado,
  - `NominaImportarView` devuelve `404` para `admision_pk` cruzado.

## Riesgo y compatibilidad
- Cambio backward compatible para rutas válidas.
- Endpoints web de nómina ahora son más estrictos con combinaciones inválidas de URL.
