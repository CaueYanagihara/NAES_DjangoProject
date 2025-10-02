from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views import View
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils.text import slugify
from django.db import models
from .models import (
    Cliente, Atendente, Empresa, HorarioFuncionamento, CategoriaServico, 
    Servico, HorarioAtendimento, Agendamento, StatusAgendamento, Tenant
)
from .forms import AgendamentoForm, EmpresaForm, CustomUserCreationForm, AtendenteForm
from .decorators import (
    AdminOrManagerMixin, ManagerOnlyMixin, AtendenteMixin, 
    ClienteAccessMixin, SuperuserRequiredMixin, ClienteOwnerMixin, 
    AgendamentoOwnerMixin, OwnerRequiredMixin
)
from django.http import HttpResponseRedirect


# Mixin para isolamento multi-tenant
class TenantMixin:
    """Mixin que automaticamente filtra dados pelo tenant do usuário logado"""
    
    def get_tenant(self):
        """Retorna o tenant do usuário logado ou cria um se não existir"""
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Usuário deve estar logado")
        
        # Usar a nova propriedade tenant
        user_tenant = self.request.user.tenant
        
        if user_tenant:
            return user_tenant
        else:
            # Se não tem tenant, criar um automaticamente
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
        
        # Associar tenant ao usuário
        user.set_tenant(tenant)
        
        return tenant
    
    def get_queryset(self):
        """Filtra queryset pelo tenant do usuário"""
        queryset = super().get_queryset()
        tenant = self.get_tenant()
        return queryset.filter(tenant=tenant)
    
    def form_valid(self, form):
        """Automaticamente associa o objeto ao tenant"""
        if hasattr(form.instance, 'tenant'):
            form.instance.tenant = self.get_tenant()
        return super().form_valid(form)

# View customizada para cadastro de usuários com criação automática de tenant
class CustomUserCreateView(CreateView):
    template_name = 'protocolos/auth/cadastro.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Cadastro de Usuário'
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.instance
        
        # Cria tenant automaticamente para o novo usuário
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
        
        # Associar tenant ao usuário através do profile
        user.set_tenant(tenant)
        
        # Adicionar usuário ao grupo Administradores automaticamente
        from django.contrib.auth.models import Group
        try:
            grupo_admin = Group.objects.get(name='Administradores')
            user.groups.add(grupo_admin)
        except Group.DoesNotExist:
            # Se grupo não existe, criar e adicionar
            grupo_admin = Group.objects.create(name='Administradores')
            user.groups.add(grupo_admin)
        
        messages.success(
            self.request, 
            f'Conta criada com sucesso! Seu espaço privado foi configurado automaticamente. '
            f'Você foi adicionado como <strong>Administrador</strong> da organização "{tenant.nome}". '
            'Agora você pode fazer login e começar a usar seu próprio sistema de agendamentos.'
        )
        return response

# Views com TenantMixin aplicado

# Empresa (apenas Administradores e Gerentes)
class EmpresaCreate(LoginRequiredMixin, AdminOrManagerMixin, TenantMixin, CreateView):
    template_name = "protocolos/empresa-form.html"
    model = Empresa
    form_class = EmpresaForm
    success_url = reverse_lazy("listar-empresa")
    extra_context = {"titulo": "Cadastro de Empresa"}
    login_url = "/protocolo/login/"

class EmpresaUpdate(LoginRequiredMixin, AdminOrManagerMixin, TenantMixin, UpdateView):
    template_name = "protocolos/empresa-form.html"
    model = Empresa
    form_class = EmpresaForm
    success_url = reverse_lazy("listar-empresa")
    extra_context = {"titulo": "Atualizar Empresa"}
    login_url = "/protocolo/login/"

class EmpresaDelete(LoginRequiredMixin, AdminOrManagerMixin, TenantMixin, DeleteView):
    template_name = "protocolos/form-excluir.html"
    model = Empresa
    success_url = reverse_lazy("listar-empresa")
    extra_context = {"titulo": "Excluir Empresa"}
    login_url = "/protocolo/login/"

class EmpresaList(LoginRequiredMixin, AtendenteMixin, TenantMixin, ListView):
    template_name = "protocolos/listas/empresa.html"
    model = Empresa
    login_url = "/protocolo/login/"

