from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from django.urls import reverse
from django.utils.safestring import mark_safe
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
    extra = 1
    fields = ['message', 'is_staff_reply']
    ordering = ['created_at']
    
    def get_readonly_fields(self, request, obj=None):
        # Se é uma resposta existente, mostrar quem criou e quando
        if obj and obj.pk:
            return ['created_at', 'user']
        return ['created_at']
    
    def save_model(self, request, obj, form, change):
        if not change:  # Se é uma nova resposta
            obj.user = request.user
            obj.is_staff_reply = True
        super().save_model(request, obj, form, change)

@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = [
        'ticket_id', 'subject_preview', 'user_display', 'status_display', 
        'priority_display', 'replies_count', 'last_activity', 'actions_column'
    ]
    list_filter = ['status', 'priority', 'created_at', 'assigned_to']
    search_fields = ['subject', 'user__email', 'user__username', 'description']
    date_hierarchy = 'created_at'
    inlines = [TicketReplyInline]
    ordering = ['-created_at']
    list_per_page = 20
    actions = ['mark_as_resolved', 'mark_as_in_progress', 'assign_to_me']
    
    readonly_fields = ['created_at', 'updated_at', 'ticket_summary']
    
    fieldsets = (
        ('Informações do Ticket', {
            'fields': ('user', 'subject', 'description', 'ticket_summary')
        }),
        ('Gerenciamento', {
            'fields': ('status', 'priority', 'assigned_to')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'assigned_to').prefetch_related('replies')
    
    def ticket_id(self, obj):
        return format_html('<strong>#{}</strong>', obj.id)
    ticket_id.short_description = 'ID'
    
    def subject_preview(self, obj):
        return obj.subject[:50] + "..." if len(obj.subject) > 50 else obj.subject
    subject_preview.short_description = 'Assunto'
    
    def user_display(self, obj):
        return format_html(
            '<div><strong>{}</strong><br><small>{}</small></div>',
            obj.user.get_full_name() or obj.user.username,
            obj.user.email
        )
    user_display.short_description = 'Usuário'
    
    def status_display(self, obj):
        colors = {
            'open': '#dc3545',
            'in_progress': '#ffc107',
            'resolved': '#28a745',
            'closed': '#6c757d'
        }
        icons = {
            'open': 'fas fa-circle',
            'in_progress': 'fas fa-clock',
            'resolved': 'fas fa-check-circle',
            'closed': 'fas fa-times-circle'
        }
        color = colors.get(obj.status, '#6c757d')
        icon = icons.get(obj.status, 'fas fa-question')
        return format_html(
            '<span style="color: {}; font-weight: bold;">'
            '<i class="{}"></i> {}</span>',
            color, icon, obj.get_status_display()
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
        if count > 0:
            return format_html('<strong>{}</strong> respostas', count)
        return '0 respostas'
    replies_count.short_description = 'Respostas'
    
    def last_activity(self, obj):
        if obj.replies.exists():
            last_reply = obj.replies.latest('created_at')
            return format_html(
                '<small>{}<br>por {}</small>',
                last_reply.created_at.strftime('%d/%m %H:%M'),
                last_reply.user.get_full_name() or last_reply.user.username
            )
        return format_html('<small>{}</small>', obj.created_at.strftime('%d/%m %H:%M'))
    last_activity.short_description = 'Última Atividade'
    
    def actions_column(self, obj):
        actions = []
        
        # Botão de resposta rápida
        if obj.status != 'closed':
            actions.append(f'<a href="#" onclick="quickReply({obj.id})" class="button">Resposta Rápida</a>')
        
        # Botão de visualizar no site
        view_url = reverse('admin:support_supportticket_change', args=[obj.id])
        actions.append(f'<a href="{view_url}" class="button">Gerenciar</a>')
        
        return format_html(' '.join(actions))
    actions_column.short_description = 'Ações'
    
    def ticket_summary(self, obj):
        """Resumo do ticket para o admin"""
        if not obj.pk:
            return "Salve o ticket para ver o resumo"
        
        replies_count = obj.replies.count()
        staff_replies = obj.replies.filter(is_staff_reply=True).count()
        user_replies = replies_count - staff_replies
        
        summary = f"""
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #007cba;">
            <h4>Resumo do Ticket #{obj.id}</h4>
            <p><strong>Total de respostas:</strong> {replies_count}</p>
            <p><strong>Respostas da equipe:</strong> {staff_replies}</p>
            <p><strong>Respostas do usuário:</strong> {user_replies}</p>
            <p><strong>Criado:</strong> {obj.created_at.strftime('%d/%m/%Y às %H:%M')}</p>
            <p><strong>Última atualização:</strong> {obj.updated_at.strftime('%d/%m/%Y às %H:%M')}</p>
        </div>
        """
        return mark_safe(summary)
    ticket_summary.short_description = 'Resumo'
    
    # Ações em massa
    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(status='resolved')
        self.message_user(request, f'{updated} ticket(s) marcado(s) como resolvido(s).')
    mark_as_resolved.short_description = "Marcar como resolvido"
    
    def mark_as_in_progress(self, request, queryset):
        updated = queryset.update(status='in_progress')
        self.message_user(request, f'{updated} ticket(s) marcado(s) como em andamento.')
    mark_as_in_progress.short_description = "Marcar como em andamento"
    
    def assign_to_me(self, request, queryset):
        updated = queryset.update(assigned_to=request.user)
        self.message_user(request, f'{updated} ticket(s) atribuído(s) a você.')
    assign_to_me.short_description = "Atribuir a mim"
    
    def save_formset(self, request, form, formset, change):
        """Salvar respostas inline"""
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, TicketReply):
                if not instance.user_id:
                    instance.user = request.user
                    instance.is_staff_reply = True
                instance.save()
        formset.save_m2m()

@admin.register(TicketReply)
class TicketReplyAdmin(admin.ModelAdmin):
    list_display = ['ticket_id', 'user', 'message_preview', 'is_staff_reply', 'created_at']
    list_filter = ['is_staff_reply', 'created_at']
    search_fields = ['ticket__subject', 'user__username', 'message']
    ordering = ['-created_at']
    
    def ticket_id(self, obj):
        return f"Ticket #{obj.ticket.id}"
    ticket_id.short_description = 'Ticket'
    
    def message_preview(self, obj):
        return obj.message[:100] + "..." if len(obj.message) > 100 else obj.message
    message_preview.short_description = 'Mensagem'

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject_preview', 'is_read_display', 'created_at', 'actions_column']
    list_filter = ['is_read', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 30
    
    readonly_fields = ['created_at']
    actions = ['mark_as_read', 'mark_as_unread']
    
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
    
    def actions_column(self, obj):
        actions = []
        if not obj.is_read:
            actions.append('<a href="#" onclick="markAsRead({})">Marcar como Lida</a>'.format(obj.id))
        actions.append('<a href="mailto:{}">Responder por Email</a>'.format(obj.email))
        return format_html(' | '.join(actions))
    actions_column.short_description = 'Ações'
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} mensagens marcadas como lidas.')
    mark_as_read.short_description = "Marcar como lidas"
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} mensagens marcadas como não lidas.')
    mark_as_unread.short_description = "Marcar como não lidas"

# CSS personalizado para o admin
admin.site.site_header = "EEAR Preparatório - Administração"
admin.site.site_title = "EEAR Admin"
admin.site.index_title = "Painel de Controle do Sistema"

# JavaScript personalizado para ações rápidas
admin.site.enable_nav_sidebar = False