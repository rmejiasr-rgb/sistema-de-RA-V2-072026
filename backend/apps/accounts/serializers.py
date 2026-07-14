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


class RolEntradaSerializer(serializers.Serializer):
    rol = serializers.ChoiceField(choices=[c[0] for c in RolAsignado.ROL_CHOICES])
    escuela = serializers.PrimaryKeyRelatedField(
        queryset=RolAsignado._meta.get_field("escuela").related_model.objects.all(),
        allow_null=True, required=False,
    )


class UsuarioAdminSerializer(serializers.ModelSerializer):
    """Serializer de gestión de usuarios (solo administrador). Permite fijar
    contraseña y asignar roles."""

    roles = RolAsignadoSerializer(many=True, read_only=True)
    roles_input = RolEntradaSerializer(many=True, write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Usuario
        fields = [
            "id", "username", "email", "first_name", "last_name", "escuela",
            "is_active", "roles", "roles_input", "password",
        ]

    def _aplicar_roles(self, usuario, roles_input):
        usuario.roles.all().delete()
        for r in roles_input:
            RolAsignado.objects.create(usuario=usuario, rol=r["rol"], escuela=r.get("escuela"))

    def create(self, validated_data):
        roles_input = validated_data.pop("roles_input", [])
        password = validated_data.pop("password", None)
        usuario = Usuario(**validated_data)
        if password:
            usuario.set_password(password)
        else:
            usuario.set_unusable_password()
        usuario.save()
        self._aplicar_roles(usuario, roles_input)
        return usuario

    def update(self, instance, validated_data):
        roles_input = validated_data.pop("roles_input", None)
        password = validated_data.pop("password", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        if password:
            instance.set_password(password)
        instance.save()
        if roles_input is not None:
            self._aplicar_roles(instance, roles_input)
        return instance
