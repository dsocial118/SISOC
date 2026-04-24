"""
Script de prueba: crea datos de test para verificar que las intervenciones
quedan correctamente atadas a cada admisión (y no al comedor en general).

Uso:
    python manage.py shell < scripts/test_intervenciones_por_admision.py

Limpieza posterior:
    python manage.py shell < scripts/test_intervenciones_por_admision.py --clean
    (o borrá manualmente los registros con num_expediente que empiecen con "TEST-")
"""

from comedores.models import Comedor
from admisiones.models.admisiones import Admision
from acompanamientos.models.acompanamiento import Acompanamiento
from acompanamientos.models.hitos import Hitos, HitosIntervenciones
from acompanamientos.acompanamiento_service import AcompanamientoService
from intervenciones.models.intervenciones import (
    Intervencion,
    SubIntervencion,
    TipoIntervencion,
    TipoDestinatario,
    TipoContacto,
)

SEPARADOR = "=" * 60

# ─── 0. Verificar que existe al menos un mapeo en HitosIntervenciones ────────
print(SEPARADOR)
mapping = HitosIntervenciones.objects.first()
if not mapping:
    print("ADVERTENCIA: HitosIntervenciones está vacía.")
    print("El trigger de hitos no va a funcionar.")
    print("Cargá el fixture de HitosIntervenciones antes de correr este script.")
else:
    print(f"HitosIntervenciones OK — primer mapeo: {mapping}")

# ─── 1. Obtener un comedor existente ─────────────────────────────────────────
print(SEPARADOR)
comedor = Comedor.objects.first()
if not comedor:
    raise RuntimeError("No hay comedores en la DB. Cargá fixtures primero.")
print(f"Usando comedor: {comedor.pk} — {comedor.nombre}")

# ─── 2. Crear 2 admisiones de test para ese comedor ──────────────────────────
print(SEPARADOR)
admision_a, created_a = Admision.objects.get_or_create(
    num_expediente="TEST-ADMISION-A",
    defaults={
        "comedor": comedor,
        "enviado_acompaniamiento": True,
        "activa": True,
        "numero_disposicion": "DISP-TEST-A",
    },
)
if not created_a:
    admision_a.comedor = comedor
    admision_a.enviado_acompaniamiento = True
    admision_a.activa = True
    admision_a.save()
print(f"Admisión A: pk={admision_a.pk} ({'creada' if created_a else 'ya existía'})")

admision_b, created_b = Admision.objects.get_or_create(
    num_expediente="TEST-ADMISION-B",
    defaults={
        "comedor": comedor,
        "enviado_acompaniamiento": True,
        "activa": True,
        "numero_disposicion": "DISP-TEST-B",
    },
)
if not created_b:
    admision_b.comedor = comedor
    admision_b.enviado_acompaniamiento = True
    admision_b.activa = True
    admision_b.save()
print(f"Admisión B: pk={admision_b.pk} ({'creada' if created_b else 'ya existía'})")

# ─── 3. Crear Acompanamiento + Hitos para cada admisión ──────────────────────
print(SEPARADOR)
acomp_a, _ = Acompanamiento.objects.get_or_create(
    admision=admision_a,
    defaults={"nro_convenio": "CONV-TEST-A"},
)
hitos_a, _ = Hitos.objects.get_or_create(acompanamiento=acomp_a)
print(f"Acompañamiento A: pk={acomp_a.pk} — Hitos A: pk={hitos_a.pk}")

acomp_b, _ = Acompanamiento.objects.get_or_create(
    admision=admision_b,
    defaults={"nro_convenio": "CONV-TEST-B"},
)
hitos_b, _ = Hitos.objects.get_or_create(acompanamiento=acomp_b)
print(f"Acompañamiento B: pk={acomp_b.pk} — Hitos B: pk={hitos_b.pk}")

# ─── 4. Obtener tipo de intervención y lookup para disparar un hito ───────────
print(SEPARADOR)

# Buscamos un mapping existente en HitosIntervenciones para disparar un hito real
mapping = HitosIntervenciones.objects.first()
tipo_nombre = mapping.intervencion if mapping else None
subtipo_nombre = mapping.subintervencion if mapping else ""
hito_verbose = mapping.hito if mapping else None

tipo = (
    TipoIntervencion.objects.filter(nombre=tipo_nombre).first() if tipo_nombre else None
)
subtipo = (
    SubIntervencion.objects.filter(
        nombre=subtipo_nombre, tipo_intervencion=tipo
    ).first()
    if subtipo_nombre and tipo
    else None
)

if not tipo:
    # Fallback: cualquier tipo existente
    tipo = TipoIntervencion.objects.first()
    subtipo = None
    subtipo_nombre = ""
    hito_verbose = None

print(f"TipoIntervencion usado: {tipo}")
print(f"SubIntervencion usada: '{subtipo}' (pk={subtipo.pk if subtipo else None})")
print(f"Hito esperado: {hito_verbose}")

destinatario = TipoDestinatario.objects.first()
contacto = TipoContacto.objects.first()

