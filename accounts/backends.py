from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class EmailBackend(ModelBackend):
    """
    Permite autenticação usando email ou username
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        
        try:
            # Tentar encontrar usuário por email ou username
            user = User.objects.get(
                Q(email__iexact=username) | Q(username__iexact=username)
            )
        except User.DoesNotExist:
            return None
        
        if user.check_password(password):
            return user
        
        return None