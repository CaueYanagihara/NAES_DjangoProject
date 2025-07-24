from django.contrib import admin
from .models import Tenant, Empresa, Cliente, HorarioFuncionamento, CategoriaServico, Servico, Atendente, HorarioAtendimento, Agendamento

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['nome', 'slug', 'owner', 'ativo', 'criado_em']
    list_filter = ['ativo', 'criado_em']
    search_fields = ['nome', 'slug', 'owner__username']
    readonly_fields = ['criado_em', 'atualizado_em']
    prepopulated_fields = {"slug": ("nome",)}

# Register your models here.
admin.site.register(Empresa)
admin.site.register(Cliente)
admin.site.register(HorarioFuncionamento)
admin.site.register(CategoriaServico)
admin.site.register(Servico)
admin.site.register(Atendente)
admin.site.register(HorarioAtendimento)
admin.site.register(Agendamento)

