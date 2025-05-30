
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import FAQ, SupportTicket, TicketReply, Contact
from .forms import ContactForm, SupportTicketForm

def faq(request):
    faqs = FAQ.objects.filter(is_active=True).order_by('category', 'order')
    
    # Group FAQs by category
    faq_categories = {}
    for faq in faqs:
        if faq.category not in faq_categories:
            faq_categories[faq.category] = []
        faq_categories[faq.category].append(faq)
    
    context = {
        'faq_categories': faq_categories,
        'category_choices': FAQ.CATEGORIES,
    }
    return render(request, 'support/faq.html', context)

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save()
            
            # Send email notification (in production)
            try:
                send_mail(
                    subject=f'Novo contato: {contact.subject}',
                    message=f'De: {contact.name} ({contact.email})\n\n{contact.message}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.CONTACT_EMAIL],
                    fail_silently=True,
                )
            except:
                pass
            
            messages.success(request, 'Sua mensagem foi enviada com sucesso! Entraremos em contato em breve.')
            return redirect('support:contact')
    else:
        form = ContactForm()
    
    return render(request, 'support/contact.html', {'form': form})

@login_required
def support_tickets(request):
    tickets = SupportTicket.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'support/tickets.html', {'tickets': tickets})

@login_required
def create_ticket(request):
    if request.method == 'POST':
        form = SupportTicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.save()
            
            messages.success(request, f'Ticket #{ticket.id} criado com sucesso!')
            return redirect('support:ticket_detail', ticket_id=ticket.id)
    else:
        form = SupportTicketForm()
    
    return render(request, 'support/create_ticket.html', {'form': form})

@login_required
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)
    replies = ticket.replies.all().order_by('created_at')
    
    if request.method == 'POST':
        message = request.POST.get('message')
        if message:
            TicketReply.objects.create(
                ticket=ticket,
                user=request.user,
                message=message,
                is_staff_reply=False
            )
            messages.success(request, 'Resposta adicionada com sucesso!')
            return redirect('support:ticket_detail', ticket_id=ticket.id)
    
    context = {
        'ticket': ticket,
        'replies': replies,
    }
    return render(request, 'support/ticket_detail.html', context)
# Create your views here.
