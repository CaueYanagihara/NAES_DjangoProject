from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.db.models import Count, Q, Sum
from django.utils import timezone
from django.utils.text import slugify
from datetime import datetime, timedelta
from protocolos.models import (
    Cliente, Agendamento, Empresa, Servico, StatusAgendamento, Tenant, Atendente
)


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

# Views públicas (não precisam de autenticação)
def index(request):
    """View da página inicial com informações dinâmicas"""
    context = {
        'titulo': 'Sistema de Agendamentos'
    }
    
    # Se usuário estiver logado, adicionar dados dinâmicos
    if request.user.is_authenticated:
        try:
            # Obter tenant do usuário
            tenant = request.user.tenant
            
            # Data atual e período para estatísticas
            hoje = timezone.now().date()
            inicio_mes = hoje.replace(day=1)
            fim_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            proxima_semana = hoje + timedelta(days=7)
            
            # Estatísticas gerais do tenant
            total_clientes = Cliente.objects.filter(tenant=tenant).count()
            total_empresas = Empresa.objects.filter(tenant=tenant).count()
            total_servicos = Servico.objects.filter(tenant=tenant).count()
            total_atendentes = Atendente.objects.filter(tenant=tenant).count()
            
            # Agendamentos do mês atual
            agendamentos_mes = Agendamento.objects.filter(
                tenant=tenant,
                dataHoraInicio__date__gte=inicio_mes,
                dataHoraInicio__date__lte=fim_mes
            )
            
            total_agendamentos_mes = agendamentos_mes.count()
            
            # Agendamentos por status
            agendamentos_pendentes = agendamentos_mes.filter(status=StatusAgendamento.PENDENTE).count()
            agendamentos_confirmados = agendamentos_mes.filter(status=StatusAgendamento.CONFIRMADO).count()
            agendamentos_concluidos = agendamentos_mes.filter(status=StatusAgendamento.CONCLUIDO).count()
            
            # Próximos agendamentos (próximos 7 dias)
            proximos_agendamentos = Agendamento.objects.filter(
                tenant=tenant,
                dataHoraInicio__date__gte=hoje,
                dataHoraInicio__date__lte=proxima_semana,
                status__in=[StatusAgendamento.PENDENTE, StatusAgendamento.CONFIRMADO]
            ).select_related('cliente', 'servico', 'atendente').order_by('dataHoraInicio')[:8]
            
            # Agendamentos de hoje
            agendamentos_hoje = Agendamento.objects.filter(
                tenant=tenant,
                dataHoraInicio__date=hoje
            ).select_related('cliente', 'servico', 'atendente').order_by('dataHoraInicio')
            
            # Filtrar dados baseado no grupo do usuário
            if request.user.groups.filter(name__in=['Administradores', 'Gerentes']).exists() or request.user.is_superuser:
                # Admin/Gerentes veem todos os dados
                clientes_queryset = Cliente.objects.filter(tenant=tenant)
                agendamentos_queryset = Agendamento.objects.filter(tenant=tenant)
            else:
                # Usuários comuns veem apenas dados que criaram
                clientes_queryset = Cliente.objects.filter(tenant=tenant, created_by=request.user)
                agendamentos_queryset = Agendamento.objects.filter(
                    Q(created_by=request.user) | Q(cliente__email=request.user.email),
                    tenant=tenant
                )
            
            # Clientes mais ativos
            clientes_ativos = clientes_queryset.annotate(
                total_agendamentos=Count('agendamentos')
            ).filter(total_agendamentos__gt=0).order_by('-total_agendamentos')[:5]
            
            # Serviços mais procurados no tenant
            servicos_populares = Servico.objects.filter(tenant=tenant).annotate(
                total_agendamentos=Count('agendamentos')
            ).filter(total_agendamentos__gt=0).order_by('-total_agendamentos')[:5]
            
            # Receita estimada do mês (se campo preço existir)
            try:
                receita_mes = agendamentos_mes.filter(
                    status=StatusAgendamento.CONCLUIDO
                ).aggregate(
                    total=Sum('servico__preco')
                )['total'] or 0
            except:
                receita_mes = 0
            
            # Estatísticas específicas para o usuário
            meus_dados = {}
            if not request.user.groups.filter(name__in=['Administradores', 'Gerentes']).exists() and not request.user.is_superuser:
                meus_dados = {
                    'meus_clientes': clientes_queryset.count(),
                    'meus_agendamentos_mes': agendamentos_queryset.filter(
                        dataHoraInicio__date__gte=inicio_mes,
                        dataHoraInicio__date__lte=fim_mes
                    ).count(),
                    'meus_agendamentos_hoje': agendamentos_queryset.filter(
                        dataHoraInicio__date=hoje
                    ).count(),
                }
            
            # Adicionar todas as estatísticas ao contexto
            context.update({
                'tenant': tenant,
                'total_clientes': total_clientes,
                'total_empresas': total_empresas,
                'total_servicos': total_servicos,
                'total_atendentes': total_atendentes,
                'total_agendamentos_mes': total_agendamentos_mes,
                'agendamentos_pendentes': agendamentos_pendentes,
                'agendamentos_confirmados': agendamentos_confirmados,
                'agendamentos_concluidos': agendamentos_concluidos,
                'proximos_agendamentos': proximos_agendamentos,
                'agendamentos_hoje': agendamentos_hoje,
                'clientes_ativos': clientes_ativos,
                'servicos_populares': servicos_populares,
                'receita_mes': receita_mes,
                'mes_atual': inicio_mes.strftime('%B %Y').title(),
                'hoje': hoje,
                'user_groups': list(request.user.groups.values_list('name', flat=True)),
                **meus_dados,
            })
            
        except Exception as e:
            # Se não tem tenant ou erro, manter contexto básico
            context.update({
                'sem_tenant': True,
                'erro_tenant': str(e) if request.user.is_superuser else None
            })
    
    return render(request, 'paginasweb/index.html', context)

