#!/usr/bin/env python3
"""
Script para depurar las optimizaciones de queries en las vistas del sistema SISOC

Para ejecutar este script:
  docker-compose exec django python manage.py shell -c "from core.debug_queries import debu        if hasattr(view, "get_object"):
            # Vista de detalle
            print(f"🔄 Ejecutando get_object() para {view_name}...")
            obj = view.get_object()
            _ = len(connection.queries)  # queries_after_get_object (no usado)

            # Asignar el objeto a la vista para evitar errores
            view.object = obj

            print(f"🔄 Ejecutando get_context_data() para {view_name}...")
            _ = view.get_context_data(object=obj)  # context (no usado)
        else:
            # Vista de lista
            print(f"🔄 Ejecutando get_queryset() para {view_name}...")
            queryset = view.get_queryset()
            _ = len(connection.queries)  # queries_after_queryset (no usado)

            print(f"🔄 Ejecutando get_context_data() para {view_name}...")
            _ = view.get_context_data(object_list=queryset)  # context (no usado)all_views()"

O importar las funciones desde Django shell:
  docker-compose exec django python manage.py shell
  >>> from core.debug_queries import debug_all_views, debug_ciudadano_detail_queries
  >>> debug_all_views()
"""
import os
import sys

import django
from django.contrib.auth.models import User
from django.db import connection, reset_queries
from django.test import RequestFactory

from ciudadanos.models import Ciudadano
from ciudadanos.views import CiudadanosDetailView

# Configurar Django (solo si se ejecuta directamente)
if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()


def debug_ciudadano_detail_queries():  # pylint: disable=too-many-locals,too-many-statements
    """Depura el método get_object y get_context_data de CiudadanosDetailView"""

    # Verificar que existe al menos un ciudadano
    try:
        ciudadano = Ciudadano.objects.first()
        if not ciudadano:
            print("❌ No hay ciudadanos en la base de datos")
            return False

        print(
            f"🧪 Probando con ciudadano ID: {ciudadano.id} ({ciudadano.nombre} {ciudadano.apellido})"
        )

        # Crear request factory y usuario
        factory = RequestFactory()
        request = factory.get(f"/ciudadanos/ver/{ciudadano.id}/")

        # Crear usuario de prueba si no existe
        try:
            user = User.objects.get(username="debuguser")
        except User.DoesNotExist:
            user = User.objects.create_user(username="debuguser", password="debugpass")

        request.user = user

        # Crear vista
        view = CiudadanosDetailView()
        view.setup(request, pk=ciudadano.id)

        # Resetear contador de queries
        reset_queries()

        print("🔄 Ejecutando get_object()...")

        # Ejecutar get_object
        obj = view.get_object()

        queries_after_get_object = len(connection.queries)
        print(f"📊 Queries después de get_object(): {queries_after_get_object}")

        # Mostrar las queries ejecutadas para get_object
        if connection.queries:
            print("\n🔍 Queries ejecutadas en get_object():")
            for i, query in enumerate(connection.queries, 1):
                sql = (
                    query["sql"][:150] + "..."
                    if len(query["sql"]) > 150
                    else query["sql"]
                )
                time = query["time"]
                print(f"  {i}. [{time}s] {sql}")

        print("\n🔄 Ejecutando get_context_data()...")

        # Ejecutar get_context_data
        context = view.get_context_data(object=obj)

        total_queries = len(connection.queries)
        queries_in_context = total_queries - queries_after_get_object

        print(f"📊 Queries adicionales en get_context_data(): {queries_in_context}")
        print(f"✅ Total queries ejecutadas: {total_queries}")

        # Mostrar las queries adicionales de get_context_data
        if queries_in_context > 0:
            print("\n🔍 Queries adicionales en get_context_data():")
            for i, query in enumerate(connection.queries[queries_after_get_object:], 1):
                sql = (
                    query["sql"][:150] + "..."
                    if len(query["sql"]) > 150
                    else query["sql"]
                )
                time = query["time"]
                print(f"  {i}. [{time}s] {sql}")

        # Mostrar estadísticas del contexto
        print("\n📈 Estadísticas del contexto:")
        print(f"  🚨 Alertas cargadas: {context.get('count_alertas', 0)}")
        print(f"  👨‍👩‍👧‍👦 Familiares cargados: {context.get('count_familia', 0)}")
        print(f"  📋 Programas: {context.get('count_programas', 0)}")
        print(f"  🏠 Hogar familiares: {context.get('hogar_count_familia', 0)}")
        print(f"  🖼️ Imágenes: {len(context.get('files_img', []))}")
        print(f"  📄 Documentos: {len(context.get('files_docs', []))}")

        # Verificar que las dimensiones se cargaron
        dimensiones_cargadas = [
            name
            for name in [
                "dimensionfamilia",
                "dimensionvivienda",
                "dimensionsalud",
                "dimensiontrabajo",
            ]
            if context.get(name) is not None
        ]
        print(f"  📋 Dimensiones cargadas: {len(dimensiones_cargadas)}/4")

        # Evaluar el rendimiento
        if total_queries <= 15:
            print(f"\n🎉 ¡Excelente! Solo {total_queries} queries ejecutadas.")
        elif total_queries <= 25:
            print(f"\n✅ Bueno. {total_queries} queries ejecutadas (aceptable).")
        elif total_queries <= 40:
            print(
                f"\n⚠️ Regular. {total_queries} queries ejecutadas (se puede mejorar)."
            )
        else:
            print(
                f"\n❌ Malo. {total_queries} queries ejecutadas (necesita optimización)."
            )

        return True

    except Exception as e:
        print(f"❌ Error al ejecutar el debug: {e}")
        import traceback

        traceback.print_exc()
        return False


