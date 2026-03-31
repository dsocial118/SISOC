from django.core.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db.models import Count, Prefetch, Q
from django.http import Http404
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from core.models import Dia, Sexo

from pwa.api_serializers import (
    ActividadEspacioPWACreateUpdateSerializer,
    ActividadEspacioPWAListSerializer,
    CatalogoActividadPWASerializer,
    ColaboradorActividadCatalogoSerializer,
    ColaboradorEspacioPWACreateUpdateSerializer,
    ColaboradorEspacioPWAListSerializer,
    ColaboradorGeneroPWAListSerializer,
    DiaSerializer,
    InscriptoActividadPWAListSerializer,
    MensajeEspacioPWASerializer,
    NominaEspacioPWACreateUpdateSerializer,
    NominaEspacioPWAListSerializer,
    NominaRenaperPreviewSerializer,
    RegistroAsistenciaNominaPWAListSerializer,
    SexoSerializer,
)
from pwa.models import (
    ActividadEspacioPWA,
    CatalogoActividadPWA,
    InscriptoActividadEspacioPWA,
    RegistroAsistenciaNominaPWA,
)
from pwa.services.actividades_service import (
    create_actividad_espacio,
    soft_delete_actividad_espacio,
    update_actividad_espacio,
)
from pwa.services.mensajes_service import (
    get_mensaje_for_espacio,
    list_mensajes_for_espacio,
    marcar_mensaje_como_visto,
)
from pwa.services.nomina_service import (
    create_nomina_persona,
    get_periodo_mensual_actual,
    is_menor,
    registrar_asistencia_nomina_mes_actual,
    soft_delete_nomina_persona,
    split_gender_bucket,
    update_nomina_persona,
)
from users.api_permissions import IsPWAAuthenticatedToken
from users.api_permissions import IsPWARepresentativeForComedor
from comedores.models import ActividadColaboradorEspacio, ColaboradorEspacio, Nomina
from comedores.services.colaborador_espacio_service import ColaboradorEspacioService
from comedores.services.comedor_service.impl import ComedorService
from ciudadanos.models import Ciudadano


class PwaHealthViewSet(viewsets.ViewSet):
    """Healthcheck básico para endpoints API de la app PWA."""

    permission_classes = [AllowAny]

    def list(self, request):
        return Response({"status": "ok"})


