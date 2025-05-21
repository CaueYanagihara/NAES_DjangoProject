from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.urls import reverse_lazy
from .models import (
    Empresa, Cliente, Endereco, HorarioFuncionamento, CategoriaServico, Servico, Atendente, HorarioAtendimento, Agendamento
)

# Empresa
class EmpresaCreate(CreateView):
    template_name = "protocolos/form.html"
    model = Empresa
    fields = ["user", "cnpj", "nomeFantasia", "descricao", "endereco", "telefone", "email", "ativo"]
    success_url = reverse_lazy("listar-empresa")
    extra_context = {"titulo": "Cadastro de Empresa"}

class EmpresaUpdate(UpdateView):
    template_name = "protocolos/form.html"
    model = Empresa
    fields = ["user", "cnpj", "nomeFantasia", "descricao", "endereco", "telefone", "email", "ativo"]
    success_url = reverse_lazy("listar-empresa")
    extra_context = {"titulo": "Atualizar Empresa"}

class EmpresaDelete(DeleteView):
    template_name = "protocolos/form-excluir.html"
    model = Empresa
    success_url = reverse_lazy("listar-empresa")
    extra_context = {"titulo": "Excluir Empresa"}

class EmpresaList(ListView):
    template_name = "protocolos/listas/empresa.html"
    model = Empresa

# Cliente
class ClienteCreate(CreateView):
    template_name = "protocolos/form.html"
    model = Cliente
    fields = ["nome", "email", "telefone", "tipo", "ativo", "cpf", "password"]
    success_url = reverse_lazy("listar-cliente")
    extra_context = {"titulo": "Cadastro de Cliente"}
    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.set_password(self.object.password)
        self.object.save()
        return response

class ClienteUpdate(UpdateView):
    template_name = "protocolos/form.html"
    model = Cliente
    fields = ["nome", "email", "telefone", "tipo", "ativo", "cpf", "password"]
    success_url = reverse_lazy("listar-cliente")
    extra_context = {"titulo": "Atualizar Cliente"}
    def form_valid(self, form):
        response = super().form_valid(form)
        if form.cleaned_data.get('password'):
            self.object.set_password(self.object.password)
            self.object.save()
        return response

class ClienteDelete(DeleteView):
    template_name = "protocolos/form-excluir.html"
    model = Cliente
    success_url = reverse_lazy("listar-cliente")
    extra_context = {"titulo": "Excluir Cliente"}

class ClienteList(ListView):
    template_name = "protocolos/listas/cliente.html"
    model = Cliente

# Endereco
class EnderecoCreate(CreateView):
    template_name = "protocolos/form.html"
    model = Endereco
    fields = ["rua", "numero", "bairro", "cidade", "estado", "cep"]
    success_url = reverse_lazy("listar-endereco")
    extra_context = {"titulo": "Cadastro de Endereço"}

class EnderecoUpdate(UpdateView):
    template_name = "protocolos/form.html"
    model = Endereco
    fields = ["rua", "numero", "bairro", "cidade", "estado", "cep"]
    success_url = reverse_lazy("listar-endereco")
    extra_context = {"titulo": "Atualizar Endereço"}

class EnderecoDelete(DeleteView):
    template_name = "protocolos/form-excluir.html"
    model = Endereco
    success_url = reverse_lazy("listar-endereco")
    extra_context = {"titulo": "Excluir Endereço"}

class EnderecoList(ListView):
    template_name = "protocolos/listas/endereco.html"
    model = Endereco

# HorarioFuncionamento
class HorarioFuncionamentoCreate(CreateView):
    template_name = "protocolos/form.html"
    model = HorarioFuncionamento
    fields = ["empresa", "diaSemana", "horaInicio", "horaFim"]
    success_url = reverse_lazy("listar-horario-funcionamento")
    extra_context = {"titulo": "Cadastro de Horário de Funcionamento"}

class HorarioFuncionamentoUpdate(UpdateView):
    template_name = "protocolos/form.html"
    model = HorarioFuncionamento
    fields = ["empresa", "diaSemana", "horaInicio", "horaFim"]
    success_url = reverse_lazy("listar-horario-funcionamento")
    extra_context = {"titulo": "Atualizar Horário de Funcionamento"}

class HorarioFuncionamentoDelete(DeleteView):
    template_name = "protocolos/form-excluir.html"
    model = HorarioFuncionamento
    success_url = reverse_lazy("listar-horario-funcionamento")
    extra_context = {"titulo": "Excluir Horário de Funcionamento"}

class HorarioFuncionamentoList(ListView):
    template_name = "protocolos/listas/horario_funcionamento.html"
    model = HorarioFuncionamento

# CategoriaServico
class CategoriaServicoCreate(CreateView):
    template_name = "protocolos/form.html"
    model = CategoriaServico
    fields = ["empresa", "nome", "descricao"]
    success_url = reverse_lazy("listar-categoria-servico")
    extra_context = {"titulo": "Cadastro de Categoria de Serviço"}

