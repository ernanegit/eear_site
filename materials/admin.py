from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import MaterialCategory, Material, Download

@admin.register(MaterialCategory)
class MaterialCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'materials_count', 'icon_display']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    def materials_count(self, obj):
        count = obj.materials.count()
        return format_html('<strong>{}</strong> materiais', count)
    materials_count.short_description = 'Materiais'
    
    def icon_display(self, obj):
        if obj.icon:
            return format_html('<i class="{}"></i> {}', obj.icon, obj.icon)
        return '-'
    icon_display.short_description = 'Ícone'

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'subject', 'material_type_display', 'is_premium_display', 'download_count', 'uploaded_by', 'created_at']
    list_filter = ['category', 'subject', 'material_type', 'is_premium', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['download_count', 'created_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 20
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('title', 'description', 'category', 'subject')
        }),
        ('Tipo e Arquivo', {
            'fields': ('material_type', 'file', 'external_url', 'thumbnail')
        }),
        ('Configurações', {
            'fields': ('is_premium', 'uploaded_by')
        }),
        ('Estatísticas', {
            'fields': ('download_count', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Se está criando um novo objeto
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)
    
    def material_type_display(self, obj):
        icons = {
            'pdf': '📄',
            'doc': '📝',
            'video': '📹',
            'audio': '🎵',
            'link': '🔗',
            'image': '🖼️'
        }
        icon = icons.get(obj.material_type, '📄')
        return format_html('{} {}', icon, obj.get_material_type_display())
    material_type_display.short_description = 'Tipo'
    
    def is_premium_display(self, obj):
        if obj.is_premium:
            return format_html('<span style="color: #ffc107; font-weight: bold;">★ Premium</span>')
        return format_html('<span style="color: #28a745;">✓ Grátis</span>')
    is_premium_display.short_description = 'Acesso'

@admin.register(Download)
class DownloadAdmin(admin.ModelAdmin):
    list_display = ['user', 'material_title', 'material_type', 'downloaded_at']
    list_filter = ['downloaded_at', 'material__material_type', 'material__category']
    search_fields = ['user__email', 'user__username', 'material__title']
    date_hierarchy = 'downloaded_at'
    ordering = ['-downloaded_at']
    list_per_page = 50
    
    def material_title(self, obj):
        return obj.material.title
    material_title.short_description = 'Material'
    
    def material_type(self, obj):
        icons = {
            'pdf': '📄',
            'doc': '📝',
            'video': '📹',
            'audio': '🎵',
            'link': '🔗',
            'image': '🖼️'
        }
        icon = icons.get(obj.material.material_type, '📄')
        return format_html('{} {}', icon, obj.material.get_material_type_display())
    material_type.short_description = 'Tipo'
# Register your models here.
