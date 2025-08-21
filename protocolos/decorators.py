from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from functools import wraps

def tenant_required(view_func):
    """
    Decorator para garantir que o usuário tenha um tenant associado
    """
    @wraps(view_func)
    @login_required(login_url='/protocolo/login/')
    def _wrapped_view(request, *args, **kwargs):
        try:
            request.user.tenant
        except:
            messages.error(request, 'Você precisa ter uma organização configurada para acessar esta página.')
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def superuser_required(view_func):
    """
    Decorator para garantir que apenas superusers acessem a view
    """
    @wraps(view_func)
    @login_required(login_url='/protocolo/login/')
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, 'Acesso negado. Apenas administradores podem acessar esta página.')
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def group_required(*group_names):
    """
    Decorator para garantir que o usuário pertença a pelo menos um dos grupos especificados
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url='/protocolo/login/')
        def _wrapped_view(request, *args, **kwargs):
            if request.user.groups.filter(name__in=group_names).exists() or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, f'Acesso negado. Você precisa ser membro de um dos grupos: {", ".join(group_names)}')
                return redirect('acesso-negado')
        return _wrapped_view
    return decorator

class TenantOwnerMixin(UserPassesTestMixin):
    """
    Mixin para garantir que o usuário seja proprietário do tenant do objeto
    """
    login_url = '/protocolo/login/'
    
    def test_func(self):
        """Verifica se o usuário é proprietário do tenant do objeto"""
        if not self.request.user.is_authenticated:
            return False
        
        obj = self.get_object()
        if hasattr(obj, 'tenant'):
            return obj.tenant.owner == self.request.user
        return True  # Se não há tenant, permite acesso
    
    def handle_no_permission(self):
        """Customiza a mensagem quando não há permissão"""
        if self.request.user.is_authenticated:
            messages.error(self.request, 'Você não tem permissão para acessar este objeto.')
        return super().handle_no_permission()

class SuperuserRequiredMixin(UserPassesTestMixin):
    """
    Mixin para garantir que apenas superusers acessem a view
    """
    login_url = '/protocolo/login/'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, 'Acesso negado. Apenas administradores podem acessar esta página.')
        return super().handle_no_permission()

class GroupRequiredMixin(UserPassesTestMixin):
    """
    Mixin para garantir que o usuário pertença a pelo menos um dos grupos especificados
    """
    login_url = '/protocolo/login/'
    required_groups = []  # Lista de grupos permitidos
    
    def test_func(self):
        """Verifica se o usuário pertence a pelo menos um dos grupos necessários"""
        if self.request.user.is_superuser:
            return True
        return self.request.user.groups.filter(name__in=self.required_groups).exists()
    
    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(
                self.request, 
                f'Acesso negado. Você precisa ser membro de um dos grupos: {", ".join(self.required_groups)}'
            )
        return super().handle_no_permission()

class AdminOrManagerMixin(GroupRequiredMixin):
    """Mixin para acesso de Administradores ou Gerentes"""
    required_groups = ['Administradores', 'Gerentes']

class ManagerOnlyMixin(GroupRequiredMixin):
    """Mixin para acesso apenas de Gerentes"""
    required_groups = ['Gerentes']

class AtendenteMixin(GroupRequiredMixin):
    """Mixin para acesso de Atendentes, Gerentes ou Administradores"""
    required_groups = ['Atendentes', 'Gerentes', 'Administradores']

class ClienteAccessMixin(UserPassesTestMixin):
    """
    Mixin para controlar acesso de clientes (apenas aos próprios dados)
    """
    login_url = '/protocolo/login/'
    
    def test_func(self):
        """Verifica se o usuário pode acessar os dados"""
        user = self.request.user
        
        # Superuser e staff sempre podem
        if user.is_superuser or user.is_staff:
            return True
        
        # Membros dos grupos administrativos podem
        if user.groups.filter(name__in=['Administradores', 'Gerentes', 'Atendentes']).exists():
            return True
        
        # Clientes só podem acessar seus próprios dados
        if user.groups.filter(name='Clientes').exists():
            obj = self.get_object()
            if hasattr(obj, 'cliente'):
                return obj.cliente.email == user.email
            elif hasattr(obj, 'user'):
                return obj.user == user
            
        return False
    
    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, 'Você só pode acessar seus próprios dados.')
        return super().handle_no_permission()

class OwnerRequiredMixin(UserPassesTestMixin):
    """
    Mixin para garantir que apenas o criador do objeto possa modificá-lo
    """
    login_url = '/protocolo/login/'
    owner_field = 'created_by'  # Campo que identifica o criador
    
    def test_func(self):
        """Verifica se o usuário é o proprietário do objeto"""
        user = self.request.user
        
        # Superuser sempre pode
        if user.is_superuser:
            return True
        
        # Administradores e Gerentes podem acessar todos os objetos do tenant
        if user.groups.filter(name__in=['Administradores', 'Gerentes']).exists():
            return True
        
        # Verificar se o usuário é o criador do objeto
        obj = self.get_object()
        if hasattr(obj, self.owner_field):
            return getattr(obj, self.owner_field) == user
        
        return False
    
    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, 'Você só pode modificar objetos que você mesmo criou.')
        return super().handle_no_permission()

class ClienteOwnerMixin(UserPassesTestMixin):
    """
    Mixin específico para Cliente - controla acesso baseado em quem criou
    """
    login_url = '/protocolo/login/'
    
    def test_func(self):
        """Verifica se o usuário pode acessar este cliente específico"""
        user = self.request.user
        
        # Superuser sempre pode
        if user.is_superuser:
            return True
        
        # Administradores e Gerentes podem acessar todos
        if user.groups.filter(name__in=['Administradores', 'Gerentes']).exists():
            return True
        
        # Atendentes podem acessar clientes do mesmo tenant
        if user.groups.filter(name='Atendentes').exists():
            obj = self.get_object()
            try:
                user_tenant = user.tenant
                return obj.tenant == user_tenant
            except:
                return False
        
        # Usuário comum só pode acessar cliente que ele criou
        obj = self.get_object()
        return hasattr(obj, 'created_by') and obj.created_by == user
    
    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, 'Você só pode acessar clientes que você cadastrou.')
        return super().handle_no_permission()

class AgendamentoOwnerMixin(UserPassesTestMixin):
    """
    Mixin específico para Agendamento - controla acesso baseado em quem criou ou é o cliente
    """
    login_url = '/protocolo/login/'
    
    def test_func(self):
        """Verifica se o usuário pode acessar este agendamento"""
        user = self.request.user
        
        # Superuser sempre pode
        if user.is_superuser:
            return True
        
        # Administradores e Gerentes podem acessar todos
        if user.groups.filter(name__in=['Administradores', 'Gerentes']).exists():
            return True
        
        # Atendentes podem acessar agendamentos do mesmo tenant
        if user.groups.filter(name='Atendentes').exists():
            obj = self.get_object()
            try:
                user_tenant = user.tenant
                return obj.tenant == user_tenant
            except:
                return False
        
        # Usuário comum pode acessar agendamentos que:
        # 1. Ele criou OU
        # 2. São agendamentos onde ele é o cliente (baseado no email)
        obj = self.get_object()
        
        # Verificar se é o criador
        if hasattr(obj, 'created_by') and obj.created_by == user:
            return True
            
        # Verificar se é o cliente do agendamento
        if hasattr(obj, 'cliente') and obj.cliente.email == user.email:
            return True
            
        return False
    
    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, 'Você só pode acessar agendamentos que você criou ou onde você é o cliente.')
        return super().handle_no_permission()