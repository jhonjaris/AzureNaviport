from django.contrib import admin
from .models import Escalamiento

@admin.register(Escalamiento)
class EscalamientoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'solicitud', 'tipo_escalamiento', 'prioridad', 'estado']
    list_filter = ['tipo_escalamiento', 'prioridad', 'estado']
    search_fields = ['codigo', 'motivo']
    ordering = ['-id']
