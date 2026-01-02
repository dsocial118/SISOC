# Revisión entre 2026-1 (compare) y development (base)

## 0) Resumen de cambios a mergear
- Alcance: feature/bugfix mixto (nuevos adjuntos en admisiones, ajustes de informes técnicos, relajación de duplas, validación de admisiones).
- Métricas delta: 10 archivos (+292/-30 LOC aprox.); 3 migraciones nuevas (`admisiones` 0043, `cdi` 0004, `comedores` 0020); tests sin cambios reportados.
- Áreas tocadas: vista de detalle de admisiones y JS asociado, servicio de informes técnicos, servicio de comedores, formularios/modelos/JS de duplas; campos `estado_legales` y `comienzo` en modelos (`admisiones`, `cdi`, `comedores`).
- Compatibilidad/contratos: se agregan choices de estado; se relaja restricción de técnicos por dupla (puede afectar reglas de negocio previas); se validan años con tope 2026 (riesgo de bloqueo futuro); se añaden campos de trazabilidad en creación/edición de informes.
- Riesgos (top 3) + mitigación: (1) Upload de "Archivos adicionales" retorna 405 porque se maneja en `get()` en vez de `post()` → mover lógica a `post()` con CSRF y respuestas JSON. (2) Validadores `MaxValueValidator(2026)` en `comienzo` (`cdi`, `comedores`) dejarán de aceptar años siguientes rápidamente → usar `datetime.date.today().year` o retirar tope rígido. (3) Eliminación de límite de técnicos por dupla sin advertencias ni validación de negocio → confirmar reglas y añadir constraints/avisos si corresponde.
- Impacto ops: migraciones solo alteran choices/validadores (sin datos); riesgo bajo de lock. Sin seeds ni flags nuevos.
- Rollback: revertir commit/PR completo o aplicar migraciones reversas (todas son `AlterField`, reversibles por Django).

## 1) Comentarios de revisión

[Major] (Logic)  
Archivo: admisiones/views/web_views.py:L561-L576

Qué:
- La carga de "Archivos adicionales" se implementa dentro de `get()`; las peticiones POST del `XMLHttpRequest` retornarán 405 (DetailView no acepta POST) y la rama nunca se ejecuta.

Dónde:
- `if request.FILES.get("archivo") and request.POST.get("nombre"):` dentro de `get()` antes de `return super().get(...)`.

Por qué:
- Ruta no alcanzable para POST → funcionalidad rota y feedback de error genérico en frontend.

Cómo arreglar:
- Mover la lógica a un `post()` explícito (o `dispatch`) y mantener el `JsonResponse`. Ejemplo:
```python
def post(self, request, *args, **kwargs):
    if request.FILES.get("archivo") and request.POST.get("nombre"):
        admision = self.get_object()
        archivo = request.FILES["archivo"]
        nombre = request.POST["nombre"].strip()
        archivo_admision, error = AdmisionService.crear_documento_personalizado(
            admision.id, nombre, archivo, request.user
        )
        status = 200 if archivo_admision else 400
        return JsonResponse({"success": bool(archivo_admision), "error": error}, status=status)
    return super().post(request, *args, **kwargs)
```

[Minor] (Data)  
Archivo: cdi/migrations/0004_alter_centrodesarrolloinfantil_comienzo.py:L14-L23 y comedores/migrations/0020_alter_comedor_comienzo.py:L14-L23

Qué:
- Se fija `MaxValueValidator(2026)` para el campo `comienzo`.

Dónde:
- Validadores con límite superior 2026.

Por qué:
- En 2027 el formulario fallará sin motivo funcional; mantenimiento anual y bloqueos innecesarios.

Cómo arreglar:
- Usar el año actual dinámico o eliminar el tope rígido. Ejemplo en migración/modelo:
```python
from django.utils.timezone import now
max_year = now().year
validators=[MinValueValidator(1900), MaxValueValidator(max_year)]
```

[Minor] (Architecture)  
Archivo: duplas/forms.py:L34-L40

Qué:
- Se permite asignar un técnico a múltiples duplas sin validación ni mensaje; cambio de regla de negocio silencioso.

Dónde:
- `self.fields["tecnico"].queryset = grupo_tecnico.user_set.all()` y se eliminó la validación de máximo.

Por qué:
- Si aún se espera exclusividad parcial, se pueden crear asignaciones inconsistentes; falta reflejar decisión en UI/validaciones.

Cómo arreglar:
- Confirmar regla. Si se requiere límite o advertencia, reintroducir validación o al menos un help_text/log para evitar confusión. Ejemplo mínimo:
```python
self.fields["tecnico"].help_text = "Un técnico puede integrarse en varias duplas."  # o revalidar límite según negocio
```

## 4) Checklist final
- Riesgos críticos detectados: [Carga de archivos adicionales no funciona por POST 405](#major-logic).
- Migraciones: todas son `AlterField`, reversibles; sin `RunPython`; riesgos de lock bajos.
- ORM: sin N+1 nuevos detectados; no se usan `select_related/prefetch_related` en el cambio de uploads (no aplica).
- Transacciones/atomicidad: `guardar_informe` sigue protegido con `transaction.atomic`.
- Seguridad: upload reutiliza CSRF token, pero la vista aún no procesa POST (ver bug). No se valida tamaño/tipo de archivo (preexistente).
- Performance: sin cambios relevantes; upload recarga página completa tras éxito.
- Observabilidad: sin logs/metrics para fallos de upload; considerar logging en backend al mover a `post()`.
- Maintainability/Complejidad: cambios acotados; validar reglas de negocio de duplas y límites de año para evitar deuda.
- Tests mínimos a exigir: (1) POST a detalle de admisión con `archivo` y `nombre` devuelve 200 y crea documento; (2) POST con faltantes devuelve 400; (3) Campo `comienzo` acepta año `now().year`; (4) Creación de dupla permite múltiples técnicos según regla esperada.
- Refactors rápidos (≤15 min): mover upload a `post()` y añadir test de vista; ajustar validador de año a dinámico.
- Refactors estructurales (a planificar): definir política de adjuntos (tamaño/tipo/logging) y reglas de asignación de técnicos por dupla documentadas.
