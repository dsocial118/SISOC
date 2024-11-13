from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from provincias.models import Proyecto
from provincias.serializers import ObservacionSerializer, ProyectoSerializer


class ProyectoViewSet(viewsets.ModelViewSet):
    queryset = Proyecto.objects.all()
    serializer_class = ProyectoSerializer


class ProyectoSubsanarView(APIView):
    def post(self, request, pk):
        observacion = request.data.get("observacion")

        if not observacion:
            return Response({"error": "Observacion es requerida"}, status=400)

        observacion = ObservacionSerializer(
            data={
                "proyecto": pk,
                "observacion": observacion,
            }
        )
        if observacion.is_valid():
            observacion.save()

            try:
                proyecto = Proyecto.objects.get(pk=pk)
                proyecto.estado = "Pendiente de subsanacion"
                proyecto.save()

                return Response(observacion.data, status=201)
            except Proyecto.DoesNotExist:
                return Response({"error": "Proyecto no encontrado"}, status=404)

        else:
            return Response(observacion.errors, status=400)
