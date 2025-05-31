from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import User, Enrollment

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = [
        'email', 'username', 'full_name_display', 'is_premium_display', 
        'is_active', 'date_joined'
    ]
    list_filter = ['is_premium', 'is_active', 'is_staff', 'date_joined', 'created_at']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-date_joined']
    list_per_page = 20
    readonly_fields = ['created_at', 'updated_at', 'last_login', 'date_joined']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Extras', {
            'fields': (
                'phone', 'birth_date', 'city', 'state', 
                'profile_picture', 'is_premium'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def full_name_display(self, obj):
        """Exibir nome completo"""
        full_name = obj.full_name
        if full_name != obj.username:
            return format_html('<strong>{}</strong>', full_name)
        return obj.username
    full_name_display.short_description = 'Nome Completo'
    
    def is_premium_display(self, obj):
        """Exibir status premium com ícone"""
        if obj.is_premium:
            return format_html(
                '<span style="color: #ffc107; font-weight: bold;">'
                '<i class="fas fa-crown"></i> Premium</span>'
            )
        return format_html(
            '<span style="color: #6c757d;">'
            '<i class="fas fa-user"></i> Básico</span>'
        )
    is_premium_display.short_description = 'Plano'
    
    def get_queryset(self, request):
        """Otimizar queries"""
        return super().get_queryset(request).select_related()

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        'user_email', 'user_full_name', 'plan_display', 'status_display', 
        'start_date', 'end_date', 'payment_method', 'days_remaining'
    ]
    list_filter = ['plan', 'status', 'start_date', 'payment_method']
    search_fields = [
        'user__email', 'user__username', 'user__first_name', 'user__last_name'
    ]
    date_hierarchy = 'start_date'
    ordering = ['-start_date']
    list_per_page = 20
    
    readonly_fields = ['start_date', 'days_remaining_display']
    
    fieldsets = (
        ('Usuário', {
            'fields': ('user',)
        }),
        ('Plano e Status', {
            'fields': ('plan', 'status', 'payment_method')
        }),
        ('Datas', {
            'fields': ('start_date', 'end_date', 'days_remaining_display')
        }),
    )
    
    def user_email(self, obj):
        """Email do usuário com link"""
        return format_html(
            '<a href="/admin/accounts/user/{}/change/">{}</a>',
            obj.user.id, obj.user.email
        )
    user_email.short_description = 'Email do Usuário'
    
    def user_full_name(self, obj):
        """Nome completo do usuário"""
        return obj.user.full_name
    user_full_name.short_description = 'Nome Completo'
    
    def plan_display(self, obj):
        """Exibir plano com cores"""
        colors = {
            'basic': '#6c757d',
            'premium': '#ffc107', 
            'annual': '#28a745'
        }
        icons = {
            'basic': 'fas fa-user',
            'premium': 'fas fa-crown',
            'annual': 'fas fa-gem'
        }
        color = colors.get(obj.plan, '#6c757d')
        icon = icons.get(obj.plan, 'fas fa-user')
        return format_html(
            '<span style="color: {}; font-weight: bold;">'
            '<i class="{}"></i> {}</span>',
            color, icon, obj.get_plan_display()
        )
    plan_display.short_description = 'Plano'
    
    def status_display(self, obj):
        """Exibir status com cores"""
        colors = {
            'pending': '#ffc107',
            'active': '#28a745',
            'expired': '#dc3545',
            'cancelled': '#6c757d'
        }
        icons = {
            'pending': 'fas fa-clock',
            'active': 'fas fa-check-circle',
            'expired': 'fas fa-times-circle',
            'cancelled': 'fas fa-ban'
        }
        color = colors.get(obj.status, '#6c757d')
        icon = icons.get(obj.status, 'fas fa-question')
        return format_html(
            '<span style="color: {}; font-weight: bold;">'
            '<i class="{}"></i> {}</span>',
            color, icon, obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def days_remaining(self, obj):
        """Calcular dias restantes"""
        if obj.end_date and obj.status == 'active':
            from django.utils import timezone
            remaining = (obj.end_date - timezone.now()).days
            if remaining > 0:
                return f"{remaining} dias"
            else:
                return "Expirado"
        return "-"
    days_remaining.short_description = 'Dias Restantes'
    
    def days_remaining_display(self, obj):
        """Exibir dias restantes no formulário"""
        return self.days_remaining(obj)
    days_remaining_display.short_description = 'Dias Restantes'
    
    def get_queryset(self, request):
        """Otimizar queries"""
        return super().get_queryset(request).select_related('user')
    
    actions = ['activate_enrollment', 'deactivate_enrollment']
    
    def activate_enrollment(self, request, queryset):
        """Ação para ativar matrículas"""
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} matrícula(s) ativada(s).')
    activate_enrollment.short_description = "Ativar matrículas selecionadas"
    
    def deactivate_enrollment(self, request, queryset):
        """Ação para desativar matrículas"""
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} matrícula(s) cancelada(s).')
    deactivate_enrollment.short_description = "Cancelar matrículas selecionadas"