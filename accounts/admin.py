from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, Enrollment

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'username', 'first_name', 'last_name', 'is_premium_display', 'is_active', 'date_joined']
    list_filter = ['is_premium', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-date_joined']
    list_per_page = 20
    
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Extras', {
            'fields': ('phone', 'birth_date', 'city', 'state', 'profile_picture', 'is_premium')
        }),
    )
    
    def is_premium_display(self, obj):
        if obj.is_premium:
            return format_html('<span style="color: #ffc107; font-weight: bold;">★ Premium</span>')
        return format_html('<span style="color: #6c757d;">Básico</span>')
    is_premium_display.short_description = 'Plano'

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'plan_display', 'status_display', 'start_date', 'end_date', 'payment_method']
    list_filter = ['plan', 'status', 'start_date', 'payment_method']
    search_fields = ['user__email', 'user__username', 'user__first_name', 'user__last_name']
    date_hierarchy = 'start_date'
    ordering = ['-start_date']
    list_per_page = 20
    
    readonly_fields = ['start_date']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email do Usuário'
    
    def plan_display(self, obj):
        colors = {
            'basic': '#6c757d',
            'premium': '#ffc107', 
            'annual': '#28a745'
        }
        color = colors.get(obj.plan, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_plan_display()
        )
    plan_display.short_description = 'Plano'
    
    def status_display(self, obj):
        colors = {
            'pending': '#ffc107',
            'active': '#28a745',
            'expired': '#dc3545',
            'cancelled': '#6c757d'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'