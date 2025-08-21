from django import template
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from protocolos.models import Agendamento, Cliente, StatusAgendamento

register = template.Library()

@register.inclusion_tag('paginasweb/widgets/estatisticas_card.html')
def estatisticas_card(user, tenant):
    """Template tag para exibir card de estatísticas"""
    hoje = timezone.now().date()
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    
    # Estatísticas da semana
    agendamentos_semana = Agendamento.objects.filter(
        tenant=tenant,
        dataHoraInicio__date__gte=inicio_semana,
        dataHoraInicio__date__lte=hoje + timedelta(days=6)
    )
    
    context = {
        'total_semana': agendamentos_semana.count(),
        'concluidos_semana': agendamentos_semana.filter(status=StatusAgendamento.CONCLUIDO).count(),
        'receita_semana': agendamentos_semana.filter(
            status=StatusAgendamento.CONCLUIDO
        ).aggregate(total=Sum('servico__preco'))['total'] or 0,
    }
    
    return context

@register.filter
def percentage(value, total):
    """Calcula porcentagem"""
    if total == 0:
        return 0
    return round((value * 100) / total, 1)

@register.filter
def multiply(value, arg):
    """Multiplica dois valores"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.simple_tag
def agendamentos_periodo(tenant, days=7):
    """Retorna agendamentos dos próximos X dias"""
    hoje = timezone.now().date()
    fim_periodo = hoje + timedelta(days=days)
    
    return Agendamento.objects.filter(
        tenant=tenant,
        dataHoraInicio__date__gte=hoje,
        dataHoraInicio__date__lte=fim_periodo,
        status__in=[StatusAgendamento.PENDENTE, StatusAgendamento.CONFIRMADO]
    ).select_related('cliente', 'servico', 'atendente')

@register.simple_tag
def top_clientes(tenant, user, limit=5):
    """Retorna top clientes baseado no usuário"""
    if user.groups.filter(name__in=['Administradores', 'Gerentes']).exists() or user.is_superuser:
        queryset = Cliente.objects.filter(tenant=tenant)
    else:
        queryset = Cliente.objects.filter(tenant=tenant, created_by=user)
    
    return queryset.annotate(
        total_agendamentos=Count('agendamentos')
    ).filter(total_agendamentos__gt=0).order_by('-total_agendamentos')[:limit]

@register.simple_tag
def crescimento_mensal(tenant, user):
    """Calcula crescimento mensal de agendamentos"""
    hoje = timezone.now().date()
    mes_atual = hoje.replace(day=1)
    mes_anterior = (mes_atual - timedelta(days=1)).replace(day=1)
    fim_mes_anterior = mes_atual - timedelta(days=1)
    
    # Filtrar baseado no usuário
    if user.groups.filter(name__in=['Administradores', 'Gerentes']).exists() or user.is_superuser:
        agendamentos_atual = Agendamento.objects.filter(
            tenant=tenant,
            dataHoraInicio__date__gte=mes_atual,
            dataHoraInicio__date__lte=hoje
        ).count()
        
        agendamentos_anterior = Agendamento.objects.filter(
            tenant=tenant,
            dataHoraInicio__date__gte=mes_anterior,
            dataHoraInicio__date__lte=fim_mes_anterior
        ).count()
    else:
        agendamentos_atual = Agendamento.objects.filter(
            Q(created_by=user) | Q(cliente__email=user.email),
            tenant=tenant,
            dataHoraInicio__date__gte=mes_atual,
            dataHoraInicio__date__lte=hoje
        ).count()
        
        agendamentos_anterior = Agendamento.objects.filter(
            Q(created_by=user) | Q(cliente__email=user.email),
            tenant=tenant,
            dataHoraInicio__date__gte=mes_anterior,
            dataHoraInicio__date__lte=fim_mes_anterior
        ).count()
    
    if agendamentos_anterior == 0:
        return {'crescimento': 0, 'tendencia': 'neutro'}
    
    crescimento = round(((agendamentos_atual - agendamentos_anterior) / agendamentos_anterior) * 100, 1)
    tendencia = 'positivo' if crescimento > 0 else 'negativo' if crescimento < 0 else 'neutro'
    
    return {
        'crescimento': abs(crescimento),
        'tendencia': tendencia,
        'atual': agendamentos_atual,
        'anterior': agendamentos_anterior
    }