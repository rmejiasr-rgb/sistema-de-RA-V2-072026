from rest_framework import serializers

from .models import Carrera, Escuela, Materia, MateriaRA, Periodo, RACatalogo


class EscuelaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Escuela
        fields = ["id", "nombre", "codigo"]


class CarreraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Carrera
        fields = ["id", "nombre", "escuela"]


class PeriodoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Periodo
        fields = ["id", "codigo", "fecha_inicio", "fecha_fin", "estado"]


class MateriaSerializer(serializers.ModelSerializer):
    escuela_codigo = serializers.CharField(source="escuela.codigo", read_only=True)

    class Meta:
        model = Materia
        fields = ["id", "codigo", "nombre", "escuela", "escuela_codigo"]


class RACatalogoSerializer(serializers.ModelSerializer):
    class Meta:
        model = RACatalogo
        fields = ["id", "codigo", "nombre", "descripcion"]


class MateriaRASerializer(serializers.ModelSerializer):
    materia_codigo = serializers.CharField(source="materia.codigo", read_only=True)
    ra_codigo = serializers.CharField(source="ra.codigo", read_only=True)

    class Meta:
        model = MateriaRA
        fields = ["id", "materia", "materia_codigo", "ra", "ra_codigo", "nivel_esperado"]