@extend_schema(tags=["PWA Mensajes"])
class MensajeEspacioPWAViewSet(viewsets.ViewSet):
    """Mensajes por espacio en PWA a partir de comunicados de la webapp."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsPWAAuthenticatedToken]

    def list(self, request, comedor_id=None):
        queryset = list_mensajes_for_espacio(comedor_id=comedor_id, user=request.user)
        items = list(queryset)
        paginator = Paginator(items, 20)
        page_number = request.query_params.get("page", 1)
        page_obj = paginator.get_page(page_number)
        serializer = MensajeEspacioPWASerializer(
            page_obj.object_list,
            many=True,
            context={
                "request": request,
                "comedor_id": comedor_id,
                "user": request.user,
            },
        )
        serialized_items = serializer.data
        unread_count = sum(1 for item in serialized_items if not item["visto"])
        unread_general_count = sum(
            1
            for item in serialized_items
            if item["seccion"] == "general" and not item["visto"]
        )
        unread_espacio_count = sum(
            1
            for item in serialized_items
            if item["seccion"] == "espacio" and not item["visto"]
        )
        return Response(
            {
                "count": paginator.count,
                "num_pages": paginator.num_pages,
                "current_page": page_obj.number,
                "unread_count": unread_count,
                "unread_general_count": unread_general_count,
                "unread_espacio_count": unread_espacio_count,
                "results": serialized_items,
                "secciones": {
                    "generales": [
                        item for item in serialized_items if item["seccion"] == "general"
                    ],
                    "espacios": [
                        item for item in serialized_items if item["seccion"] == "espacio"
                    ],
                },
            },
            status=status.HTTP_200_OK,
        )

    def retrieve(self, request, comedor_id=None, pk=None):
        try:
            mensaje = get_mensaje_for_espacio(
                comedor_id=comedor_id,
                comunicado_id=int(pk),
                user=request.user,
            )
        except (TypeError, ValueError):
            return Response(
                {"detail": "mensaje_id inválido."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Http404 as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = MensajeEspacioPWASerializer(
            mensaje,
            context={
                "request": request,
                "comedor_id": comedor_id,
                "user": request.user,
            },
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def marcar_visto(self, request, comedor_id=None, pk=None):
        try:
            mensaje, _ = marcar_mensaje_como_visto(
                comedor_id=comedor_id,
                comunicado_id=int(pk),
                actor=request.user,
            )
        except (TypeError, ValueError):
            return Response(
                {"detail": "mensaje_id inválido."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Http404 as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = MensajeEspacioPWASerializer(
            mensaje,
            context={
                "request": request,
                "comedor_id": comedor_id,
                "user": request.user,
            },
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(tags=["PWA Colaboradores"])
class ColaboradorEspacioPWAViewSet(viewsets.ViewSet):
    """CRUD de colaboradores por espacio para la app PWA."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsPWARepresentativeForComedor]

    def _get_queryset(self):
        comedor_id = self.kwargs["comedor_id"]
        return (
            ColaboradorEspacio.objects.filter(comedor_id=comedor_id)
            .select_related("ciudadano__sexo")
            .prefetch_related("actividades")
            .order_by("fecha_baja", "ciudadano__apellido", "ciudadano__nombre", "-id")
        )

    def _get_object(self):
        return self._get_queryset().filter(pk=self.kwargs["pk"]).first()

    def list(self, request, comedor_id=None):
        serializer = ColaboradorEspacioPWAListSerializer(
            self._get_queryset(), many=True
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, comedor_id=None):
        serializer = ColaboradorEspacioPWACreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comedor = ComedorService.get_scoped_comedor_or_404(comedor_id, request.user)
        cleaned_data = dict(serializer.validated_data)
        dni = cleaned_data.pop("dni", None)
        ciudadano_id = cleaned_data.pop("ciudadano_id", None)
        actividad_ids = cleaned_data.pop("actividad_ids", [])
        if actividad_ids:
            cleaned_data["actividades"] = list(
                ActividadColaboradorEspacio.objects.filter(
                    id__in=actividad_ids,
                    activo=True,
                ).order_by("orden", "id")
            )

        result = ColaboradorEspacioService.create_for_comedor(
            comedor=comedor,
            actor=request.user,
            cleaned_data=cleaned_data,
            ciudadano_id=ciudadano_id,
            dni=dni,
        )
        if not result.get("success"):
            return Response(
                {"detail": result.get("message", "No se pudo crear el colaborador.")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        response_serializer = ColaboradorEspacioPWAListSerializer(result["colaborador"])
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, comedor_id=None, pk=None):
        colaborador = self._get_object()
        if not colaborador:
            return Response(
                {"detail": "Colaborador no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = ColaboradorEspacioPWACreateUpdateSerializer(
            colaborador,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        cleaned_data = dict(serializer.validated_data)
        actividad_ids = cleaned_data.pop("actividad_ids", None)
        if actividad_ids is not None:
            cleaned_data["actividades"] = list(
                ActividadColaboradorEspacio.objects.filter(
                    id__in=actividad_ids,
                    activo=True,
                ).order_by("orden", "id")
            )
        result = ColaboradorEspacioService.update_for_comedor(
            colaborador=colaborador,
            actor=request.user,
            cleaned_data=cleaned_data,
        )
        if not result.get("success"):
            return Response(
                {
                    "detail": result.get(
                        "message", "No se pudo actualizar el colaborador."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        response_serializer = ColaboradorEspacioPWAListSerializer(result["colaborador"])
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, comedor_id=None, pk=None):
        colaborador = self._get_object()
        if not colaborador:
            return Response(
                {"detail": "Colaborador no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        result = ColaboradorEspacioService.soft_delete(
            colaborador=colaborador, actor=request.user
        )
        if not result.get("success"):
            return Response(
                {
                    "detail": result.get(
                        "message", "No se pudo dar de baja el colaborador."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def generos(self, request, comedor_id=None):
        serializer = ColaboradorGeneroPWAListSerializer(
            [
                {"id": code, "label": label}
                for code, label in ColaboradorEspacio.GeneroChoices.choices
            ],
            many=True,
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def actividades(self, request, comedor_id=None):
        queryset = ActividadColaboradorEspacio.objects.filter(activo=True).order_by(
            "orden", "id"
        )
        serializer = ColaboradorActividadCatalogoSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @staticmethod
    def _renaper_unavailable_message():
        return (
            "No se pudo conectar con RENAPER en este momento. "
            "Probá nuevamente en unos minutos."
        )

    @classmethod
    def _normalize_renaper_error_message(cls, message):
        normalized_message = str(
            message or "No se pudieron obtener datos desde RENAPER."
        )
        lowered = normalized_message.lower()
        if (
            "timed out" in lowered
            or "connectionpool" in lowered
            or "max retries exceeded" in lowered
        ):
            return cls._renaper_unavailable_message()
        return normalized_message

    def preview_dni(self, request, comedor_id=None):
        serializer = NominaRenaperPreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dni = serializer.validated_data["dni"]

        ciudadano = (
            Ciudadano.objects.select_related("sexo")
            .filter(
                documento=int(dni),
                deleted_at__isnull=True,
            )
            .first()
        )
        if ciudadano:
            data = ColaboradorEspacioService.build_preview_from_ciudadano(ciudadano)
            colaborador_existente = ColaboradorEspacio.objects.filter(
                comedor_id=comedor_id,
                ciudadano=ciudadano,
                fecha_baja__isnull=True,
            ).first()
            return Response(
                {
                    "source": "sisoc",
                    "ciudadano_id": ciudadano.id,
                    "ya_registrado_en_espacio": bool(colaborador_existente),
                    "colaborador_activo_id": (
                        colaborador_existente.id if colaborador_existente else None
                    ),
                    **data,
                },
                status=status.HTTP_200_OK,
            )

        try:
            renaper_result = ComedorService.obtener_datos_ciudadano_desde_renaper(dni)
        except Exception:
            return Response(
                {"detail": self._renaper_unavailable_message()},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not renaper_result.get("success"):
            message = self._normalize_renaper_error_message(
                renaper_result.get("message")
            )
            return Response(
                {"detail": message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = ColaboradorEspacioService.build_preview_from_renaper_data(
            renaper_result.get("data") or {}
        )
        return Response(
            {
                "source": "renaper",
                "ciudadano_id": None,
                "ya_registrado_en_espacio": False,
                "colaborador_activo_id": None,
                **data,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["PWA Actividades"])
class CatalogoActividadPWAViewSet(viewsets.ViewSet):
    """Listado de catalogo cerrado de actividades para formularios PWA."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsPWARepresentativeForComedor]

    def list(self, request, comedor_id=None):
        queryset = CatalogoActividadPWA.objects.filter(activo=True).order_by(
            "categoria", "actividad", "id"
        )
        serializer = CatalogoActividadPWASerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def dias(self, request, comedor_id=None):
        queryset = Dia.objects.order_by("id")
        serializer = DiaSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(tags=["PWA Actividades"])
class ActividadEspacioPWAViewSet(viewsets.ViewSet):
    """CRUD de actividades por espacio para la app PWA."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsPWARepresentativeForComedor]

    def _get_queryset(self):
        comedor_id = self.kwargs["comedor_id"]
        return (
            ActividadEspacioPWA.objects.filter(
                comedor_id=comedor_id,
                activo=True,
            )
            .select_related("catalogo_actividad", "dia_actividad")
            .annotate(
                cantidad_inscriptos=Count(
                    "inscriptos",
                    filter=Q(inscriptos__activo=True),
                )
            )
            .order_by("dia_actividad_id", "hora_inicio", "hora_fin", "catalogo_actividad__actividad", "id")
        )

    def _get_object(self):
        return self._get_queryset().filter(pk=self.kwargs["pk"]).first()

    def list(self, request, comedor_id=None):
        serializer = ActividadEspacioPWAListSerializer(self._get_queryset(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, comedor_id=None, pk=None):
        actividad = self._get_object()
        if not actividad:
            return Response(
                {"detail": "Actividad no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = ActividadEspacioPWAListSerializer(actividad)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, comedor_id=None):
        serializer = ActividadEspacioPWACreateUpdateSerializer(
            data=request.data,
            context={"comedor_id": comedor_id},
        )
        serializer.is_valid(raise_exception=True)
        actividad = create_actividad_espacio(
            comedor_id=comedor_id,
            actor=request.user,
            data=serializer.validated_data,
        )
        actividad = self._get_queryset().filter(pk=actividad.pk).first()
        response_serializer = ActividadEspacioPWAListSerializer(actividad)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, comedor_id=None, pk=None):
        actividad = self._get_object()
        if not actividad:
            return Response(
                {"detail": "Actividad no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = ActividadEspacioPWACreateUpdateSerializer(
            actividad,
            data=request.data,
            partial=True,
            context={"comedor_id": comedor_id},
        )
        serializer.is_valid(raise_exception=True)
        actividad = update_actividad_espacio(
            actividad=actividad,
            actor=request.user,
            data=serializer.validated_data,
        )
        actividad = self._get_queryset().filter(pk=actividad.pk).first()
        response_serializer = ActividadEspacioPWAListSerializer(actividad)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, comedor_id=None, pk=None):
        actividad = self._get_object()
        if not actividad:
            return Response(
                {"detail": "Actividad no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            soft_delete_actividad_espacio(actividad=actividad, actor=request.user)
        except ValidationError as exc:
            detail = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def inscriptos(self, request, comedor_id=None, pk=None):
        actividad = self._get_object()
        if not actividad:
            return Response(
                {"detail": "Actividad no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )
        queryset = (
            actividad.inscriptos.filter(activo=True)
            .select_related("nomina", "nomina__ciudadano", "nomina__ciudadano__sexo")
            .order_by("nomina__ciudadano__apellido", "nomina__ciudadano__nombre", "id")
        )
        serializer = InscriptoActividadPWAListSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(tags=["PWA Nómina"])
class NominaEspacioPWAViewSet(viewsets.ViewSet):
    """Gestión de nómina consolidada para la app PWA."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsPWARepresentativeForComedor]

    def _safe_profile(self, row):
        try:
            return row.perfil_pwa
        except ObjectDoesNotExist:
            return None

    def _base_queryset(self):
        comedor_id = self.kwargs["comedor_id"]
        periodo_actual = get_periodo_mensual_actual()
        return (
            Nomina.objects.filter(
                admision__comedor_id=comedor_id,
                deleted_at__isnull=True,
                estado=Nomina.ESTADO_ACTIVO,
            )
            .select_related("ciudadano", "ciudadano__sexo", "perfil_pwa")
            .annotate(
                cantidad_actividades_pwa=Count(
                    "inscripciones_actividad_pwa__actividad_espacio__catalogo_actividad_id",
                    filter=Q(inscripciones_actividad_pwa__activo=True),
                    distinct=True,
                )
            )
            .prefetch_related(
                Prefetch(
                    "registros_asistencia_pwa",
                    queryset=RegistroAsistenciaNominaPWA.objects.filter(
                        periodicidad=RegistroAsistenciaNominaPWA.PERIODICIDAD_MENSUAL,
                        periodo_referencia=periodo_actual,
                    )
                    .select_related("tomado_por")
                    .order_by("-fecha_toma_asistencia", "-id"),
                    to_attr="asistencia_mes_actual_pwa",
                )
            )
            .order_by("ciudadano__apellido", "ciudadano__nombre", "id")
        )

    def _detail_queryset(self):
        return self._base_queryset().prefetch_related(
            Prefetch(
                "inscripciones_actividad_pwa",
                queryset=InscriptoActividadEspacioPWA.objects.filter(activo=True)
                .select_related(
                    "actividad_espacio",
                    "actividad_espacio__catalogo_actividad",
                    "actividad_espacio__dia_actividad",
                )
                .order_by("id"),
                to_attr="inscripciones_actividad_pwa_activas",
            )
        )

    def _apply_tab_filter(self, rows: list[Nomina], tab: str) -> list[Nomina]:
        tab = (tab or "consolidada").strip().lower()
        if tab == "alimentaria":
            return [
                row
                for row in rows
                if getattr(self._safe_profile(row), "asistencia_alimentaria", True)
            ]
        if tab == "formacion":
            return [
                row
                for row in rows
                if getattr(self._safe_profile(row), "asistencia_actividades", False)
            ]
        return rows

    def _apply_search_filter(self, rows: list[Nomina], q: str) -> list[Nomina]:
        term = (q or "").strip().lower()
        if not term:
            return rows

        filtered = []
        for row in rows:
            ciudadano = getattr(row, "ciudadano", None)
            if not ciudadano:
                continue
            gender_name = getattr(getattr(ciudadano, "sexo", None), "sexo", "") or ""
            candidate_parts = [
                str(getattr(ciudadano, "documento", "") or ""),
                str(getattr(ciudadano, "apellido", "") or ""),
                str(getattr(ciudadano, "nombre", "") or ""),
                str(gender_name or ""),
            ]
            hay_match = any(term in part.lower() for part in candidate_parts if part)
            if hay_match:
                filtered.append(row)
        return filtered

    def _dedupe_rows(self, rows: list[Nomina]) -> list[Nomina]:
        unique_rows = []
        seen_ciudadano_ids = set()
        for row in rows:
            ciudadano_id = getattr(row, "ciudadano_id", None)
            dedupe_key = ciudadano_id if ciudadano_id else row.id
            if dedupe_key in seen_ciudadano_ids:
                continue
            seen_ciudadano_ids.add(dedupe_key)
            unique_rows.append(row)
        return unique_rows

    def _build_stats(self, rows: list[Nomina]) -> dict:
        genders = {"M": 0, "F": 0, "X": 0}
        menores = 0
        mayores = 0
        for row in rows:
            ciudadano = getattr(row, "ciudadano", None)
            if not ciudadano:
                continue
            gender_name = getattr(getattr(ciudadano, "sexo", None), "sexo", "")
            bucket = split_gender_bucket(gender_name)
            genders[bucket] += 1
            if is_menor(getattr(ciudadano, "fecha_nacimiento", None)):
                menores += 1
            else:
                mayores += 1
        return {
            "total_nomina": len(rows),
            "genero": genders,
            "menores_edad": menores,
            "mayores_edad": mayores,
        }

    def list(self, request, comedor_id=None):
        rows = list(self._base_queryset())
        rows = self._dedupe_rows(rows)
        tab = request.query_params.get("tab", "consolidada")
        q = request.query_params.get("q", "")
        rows = self._apply_tab_filter(rows, tab)
        rows = self._apply_search_filter(rows, q)
        serializer = NominaEspacioPWAListSerializer(
            rows,
            many=True,
            context={"include_details": False},
        )
        return Response(
            {
                "tab": tab,
                "stats": self._build_stats(rows),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def create(self, request, comedor_id=None):
        serializer = NominaEspacioPWACreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            nomina = create_nomina_persona(
                comedor_id=comedor_id,
                actor=request.user,
                data=serializer.validated_data,
            )
        except ValidationError as exc:
            detail = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)
        nomina = self._base_queryset().filter(pk=nomina.pk).first()
        response_serializer = NominaEspacioPWAListSerializer(nomina)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def _get_object(self):
        return self._detail_queryset().filter(pk=self.kwargs["pk"]).first()

    def retrieve(self, request, comedor_id=None, pk=None):
        nomina = self._get_object()
        if not nomina:
            return Response(
                {"detail": "Registro de nómina no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        response_serializer = NominaEspacioPWAListSerializer(
            nomina,
            context={"include_details": True},
        )
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, comedor_id=None, pk=None):
        nomina = self._get_object()
        if not nomina:
            return Response(
                {"detail": "Registro de nómina no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = NominaEspacioPWACreateUpdateSerializer(
            data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        try:
            nomina = update_nomina_persona(
                nomina=nomina,
                actor=request.user,
                data=serializer.validated_data,
            )
        except ValidationError as exc:
            detail = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)
        nomina = self._base_queryset().filter(pk=nomina.pk).first()
        response_serializer = NominaEspacioPWAListSerializer(nomina)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, comedor_id=None, pk=None):
        nomina = self._get_object()
        if not nomina:
            return Response(
                {"detail": "Registro de nómina no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            soft_delete_nomina_persona(nomina=nomina, actor=request.user)
        except ValidationError as exc:
            detail = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def registrar_asistencia(self, request, comedor_id=None, pk=None):
        nomina = self._get_object()
        if not nomina:
            return Response(
                {"detail": "Registro de nómina no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        registro, created = registrar_asistencia_nomina_mes_actual(
            nomina=nomina,
            actor=request.user,
        )
        serializer = RegistroAsistenciaNominaPWAListSerializer(registro)
        return Response(
            {
                "created": created,
                "registro": serializer.data,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def historial_asistencia(self, request, comedor_id=None, pk=None):
        nomina = self._get_object()
        if not nomina:
            return Response(
                {"detail": "Registro de nómina no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        registros = nomina.registros_asistencia_pwa.select_related("tomado_por").order_by(
            "-periodo_referencia", "-fecha_toma_asistencia", "-id"
        )
        serializer = RegistroAsistenciaNominaPWAListSerializer(registros, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def generos(self, request, comedor_id=None):
        serializer = SexoSerializer(Sexo.objects.order_by("id"), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @staticmethod
    def _renaper_unavailable_message():
        return (
            "No se pudo conectar con RENAPER en este momento. "
            "Probá nuevamente en unos minutos."
        )

    @staticmethod
    def _serialize_ciudadano_local(ciudadano, dni):
        sexo_local = (
            getattr(ciudadano.sexo, "sexo", "")
            if getattr(ciudadano, "sexo", None)
            else ""
        )
        fecha_local = (
            ciudadano.fecha_nacimiento.isoformat()
            if getattr(ciudadano, "fecha_nacimiento", None)
            else None
        )
        return {
            "nombre": ciudadano.nombre or "",
            "apellido": ciudadano.apellido or "",
            "documento": str(ciudadano.documento or dni),
            "fecha_nacimiento": fecha_local,
            "sexo": sexo_local,
        }

    @classmethod
    def _normalize_renaper_error_message(cls, message):
        normalized_message = str(
            message or "No se pudieron obtener datos desde RENAPER."
        )
        lowered = normalized_message.lower()
        if (
            "timed out" in lowered
            or "connectionpool" in lowered
            or "max retries exceeded" in lowered
        ):
            return cls._renaper_unavailable_message()
        return normalized_message

    @staticmethod
    def _resolve_sexo_label(sexo_value):
        sexo_label = ""
        if not sexo_value:
            return sexo_label
        if hasattr(sexo_value, "sexo"):
            sexo_label = getattr(sexo_value, "sexo", "") or ""
        elif isinstance(sexo_value, str):
            sexo_normalizado = sexo_value.strip().upper()
            if sexo_normalizado in ("M", "MASCULINO"):
                sexo_label = "Masculino"
            elif sexo_normalizado in ("F", "FEMENINO"):
                sexo_label = "Femenino"
            elif sexo_normalizado in ("X", "NO BINARIO", "NB"):
                sexo_label = "X"
            else:
                sexo_label = sexo_value.strip()
        else:
            sexo_obj = Sexo.objects.filter(pk=sexo_value).first()
            sexo_label = getattr(sexo_obj, "sexo", "") if sexo_obj else ""
        return sexo_label

    @classmethod
    def _serialize_renaper_data(cls, data, dni):
        fecha_nacimiento = data.get("fecha_nacimiento")
        if fecha_nacimiento and hasattr(fecha_nacimiento, "isoformat"):
            fecha_nacimiento = fecha_nacimiento.isoformat()

        return {
            "nombre": data.get("nombre") or "",
            "apellido": data.get("apellido") or "",
            "documento": str(data.get("documento") or dni),
            "fecha_nacimiento": fecha_nacimiento,
            "sexo": cls._resolve_sexo_label(data.get("sexo")),
        }

    def preview_dni(self, request, comedor_id=None):
        serializer = NominaRenaperPreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dni = serializer.validated_data["dni"]

        # Fallback local para no depender del servicio externo cuando el ciudadano ya existe.
        ciudadano_local = Ciudadano.objects.filter(
            documento=int(dni),
            deleted_at__isnull=True,
        ).first()
        if ciudadano_local:
            return Response(
                self._serialize_ciudadano_local(ciudadano_local, dni),
                status=status.HTTP_200_OK,
            )

        try:
            renaper_result = ComedorService.obtener_datos_ciudadano_desde_renaper(dni)
        except Exception:
            return Response(
                {"detail": self._renaper_unavailable_message()},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not renaper_result.get("success"):
            message = self._normalize_renaper_error_message(
                renaper_result.get("message")
            )
            return Response(
                {"detail": message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = renaper_result.get("data") or {}
        return Response(
            self._serialize_renaper_data(data, dni),
            status=status.HTTP_200_OK,
        )