def show_query_analysis():
    """Muestra análisis detallado de las queries"""
    print("\n📊 Análisis de queries:")
    total_time = sum(float(q["time"]) for q in connection.queries)
    print(f"⏱️ Tiempo total: {total_time:.4f}s")

    # Agrupar queries por tipo
    select_queries = [
        q for q in connection.queries if q["sql"].strip().upper().startswith("SELECT")
    ]
    insert_queries = [
        q for q in connection.queries if q["sql"].strip().upper().startswith("INSERT")
    ]
    update_queries = [
        q for q in connection.queries if q["sql"].strip().upper().startswith("UPDATE")
    ]

    print(f"🔍 SELECT queries: {len(select_queries)}")
    print(f"➕ INSERT queries: {len(insert_queries)}")
    print(f"✏️ UPDATE queries: {len(update_queries)}")

    # Mostrar las queries más lentas
    slow_queries = sorted(
        connection.queries, key=lambda x: float(x["time"]), reverse=True
    )[:3]
    if slow_queries:
        print("\n🐌 3 queries más lentas:")
        for i, query in enumerate(slow_queries, 1):
            sql = (
                query["sql"][:100] + "..." if len(query["sql"]) > 100 else query["sql"]
            )
            print(f"  {i}. [{query['time']}s] {sql}")