# Cliente (controle de propriedade - usuário só pode editar/excluir clientes que criou)
class ClienteCreate(LoginRequiredMixin, AtendenteMixin, TenantMixin, CreateView):
    template_name = "protocolos/form.html"
    model = Cliente
    fields = ["nome", "email", "telefone", "cpf", "rua", "numero", "bairro", "cidade", "estado", "cep"]
    success_url = reverse_lazy("listar-cliente")
    extra_context = {"titulo": "Cadastro de Cliente"}
    login_url = "/protocolo/login/"
    
    def form_valid(self, form):
        # Automaticamente associa o usuário como criador
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'Cliente {form.instance.nome} cadastrado com sucesso!')
        return response

class ClienteUpdate(LoginRequiredMixin, ClienteOwnerMixin, TenantMixin, UpdateView):
    template_name = "protocolos/form.html"
    model = Cliente
    fields = ["nome", "email", "telefone", "cpf", "rua", "numero", "bairro", "cidade", "estado", "cep"]
    success_url = reverse_lazy("listar-cliente")
    extra_context = {"titulo": "Atualizar Cliente"}
    login_url = "/protocolo/login/"

class ClienteDelete(LoginRequiredMixin, ClienteOwnerMixin, TenantMixin, DeleteView):
    template_name = "protocolos/form-excluir.html"
    model = Cliente
    success_url = reverse_lazy("listar-cliente")
    extra_context = {"titulo": "Excluir Cliente"}
    login_url = "/protocolo/login/"

