# Cambios: Fix de Botones "Volver" en VAT

**Fecha:** 2026-03-28  
**Estado:** ✅ COMPLETADO  
**Impacto:** ALTO - Mejora en UX de navegación

---

## Resumen Ejecutivo

Se corrigieron 2 botones "Volver" críticos en pantallas de detalle de VAT que apuntaban a listas genéricas en lugar de navegar al contexto original.

**Resultado:** El usuario ahora preserva el flujo Centro → Oferta → Comisión → Inscripción al hacer clic "atrás".

---

## Cambios Realizados

### 1️⃣ Comisión Detail - FIX CRÍTICO

**Archivo:** `VAT/templates/vat/oferta_institucional/comision_detail.html`  
**Línea:** 242

**ANTES:**
```django
<a href="{% url 'vat_comision_list' %}" class="ci-back">
    <i class="bi bi-arrow-left"></i>
</a>
```

**DESPUÉS:**
```django
<a href="{% url 'vat_oferta_institucional_detail' comision.oferta.id %}" class="ci-back">
    <i class="bi bi-arrow-left"></i>
</a>
```

**Impacto:**
- ❌ ANTES: Click → `/vat/comisiones/` (lista de todas las comisiones)
- ✅ DESPUÉS: Click → `/vat/ofertas-institucionales/X/` (oferta específica)
- 📈 Ganancia: Usuario regresa al contexto correcto

---

### 2️⃣ Inscripción Detail - FIX CRÍTICO

**Archivo:** `VAT/templates/vat/persona/inscripcion_detail.html`  
**Línea:** 113

**ANTES:**
```django
<a href="{% url 'vat_inscripcion_list' %}" class="ci-back">
    <i class="bi bi-arrow-left"></i>
</a>
```

**DESPUÉS:**
```django
<a href="{% url 'vat_comision_detail' inscripcion.comision_id %}" class="ci-back">
    <i class="bi bi-arrow-left"></i>
</a>
```

**Impacto:**
- ❌ ANTES: Click → `/vat/inscripciones/` (lista de todas las inscripciones)
- ✅ DESPUÉS: Click → `/vat/comisiones/X/` (comisión específica)
- 📈 Ganancia: Usuario regresa a la comisión donde estaba inscripto

---

## Jerrarquía de Navegación Reparada

```
Centro Detail (/vat/centros/X/)
    ↓ (click en oferta)
Oferta Detail (/vat/ofertas-institucionales/X/)
    ↓ (click en comisión)
Comisión Detail (/vat/comisiones/X/)
    ↑ ← BOTÓN VOLVER AHORA APUNTA AQUÍ (era Lista)
    ↓ (click en inscripción)
Inscripción Detail (/vat/inscripciones/X/)
    ↑ ← BOTÓN VOLVER AHORA APUNTA AQUÍ (era Lista)
```

---

## Verificaciones Ejecutadas

✅ **Compilación de Templates**
```
comision_detail.html → OK (sin errores de sintaxis)
inscripcion_detail.html → OK (sin errores de sintaxis)
```

✅ **URLs Validadas**
```
vat_oferta_institucional_detail → /vat/ofertas-institucionales/1/
vat_comision_detail → /vat/comisiones/1/
vat_inscripcion_detail → /vat/inscripciones/1/
```

✅ **Contexto Disponible**
```
comision.oferta.id → FK siempre existe en modelo
inscripcion.comision_id → FK siempre existe en modelo
```

---

## Testing Recomendado

### Flujo 1: Comisión
1. Navega a Centro → selecciona Oferta → ve Comisión
2. En comisión detail, click botón "Volver" (flecha izquierda en header)
3. ✅ Verifica: Deberías estar en **Oferta Detail** (no lista de comisiones)

### Flujo 2: Inscripción
1. Navega a Centro → Oferta → Comisión → Inscripción
2. En inscripción detail, click botón "Volver"
3. ✅ Verifica: Deberías estar en **Comisión Detail** (no lista de inscripciones)

### Flujo 3: Mobile
1. Abre en celular/tablet
2. Verifica que botón "atrás" (flecha izquierda) funciona correctamente
3. ✅ Verifica: Navegación funciona en pantallas pequeñas

---

## Notas Técnicas

- **No hay cambios en models.py** - Solo templates
- **No hay migraciones pendientes** - Solo ajustes de URL
- **Compatibilidad hacia atrás:** 100% - No afecta otros flujos
- **Permisos:** Las vistas target (`vat_oferta_institucional_detail`, `vat_comision_detail`) tienen `LoginRequiredMixin` ✅

---

## Archivos Impactados

| Archivo | Tipo | Cambios |
|---------|------|---------|
| `VAT/templates/vat/oferta_institucional/comision_detail.html` | Template | 1 línea (URL) |
| `VAT/templates/vat/persona/inscripcion_detail.html` | Template | 1 línea (URL) |
| `VAT/urls.py` | Config | Sin cambios (URLs ya existen) |
| `VAT/models.py` | Modelo | Sin cambios |

---

## Seguimiento

- ✅ Análisis completo: `docs/registro/analisis/2026-03-28-botones-volver-vat.md`
- ✅ Este registro de cambios
- ⏳ Próximo: Testing manual en browser (acción del usuario)

---

## Autor

Claude (AI Assistant)  
GitHub Copilot
