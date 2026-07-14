from django.urls import path

from . import views

urlpatterns = [
    path("cargar/", views.CargaUploadView.as_view(), name="carga-upload"),
    path("cargas/", views.CargaListView.as_view(), name="carga-list"),
    path("evaluaciones/", views.EvaluacionListView.as_view(), name="evaluacion-list"),
    path("evaluaciones/<int:pk>/", views.EvaluacionDetalleView.as_view(), name="evaluacion-detail"),
    path("evaluaciones/<int:pk>/metadatos/", views.EvaluacionMetadatosView.as_view(), name="evaluacion-metadatos"),
    path("estudiantes/<int:pk>/metadatos/", views.EstudianteMetadatosView.as_view(), name="estudiante-metadatos"),
    path("auditoria/", views.AuditLogView.as_view(), name="auditoria"),
]