def debug_view_queries(  # pylint: disable=too-many-locals,too-many-statements,too-many-branches
    view_class, url_pattern, model_class, view_name, pk=None, pk_kwarg="pk"
):
    """Framework genérico para depurar queries de cualquier vista"""

    # Verificar que existe al menos un objeto del modelo
    try:
        if pk:
            obj = model_class.objects.filter(pk=pk).first()
        else:
            obj = model_class.objects.first()

        if not obj:
            print(f"❌ No hay objetos {model_class.__name__} en la base de datos")
            return False, 0

        obj_id = obj.id
        print(f"🧪 Probando {view_name} con {model_class.__name__} ID: {obj_id}")

    except Exception as e:
        print(f"❌ Error al obtener {model_class.__name__}: {e}")
        return False, 0

    # Crear request factory y usuario
    factory = RequestFactory()
    url = url_pattern.format(**{pk_kwarg: obj_id}) if pk else url_pattern
    request = factory.get(url)

    # Crear usuario de prueba si no existe
    try:
        user = User.objects.get(username="debuguser")
    except User.DoesNotExist:
        user = User.objects.create_user(username="debuguser", password="debugpass")

    request.user = user

    # Crear vista
    view = view_class()
    setup_kwargs = {pk_kwarg: obj_id} if pk else {}
    view.setup(request, **setup_kwargs)

    # Resetear contador de queries
    reset_queries()

    try:
        if hasattr(view, "get_object") and pk:
            # Vista de detalle
            print(f"🔄 Ejecutando get_object() para {view_name}...")
            obj = view.get_object()
            queries_after_get_object = len(connection.queries)

            # Asignar el objeto a la vista para evitar errores
            view.object = obj

            print(f"🔄 Ejecutando get_context_data() para {view_name}...")
            context = view.get_context_data(object=obj)
        else:
            # Vista de lista
            print(f"🔄 Ejecutando get_queryset() para {view_name}...")
            queryset = view.get_queryset()
            queries_after_queryset = len(connection.queries)

            print(f"🔄 Ejecutando get_context_data() para {view_name}...")
            context = view.get_context_data(object_list=queryset)

        total_queries = len(connection.queries)

        print(f"✅ {view_name}: {total_queries} queries ejecutadas")

        # Mostrar queries ejecutadas
        if connection.queries:
            print(f"\n🔍 Queries en {view_name}:")
            for i, query in enumerate(connection.queries, 1):
                sql = (
                    query["sql"][:100] + "..."
                    if len(query["sql"]) > 100
                    else query["sql"]
                )
                time = query["time"]
                print(f"  {i}. [{time}s] {sql}")

        return True, total_queries

    except Exception as e:
        print(f"❌ Error en {view_name}: {e}")
        import traceback

        traceback.print_exc()
        return False, 0


