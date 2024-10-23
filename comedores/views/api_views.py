from django.forms.models import model_to_dict
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_api_key.permissions import HasAPIKey
from comedores.models import Comedor, Observacion, Relevamiento
from comedores.serializers.comedor_serializer import ComedorSerializer
from comedores.serializers.relevamiento_serializer import RelevamientoSerializer
from comedores.serializers.observacion_serializer import ObservacionSerializer
from comedores.utils import format_serializer_errors, format_fecha_django


class ComedorRelevamientoObservacionApiView(APIView):
    permission_classes = [HasAPIKey]

    def post(self, request):
        comedor_data = request.data.get("comedor")
        relevamiento_data = request.data.get("relevamiento")
        observacion_data = request.data.get("observacion")

        try:
            comedor = Comedor.objects.get(gestionar_uid=comedor_data["gestionar_uid"])
        except Comedor.DoesNotExist:
            comedor_serializer = ComedorSerializer(data=comedor_data).clean()
            if comedor_serializer.is_valid():
                comedor_serializer.save()
                comedor = comedor_serializer.instance
            else:
                error_message_str = format_serializer_errors(comedor_serializer)

                return Response(
                    f"Error en comedor: '{error_message_str}'",
                    status=status.HTTP_400_BAD_REQUEST,
                )

        relevamiento_data["comedor"] = comedor.id
        relevamiento_serializer = RelevamientoSerializer(data=relevamiento_data).clean()
        if relevamiento_serializer.is_valid():
            relevamiento_serializer.save()
        else:
            error_message_str = format_serializer_errors(relevamiento_serializer)

            return Response(
                f"Error en relevamiento: '{error_message_str}'",
                status=status.HTTP_400_BAD_REQUEST,
            )

        observacion_data["comedor"] = comedor.id
        observacion_serializer = ObservacionSerializer(data=observacion_data).clean()
        if observacion_serializer.is_valid():
            observacion_serializer.save()
        else:
            error_message_str = format_serializer_errors(observacion_serializer)

            return Response(
                f"Error en observación: '{error_message_str}'",
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "comedor": model_to_dict(comedor),
                "relevamiento": relevamiento_serializer.data,
                "observacion": observacion_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class ComedorApiView(APIView):
    permission_classes = [HasAPIKey]

    def patch(self, request):
        comedor = Comedor.objects.get(gestionar_uid=request.data["gestionar_uid"])
        comedor_serializer = ComedorSerializer(
            comedor, data=request.data, partial=True
        ).clean()
        if comedor_serializer.is_valid():
            comedor_serializer.save()
            comedor = comedor_serializer.instance
        else:
            error_message_str = format_serializer_errors(comedor_serializer)

            return Response(
                f"Error en comedor: '{error_message_str}'",
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(ComedorSerializer(comedor).data, status=status.HTTP_200_OK)


class RelevamientoApiView(APIView):
    permission_classes = [HasAPIKey]

    def patch(self, request):
        comedor = Comedor.objects.get(
            gestionar_uid=request.data["comedor_gestionar_uid"]
        ).id
        relevamiento = Relevamiento.objects.get(
            comedor=comedor,
            fecha_visita=format_fecha_django(request.data["fecha_visita"]),
        )
        relevamiento_serializer = RelevamientoSerializer(
            relevamiento, data=request.data, partial=True
        ).clean()
        if relevamiento_serializer.is_valid():
            relevamiento_serializer.save()
            relevamiento = relevamiento_serializer.instance
        else:
            error_message_str = format_serializer_errors(relevamiento_serializer)

            return Response(
                f"Error en relevamiento: '{error_message_str}'",
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            RelevamientoSerializer(relevamiento).data, status=status.HTTP_200_OK
        )


class ObservacionApiView(APIView):
    permission_classes = [HasAPIKey]

    def patch(self, request):
        comedor = Comedor.objects.get(
            gestionar_uid=request.data["comedor_gestionar_uid"]
        ).id
        observacion = Observacion.objects.get(
            comedor=comedor,
            fecha_visita=format_fecha_django(request.data["fecha_visita"]),
        )
        observacion_serializer = ObservacionSerializer(
            observacion, data=request.data, partial=True
        ).clean()
        if observacion_serializer.is_valid():
            observacion_serializer.save()
            observacion = observacion_serializer.instance
        else:
            error_message_str = format_serializer_errors(observacion_serializer)

            return Response(
                f"Error en observación: '{error_message_str}'",
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            ObservacionSerializer(observacion).data, status=status.HTTP_200_OK
        )