class ClienteList(LoginRequiredMixin, AtendenteMixin, TenantMixin, ListView):
    template_name = "protocolos/listas/cliente.html"
    model = Cliente
    login_url = "/protocolo/login/"
    
    def get_queryset(self):
        """Filtra clientes baseado no grupo do usuário"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Superuser vê todos
        if user.is_superuser:
            return queryset
        
        # Administradores e Gerentes veem todos do tenant
        if user.groups.filter(name__in=['Administradores', 'Gerentes']).exists():
            return queryset
        
        # Atendentes veem todos do tenant
        if user.groups.filter(name='Atendentes').exists():
            return queryset
            
        # Usuários comuns só veem clientes que eles criaram
        return queryset.filter(created_by=user)

# Atendente (apenas Administradores e Gerentes podem gerenciar)
class AtendenteCreate(LoginRequiredMixin, AdminOrManagerMixin, TenantMixin, CreateView):
    template_name = "protocolos/atendente-form.html"
    model = Atendente
    form_class = AtendenteForm
    success_url = reverse_lazy("listar-atendente")
    extra_context = {"titulo": "Cadastro de Atendente"}
    login_url = "/protocolo/login/"
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.get_tenant()
        return kwargs
    
    def form_valid(self, form):
        response = super().form_valid(form)
        atendente = form.instance
        
        # Verificar se senha foi gerada automaticamente
        if hasattr(form, 'senha_gerada') and form.senha_gerada:
            messages.success(
                self.request,
                f'Atendente {atendente.nome} cadastrado com sucesso! '
                f'Senha gerada automaticamente: <strong>{form.senha_gerada}</strong> '
                '(Anote esta senha, ela não será exibida novamente)'
            )
        else:
            messages.success(
                self.request,
                f'Atendente {atendente.nome} cadastrado com sucesso! '
                'O usuário já pode fazer login no sistema com o email cadastrado.'
            )
        
        return response

class AtendenteUpdate(LoginRequiredMixin, AdminOrManagerMixin, TenantMixin, UpdateView):
    template_name = "protocolos/form.html"
    model = Atendente
    fields = ["empresa", "nome", "email", "telefone", "especialidades"]
    success_url = reverse_lazy("listar-atendente")
    extra_context = {"titulo": "Atualizar Atendente"}
    login_url = "/protocolo/login/"
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        tenant = self.get_tenant()
        form.fields['empresa'].queryset = Empresa.objects.filter(tenant=tenant)
        form.fields['especialidades'].queryset = Servico.objects.filter(tenant=tenant)
        return form
    
    def form_valid(self, form):
        # Atualizar dados do usuário associado
        atendente = form.instance
        if atendente.user:
            user = atendente.user
            user.email = atendente.email
            user.username = atendente.email
            user.first_name = atendente.nome.split()[0] if atendente.nome else ''
            user.last_name = ' '.join(atendente.nome.split()[1:]) if len(atendente.nome.split()) > 1 else ''
            user.save()
        
        messages.success(self.request, f'Dados do atendente {atendente.nome} atualizados com sucesso!')
        return super().form_valid(form)

class AtendenteDelete(LoginRequiredMixin, AdminOrManagerMixin, TenantMixin, DeleteView):
    template_name = "protocolos/form-excluir.html"
    model = Atendente
    success_url = reverse_lazy("listar-atendente")
    extra_context = {"titulo": "Excluir Atendente"}
    login_url = "/protocolo/login/"

class AtendenteList(LoginRequiredMixin, AtendenteMixin, TenantMixin, ListView):
    template_name = "protocolos/listas/atendente.html"
    model = Atendente
    login_url = "/protocolo/login/"

# Continuando com as outras views...
class HorarioFuncionamentoCreate(LoginRequiredMixin, TenantMixin, CreateView):
    template_name = "protocolos/form.html"
    model = HorarioFuncionamento
    fields = ["empresa", "diaSemana", "horaInicio", "horaFim"]
    success_url = reverse_lazy("listar-horario-funcionamento")
    extra_context = {"titulo": "Cadastro de Horário de Funcionamento"}
    login_url = "/protocolo/login/"
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['empresa'].queryset = Empresa.objects.filter(tenant=self.get_tenant())
        return form

class HorarioFuncionamentoUpdate(LoginRequiredMixin, TenantMixin, UpdateView):
    template_name = "protocolos/form.html"
    model = HorarioFuncionamento
    fields = ["empresa", "diaSemana", "horaInicio", "horaFim"]
    success_url = reverse_lazy("listar-horario-funcionamento")
    extra_context = {"titulo": "Atualizar Horário de Funcionamento"}
    login_url = "/protocolo/login/"
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['empresa'].queryset = Empresa.objects.filter(tenant=self.get_tenant())
        return form

class HorarioFuncionamentoDelete(LoginRequiredMixin, TenantMixin, DeleteView):
    template_name = "protocolos/form-excluir.html"
    model = HorarioFuncionamento
    success_url = reverse_lazy("listar-horario-funcionamento")
    extra_context = {"titulo": "Excluir Horário de Funcionamento"}
    login_url = "/protocolo/login/"

class HorarioFuncionamentoList(LoginRequiredMixin, TenantMixin, ListView):
    template_name = "protocolos/listas/horario_funcionamento.html"
    model = HorarioFuncionamento
    login_url = "/protocolo/login/"

# CategoriaServico (apenas Admin/Gerentes criam/editam, Atendentes visualizam)
class CategoriaServicoCreate(LoginRequiredMixin, AdminOrManagerMixin, TenantMixin, CreateView):
    template_name = "protocolos/form.html"
    model = CategoriaServico
    fields = ["empresa", "nome", "descricao"]
    success_url = reverse_lazy("listar-categoria-servico")
    extra_context = {"titulo": "Cadastro de Categoria de Serviço"}
    login_url = "/protocolo/login/"
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['empresa'].queryset = Empresa.objects.filter(tenant=self.get_tenant())
        return form

class CategoriaServicoUpdate(LoginRequiredMixin, AdminOrManagerMixin, TenantMixin, UpdateView):
    template_name = "protocolos/form.html"
    model = CategoriaServico
    fields = ["empresa", "nome", "descricao"]
    success_url = reverse_lazy("listar-categoria-servico")
    extra_context = {"titulo": "Atualizar Categoria de Serviço"}
    login_url = "/protocolo/login/"
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['empresa'].queryset = Empresa.objects.filter(tenant=self.get_tenant())
        return form

class CategoriaServicoDelete(LoginRequiredMixin, AdminOrManagerMixin, TenantMixin, DeleteView):
    template_name = "protocolos/form-excluir.html"
    model = CategoriaServico
    success_url = reverse_lazy("listar-categoria-servico")
    extra_context = {"titulo": "Excluir Categoria de Serviço"}
    login_url = "/protocolo/login/"

class CategoriaServicoList(LoginRequiredMixin, AtendenteMixin, TenantMixin, ListView):
    template_name = "protocolos/listas/categoria_servico.html"
    model = CategoriaServico
    login_url = "/protocolo/login/"

# Servico (apenas Admin/Gerentes criam/editam, Atendentes visualizam)
class ServicoCreate(LoginRequiredMixin, AdminOrManagerMixin, TenantMixin, CreateView):
    template_name = "protocolos/form.html"
    model = Servico
    fields = ["categoria", "nome", "descricao", "preco", "duracaoMinutos"]
    success_url = reverse_lazy("listar-servico")
    extra_context = {"titulo": "Cadastro de Serviço"}
    login_url = "/protocolo/login/"
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['categoria'].queryset = CategoriaServico.objects.filter(tenant=self.get_tenant())
        return form

class ServicoUpdate(LoginRequiredMixin, AdminOrManagerMixin, TenantMixin, UpdateView):
    template_name = "protocolos/form.html"
    model = Servico
    fields = ["categoria", "nome", "descricao", "preco", "duracaoMinutos"]
    success_url = reverse_lazy("listar-servico")
    extra_context = {"titulo": "Atualizar Serviço"}
    login_url = "/protocolo/login/"
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['categoria'].queryset = CategoriaServico.objects.filter(tenant=self.get_tenant())
        return form

class ServicoDelete(LoginRequiredMixin, AdminOrManagerMixin, TenantMixin, DeleteView):
    template_name = "protocolos/form-excluir.html"
    model = Servico
    success_url = reverse_lazy("listar-servico")
    extra_context = {"titulo": "Excluir Serviço"}
    login_url = "/protocolo/login/"

class ServicoList(LoginRequiredMixin, AtendenteMixin, TenantMixin, ListView):
    template_name = "protocolos/listas/servico.html"
    model = Servico
    login_url = "/protocolo/login/"

# HorarioAtendimento
class HorarioAtendimentoCreate(LoginRequiredMixin, TenantMixin, CreateView):
    template_name = "protocolos/form.html"
    model = HorarioAtendimento
    fields = ["atendente", "diaSemana", "horaInicio", "horaFim"]
    success_url = reverse_lazy("listar-horario-atendimento")
    extra_context = {"titulo": "Cadastro de Horário de Atendimento"}
    login_url = "/protocolo/login/"
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['atendente'].queryset = Atendente.objects.filter(tenant=self.get_tenant())
        return form

class HorarioAtendimentoUpdate(LoginRequiredMixin, TenantMixin, UpdateView):
    template_name = "protocolos/form.html"
    model = HorarioAtendimento
    fields = ["atendente", "diaSemana", "horaInicio", "horaFim"]
    success_url = reverse_lazy("listar-horario-atendimento")
    extra_context = {"titulo": "Atualizar Horário de Atendimento"}
    login_url = "/protocolo/login/"
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['atendente'].queryset = Atendente.objects.filter(tenant=self.get_tenant())
        return form

class HorarioAtendimentoDelete(LoginRequiredMixin, TenantMixin, DeleteView):
    template_name = "protocolos/form-excluir.html"
    model = HorarioAtendimento
    success_url = reverse_lazy("listar-horario-atendimento")
    extra_context = {"titulo": "Excluir Horário de Atendimento"}
    login_url = "/protocolo/login/"

class HorarioAtendimentoList(LoginRequiredMixin, TenantMixin, ListView):
    template_name = "protocolos/listas/horario_atendimento.html"
    model = HorarioAtendimento
    login_url = "/protocolo/login/"

# Agendamento (controle de propriedade - usuário só pode modificar agendamentos que criou)
class AgendamentoCreate(LoginRequiredMixin, TenantMixin, CreateView):
    template_name = "protocolos/form.html"
    model = Agendamento
    form_class = AgendamentoForm
    success_url = reverse_lazy("listar-agendamento")
    extra_context = {"titulo": "Cadastro de Agendamento"}
    login_url = "/protocolo/login/"
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        tenant = self.get_tenant()
        user = self.request.user
        
        # Filtrar opções baseado no usuário
        if user.groups.filter(name__in=['Administradores', 'Gerentes']).exists() or user.is_superuser:
            # Admin/Gerentes veem todos os clientes do tenant
            form.fields['cliente'].queryset = Cliente.objects.filter(tenant=tenant)
        else:
            # Usuários comuns só veem clientes que eles criaram
            form.fields['cliente'].queryset = Cliente.objects.filter(tenant=tenant, created_by=user)
        
        form.fields['empresa'].queryset = Empresa.objects.filter(tenant=tenant)
        form.fields['servico'].queryset = Servico.objects.filter(tenant=tenant)
        form.fields['atendente'].queryset = Atendente.objects.filter(tenant=tenant)
        return form
    
    def form_valid(self, form):
        # Automaticamente associa o usuário como criador
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'Agendamento para {form.instance.cliente.nome} criado com sucesso!')
        return response

class AgendamentoUpdate(LoginRequiredMixin, AgendamentoOwnerMixin, TenantMixin, UpdateView):
    template_name = "protocolos/form.html"
    model = Agendamento
    form_class = AgendamentoForm
    success_url = reverse_lazy("listar-agendamento")
    extra_context = {"titulo": "Atualizar Agendamento"}
    login_url = "/protocolo/login/"
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        tenant = self.get_tenant()
        user = self.request.user
        
        # Filtrar opções baseado no usuário
        if user.groups.filter(name__in=['Administradores', 'Gerentes']).exists() or user.is_superuser:
            form.fields['cliente'].queryset = Cliente.objects.filter(tenant=tenant)
        else:
            form.fields['cliente'].queryset = Cliente.objects.filter(tenant=tenant, created_by=user)
        
        form.fields['empresa'].queryset = Empresa.objects.filter(tenant=tenant)
        form.fields['servico'].queryset = Servico.objects.filter(tenant=tenant)
        form.fields['atendente'].queryset = Atendente.objects.filter(tenant=tenant)
        return form

class AgendamentoDelete(LoginRequiredMixin, AgendamentoOwnerMixin, TenantMixin, DeleteView):
    template_name = "protocolos/form-excluir.html"
    model = Agendamento
    success_url = reverse_lazy("listar-agendamento")
    extra_context = {"titulo": "Excluir Agendamento"}
    login_url = "/protocolo/login/"

class AgendamentoList(LoginRequiredMixin, TenantMixin, ListView):
    template_name = "protocolos/listas/agendamento.html"
    model = Agendamento
    login_url = "/protocolo/login/"
    
    def get_queryset(self):
        """Filtra agendamentos baseado no grupo do usuário"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Superuser vê todos
        if user.is_superuser:
            return queryset
        
        # Administradores e Gerentes veem todos do tenant
        if user.groups.filter(name__in=['Administradores', 'Gerentes']).exists():
            return queryset
        
        # Atendentes veem todos do tenant
        if user.groups.filter(name='Atendentes').exists():
            return queryset
            
        # Usuários comuns só veem agendamentos que eles criaram OU onde são o cliente
        return queryset.filter(
            models.Q(created_by=user) | 
            models.Q(cliente__email=user.email)
        )

