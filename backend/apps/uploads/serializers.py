from rest_framework import serializers

from .models import (
    AuditLog,
    Carga,
    Criterio,
    Evaluacion,
    ResultadoCriterio,
    ResultadoEstudiante,
)


class AuditLogSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source="usuario.get_full_name", read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = [
            "id", "timestamp", "usuario", "usuario_nombre", "entidad", "entidad_id",
            "campo", "valor_anterior", "valor_nuevo", "motivo",
        ]


class CargaSerializer(serializers.ModelSerializer):
    materia_codigo = serializers.CharField(source="materia.codigo", read_only=True, default=None)
    ra_codigo = serializers.CharField(source="ra.codigo", read_only=True, default=None)
    periodo_codigo = serializers.CharField(source="periodo.codigo", read_only=True, default=None)
    usuario_nombre = serializers.CharField(source="usuario.get_full_name", read_only=True, default=None)

    class Meta:
        model = Carga
        fields = [
            "id", "archivo_nombre_original", "version", "estado", "creado_en",
            "resultado_validacion", "usuario", "usuario_nombre",
            "periodo", "periodo_codigo", "materia", "materia_codigo",
            "seccion", "profesor_nombre", "ra", "ra_codigo", "nivel",
        ]
        read_only_fields = fields


class CriterioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Criterio
        fields = ["id", "nombre", "orden"]


class ResultadoCriterioSerializer(serializers.ModelSerializer):
    criterio_nombre = serializers.CharField(source="criterio.nombre", read_only=True)

    class Meta:
        model = ResultadoCriterio
        fields = ["id", "criterio", "criterio_nombre", "nivel"]


class ResultadoEstudianteSerializer(serializers.ModelSerializer):
    resultados_criterios = ResultadoCriterioSerializer(many=True, read_only=True)

    class Meta:
        model = ResultadoEstudiante
        fields = ["id", "grupo", "nombre", "carrera", "nota", "resultados_criterios"]


class EvaluacionSerializer(serializers.ModelSerializer):
    materia_codigo = serializers.CharField(source="materia.codigo", read_only=True)
    materia_nombre = serializers.CharField(source="materia.nombre", read_only=True)
    ra_codigo = serializers.CharField(source="ra.codigo", read_only=True)
    periodo_codigo = serializers.CharField(source="periodo.codigo", read_only=True)
    escuela_id = serializers.IntegerField(source="materia.escuela_id", read_only=True)
    version = serializers.IntegerField(source="carga.version", read_only=True)

    class Meta:
        model = Evaluacion
        fields = [
            "id", "periodo", "periodo_codigo", "materia", "materia_codigo", "materia_nombre",
            "seccion", "profesor_nombre", "ra", "ra_codigo", "nivel", "actividad",
            "fecha_actividad", "pct_aprobados_declarado", "pct_aprobados_recalculado",
            "vigente", "version", "escuela_id",
        ]


class EvaluacionDetalleSerializer(EvaluacionSerializer):
    criterios = CriterioSerializer(many=True, read_only=True)
    resultados_estudiantes = ResultadoEstudianteSerializer(many=True, read_only=True)

    class Meta(EvaluacionSerializer.Meta):
        fields = EvaluacionSerializer.Meta.fields + ["criterios", "resultados_estudiantes"]
