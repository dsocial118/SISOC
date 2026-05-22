# VAT Telefono +54 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir que `Ciudadano` acepte y persista teléfonos internacionales con `+54` y formato extendido en el flujo VAT.

**Architecture:** El cambio se concentra en el modelo `Ciudadano`, elevando la longitud máxima de ambos campos de teléfono y acompañándolo con una migración explícita para alinear el schema desplegado. La cobertura se reparte entre un test de modelo para el contrato del campo y una aserción del flujo VAT para la persistencia operativa.

**Tech Stack:** Django 4.2, ORM de Django, pytest, Docker Compose.

---

### Task 1: Cubrir el contrato del modelo

**Files:**
- Modify: `tests/test_ciudadanos_models_unit.py`

- [ ] **Step 1: Write the failing test**

```python
def test_ciudadano_full_clean_acepta_telefono_internacional_formateado(db):
    ciudadano = Ciudadano(
        nombre="Ana",
        apellido="Perez",
        fecha_nacimiento=date(1990, 1, 1),
        documento=12345678,
        telefono="+54 9 351 398-9965 interno 1234",
    )

    ciudadano.full_clean()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker compose exec -T django pytest tests/test_ciudadanos_models_unit.py -k telefono_internacional_formateado -q`
Expected: FAIL con validación de `max_length=30`.

- [ ] **Step 3: Write minimal implementation**

```python
telefono = models.CharField(max_length=50, null=True, blank=True)
telefono_alternativo = models.CharField(max_length=50, null=True, blank=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `docker compose exec -T django pytest tests/test_ciudadanos_models_unit.py -k telefono_internacional_formateado -q`
Expected: PASS.

### Task 2: Alinear schema y regresión VAT

**Files:**
- Create: `ciudadanos/migrations/0023_alter_ciudadano_telefono_longitud.py`
- Modify: `VAT/tests.py`
- Modify: `docs/vat/api_web.md`

- [ ] **Step 1: Persist schema change**

```python
operations = [
    migrations.AlterField(
        model_name="ciudadano",
        name="telefono",
        field=models.CharField(blank=True, max_length=50, null=True),
    ),
    migrations.AlterField(
        model_name="ciudadano",
        name="telefono_alternativo",
        field=models.CharField(blank=True, max_length=50, null=True),
    ),
]
```

- [ ] **Step 2: Verify VAT flow keeps the international phone**

```python
assert ciudadano.telefono == "+54-351-3989965"
```

- [ ] **Step 3: Run focused verification**

Run: `docker compose exec -T django pytest tests/test_ciudadanos_models_unit.py -k telefono_internacional_formateado -q`
Run: `docker compose exec -T django pytest VAT/tests.py -k inscripcion_crea_ciudadano_desde_datos_postulante -q`
Expected: PASS en ambos casos.