def debug_all_views():  # pylint: disable=too-many-locals,too-many-statements,too-many-branches,unused-variable
    """Depura todas las vistas principales del sistema"""

    print("🔍 Depurando queries en todas las vistas principales...\n")

    results = {}

    # Debug CiudadanosDetailView (ya optimizada)
    from ciudadanos.views import CiudadanosDetailView
    from ciudadanos.models import Ciudadano

    _, queries = debug_view_queries(
        CiudadanosDetailView,
        "/ciudadanos/ver/{pk}/",
        Ciudadano,
        "CiudadanosDetailView",
        pk=True,
        pk_kwarg="pk",  # CiudadanosDetailView usa 'pk' por defecto
    )
    results["CiudadanosDetailView"] = queries

    # Debug ComedoresAcompanamientoListView (acompañamientos)
    # Debug Toolbar: 14 queries en 33.73ms
    print("\n" + "=" * 50)
    from acompanamientos.views import ComedoresAcompanamientoListView
    from comedores.models import Comedor

    success, queries = debug_view_queries(
        ComedoresAcompanamientoListView,
        "/acompanamientos/acompanamiento/",
        Comedor,
        "ComedoresAcompanamientoListView (acompañamientos/list)",
        pk=False,  # Es una ListView
    )
    results["ComedoresAcompanamientoListView"] = queries

    # Debug AcompanamientoDetailView
    print("\n" + "=" * 50)
    try:
        from acompanamientos.views import AcompanamientoDetailView

        success, queries = debug_view_queries(
            AcompanamientoDetailView,
            "/acompanamientos/ver/{comedor_id}/",
            Comedor,  # Usa el modelo Comedor
            "AcompanamientoDetailView (acompañamientos/detail)",
            pk=True,
            pk_kwarg="comedor_id",  # Usar comedor_id como especifica la vista
        )
        results["AcompanamientoDetailView"] = queries
    except Exception as e:
        print(f"❌ No se pudo depurar AcompanamientoDetailView: {e}")

    # Debug ComedorListView
    print("\n" + "=" * 50)
    try:
        from comedores.views import ComedorListView

        success, queries = debug_view_queries(
            ComedorListView,
            "/comedores/",
            Comedor,
            "ComedorListView (comedores/list)",
            pk=False,
        )
        results["ComedorListView"] = queries
    except Exception as e:
        print(f"❌ No se pudo depurar ComedorListView: {e}")

    # Debug ComedorDetailView
    print("\n" + "=" * 50)
    try:
        from comedores.views import ComedorDetailView

        success, queries = debug_view_queries(
            ComedorDetailView,
            "/comedores/ver/{pk}/",
            Comedor,
            "ComedorDetailView (comedores/detail)",
            pk=True,
            pk_kwarg="pk",  # ComedorDetailView usa 'pk' por defecto
        )
        results["ComedorDetailView"] = queries
    except Exception as e:
        print(f"❌ No se pudo depurar ComedorDetailView: {e}")

    # Debug CiudadanosListView
    print("\n" + "=" * 50)
    try:
        from ciudadanos.views import CiudadanosListView

        success, queries = debug_view_queries(
            CiudadanosListView,
            "/ciudadanos/",
            Ciudadano,
            "CiudadanosListView (ciudadanos/list)",
            pk=False,
        )
        results["CiudadanosListView"] = queries
    except Exception as e:
        print(f"❌ No se pudo depurar CiudadanosListView: {e}")

    # Debug OrganizacionListView
    print("\n" + "=" * 50)
    try:
        from organizaciones.views import OrganizacionListView
        from organizaciones.models import Organizacion

        success, queries = debug_view_queries(
            OrganizacionListView,
            "/organizaciones/",
            Organizacion,
            "OrganizacionListView (organizaciones/list)",
            pk=False,
        )
        results["OrganizacionListView"] = queries
    except Exception as e:
        print(f"❌ No se pudo depurar OrganizacionListView: {e}")

    # Debug OrganizacionDetailView
    print("\n" + "=" * 50)
    try:
        from organizaciones.views import OrganizacionDetailView
        from organizaciones.models import Organizacion

        success, queries = debug_view_queries(
            OrganizacionDetailView,
            "/organizaciones/ver/{pk}/",
            Organizacion,
            "OrganizacionDetailView (organizaciones/detail)",
            pk=True,
            pk_kwarg="pk",
        )
        results["OrganizacionDetailView"] = queries
    except Exception as e:
        print(f"❌ No se pudo depurar OrganizacionDetailView: {e}")

    # Debug DuplaListView
    print("\n" + "=" * 50)
    try:
        from duplas.views import DuplaListView
        from duplas.models import Dupla

        success, queries = debug_view_queries(
            DuplaListView,
            "/duplas/",
            Dupla,
            "DuplaListView (duplas/list)",
            pk=False,
        )
        results["DuplaListView"] = queries
    except Exception as e:
        print(f"❌ No se pudo depurar DuplaListView: {e}")

    # Debug DuplaDetailView
    print("\n" + "=" * 50)
    try:
        from duplas.views import DuplaDetailView
        from duplas.models import Dupla

        success, queries = debug_view_queries(
            DuplaDetailView,
            "/duplas/ver/{pk}/",
            Dupla,
            "DuplaDetailView (duplas/detail)",
            pk=True,
            pk_kwarg="pk",
        )
        results["DuplaDetailView"] = queries
    except Exception as e:
        print(f"❌ No se pudo depurar DuplaDetailView: {e}")

    # Debug ExpedientesPagosListView
    print("\n" + "=" * 50)
    try:
        from expedientespagos.views import ExpedientesPagosListView
        from expedientespagos.models import ExpedientePago

        success, queries = debug_view_queries(
            ExpedientesPagosListView,
            "/expedientes-pagos/",
            ExpedientePago,
            "ExpedientesPagosListView (expedientes/list)",
            pk=False,
        )
        results["ExpedientesPagosListView"] = queries
    except Exception as e:
        print(f"❌ No se pudo depurar ExpedientesPagosListView: {e}")

    # Debug ExpedientesPagosDetailView
    print("\n" + "=" * 50)
    try:
        from expedientespagos.views import ExpedientesPagosDetailView
        from expedientespagos.models import ExpedientePago

        success, queries = debug_view_queries(
            ExpedientesPagosDetailView,
            "/expedientes-pagos/ver/{pk}/",
            ExpedientePago,
            "ExpedientesPagosDetailView (expedientes/detail)",
            pk=True,
            pk_kwarg="pk",
        )
        results["ExpedientesPagosDetailView"] = queries
    except Exception as e:
        print(f"❌ No se pudo depurar ExpedientesPagosDetailView: {e}")

    # Debug RendicionCuentaMensualListView
    print("\n" + "=" * 50)
    try:
        from rendicioncuentasmensual.views import RendicionCuentaMensualListView
        from rendicioncuentasmensual.models import RendicionCuentaMensual

        success, queries = debug_view_queries(
            RendicionCuentaMensualListView,
            "/rendicion-mensual/",
            RendicionCuentaMensual,
            "RendicionCuentaMensualListView (rendicion-mensual/list)",
            pk=False,
        )
        results["RendicionCuentaMensualListView"] = queries
    except Exception as e:
        print(f"❌ No se pudo depurar RendicionCuentaMensualListView: {e}")

    # Debug RendicionCuentaMensualDetailView
    print("\n" + "=" * 50)
    try:
        from rendicioncuentasmensual.views import RendicionCuentaMensualDetailView
        from rendicioncuentasmensual.models import RendicionCuentaMensual

        success, queries = debug_view_queries(
            RendicionCuentaMensualDetailView,
            "/rendicion-mensual/ver/{pk}/",
            RendicionCuentaMensual,
            "RendicionCuentaMensualDetailView (rendicion-mensual/detail)",
            pk=True,
            pk_kwarg="pk",
        )
        results["RendicionCuentaMensualDetailView"] = queries
    except Exception as e:
        print(f"❌ No se pudo depurar RendicionCuentaMensualDetailView: {e}")

    # Debug DerivacionListView (ciudadanos adicional)
    print("\n" + "=" * 50)
    try:
        from ciudadanos.views import DerivacionListView
        from ciudadanos.models import Derivacion

        success, queries = debug_view_queries(
            DerivacionListView,
            "/ciudadanos/derivaciones/",
            Derivacion,
            "DerivacionListView (ciudadanos/derivaciones/list)",
            pk=False,
        )
        results["DerivacionListView"] = queries
    except Exception as e:
        print(f"❌ No se pudo depurar DerivacionListView: {e}")

    # Debug DerivacionDetailView (ciudadanos adicional)
    print("\n" + "=" * 50)
    try:
        from ciudadanos.views import DerivacionDetailView
        from ciudadanos.models import Derivacion

        success, queries = debug_view_queries(
            DerivacionDetailView,
            "/ciudadanos/derivaciones/ver/{pk}/",
            Derivacion,
            "DerivacionDetailView (ciudadanos/derivaciones/detail)",
            pk=True,
            pk_kwarg="pk",
        )
        results["DerivacionDetailView"] = queries
    except Exception as e:
        print(f"❌ No se pudo depurar DerivacionDetailView: {e}")

    # Debug AlertaListView (ciudadanos adicional)
    print("\n" + "=" * 50)
    try:
        from ciudadanos.views import AlertaListView
        from ciudadanos.models import Alerta

        success, queries = debug_view_queries(
            AlertaListView,
            "/ciudadanos/alertas/",
            Alerta,
            "AlertaListView (ciudadanos/alertas/list)",
            pk=False,
        )
        results["AlertaListView"] = queries
    except Exception as e:
        print(f"❌ No se pudo depurar AlertaListView: {e}")

    # Resumen final
    print("\n📊 Resumen de queries por vista:")
    for view_name, query_count in results.items():
        if query_count <= 15:
            status = "🎉 Excelente"
        elif query_count <= 25:
            status = "✅ Bueno"
        elif query_count <= 40:
            status = "⚠️ Regular"
        else:
            status = "❌ Necesita optimización"

        print(f"  {view_name}: {query_count} queries - {status}")

    return results


if __name__ == "__main__":
    print("🔍 Depurando todas las vistas del sistema SISOC...")

    # Depurar todas las vistas
    results = debug_all_views()

    if results:
        print("\n📊 Análisis general:")
        show_query_analysis()

        # Mostrar recomendaciones
        print("\n💡 Recomendaciones:")
        for view_name, query_count in results.items():
            if query_count > 25:
                print(
                    f"  ⚠️ {view_name}: Considerar optimización ({query_count} queries)"
                )
            elif query_count > 15:
                print(
                    f"  📝 {view_name}: Revisar si se puede mejorar ({query_count} queries)"
                )
            else:
                print(f"  ✅ {view_name}: Buen rendimiento ({query_count} queries)")

    sys.exit(0 if results else 1)
