"""
Administração do aplicativo Protocolos.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.contrib.admin.sites import NotRegistered
from .models import (
    Tenant, Empresa, Cliente, HorarioFuncionamento, CategoriaServico, Servico, Atendente,
    HorarioAtendimento, Agendamento, UserProfile
)

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    """Administração para o modelo Tenant."""
    list_display = ['nome', 'slug', 'owner', 'ativo', 'criado_em']
    list_filter = ['ativo', 'criado_em']
    search_fields = ['nome', 'slug', 'owner__username']
    readonly_fields = ['criado_em', 'atualizado_em']
    prepopulated_fields = {"slug": ("nome",)}

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Administração para o modelo UserProfile."""
    list_display = ['user', 'tenant', 'user_email', 'user_groups']
    list_filter = ['tenant', 'user__is_active', 'user__is_staff']
    search_fields = ['user__username', 'user__email', 'tenant__nome']
    raw_id_fields = ['user', 'tenant']

    def user_email(self, obj):
        """Retorna o email do usuário associado ao perfil."""
        return obj.user.email
    user_email.short_description = 'Email'

    def user_groups(self, obj):
        """Retorna os grupos aos quais o usuário pertence."""
        return ', '.join([group.name for group in obj.user.groups.all()])
    user_groups.short_description = 'Grupos'

class UserProfileInline(admin.StackedInline):
    """Inline para exibir o perfil do usuário no admin."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfil'

class UserAdmin(BaseUserAdmin):
    """Administração estendida para o modelo User."""
    inlines = (UserProfileInline,)

try:
    admin.site.unregister(User)
except NotRegistered:
    pass

admin.site.register(User, UserAdmin)

admin.site.register(Empresa)
admin.site.register(Cliente)
admin.site.register(HorarioFuncionamento)
admin.site.register(CategoriaServico)
admin.site.register(Servico)
admin.site.register(Atendente)
admin.site.register(HorarioAtendimento)
admin.site.register(Agendamento)

