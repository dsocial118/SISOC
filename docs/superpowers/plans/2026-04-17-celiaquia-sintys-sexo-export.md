# Exportacion Nomina Sintys Con Sexo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Agregar la columna `Sexo` al Excel descargado desde `/celiaquia/expedientes/<pk>/` al exportar la nomina Sintys.

**Architecture:** El cambio se concentra en la generacion del Excel en `CruceService`, que ya define las columnas exportadas. La cobertura se extiende sobre el test puntual de la descarga para fijar encabezado y valor exportado sin modificar el flujo de seleccion de legajos.

**Tech Stack:** Django 4.2, pytest, openpyxl, pandas.

---

### Task 1: Cubrir la exportacion con un test de regresion

**Files:**
- Modify: `celiaquia/tests/test_nomina_sintys_export.py`
- Test: `celiaquia/tests/test_nomina_sintys_export.py`

- [ ] **Step 1: Write the failing test**

```python
sexo = Sexo.objects.create(sexo="Masculino")
ciudadano = Ciudadano.objects.create(
    apellido="Perez",
    nombre="Juan",
    fecha_nacimiento="2000-01-01",
    documento=12345678,
    tipo_documento=Ciudadano.DOCUMENTO_DNI,
    sexo=sexo,
)
...
assert header == [
    "Numero_documento",
    "TipoDocumento",
    "nombre",
    "apellido",
    "sexo",
]
assert row[4] == "Masculino"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `& 'C:/Users/Juanito/Desktop/Repos-Codex/worktrees/predeploy-development-main-20260416/.venv/Scripts/python.exe' -m pytest celiaquia/tests/test_nomina_sintys_export.py -q`
Expected: FAIL porque el archivo exportado todavia no incluye la columna `sexo`.

- [ ] **Step 3: Write minimal implementation**

```python
"sexo": getattr(getattr(ciudadano, "sexo", None), "sexo", "") or "",
```

Agregar la clave en ambos caminos de exportacion y extender la lista de columnas del `DataFrame`.

- [ ] **Step 4: Run test to verify it passes**

Run: `& 'C:/Users/Juanito/Desktop/Repos-Codex/worktrees/predeploy-development-main-20260416/.venv/Scripts/python.exe' -m pytest celiaquia/tests/test_nomina_sintys_export.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add celiaquia/services/cruce_service/impl.py celiaquia/tests/test_nomina_sintys_export.py docs/registro/cambios/2026-04-17-celiaquia-nomina-sintys-sexo.md docs/superpowers/plans/2026-04-17-celiaquia-sintys-sexo-export.md
git commit -m "fix(celiaquia): agregar sexo a nomina sintys"
```

### Task 2: Registrar el cambio spec-as-source

**Files:**
- Create: `docs/registro/cambios/2026-04-17-celiaquia-nomina-sintys-sexo.md`

- [ ] **Step 1: Document the behavior change**

```md
# Exportacion nomina Sintys con sexo

- Se agrega la columna `Sexo` a la exportacion Excel de la nomina Sintys.
- Se mantiene el criterio actual de legajos exportados.
- Se agrega test de regresion para encabezado y valor exportado.
```

- [ ] **Step 2: Verify docs are present in the branch**

Run: `git status --short`
Expected: aparecen el doc de plan y el registro de cambio junto con los archivos funcionales.
