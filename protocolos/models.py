import uuid
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class TipoUsuario(models.TextChoices):
    EMPRESA = 'EMPRESA', 'Empresa'
    CLIENTE = 'CLIENTE', 'Cliente'

class DiaSemana(models.IntegerChoices):
    SEGUNDA = 1, 'Segunda-feira'
    TERCA = 2, 'Terça-feira'
    QUARTA = 3, 'Quarta-feira'
    QUINTA = 4, 'Quinta-feira'
    SEXTA = 5, 'Sexta-feira'
    SABADO = 6, 'Sábado'
    DOMINGO = 7, 'Domingo'

class StatusAgendamento(models.TextChoices):
    PENDENTE = 'PENDENTE', 'Pendente'
    CONFIRMADO = 'CONFIRMADO', 'Confirmado'
    CANCELADO = 'CANCELADO', 'Cancelado'
    CONCLUIDO = 'CONCLUIDO', 'Concluído'

# NOVO: Modelo Tenant para isolamento de dados
class Tenant(models.Model):
    """Representa uma organização/site isolado no sistema"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=255, help_text="Nome da organização/empresa")
    slug = models.SlugField(unique=True, max_length=50, help_text="Identificador único (URL amigável)")
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='tenant', verbose_name="Proprietário")
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    # Configurações do tenant
    max_empresas = models.PositiveIntegerField(default=5, help_text="Limite de empresas")
    max_clientes = models.PositiveIntegerField(default=1000, help_text="Limite de clientes")
    max_agendamentos_mes = models.PositiveIntegerField(default=500, help_text="Limite de agendamentos por mês")

    class Meta:
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.slug})"

    def get_absolute_url(self):
        return f"/{self.slug}/"

class Cliente(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=255)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    tipo = models.CharField(max_length=10, choices=TipoUsuario.choices, default=TipoUsuario.CLIENTE)
    ativo = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    cpf = models.CharField(max_length=14)
    
    # Campos de endereço diretos (opcionais)
    rua = models.CharField(max_length=255, blank=True, verbose_name="Rua")
    numero = models.CharField(max_length=20, blank=True, verbose_name="Número")
    bairro = models.CharField(max_length=100, blank=True, verbose_name="Bairro")
    cidade = models.CharField(max_length=100, blank=True, verbose_name="Cidade")
    estado = models.CharField(max_length=2, blank=True, verbose_name="Estado")
    cep = models.CharField(max_length=10, blank=True, verbose_name="CEP")
    
    # Campo tenant opcional inicialmente
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, verbose_name="Organização", null=True, blank=True)
    
    # Campo para controle de propriedade
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                 related_name='clientes_criados', verbose_name="Criado por")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return self.nome
    
    @property
    def endereco_completo(self):
        """Retorna o endereço completo formatado"""
        if not any([self.rua, self.numero, self.bairro, self.cidade]):
            return "Endereço não informado"
        return f"{self.rua}, {self.numero} - {self.bairro}, {self.cidade}/{self.estado} - CEP: {self.cep}"

class Empresa(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cnpj = models.CharField(max_length=18)
    nomeFantasia = models.CharField(max_length=255)
    descricao = models.TextField(blank=True)
    
    # Campos de endereço diretos
    rua = models.CharField(max_length=255, verbose_name="Rua")
    numero = models.CharField(max_length=20, verbose_name="Número")
    bairro = models.CharField(max_length=100, verbose_name="Bairro")
    cidade = models.CharField(max_length=100, verbose_name="Cidade")
    estado = models.CharField(max_length=2, verbose_name="Estado")
    cep = models.CharField(max_length=10, verbose_name="CEP")
    
    telefone = models.CharField(max_length=20)
    email = models.EmailField()
    ativo = models.BooleanField(default=True)
    # Campo tenant opcional inicialmente
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, verbose_name="Organização", null=True, blank=True)

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"

    def __str__(self):
        return self.nomeFantasia

    @property
    def endereco_completo(self):
        return f"{self.rua}, {self.numero} - {self.bairro}, {self.cidade}/{self.estado} - CEP: {self.cep}"

class HorarioFuncionamento(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='horarios_funcionamento')
    diaSemana = models.IntegerField(choices=DiaSemana.choices)
    horaInicio = models.TimeField()
    horaFim = models.TimeField()
    # Campo tenant opcional inicialmente
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, verbose_name="Organização", null=True, blank=True)

    class Meta:
        verbose_name = "Horário de Funcionamento"
        verbose_name_plural = "Horários de Funcionamento"

    def __str__(self):
        return f"{self.empresa.nomeFantasia} - {self.get_diaSemana_display()}"

class CategoriaServico(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='categorias_servicos')
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    # Campo tenant opcional inicialmente
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, verbose_name="Organização", null=True, blank=True)

    class Meta:
        verbose_name = "Categoria de Serviço"
        verbose_name_plural = "Categorias de Serviços"

    def __str__(self):
        return self.nome

class Servico(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    categoria = models.ForeignKey(CategoriaServico, on_delete=models.CASCADE, related_name='servicos')
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    duracaoMinutos = models.PositiveIntegerField()
    # Campo tenant opcional inicialmente
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, verbose_name="Organização", null=True, blank=True)

    class Meta:
        verbose_name = "Serviço"
        verbose_name_plural = "Serviços"

    def __str__(self):
        return self.nome

class Atendente(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='atendentes')
    nome = models.CharField(max_length=255)
    email = models.EmailField(unique=True, help_text="Email que será usado para login no sistema")
    telefone = models.CharField(max_length=20, blank=True)
    especialidades = models.ManyToManyField(Servico, related_name='atendentes')
    # Vinculação com usuário do sistema
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='atendente', null=True, blank=True)
    # Campo tenant opcional inicialmente
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, verbose_name="Organização", null=True, blank=True)

    class Meta:
        verbose_name = "Atendente"
        verbose_name_plural = "Atendentes"
        unique_together = [['tenant', 'email']]  # Email único apenas dentro do tenant

    def __str__(self):
        return f"{self.nome} ({self.email})"

class HorarioAtendimento(models.Model):
    atendente = models.ForeignKey(Atendente, on_delete=models.CASCADE, related_name='disponibilidade')
    diaSemana = models.IntegerField(choices=DiaSemana.choices)
    horaInicio = models.TimeField()
    horaFim = models.TimeField()
    # Campo tenant opcional inicialmente
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, verbose_name="Organização", null=True, blank=True)

    class Meta:
        verbose_name = "Horário de Atendimento"
        verbose_name_plural = "Horários de Atendimento"

    def __str__(self):
        return f"{self.atendente.nome} - {self.get_diaSemana_display()}"

class Agendamento(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dataHoraInicio = models.DateTimeField()
    dataHoraFim = models.DateTimeField()
    status = models.CharField(max_length=10, choices=StatusAgendamento.choices, default=StatusAgendamento.PENDENTE)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='agendamentos')
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='agendamentos')
    servico = models.ForeignKey(Servico, on_delete=models.CASCADE, related_name='agendamentos')
    atendente = models.ForeignKey(Atendente, on_delete=models.CASCADE, related_name='agendamentos')
    # Campo tenant opcional inicialmente
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, verbose_name="Organização", null=True, blank=True)
    
    # Campo para controle de propriedade
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                 related_name='agendamentos_criados', verbose_name="Criado por")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Agendamento"
        verbose_name_plural = "Agendamentos"

    def __str__(self):
        return f"{self.cliente.nome} - {self.servico.nome} ({self.dataHoraInicio.strftime('%d/%m/%Y %H:%M')})"

# Extend User model with tenant relationship
class UserProfile(models.Model):
    """Extensão do modelo User para adicionar relação com Tenant"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'
    
    def __str__(self):
        return f"{self.user.username} - {self.tenant.nome if self.tenant else 'Sem organização'}"

# Signal para criar profile automaticamente
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Cria profile automaticamente quando User é criado"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Salva profile quando User é salvo"""
    if hasattr(instance, 'profile'):
        instance.profile.save()

# Adicionar propriedade tenant ao User
def get_user_tenant(self):
    """Retorna o tenant do usuário através do profile"""
    try:
        return self.profile.tenant
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=self)
        return None

def set_user_tenant(self, tenant):
    """Define o tenant do usuário"""
    profile, created = UserProfile.objects.get_or_create(user=self)
    profile.tenant = tenant
    profile.save()

# Monkey patch para adicionar métodos ao User
User.add_to_class('tenant', property(get_user_tenant))
User.add_to_class('set_tenant', set_user_tenant)