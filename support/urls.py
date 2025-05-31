from django.urls import path
from . import views, admin_views

app_name = 'support'

urlpatterns = [
    # URLs públicas
    path('faq/', views.faq, name='faq'),
    path('contact/', views.contact, name='contact'),
    path('tickets/', views.support_tickets, name='tickets'),
    path('tickets/create/', views.create_ticket, name='create_ticket'),
    path('tickets/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    
    # URLs do admin para gerenciar tickets
    path('admin/tickets/<int:ticket_id>/quick-reply/', admin_views.admin_quick_reply, name='admin_quick_reply'),
    path('admin/tickets/<int:ticket_id>/update-status/', admin_views.admin_update_ticket_status, name='admin_update_status'),
    path('admin/tickets/<int:ticket_id>/assign/', admin_views.admin_assign_ticket, name='admin_assign'),
]