# Movimento: Progredir Status do Agendamento
class ProgredirStatusAgendamentoView(LoginRequiredMixin, TenantMixin, View):
    login_url = "/protocolo/login/"
    STATUS_PROXIMO = {
        StatusAgendamento.PENDENTE: StatusAgendamento.CONFIRMADO,
        StatusAgendamento.CONFIRMADO: StatusAgendamento.CONCLUIDO,
    }

    MENSAGENS = {
        StatusAgendamento.PENDENTE: "Agendamento confirmado com sucesso!",
        StatusAgendamento.CONFIRMADO: "Agendamento concluído com sucesso!",
    }

    def post(self, request, pk):
        tenant = self.get_tenant()
        agendamento = get_object_or_404(Agendamento, pk=pk, tenant=tenant)
        status_atual = agendamento.status
        proximo_status = self.STATUS_PROXIMO.get(status_atual)
        if proximo_status:
            agendamento.status = proximo_status
            agendamento.save()
            messages.success(request, self.MENSAGENS[status_atual])
        else:
            messages.warning(request, "Ação não permitida para o status atual.")
        return redirect("listar-agendamento")

# View específica para cadastro público de clientes (mantida sem tenant, mas com autenticação opcional)
class ClienteCreatePublico(CreateView):
    template_name = "protocolos/cadastro-cliente-publico.html"
    model = Cliente
    fields = ["nome", "email", "telefone", "cpf", "rua", "numero", "bairro", "cidade", "estado", "cep"]
    success_url = reverse_lazy("index")
    extra_context = {"titulo": "Cadastro de Cliente"}
    
    def form_valid(self, form):
        # Se não há usuário logado, criar cliente sem tenant
        if not self.request.user.is_authenticated:
            form.instance.tenant = None
        else:
            # Se há usuário logado, associar ao tenant
            try:
                form.instance.tenant = self.request.user.tenant
            except:
                form.instance.tenant = None
        
        messages.success(self.request, 'Cliente cadastrado com sucesso!')
        return super().form_valid(form)

