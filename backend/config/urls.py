from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

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
