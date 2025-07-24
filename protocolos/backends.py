from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q

class EmailBackend(ModelBackend):
    """Backend de autenticação que permite login com email ou username"""
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Tentar encontrar usuário por email ou username
            user = User.objects.get(
                Q(username=username) | Q(email=username)
            )
            
            # Verificar se a senha está correta
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except User.DoesNotExist:
            return None
        
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None