def custom_logout(request):
    """View customizada para logout com mensagem de confirmação"""
    from django.contrib.auth import logout
    from django.shortcuts import render
    
    logout(request)
    messages.success(request, 'Você foi desconectado com sucesso!')
    return render(request, 'protocolos/auth/logout.html')

# Views de autenticação personalizadas
class CustomLoginView(LoginView):
    template_name = 'protocolos/auth/login.html'
    redirect_authenticated_user = True
    
    def dispatch(self, request, *args, **kwargs):
        # Limpar mensagens antigas ao carregar a página de login
        if request.method == 'GET':
            # Limpa todas as mensagens existentes da sessão
            storage = messages.get_messages(request)
            for message in storage:
                pass  # Isso consome as mensagens
            storage.used = True
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        # Primeiro verifica se há um 'next' parameter na URL
        next_url = self.get_redirect_url()
        if next_url:
            return next_url
        
        # Se não há 'next', redireciona para dashboard se o usuário estiver autenticado
        if self.request.user.is_authenticated:
            return reverse_lazy('dashboard')
        
        # Fallback para página inicial
        return reverse_lazy('index')
    
    def form_valid(self, form):
        messages.success(self.request, f'Bem-vindo, {form.get_user().get_full_name() or form.get_user().username}!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Email ou senha incorretos. Tente novamente.')
        return super().form_invalid(form)

