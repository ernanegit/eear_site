


# Register your models here.# Editar o admin do support
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import FAQ, SupportTicket, TicketReply, Contact

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question_preview', 'category_display', 'order', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    list_editable = ['order', 'is_active']
    search_fields = ['question', 'answer']
    ordering = ['category', 'order']
    list_per_page = 20
    
    fieldsets = (
        ('Pergunta e Resposta', {
            'fields': ('question', 'answer')
        }),
        ('Configurações', {
            'fields': ('category', 'order', 'is_active')
        }),
    )
    
    def question_preview(self, obj):
        return obj.question[:80] + "..." if len(obj.question) > 80 else obj.question
    question_preview.short_description = 'Pergunta'
    
    def category_display(self, obj):
        icons = {
            'general': '📋',
            'account': '👤',
            'payment': '💳',
            'technical': '🔧',
            'courses': '📚'
        }
        icon = icons.get(obj.category, '📋')
        return format_html('{} {}', icon, obj.get_category_display())
    category_display.short_description = 'Categoria'

class TicketReplyInline(admin.TabularInline):
    model = TicketReply
    extra = 0
    readonly_fields = ['created_at']
    fields = ['user', 'message', 'is_staff_reply', 'created_at']
    ordering = ['created_at']

@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ['ticket_id', 'subject_preview', 'user', 'status_display', 'priority_display', 'replies_count', 'created_at']
    list_filter = ['status', 'priority', 'created_at', 'assigned_to']
    search_fields = ['subject', 'user__email', 'user__username', 'description']
    date_hierarchy = 'created_at'
    inlines = [TicketReplyInline]
    ordering = ['-created_at']
    list_per_page = 20
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informações do Ticket', {
            'fields': ('user', 'subject', 'description')
        }),
        ('Status e Prioridade', {
            'fields': ('status', 'priority', 'assigned_to')
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def ticket_id(self, obj):
        return format_html('<strong>#{}</strong>', obj.id)
    ticket_id.short_description = 'ID'
    
    def subject_preview(self, obj):
        return obj.subject[:50] + "..." if len(obj.subject) > 50 else obj.subject
    subject_preview.short_description = 'Assunto'
    
    def status_display(self, obj):
        colors = {
            'open': '#dc3545',
            'in_progress': '#ffc107',
            'resolved': '#28a745',
            'closed': '#6c757d'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def priority_display(self, obj):
        colors = {
            'low': '#28a745',
            'medium': '#ffc107',
            'high': '#fd7e14',
            'urgent': '#dc3545'
        }
        color = colors.get(obj.priority, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_priority_display()
        )
    priority_display.short_description = 'Prioridade'
    
    def replies_count(self, obj):
        count = obj.replies.count()
        return format_html('<strong>{}</strong> respostas', count)
    replies_count.short_description = 'Respostas'

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject_preview', 'is_read_display', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 30
    
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Informações de Contato', {
            'fields': ('name', 'email', 'subject')
        }),
        ('Mensagem', {
            'fields': ('message',)
        }),
        ('Status', {
            'fields': ('is_read', 'created_at')
        }),
    )
    
    def subject_preview(self, obj):
        return obj.subject[:50] + "..." if len(obj.subject) > 50 else obj.subject
    subject_preview.short_description = 'Assunto'
    
    def is_read_display(self, obj):
        if obj.is_read:
            return format_html('<span style="color: #28a745; font-weight: bold;">✓ Lida</span>')
        return format_html('<span style="color: #dc3545; font-weight: bold;">✉️ Nova</span>')
    is_read_display.short_description = 'Status'
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} mensagens marcadas como lidas.')
    mark_as_read.short_description = "Marcar como lidas"
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} mensagens marcadas como não lidas.')
    mark_as_unread.short_description = "Marcar como não lidas"