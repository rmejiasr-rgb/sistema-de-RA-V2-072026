from django.urls import path

from . import views

urlpatterns = [
    path("cargar/", views.CargaUploadView.as_view(), name="carga-upload"),
    path("cargas/", views.CargaListView.as_view(), name="carga-list"),
    path("evaluaciones/", views.EvaluacionListView.as_view(), name="evaluacion-list"),
    path("evaluaciones/<int:pk>/", views.EvaluacionDetalleView.as_view(), name="evaluacion-detail"),
]
