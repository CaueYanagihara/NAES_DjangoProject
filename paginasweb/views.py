from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class PaginaInicial(TemplateView):
    template_name = "paginasweb/index.html"


class SobreView(TemplateView):
    template_name = "paginasweb/sobre.html"


class ContatoView(TemplateView):
    template_name = "paginasweb/contato.html"


class EscolherCadastroView(TemplateView):
    template_name = "paginasweb/escolher_cadastro.html"


class HomeView(LoginRequiredMixin, TemplateView):
    """Página inicial após login - Dashboard"""
    template_name = "paginasweb/home.html"
    login_url = "/protocolo/login/"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Dashboard'
        return context