class CategoriaServicoUpdate(UpdateView):
    template_name = "protocolos/form.html"
    model = CategoriaServico
    fields = ["empresa", "nome", "descricao"]
    success_url = reverse_lazy("listar-categoria-servico")
    extra_context = {"titulo": "Atualizar Categoria de Serviço"}

class CategoriaServicoDelete(DeleteView):
    template_name = "protocolos/form-excluir.html"
    model = CategoriaServico
    success_url = reverse_lazy("listar-categoria-servico")
    extra_context = {"titulo": "Excluir Categoria de Serviço"}

class CategoriaServicoList(ListView):
    template_name = "protocolos/listas/categoria_servico.html"
    model = CategoriaServico

# Servico
class ServicoCreate(CreateView):
    template_name = "protocolos/form.html"
    model = Servico
    fields = ["categoria", "nome", "descricao", "preco", "duracaoMinutos"]
    success_url = reverse_lazy("listar-servico")
    extra_context = {"titulo": "Cadastro de Serviço"}

class ServicoUpdate(UpdateView):
    template_name = "protocolos/form.html"
    model = Servico
    fields = ["categoria", "nome", "descricao", "preco", "duracaoMinutos"]
    success_url = reverse_lazy("listar-servico")
    extra_context = {"titulo": "Atualizar Serviço"}

class ServicoDelete(DeleteView):
    template_name = "protocolos/form-excluir.html"
    model = Servico
    success_url = reverse_lazy("listar-servico")
    extra_context = {"titulo": "Excluir Serviço"}

class ServicoList(ListView):
    template_name = "protocolos/listas/servico.html"
    model = Servico

# Atendente
class AtendenteCreate(CreateView):
    template_name = "protocolos/form.html"
    model = Atendente
    fields = ["empresa", "nome", "especialidades"]
    success_url = reverse_lazy("listar-atendente")
    extra_context = {"titulo": "Cadastro de Atendente"}

class AtendenteUpdate(UpdateView):
    template_name = "protocolos/form.html"
    model = Atendente
    fields = ["empresa", "nome", "especialidades"]
    success_url = reverse_lazy("listar-atendente")
    extra_context = {"titulo": "Atualizar Atendente"}

class AtendenteDelete(DeleteView):
    template_name = "protocolos/form-excluir.html"
    model = Atendente
    success_url = reverse_lazy("listar-atendente")
    extra_context = {"titulo": "Excluir Atendente"}

class AtendenteList(ListView):
    template_name = "protocolos/listas/atendente.html"
    model = Atendente

# HorarioAtendimento
class HorarioAtendimentoCreate(CreateView):
    template_name = "protocolos/form.html"
    model = HorarioAtendimento
    fields = ["atendente", "diaSemana", "horaInicio", "horaFim"]
    success_url = reverse_lazy("listar-horario-atendimento")
    extra_context = {"titulo": "Cadastro de Horário de Atendimento"}

class HorarioAtendimentoUpdate(UpdateView):
    template_name = "protocolos/form.html"
    model = HorarioAtendimento
    fields = ["atendente", "diaSemana", "horaInicio", "horaFim"]
    success_url = reverse_lazy("listar-horario-atendimento")
    extra_context = {"titulo": "Atualizar Horário de Atendimento"}

class HorarioAtendimentoDelete(DeleteView):
    template_name = "protocolos/form-excluir.html"
    model = HorarioAtendimento
    success_url = reverse_lazy("listar-horario-atendimento")
    extra_context = {"titulo": "Excluir Horário de Atendimento"}

class HorarioAtendimentoList(ListView):
    template_name = "protocolos/listas/horario_atendimento.html"
    model = HorarioAtendimento

# Agendamento
class AgendamentoCreate(CreateView):
    template_name = "protocolos/form.html"
    model = Agendamento
    fields = ["dataHoraInicio", "dataHoraFim", "status", "cliente", "empresa", "servico", "atendente"]
    success_url = reverse_lazy("listar-agendamento")
    extra_context = {"titulo": "Cadastro de Agendamento"}

class AgendamentoUpdate(UpdateView):
    template_name = "protocolos/form.html"
    model = Agendamento
    fields = ["dataHoraInicio", "dataHoraFim", "status", "cliente", "empresa", "servico", "atendente"]
    success_url = reverse_lazy("listar-agendamento")
    extra_context = {"titulo": "Atualizar Agendamento"}

class AgendamentoDelete(DeleteView):
    template_name = "protocolos/form-excluir.html"
    model = Agendamento
    success_url = reverse_lazy("listar-agendamento")
    extra_context = {"titulo": "Excluir Agendamento"}

class AgendamentoList(ListView):
    template_name = "protocolos/listas/agendamento.html"
    model = Agendamento
