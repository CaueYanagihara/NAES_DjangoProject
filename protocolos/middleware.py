from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin

class AuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware personalizado para verificar autenticação em páginas específicas
    """
    
    # URLs que requerem autenticação
    PROTECTED_URLS = [
        '/escolher-cadastro/',
        '/protocolo/',  # Todas as URLs do app protocolos exceto login/logout/cadastro
    ]
    
    # URLs que são públicas mesmo dentro de apps protegidos
    PUBLIC_URLS = [
        '/protocolo/login/',
        '/protocolo/logout/',
        '/protocolo/cadastrar-usuario/',
    ]
    
    def process_request(self, request):
        """
        Processa a requisição antes da view ser chamada
        """
        path = request.path_info
        
        # Verifica se a URL está na lista de proteção
        for protected_url in self.PROTECTED_URLS:
            if path.startswith(protected_url):
                # Verifica se não é uma URL pública
                is_public = any(path.startswith(public_url) for public_url in self.PUBLIC_URLS)
                
                if not is_public and not request.user.is_authenticated:
                    messages.warning(request, 'Você precisa fazer login para acessar esta página.')
                    return redirect('login')
        
        return None

class TenantMiddleware(MiddlewareMixin):
    """
    Middleware para verificar se o usuário tem tenant configurado
    """
    
    # URLs que requerem tenant
    TENANT_REQUIRED_URLS = [
        '/protocolo/empresa/',
        '/protocolo/cliente/',
        '/protocolo/atendente/',
        '/protocolo/servico/',
        '/protocolo/agendamento/',
        '/protocolo/categoria-servico/',
        '/protocolo/horario-funcionamento/',
        '/protocolo/horario-atendimento/',
    ]
    
    def process_request(self, request):
        """
        Verifica se o usuário tem tenant configurado para URLs específicas
        """
        if not request.user.is_authenticated:
            return None
        
        path = request.path_info
        
        # Verifica se a URL requer tenant
        requires_tenant = any(path.startswith(url) for url in self.TENANT_REQUIRED_URLS)
        
        if requires_tenant:
            try:
                tenant = request.user.tenant
                # Adiciona o tenant ao request para facilitar acesso
                request.tenant = tenant
            except:
                messages.error(request, 'Você precisa ter uma organização configurada.')
                return redirect('index')
        
        return None