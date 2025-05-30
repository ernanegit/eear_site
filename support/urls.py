from django.urls import path
from . import views

app_name = 'support'

urlpatterns = [
    path('faq/', views.faq, name='faq'),
    path('contact/', views.contact, name='contact'),
    path('tickets/', views.support_tickets, name='tickets'),
    path('tickets/create/', views.create_ticket, name='create_ticket'),
    path('tickets/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
]