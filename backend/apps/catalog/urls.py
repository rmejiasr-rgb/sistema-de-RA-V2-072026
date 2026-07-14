from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("escuelas", views.EscuelaViewSet, basename="escuela")
router.register("carreras", views.CarreraViewSet, basename="carrera")
router.register("periodos", views.PeriodoViewSet, basename="periodo")
router.register("materias", views.MateriaViewSet, basename="materia")
router.register("ras", views.RACatalogoViewSet, basename="ra")
router.register("materia-ras", views.MateriaRAViewSet, basename="materia-ra")

urlpatterns = router.urls + [
    path("periodos/<int:pk>/completitud/", views.CompletitudPeriodoView.as_view(), name="periodo-completitud"),
    path("periodos/<int:pk>/cerrar/", views.CerrarPeriodoView.as_view(), name="periodo-cerrar"),
]
