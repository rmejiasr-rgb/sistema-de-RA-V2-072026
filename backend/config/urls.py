from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import FileResponse, HttpResponseNotFound
from django.urls import include, path, re_path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/catalog/", include("apps.catalog.urls")),
    path("api/uploads/", include("apps.uploads.urls")),
    path("api/dashboard/", include("apps.dashboard.urls")),
]

if settings.SSO_ENABLED:
    # SSO Microsoft Entra ID (django-allauth). Ver docs/SSO_ENTRA.md.
    urlpatterns += [path("accounts/", include("allauth.urls"))]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# Comodín para la aplicación visual (React): cualquier ruta que no sea de la API
# ni del panel admin devuelve index.html, para que el enrutado del lado del
# navegador (p. ej. abrir /tablero directamente o recargar) funcione. Solo se
# activa cuando la app compilada está presente (producción).
def spa_index(request):
    index = settings.SPA_DIR / "index.html"
    if index.exists():
        return FileResponse(open(index, "rb"))
    return HttpResponseNotFound("Aplicación visual no compilada.")


if settings.SPA_DIR.exists():
    urlpatterns += [
        re_path(r"^(?!api/|admin/|static/|media/|accounts/).*$", spa_index),
    ]