class CustomLogoutView(LogoutView):
    template_name = 'protocolos/auth/logout.html'
    http_method_names = ['get', 'post']  # Permitir GET e POST
    
    def get(self, request, *args, **kwargs):
        """Handle GET request - perform logout and show template"""
        logout(request)
        return self.render_to_response(self.get_context_data())
    
    def post(self, request, *args, **kwargs):
        """Handle POST request - perform logout and show template"""
        logout(request)
        return self.render_to_response(self.get_context_data())

# View personalizada para acesso negado
def acesso_negado(request):
    """View para exibir página de acesso negado"""
    return render(request, 'protocolos/auth/acesso_negado.html', status=403)

# View para exibir perfil do usuário com informações de grupos
@login_required(login_url='/protocolo/login/')
def perfil_usuario(request):
    """View para exibir informações sobre grupos e permissões do usuário"""
    context = {
        'titulo': 'Meu Perfil de Acesso',
        'user': request.user,
    }
    return render(request, 'protocolos/auth/perfil.html', context)

# Tenant Views (apenas para superusers)
class TenantCreate(LoginRequiredMixin, CreateView):
    template_name = "protocolos/form.html"
    model = Tenant
    fields = ["nome", "slug", "max_empresas", "max_clientes", "max_agendamentos_mes"]
    success_url = reverse_lazy("listar-tenant")
    extra_context = {"titulo": "Cadastro de Tenant"}
    login_url = "/protocolo/login/"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, 'Acesso negado. Apenas administradores podem gerenciar tenants.')
            return redirect('index')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

class TenantUpdate(LoginRequiredMixin, UpdateView):
    template_name = "protocolos/form.html"
    model = Tenant
    fields = ["nome", "slug", "max_empresas", "max_clientes", "max_agendamentos_mes"]
    success_url = reverse_lazy("listar-tenant")
    extra_context = {"titulo": "Atualizar Tenant"}
    login_url = "/protocolo/login/"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, 'Acesso negado. Apenas administradores podem gerenciar tenants.')
            return redirect('index')
        return super().dispatch(request, *args, **kwargs)

class TenantDelete(LoginRequiredMixin, DeleteView):
    template_name = "protocolos/form-excluir.html"
    model = Tenant
    success_url = reverse_lazy("listar-tenant")
    extra_context = {"titulo": "Excluir Tenant"}
    login_url = "/protocolo/login/"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, 'Acesso negado. Apenas administradores podem gerenciar tenants.')
            return redirect('index')
        return super().dispatch(request, *args, **kwargs)

class TenantList(LoginRequiredMixin, ListView):
    template_name = "protocolos/listas/tenant.html"
    model = Tenant
    login_url = "/protocolo/login/"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, 'Acesso negado. Apenas administradores podem gerenciar tenants.')
            return redirect('index')
        return super().dispatch(request, *args, **kwargs)
