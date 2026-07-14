from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import RolAsignado, Usuario


class RolAsignadoInline(admin.TabularInline):
    model = RolAsignado
    extra = 1


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Datos institucionales", {"fields": ("escuela",)}),
    )
    list_display = ("username", "email", "first_name", "last_name", "escuela", "is_staff")
    list_filter = UserAdmin.list_filter + ("escuela",)
    inlines = [RolAsignadoInline]


@admin.register(RolAsignado)
class RolAsignadoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "rol", "escuela")
    list_filter = ("rol", "escuela")
    search_fields = ("usuario__username", "usuario__email")
