from django.contrib import admin
from .models import Empresa, Cliente, Endereco, HorarioFuncionamento, CategoriaServico, Servico, Atendente, HorarioAtendimento, Agendamento

# Register your models here.
admin.site.register(Empresa)
admin.site.register(Cliente)
admin.site.register(Endereco)
admin.site.register(HorarioFuncionamento)
admin.site.register(CategoriaServico)
admin.site.register(Servico)
admin.site.register(Atendente)
admin.site.register(HorarioAtendimento)
admin.site.register(Agendamento)

