from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta

class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=2, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_premium = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']  # Corrigido: removido 'email'

    def save(self, *args, **kwargs):
        # Garantir que email seja único e em lowercase
        if self.email:
            self.email = self.email.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

class Enrollment(models.Model):
    PLAN_CHOICES = [
        ('basic', 'Plano Básico - Grátis'),
        ('premium', 'Plano Premium - R$ 49,90/mês'),
        ('annual', 'Plano Anual - R$ 399,90/ano'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('active', 'Ativo'),
        ('expired', 'Expirado'),
        ('cancelled', 'Cancelado'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='basic')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    
    def save(self, *args, **kwargs):
        if self.plan == 'premium' and not self.end_date:
            self.end_date = timezone.now() + timedelta(days=30)
        elif self.plan == 'annual' and not self.end_date:
            self.end_date = timezone.now() + timedelta(days=365)
        
        # Update user premium status
        if self.status == 'active' and self.plan in ['premium', 'annual']:
            self.user.is_premium = True
            self.user.save()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.email} - {self.get_plan_display()}"