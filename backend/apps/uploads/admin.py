from django.contrib import admin

from .models import AuditLog, Carga, Criterio, Evaluacion, ResultadoCriterio, ResultadoEstudiante


@admin.register(Carga)
class CargaAdmin(admin.ModelAdmin):
    list_display = ("archivo_nombre_original", "version", "estado", "usuario", "materia", "seccion", "periodo", "creado_en")
    list_filter = ("estado", "periodo", "materia__escuela")
    search_fields = ("archivo_nombre_original", "profesor_nombre", "archivo_hash")
    readonly_fields = ("archivo_hash", "resultado_validacion")


class CriterioInline(admin.TabularInline):
    model = Criterio
    extra = 0


@admin.register(Evaluacion)
class EvaluacionAdmin(admin.ModelAdmin):
    list_display = (
        "materia", "seccion", "profesor_nombre", "ra", "nivel", "periodo",
        "pct_aprobados_declarado", "pct_aprobados_recalculado", "vigente",
    )
    list_filter = ("vigente", "periodo", "ra", "materia__escuela")
    search_fields = ("materia__codigo", "profesor_nombre")
    inlines = [CriterioInline]


@admin.register(ResultadoEstudiante)
class ResultadoEstudianteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "evaluacion", "grupo", "carrera", "nota")
    search_fields = ("nombre",)
    list_filter = ("evaluacion__periodo",)


@admin.register(ResultadoCriterio)
class ResultadoCriterioAdmin(admin.ModelAdmin):
    list_display = ("resultado_estudiante", "criterio", "nivel")
    list_filter = ("nivel",)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "usuario", "entidad", "entidad_id", "campo")
    list_filter = ("entidad",)
    search_fields = ("entidad_id", "usuario__username")
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
