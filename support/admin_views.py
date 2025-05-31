from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from .models import SupportTicket, TicketReply

@staff_member_required
@require_POST
@csrf_protect
def admin_quick_reply(request, ticket_id):
    """View para processar resposta rápida do admin"""
    ticket = get_object_or_404(SupportTicket, id=ticket_id)
    message = request.POST.get('quick_reply', '').strip()
    
    if not message:
        messages.error(request, 'Mensagem não pode estar vazia.')
        return redirect(f'/admin/support/supportticket/{ticket_id}/change/')
    
    # Criar resposta do staff
    reply = TicketReply.objects.create(
        ticket=ticket,
        user=request.user,
        message=message,
        is_staff_reply=True
    )
    
    # Atualizar status do ticket se necessário
    if ticket.status == 'open':
        ticket.status = 'in_progress'
        ticket.assigned_to = request.user
        ticket.save()
    
    messages.success(request, 'Resposta enviada com sucesso!')
    return redirect(f'/admin/support/supportticket/{ticket_id}/change/')

@staff_member_required
@require_POST
def admin_update_ticket_status(request, ticket_id):
    """AJAX view para atualizar status do ticket"""
    ticket = get_object_or_404(SupportTicket, id=ticket_id)
    new_status = request.POST.get('status')
    
    if new_status in dict(SupportTicket.STATUS_CHOICES):
        old_status = ticket.get_status_display()
        ticket.status = new_status
        
        # Se está marcando como em progresso, atribuir ao usuário atual
        if new_status == 'in_progress' and not ticket.assigned_to:
            ticket.assigned_to = request.user
        
        ticket.save()
        
        # Criar uma nota automática sobre a mudança de status
        TicketReply.objects.create(
            ticket=ticket,
            user=request.user,
            message=f'Status alterado de "{old_status}" para "{ticket.get_status_display()}"',
            is_staff_reply=True
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Status atualizado para {ticket.get_status_display()}'
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Status inválido'
    })

@staff_member_required
def admin_assign_ticket(request, ticket_id):
    """Atribuir ticket ao usuário atual"""
    ticket = get_object_or_404(SupportTicket, id=ticket_id)
    
    if request.method == 'POST':
        ticket.assigned_to = request.user
        if ticket.status == 'open':
            ticket.status = 'in_progress'
        ticket.save()
        
        # Criar nota sobre atribuição
        TicketReply.objects.create(
            ticket=ticket,
            user=request.user,
            message=f'Ticket atribuído a {request.user.get_full_name() or request.user.username}',
            is_staff_reply=True
        )
        
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({'success': True})
        
        messages.success(request, 'Ticket atribuído a você com sucesso!')
    
    return redirect(f'/admin/support/supportticket/{ticket_id}/change/')