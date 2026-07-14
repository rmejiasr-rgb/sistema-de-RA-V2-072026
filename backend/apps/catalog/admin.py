from django.contrib import admin

from .models import Carrera, Escuela, Materia, MateriaRA, Periodo, RACatalogo


@admin.register(Escuela)
class EscuelaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre")
    search_fields = ("codigo", "nombre")


@admin.register(Carrera)
class CarreraAdmin(admin.ModelAdmin):
    list_display = ("nombre", "escuela")
    list_filter = ("escuela",)
    search_fields = ("nombre",)


@admin.register(Periodo)
class PeriodoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "fecha_inicio", "fecha_fin", "estado")
    list_filter = ("estado",)
    search_fields = ("codigo",)


@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "escuela")
    list_filter = ("escuela",)
    search_fields = ("codigo", "nombre")


@admin.register(RACatalogo)
class RACatalogoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre")
    search_fields = ("codigo", "nombre")


class MateriaRAInline(admin.TabularInline):
    model = MateriaRA
    extra = 1


@admin.register(MateriaRA)
class MateriaRAAdmin(admin.ModelAdmin):
    list_display = ("materia", "ra", "nivel_esperado")
    list_filter = ("materia__escuela", "nivel_esperado")
    search_fields = ("materia__codigo", "ra__codigo")
    autocomplete_fields = ("materia", "ra")


admin.site.site_header = "Sistema RA · UNIMET"
admin.site.site_title = "Sistema RA"
admin.site.index_title = "Administración"