if not destinatario:
    raise RuntimeError("No hay TipoDestinatario en la DB. Cargá fixtures primero.")
if not contacto:
    raise RuntimeError("No hay TipoContacto en la DB. Cargá fixtures primero.")

# ─── 5. Crear intervenciones — una para A, otra para B ───────────────────────
print(SEPARADOR)

# Intervención ligada a admisión A (debe disparar hito solo en A)
intervencion_a = Intervencion.objects.create(
    comedor=comedor,
    admision=admision_a,
    tipo_intervencion=tipo,
    subintervencion=subtipo,
    destinatario=destinatario,
    forma_contacto=contacto,
    observaciones="[TEST] Intervención de prueba para admisión A",
)
print(
    f"Intervención A: pk={intervencion_a.pk} — admision_id={intervencion_a.admision_id}"
)

# Intervención ligada a admisión B — tipo SIN mapping en HitosIntervenciones
# para verificar que el hito de A no se copia en B
tipo_sin_hito = TipoIntervencion.objects.exclude(
    nombre__in=HitosIntervenciones.objects.values_list("intervencion", flat=True)
).first()
if not tipo_sin_hito:
    # Fallback: usamos el mismo tipo pero al menos verificamos que B no hereda el hito de A
    tipo_sin_hito = tipo
intervencion_b = Intervencion.objects.create(
    comedor=comedor,
    admision=admision_b,
    tipo_intervencion=tipo_sin_hito,
    destinatario=destinatario,
    forma_contacto=contacto,
    observaciones="[TEST] Intervención de prueba para admisión B (sin hito)",
)
print(
    f"Intervención B: pk={intervencion_b.pk} — admision_id={intervencion_b.admision_id}"
)

# ─── 6. Verificar que los hitos no se contaminaron entre sí ──────────────────
print(SEPARADOR)
print("Verificando aislamiento de hitos...")

hitos_a.refresh_from_db()
hitos_b.refresh_from_db()

campos_hitos = [
    f.name for f in Hitos._meta.fields if f.get_internal_type() == "BooleanField"
]

hitos_a_activos = [c for c in campos_hitos if getattr(hitos_a, c)]
hitos_b_activos = [c for c in campos_hitos if getattr(hitos_b, c)]

print(f"Hitos activos en A: {hitos_a_activos or 'ninguno'}")
print(f"Hitos activos en B: {hitos_b_activos or 'ninguno'}")

if hito_verbose:
    from acompanamientos.models.hitos import Hitos as HitosModel

    campo_esperado = next(
        (f.name for f in HitosModel._meta.fields if f.verbose_name == hito_verbose),
        None,
    )
    if campo_esperado:
        val_a = getattr(hitos_a, campo_esperado)
        val_b = getattr(hitos_b, campo_esperado)
        print(f"\nCampo '{campo_esperado}' (verbose: '{hito_verbose}'):")
        print(f"  Hitos A: {val_a} {'✓' if val_a else '✗'}")
        print(f"  Hitos B: {val_b} {'✗ CONTAMINADO' if val_b else '✓ aislado'}")

# ─── 7. Verificar obtener_fechas_hitos por admisión ──────────────────────────
print(SEPARADOR)
print("Verificando obtener_fechas_hitos por admisión...")

fechas_a = AcompanamientoService.obtener_fechas_hitos(
    comedor, admision_id=admision_a.id
)
fechas_b = AcompanamientoService.obtener_fechas_hitos(
    comedor, admision_id=admision_b.id
)

print(f"Fechas hitos A: {fechas_a}")
print(f"Fechas hitos B: {fechas_b}")

# ─── 8. Verificar filtrado de intervenciones por admisión ────────────────────
print(SEPARADOR)
print("Verificando filtrado de intervenciones por admision_id...")

intervs_a = Intervencion.objects.filter(admision_id=admision_a.id)
intervs_b = Intervencion.objects.filter(admision_id=admision_b.id)
intervs_comedor = Intervencion.objects.filter(comedor=comedor)

print(f"Intervenciones admisión A: {intervs_a.count()}")
print(f"Intervenciones admisión B: {intervs_b.count()}")
print(f"Intervenciones totales del comedor (sin filtro): {intervs_comedor.count()}")

# ─── 9. Resumen final ────────────────────────────────────────────────────────
print(SEPARADOR)
print("RESUMEN")
print(f"  Comedor: {comedor.pk} — {comedor.nombre}")
print(
    f"  Admisión A: pk={admision_a.pk}  →  URL test: /comedores/intervencion/ver/{comedor.pk}/?admision_id={admision_a.pk}"
)
print(
    f"  Admisión B: pk={admision_b.pk}  →  URL test: /comedores/intervencion/ver/{comedor.pk}/?admision_id={admision_b.pk}"
)
print(f"  Acompañamiento: /acompanamiento/{comedor.pk}/detalle/")
print()
print("Para limpiar los datos de test:")
print("  Intervencion.objects.filter(observaciones__startswith='[TEST]').delete()")
print("  Admision.objects.filter(num_expediente__startswith='TEST-').delete()")
print(SEPARADOR)
