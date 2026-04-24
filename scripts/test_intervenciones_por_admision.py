"""
Script manual para verificar que las intervenciones quedan atadas a cada
admision y no al comedor en general.

Uso:
    python manage.py shell < scripts/test_intervenciones_por_admision.py
"""

from acompanamientos.acompanamiento_service import AcompanamientoService
from acompanamientos.models.acompanamiento import Acompanamiento
from acompanamientos.models.hitos import Hitos, HitosIntervenciones
from admisiones.models.admisiones import Admision
from comedores.models import Comedor
from intervenciones.models.intervenciones import (
    Intervencion,
    SubIntervencion,
    TipoContacto,
    TipoDestinatario,
    TipoIntervencion,
)

__test__ = False

SEPARADOR = "=" * 60


def _print_separator():
    print(SEPARADOR)


def _get_required_lookup():
    mapping = HitosIntervenciones.objects.first()
    tipo_nombre = mapping.intervencion if mapping else None
    subtipo_nombre = mapping.subintervencion if mapping else ""
    hito_verbose = mapping.hito if mapping else None

    tipo = (
        TipoIntervencion.objects.filter(nombre=tipo_nombre).first()
        if tipo_nombre
        else None
    )
    subtipo = (
        SubIntervencion.objects.filter(
            nombre=subtipo_nombre,
            tipo_intervencion=tipo,
        ).first()
        if subtipo_nombre and tipo
        else None
    )
    if not tipo:
        tipo = TipoIntervencion.objects.first()
        subtipo = None
        subtipo_nombre = ""
        hito_verbose = None
    return mapping, tipo, subtipo, subtipo_nombre, hito_verbose


