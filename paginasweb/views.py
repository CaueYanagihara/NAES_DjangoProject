from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.utils.text import slugify
from protocolos.models import Tenant


# Importar o TenantMixin das views de protocolos
class TenantMixin:
    """Mixin que automaticamente filtra dados pelo tenant do usuário logado"""
    
    def get_tenant(self):
        """Retorna o tenant do usuário logado ou cria um se não existir"""
        if not self.request.user.is_authenticated:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Usuário deve estar logado")
        
        try:
            return self.request.user.tenant
        except Tenant.DoesNotExist:
            return self.create_tenant_for_user()
    
    def create_tenant_for_user(self):
        """Cria um tenant automaticamente para o usuário"""
        user = self.request.user
        base_slug = slugify(user.username)
        slug = base_slug
        counter = 1
        
        while Tenant.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        tenant = Tenant.objects.create(
            nome=f"Organização de {user.get_full_name() or user.username}",
            slug=slug,
            owner=user
        )
        return tenant

class PaginaInicial(TemplateView):
    template_name = "paginasweb/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['referer'] = self.request.META.get('HTTP_REFERER', '/')
        return context


class SobreView(TemplateView):
    template_name = "paginasweb/sobre.html"


class ContatoView(TemplateView):
    template_name = "paginasweb/contato.html"


class EscolherCadastroView(LoginRequiredMixin, TemplateView):
    template_name = "paginasweb/escolher_cadastro.html"
    login_url = "/protocolo/login/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['referer'] = self.request.META.get('HTTP_REFERER', '/')
        return context


class HomeView(LoginRequiredMixin, TenantMixin, TemplateView):
    """Página inicial após login - Dashboard com informações do tenant"""
    template_name = "paginasweb/home.html"
    login_url = "/protocolo/login/"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Dashboard'
        
        # Adicionar informações do tenant
        tenant = self.get_tenant()
        context['tenant'] = tenant
        
        # Estatísticas do tenant
        from protocolos.models import Empresa, Cliente, Agendamento
        context['stats'] = {
            'empresas': Empresa.objects.filter(tenant=tenant).count(),
            'clientes': Cliente.objects.filter(tenant=tenant).count(),
            'agendamentos': Agendamento.objects.filter(tenant=tenant).count(),
        }
        
        return context