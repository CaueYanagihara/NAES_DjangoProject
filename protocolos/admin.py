from django.contrib import admin
from .models import Tenant, Empresa, Cliente, HorarioFuncionamento, CategoriaServico, Servico, Atendente, HorarioAtendimento, Agendamento, UserProfile
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['nome', 'slug', 'owner', 'ativo', 'criado_em']
    list_filter = ['ativo', 'criado_em']
    search_fields = ['nome', 'slug', 'owner__username']
    readonly_fields = ['criado_em', 'atualizado_em']
    prepopulated_fields = {"slug": ("nome",)}

# Registrar UserProfile no admin
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'tenant', 'user_email', 'user_groups']
    list_filter = ['tenant', 'user__is_active', 'user__is_staff']
    search_fields = ['user__username', 'user__email', 'tenant__nome']
    raw_id_fields = ['user', 'tenant']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    
    def user_groups(self, obj):
        return ', '.join([group.name for group in obj.user.groups.all()])
    user_groups.short_description = 'Grupos'

# Inline para mostrar profile no admin do User
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfil'

# Estender o admin do User
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Register your models here.
admin.site.register(Empresa)
admin.site.register(Cliente)
admin.site.register(HorarioFuncionamento)
admin.site.register(CategoriaServico)
admin.site.register(Servico)
admin.site.register(Atendente)
admin.site.register(HorarioAtendimento)
admin.site.register(Agendamento)

