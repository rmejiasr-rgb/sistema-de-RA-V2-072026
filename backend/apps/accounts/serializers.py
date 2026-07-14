from rest_framework import serializers

from .models import RolAsignado, Usuario


class RolAsignadoSerializer(serializers.ModelSerializer):
    escuela_codigo = serializers.CharField(source="escuela.codigo", read_only=True, default=None)

    class Meta:
        model = RolAsignado
        fields = ["id", "rol", "escuela", "escuela_codigo"]


class UsuarioSerializer(serializers.ModelSerializer):
    roles = RolAsignadoSerializer(many=True, read_only=True)
    escuela_codigo = serializers.CharField(source="escuela.codigo", read_only=True, default=None)

    class Meta:
        model = Usuario
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "escuela", "escuela_codigo", "roles", "is_superuser",
        ]
