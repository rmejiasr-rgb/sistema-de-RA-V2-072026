from django.urls import path

from . import views

urlpatterns = [
    path("cumplimiento-ra/", views.CumplimientoRAView.as_view(), name="dashboard-cumplimiento-ra"),
    path("criterios/", views.DesagregacionCriterioView.as_view(), name="dashboard-criterios"),
]
