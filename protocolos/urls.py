from django.urls import path
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import UserCreationForm
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from . import views
from .forms import CustomUserCreationForm

# Importar suas views (removendo EnderecoCreate, EnderecoUpdate, EnderecoDelete, EnderecoList)
from .views import (
    EmpresaCreate, EmpresaUpdate, EmpresaDelete, EmpresaList,
    ClienteCreate, ClienteUpdate, ClienteDelete, ClienteList, ClienteCreatePublico,
    HorarioFuncionamentoCreate, HorarioFuncionamentoUpdate, HorarioFuncionamentoDelete, HorarioFuncionamentoList,
    CategoriaServicoCreate, CategoriaServicoUpdate, CategoriaServicoDelete, CategoriaServicoList,
    ServicoCreate, ServicoUpdate, ServicoDelete, ServicoList,
    AtendenteCreate, AtendenteUpdate, AtendenteDelete, AtendenteList,
    HorarioAtendimentoCreate, HorarioAtendimentoUpdate, HorarioAtendimentoDelete, HorarioAtendimentoList,
    AgendamentoCreate, AgendamentoUpdate, AgendamentoDelete, AgendamentoList,
    ProgredirStatusAgendamentoView, CustomUserCreateView,
)

urlpatterns = [
    # Empresa
    path('empresa/cadastrar/', EmpresaCreate.as_view(), name='cadastrar-empresa'),
    path('empresa/editar/<uuid:pk>/', EmpresaUpdate.as_view(), name='editar-empresa'),
    path('empresa/excluir/<uuid:pk>/', EmpresaDelete.as_view(), name='excluir-empresa'),
    path('empresa/listar/', EmpresaList.as_view(), name='listar-empresa'),

    # Cliente
    path('cliente/cadastrar/', ClienteCreate.as_view(), name='cadastrar-cliente'),
    path('cliente/editar/<uuid:pk>/', ClienteUpdate.as_view(), name='editar-cliente'),
    path('cliente/excluir/<uuid:pk>/', ClienteDelete.as_view(), name='excluir-cliente'),
    path('cliente/listar/', ClienteList.as_view(), name='listar-cliente'),

    # HorarioFuncionamento
    path('horario-funcionamento/cadastrar/', HorarioFuncionamentoCreate.as_view(), name='cadastrar-horario-funcionamento'),
    path('horario-funcionamento/editar/<int:pk>/', HorarioFuncionamentoUpdate.as_view(), name='editar-horario-funcionamento'),
    path('horario-funcionamento/excluir/<int:pk>/', HorarioFuncionamentoDelete.as_view(), name='excluir-horario-funcionamento'),
    path('horario-funcionamento/listar/', HorarioFuncionamentoList.as_view(), name='listar-horario-funcionamento'),

    # CategoriaServico
    path('categoria-servico/cadastrar/', CategoriaServicoCreate.as_view(), name='cadastrar-categoria-servico'),
    path('categoria-servico/editar/<uuid:pk>/', CategoriaServicoUpdate.as_view(), name='editar-categoria-servico'),
    path('categoria-servico/excluir/<uuid:pk>/', CategoriaServicoDelete.as_view(), name='excluir-categoria-servico'),
    path('categoria-servico/listar/', CategoriaServicoList.as_view(), name='listar-categoria-servico'),

    # Servico
    path('servico/cadastrar/', ServicoCreate.as_view(), name='cadastrar-servico'),
    path('servico/editar/<uuid:pk>/', ServicoUpdate.as_view(), name='editar-servico'),
    path('servico/excluir/<uuid:pk>/', ServicoDelete.as_view(), name='excluir-servico'),
    path('servico/listar/', ServicoList.as_view(), name='listar-servico'),

    # Atendente
    path('atendente/cadastrar/', AtendenteCreate.as_view(), name='cadastrar-atendente'),
    path('atendente/editar/<uuid:pk>/', AtendenteUpdate.as_view(), name='editar-atendente'),
    path('atendente/excluir/<uuid:pk>/', AtendenteDelete.as_view(), name='excluir-atendente'),
    path('atendente/listar/', AtendenteList.as_view(), name='listar-atendente'),

    # HorarioAtendimento
    path('horario-atendimento/cadastrar/', HorarioAtendimentoCreate.as_view(), name='cadastrar-horario-atendimento'),
    path('horario-atendimento/editar/<int:pk>/', HorarioAtendimentoUpdate.as_view(), name='editar-horario-atendimento'),
    path('horario-atendimento/excluir/<int:pk>/', HorarioAtendimentoDelete.as_view(), name='excluir-horario-atendimento'),
    path('horario-atendimento/listar/', HorarioAtendimentoList.as_view(), name='listar-horario-atendimento'),

    # Agendamento
    path('agendamento/cadastrar/', AgendamentoCreate.as_view(), name='cadastrar-agendamento'),
    path('agendamento/editar/<uuid:pk>/', AgendamentoUpdate.as_view(), name='editar-agendamento'),
    path('agendamento/excluir/<uuid:pk>/', AgendamentoDelete.as_view(), name='excluir-agendamento'),
    path('agendamento/listar/', AgendamentoList.as_view(), name='listar-agendamento'),
    path('agendamento/progredir-status/<uuid:pk>/', ProgredirStatusAgendamentoView.as_view(), name='progredir-status-agendamento'),

    # URLs de autenticação do Django
    # URLs de autenticação
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('cadastrar-usuario/', views.CustomUserCreateView.as_view(), name='cadastrar-usuario'),
    path('acesso-negado/', views.acesso_negado, name='acesso-negado'),
    path('meu-perfil/', views.perfil_usuario, name='perfil-usuario'),

    # Cadastro de usuário do sistema (autenticação) - MELHORADO COM VIEW CUSTOMIZADA
    path('cadastrar-usuario/', CustomUserCreateView.as_view(), name='cadastrar-usuario'),

    # Cadastro de cliente da loja (entidade de negócio)
    path('cadastrar/', ClienteCreatePublico.as_view(), name='cadastrar-cliente-publico'),

    # Adicionando URLs para Tenant
    path('tenant/cadastrar/', TenantCreate.as_view(), name='cadastrar-tenant'),
    path('tenant/editar/<uuid:pk>/', TenantUpdate.as_view(), name='editar-tenant'),
    path('tenant/excluir/<uuid:pk>/', TenantDelete.as_view(), name='excluir-tenant'),
    path('tenant/listar/', TenantList.as_view(), name='listar-tenant'),

    # Cadastro de usuários
    path('cadastro/', views.CustomUserCreateView.as_view(), name='cadastro'),
]