from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm, UserUpdateForm, EnrollmentForm
from .models import User, Enrollment

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('accounts:login')
    
    def form_valid(self, form):
        messages.success(self.request, 'Conta criada com sucesso! Faça login para continuar.')
        return super().form_valid(form)

@login_required
def profile(request):
    try:
        enrollment = request.user.enrollment
    except Enrollment.DoesNotExist:
        enrollment = None
    
    context = {
        'user': request.user,
        'enrollment': enrollment,
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('accounts:profile')
    else:
        form = UserUpdateForm(instance=request.user)
    
    return render(request, 'accounts/edit_profile.html', {'form': form})

@login_required
def enrollment(request):
    try:
        enrollment = request.user.enrollment
    except Enrollment.DoesNotExist:
        enrollment = None
    
    if request.method == 'POST':
        form = EnrollmentForm(request.POST, instance=enrollment)
        if form.is_valid():
            enrollment = form.save(commit=False)
            enrollment.user = request.user
            enrollment.status = 'active'  # In production, this would be set after payment
            enrollment.save()
            messages.success(request, 'Matrícula realizada com sucesso!')
            return redirect('courses:dashboard')
    else:
        form = EnrollmentForm(instance=enrollment)
    
    return render(request, 'accounts/enrollment.html', {'form': form})

def logout_view(request):
    """View de logout que funciona com GET e POST"""
    if request.user.is_authenticated:
        username = request.user.get_full_name() or request.user.username
        
        # Fazer logout efetivamente
        logout(request)
        
        # Limpar sessão completamente
        if hasattr(request, 'session'):
            request.session.flush()
        
        # Adicionar mensagem de sucesso
        messages.success(request, f'Até logo, {username}! Logout realizado com sucesso.')
        
        # Se for GET, mostrar página de confirmação
        if request.method == 'GET':
            return render(request, 'accounts/logout.html', {
                'logout_success': True,
                'username': username
            })
    
    # Sempre redirecionar para home no final
    return redirect('home')