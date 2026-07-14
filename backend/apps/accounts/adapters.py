"""
Adapter de django-allauth para el SSO de Microsoft Entra ID (Fase 3).

Restringe el acceso a correos del dominio institucional (@unimet.edu.ve) y
asigna el rol de Profesor por defecto a los usuarios nuevos que ingresan por SSO.
Solo se usa cuando SSO_ENABLED=True.
"""

from django.conf import settings

try:
    from allauth.account.adapter import DefaultAccountAdapter
    from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
    from allauth.exceptions import ImmediateHttpResponse
except ImportError:  # allauth no instalado (SSO desactivado)
    DefaultAccountAdapter = object
    DefaultSocialAccountAdapter = object


class DominioSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        from django.http import HttpResponseForbidden

        email = (sociallogin.user.email or "").lower()
        dominio = settings.SSO_DOMINIO_PERMITIDO.lower()
        if not email.endswith("@" + dominio):
            raise ImmediateHttpResponse(
                HttpResponseForbidden(
                    f"Solo se permite el acceso con correos @{dominio}."
                )
            )

    def save_user(self, request, sociallogin, form=None):
        usuario = super().save_user(request, sociallogin, form)
        # Asignar rol de Profesor por defecto (el administrador ajusta luego).
        from .models import RolAsignado
        if not usuario.roles.exists():
            RolAsignado.objects.create(usuario=usuario, rol=RolAsignado.PROFESOR)
        return usuario
