from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .metadatos import editar_estudiante, editar_metadatos_evaluacion
from .models import AuditLog, Carga, Evaluacion, ResultadoEstudiante
from .permisos import cargas_visibles, evaluaciones_visibles, puede_editar_metadatos
from .serializers import (
    AuditLogSerializer,
    CargaSerializer,
    EvaluacionDetalleSerializer,
    EvaluacionSerializer,
)
from .services import CargaRechazada, procesar_carga


class CargaUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        archivo = request.FILES.get("archivo")
        if archivo is None:
            return Response(
                {"errores": [{"codigo": "SIN_ARCHIVO", "mensaje": "Debe adjuntar un archivo .xlsx."}]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not archivo.name.lower().endswith(".xlsx"):
            return Response(
                {"errores": [{"codigo": "TIPO_INVALIDO", "mensaje": "El archivo debe ser .xlsx."}]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        confirmar = str(request.data.get("confirmar_nueva_version", "")).lower() in ("1", "true", "on")

        try:
            carga, reporte = procesar_carga(archivo, request.user, confirmar_nueva_version=confirmar)
        except CargaRechazada as exc:
            http_status = (
                status.HTTP_409_CONFLICT
                if exc.resultado_json.get("requiere_confirmacion")
                else status.HTTP_422_UNPROCESSABLE_ENTITY
            )
            return Response(exc.resultado_json, status=http_status)

        return Response(
            {**reporte, "carga": CargaSerializer(carga).data}, status=status.HTTP_201_CREATED
        )


class CargaListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CargaSerializer

    def get_queryset(self):
        qs = cargas_visibles(self.request.user).select_related(
            "usuario", "materia", "ra", "periodo"
        )
        params = self.request.query_params
        for campo, param in (
            ("periodo", "periodo"), ("materia", "materia"), ("ra", "ra"), ("estado", "estado"),
        ):
            valor = params.get(param)
            if valor:
                qs = qs.filter(**{campo: valor})
        return qs


class EvaluacionListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EvaluacionSerializer

    def get_queryset(self):
        qs = evaluaciones_visibles(self.request.user).filter(vigente=True).select_related(
            "materia", "materia__escuela", "ra", "periodo"
        )
        params = self.request.query_params
        mapa = {
            "periodo": "periodo_id", "escuela": "materia__escuela_id", "carrera": None,
            "materia": "materia_id", "seccion": "seccion", "profesor": "profesor_nombre",
            "ra": "ra_id", "nivel": "nivel",
        }
        for param, campo in mapa.items():
            valor = params.get(param)
            if valor and campo:
                qs = qs.filter(**{campo: valor})
        return qs


class EvaluacionDetalleView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EvaluacionDetalleSerializer

    def get_queryset(self):
        return evaluaciones_visibles(self.request.user).select_related(
            "materia", "ra", "periodo"
        ).prefetch_related("criterios", "resultados_estudiantes__resultados_criterios__criterio")


class EvaluacionMetadatosView(APIView):
    """PATCH de metadatos (actividad, fecha, profesor, sección) con auditoría.
    Las notas/resultados NO se editan aquí: solo re-subiendo el archivo."""

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        evaluacion = evaluaciones_visibles(request.user).select_related(
            "carga", "materia"
        ).filter(pk=pk).first()
        if evaluacion is None:
            return Response({"detail": "Evaluación no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        if not puede_editar_metadatos(request.user, evaluacion):
            return Response({"detail": "No tiene permiso para editar esta evaluación."},
                            status=status.HTTP_403_FORBIDDEN)

        motivo = request.data.get("motivo", "")
        cambios = editar_metadatos_evaluacion(request.user, evaluacion, request.data, motivo=motivo)
        return Response({"cambios": cambios, "evaluacion": EvaluacionSerializer(evaluacion).data})


class EstudianteMetadatosView(APIView):
    """PATCH de nombre/carrera/grupo de un estudiante (corrección de nombre mal escrito)."""

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        estudiante = ResultadoEstudiante.objects.select_related(
            "evaluacion__carga", "evaluacion__materia"
        ).filter(pk=pk).first()
        if estudiante is None:
            return Response({"detail": "Estudiante no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        if not evaluaciones_visibles(request.user).filter(pk=estudiante.evaluacion_id).exists():
            return Response({"detail": "No encontrado."}, status=status.HTTP_404_NOT_FOUND)
        if not puede_editar_metadatos(request.user, estudiante.evaluacion):
            return Response({"detail": "No tiene permiso para editar este registro."},
                            status=status.HTTP_403_FORBIDDEN)

        motivo = request.data.get("motivo", "")
        cambios = editar_estudiante(request.user, estudiante, request.data, motivo=motivo)
        return Response({"cambios": cambios})


class AuditLogView(generics.ListAPIView):
    """Historial de auditoría de una entidad (para mostrar en la UI)."""

    permission_classes = [IsAuthenticated]
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        qs = AuditLog.objects.select_related("usuario")
        entidad = self.request.query_params.get("entidad")
        entidad_id = self.request.query_params.get("entidad_id")
        if entidad:
            qs = qs.filter(entidad=entidad)
        if entidad_id:
            qs = qs.filter(entidad_id=str(entidad_id))
        return qs