def main():
    _print_separator()
    mapping = HitosIntervenciones.objects.first()
    if not mapping:
        print("ADVERTENCIA: HitosIntervenciones esta vacia.")
        print("El trigger de hitos no va a funcionar.")
        print("Carga el fixture de HitosIntervenciones antes de correr este script.")
    else:
        print(f"HitosIntervenciones OK - primer mapeo: {mapping}")

    _print_separator()
    comedor = Comedor.objects.first()
    if not comedor:
        raise RuntimeError("No hay comedores en la DB. Carga fixtures primero.")
    print(f"Usando comedor: {comedor.pk} - {comedor.nombre}")

    _print_separator()
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
    print(f"Admision A: pk={admision_a.pk} ({'creada' if created_a else 'ya existia'})")

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
    print(f"Admision B: pk={admision_b.pk} ({'creada' if created_b else 'ya existia'})")

    _print_separator()
    acomp_a, _ = Acompanamiento.objects.get_or_create(
        admision=admision_a,
        defaults={"nro_convenio": "CONV-TEST-A"},
    )
    hitos_a, _ = Hitos.objects.get_or_create(acompanamiento=acomp_a)
    print(f"Acompanamiento A: pk={acomp_a.pk} - Hitos A: pk={hitos_a.pk}")

    acomp_b, _ = Acompanamiento.objects.get_or_create(
        admision=admision_b,
        defaults={"nro_convenio": "CONV-TEST-B"},
    )
    hitos_b, _ = Hitos.objects.get_or_create(acompanamiento=acomp_b)
    print(f"Acompanamiento B: pk={acomp_b.pk} - Hitos B: pk={hitos_b.pk}")

    _print_separator()
    _, tipo, subtipo, _, hito_verbose = _get_required_lookup()
    print(f"TipoIntervencion usado: {tipo}")
    print(f"SubIntervencion usada: '{subtipo}' (pk={subtipo.pk if subtipo else None})")
    print(f"Hito esperado: {hito_verbose}")

    destinatario = TipoDestinatario.objects.first()
    contacto = TipoContacto.objects.first()
    if not destinatario:
        raise RuntimeError("No hay TipoDestinatario en la DB. Carga fixtures primero.")
    if not contacto:
        raise RuntimeError("No hay TipoContacto en la DB. Carga fixtures primero.")

    _print_separator()
    intervencion_a = Intervencion.objects.create(
        comedor=comedor,
        admision=admision_a,
        tipo_intervencion=tipo,
        subintervencion=subtipo,
        destinatario=destinatario,
        forma_contacto=contacto,
        observaciones="[TEST] Intervencion de prueba para admision A",
    )
    print(
        f"Intervencion A: pk={intervencion_a.pk} - admision_id={intervencion_a.admision_id}"
    )

    tipo_sin_hito = TipoIntervencion.objects.exclude(
        nombre__in=HitosIntervenciones.objects.values_list("intervencion", flat=True)
    ).first()
    if not tipo_sin_hito:
        tipo_sin_hito = tipo
    intervencion_b = Intervencion.objects.create(
        comedor=comedor,
        admision=admision_b,
        tipo_intervencion=tipo_sin_hito,
        destinatario=destinatario,
        forma_contacto=contacto,
        observaciones="[TEST] Intervencion de prueba para admision B (sin hito)",
    )
    print(
        f"Intervencion B: pk={intervencion_b.pk} - admision_id={intervencion_b.admision_id}"
    )

    _print_separator()
    print("Verificando aislamiento de hitos...")
    hitos_a.refresh_from_db()
    hitos_b.refresh_from_db()
    campos_hitos = [
        field.name
        for field in Hitos._meta.fields
        if field.get_internal_type() == "BooleanField"
    ]
    hitos_a_activos = [campo for campo in campos_hitos if getattr(hitos_a, campo)]
    hitos_b_activos = [campo for campo in campos_hitos if getattr(hitos_b, campo)]
    print(f"Hitos activos en A: {hitos_a_activos or 'ninguno'}")
    print(f"Hitos activos en B: {hitos_b_activos or 'ninguno'}")

    if hito_verbose:
        campo_esperado = next(
            (
                field.name
                for field in Hitos._meta.fields
                if field.verbose_name == hito_verbose
            ),
            None,
        )
        if campo_esperado:
            val_a = getattr(hitos_a, campo_esperado)
            val_b = getattr(hitos_b, campo_esperado)
            print(f"\nCampo '{campo_esperado}' (verbose: '{hito_verbose}'):")
            print(f"  Hitos A: {val_a}")
            print(f"  Hitos B: {val_b}")

    _print_separator()
    print("Verificando obtener_fechas_hitos por admision...")
    fechas_a = AcompanamientoService.obtener_fechas_hitos(
        comedor,
        admision_id=admision_a.id,
    )
    fechas_b = AcompanamientoService.obtener_fechas_hitos(
        comedor,
        admision_id=admision_b.id,
    )
    print(f"Fechas hitos A: {fechas_a}")
    print(f"Fechas hitos B: {fechas_b}")

    _print_separator()
    print("Verificando filtrado de intervenciones por admision_id...")
    intervs_a = Intervencion.objects.filter(admision_id=admision_a.id)
    intervs_b = Intervencion.objects.filter(admision_id=admision_b.id)
    intervs_comedor = Intervencion.objects.filter(comedor=comedor)
    print(f"Intervenciones admision A: {intervs_a.count()}")
    print(f"Intervenciones admision B: {intervs_b.count()}")
    print(f"Intervenciones totales del comedor: {intervs_comedor.count()}")

    _print_separator()
    print("RESUMEN")
    print(f"  Comedor: {comedor.pk} - {comedor.nombre}")
    print(
        "  Admision A: "
        f"pk={admision_a.pk} -> /comedores/intervencion/ver/{comedor.pk}/?admision_id={admision_a.pk}"
    )
    print(
        "  Admision B: "
        f"pk={admision_b.pk} -> /comedores/intervencion/ver/{comedor.pk}/?admision_id={admision_b.pk}"
    )
    print(f"  Acompanamiento: /acompanamiento/{comedor.pk}/detalle/")
    print()
    print("Para limpiar los datos de test:")
    print("  Intervencion.objects.filter(observaciones__startswith='[TEST]').delete()")
    print("  Admision.objects.filter(num_expediente__startswith='TEST-').delete()")
    _print_separator()


if __name__ in {"__main__", "__console__"}:
    main()