def sobre(request):
    return render(request, 'paginasweb/sobre.html')

def contato(request):
    return render(request, 'paginasweb/contato.html')

# Views protegidas (precisam de autenticação)
@login_required(login_url='/protocolo/login/')
def escolher_cadastro(request):
    """View protegida - apenas usuários logados podem acessar"""
    return render(request, 'paginasweb/escolher_cadastro.html')

# View baseada em classe protegida
class DashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard principal - apenas para usuários autenticados"""
    template_name = 'paginasweb/dashboard.html'
    login_url = '/protocolo/login/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Dashboard'
        
        # Adicionar dados específicos do dashboard
        if hasattr(self.request.user, 'tenant'):
            tenant = self.request.user.tenant
            
            # Estatísticas avançadas para o dashboard
            context.update({
                'tenant': tenant,
                'resumo_completo': True,
            })
        
        return context

# View para dados JSON (AJAX)
@login_required(login_url='/protocolo/login/')
def dashboard_data(request):
    """API para dados do dashboard em JSON"""
    from django.http import JsonResponse
    from datetime import datetime, timedelta
    
    if not hasattr(request.user, 'tenant'):
        return JsonResponse({'error': 'Tenant não encontrado'}, status=400)
    
    tenant = request.user.tenant
    hoje = timezone.now().date()
    
    # Dados dos últimos 7 dias
    dados_semana = []
    for i in range(7):
        data = hoje - timedelta(days=6-i)
        agendamentos_dia = Agendamento.objects.filter(
            tenant=tenant,
            dataHoraInicio__date=data
        ).count()
        dados_semana.append({
            'dia': data.strftime('%a'),
            'data': data.strftime('%d/%m'),
            'agendamentos': agendamentos_dia
        })
    
    # Dados por status
    status_data = {
        'pendentes': Agendamento.objects.filter(
            tenant=tenant, status=StatusAgendamento.PENDENTE
        ).count(),
        'confirmados': Agendamento.objects.filter(
            tenant=tenant, status=StatusAgendamento.CONFIRMADO
        ).count(),
        'concluidos': Agendamento.objects.filter(
            tenant=tenant, status=StatusAgendamento.CONCLUIDO
        ).count(),
    }
    
    # Serviços mais populares
    servicos_data = list(
        Servico.objects.filter(tenant=tenant)
        .annotate(total=Count('agendamentos'))
        .filter(total__gt=0)
        .order_by('-total')[:5]
        .values('nome', 'total')
    )
    
    return JsonResponse({
        'semana': dados_semana,
        'status': status_data,
        'servicos': servicos_data,
        'success': True
    })