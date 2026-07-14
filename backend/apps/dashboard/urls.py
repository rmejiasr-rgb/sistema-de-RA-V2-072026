from django.urls import path

from . import views

urlpatterns = [
    path("cumplimiento-ra/", views.CumplimientoRAView.as_view(), name="dashboard-cumplimiento-ra"),
    path("criterios/", views.DesagregacionCriterioView.as_view(), name="dashboard-criterios"),
    path("heatmap-materia-ra/", views.HeatmapMateriaRAView.as_view(), name="dashboard-heatmap-materia-ra"),
    path("heatmap-criterio-seccion/", views.HeatmapCriterioSeccionView.as_view(), name="dashboard-heatmap-criterio-seccion"),
    path("carrera-grupo/", views.DesgloseCarreraGrupoView.as_view(), name="dashboard-carrera-grupo"),
    path("tendencias/", views.TendenciasView.as_view(), name="dashboard-tendencias"),
    path("cobertura/", views.CoberturaView.as_view(), name="dashboard-cobertura"),
    path("riesgo/", views.RiesgoAcreditacionView.as_view(), name="dashboard-riesgo"),
    path("proxy-consistencia/", views.ProxyConsistenciaView.as_view(), name="dashboard-proxy"),
]
