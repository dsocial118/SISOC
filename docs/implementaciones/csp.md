# CSP en SISOC

Guía práctica de uso de Content Security Policy (CSP) en SISOC.

## Objetivo

- Reducir riesgo de XSS en templates y scripts inline.
- Detectar errores en desarrollo local (antes de QA) con `Report-Only`.
- Endurecer gradualmente hasta enforcement completo.

## Configuración actual (default)

Fuente: `config/settings.py` y `.env.example`.

```env
ENABLE_CSP=true
CSP_REPORT_ONLY=true
CSP_ALLOW_UNSAFE_INLINE_SCRIPTS=false
CSP_ALLOW_UNSAFE_EVAL=false
```

### Qué significa

- `ENABLE_CSP=true`: siempre se envía header CSP.
- `CSP_REPORT_ONLY=true`: no bloquea ejecución, pero reporta violaciones en consola del navegador.
- `CSP_ALLOW_UNSAFE_INLINE_SCRIPTS=false`: scripts inline **deben** tener `nonce`.
- `CSP_ALLOW_UNSAFE_EVAL=false`: evita `eval/new Function` por defecto.

## Middleware y nonce

El middleware `config/middlewares/csp.py`:

- Genera `request.csp_nonce` por request.
- Construye `script-src` con:
  - `'self'`
  - `'nonce-<valor>'` cuando `CSP_ALLOW_UNSAFE_INLINE_SCRIPTS=false`
- Envía uno de estos headers:
  - `Content-Security-Policy-Report-Only` (si `CSP_REPORT_ONLY=true`)
  - `Content-Security-Policy` (si `CSP_REPORT_ONLY=false`)

## Uso correcto en templates

### 1) Script inline

```html
<script nonce="{{ request.csp_nonce }}">
  // JS inline
</script>
```

### 2) Script externo

No requiere nonce.

```html
<script src="{% static 'custom/js/base.js' %}"></script>
```

### 3) Evitar handlers inline

Preferir listeners en JS externo en vez de atributos HTML inline.

✅ Mejor:

```html
<button data-call-click="guardar">Guardar</button>
```

❌ Evitar:

```html
<button onclick="guardar()">Guardar</button>
```

## Flujo recomendado por entorno

### Desarrollo local

- Mantener `CSP_REPORT_ONLY=true`.
- Revisar consola del navegador para violaciones CSP.
- Corregir nonce/scripts antes de enviar PR.

### QA

- Mantener `CSP_REPORT_ONLY=true` al principio.
- Validar que no haya violaciones en flujos críticos.

### Producción

- Cambiar a `CSP_REPORT_ONLY=false` cuando QA esté limpio.
- Mantener `unsafe-inline/eval` deshabilitados.

## Checklist de PR para cambios de frontend

- Si agregaste script inline, ¿incluye `nonce`?
- ¿Evitaste `onclick/onchange` inline?
- ¿No dependés de `eval`?
- ¿Probaste vista en local y revisaste consola CSP?
- ¿Corren tests de CSP?

## Validación automática en repo

- `tests/test_csp_middleware_unit.py`: valida header y modo estricto.
- `tests/test_templates_inline_scripts_nonce_unit.py`: falla si encuentra `<script>` inline sin nonce.

## Problemas comunes

### “Me falla un script inline”

- Verificar que tenga `nonce="{{ request.csp_nonce }}"`.
- Confirmar que la vista pase por middleware (está en `MIDDLEWARE` en settings).

### “No veo bloqueos pero sí warnings”

- Es esperado con `CSP_REPORT_ONLY=true`.
- El objetivo en dev/qa es detectar y corregir antes de enforcement.

### “Quiero permitir inline temporalmente”

- Evitarlo. Si es estrictamente necesario para desbloquear, hacerlo solo de forma temporal y documentada:

```env
CSP_ALLOW_UNSAFE_INLINE_SCRIPTS=true
```

- Volver a `false` en el mismo ciclo de cambios.
