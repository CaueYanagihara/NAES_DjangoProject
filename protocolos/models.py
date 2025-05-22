import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

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

class UsuarioManager(BaseUserManager):
    def create_user(self, email, nome, senha=None, **extra_fields):
        if not email:
            raise ValueError('O email é obrigatório')
        email = self.normalize_email(email)
        user = self.model(email=email, nome=nome, **extra_fields)
        user.set_password(senha)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nome, senha=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, nome, senha, **extra_fields)

class Cliente(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=20)
    tipo = models.CharField(max_length=10, choices=TipoUsuario.choices, default=TipoUsuario.CLIENTE)
    ativo = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    cpf = models.CharField(max_length=14, unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome']

    objects = UsuarioManager()

    def __str__(self):
        return self.nome

class Endereco(models.Model):
    rua = models.CharField(max_length=255)
    numero = models.CharField(max_length=20)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    cep = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.rua}, {self.numero} - {self.bairro}, {self.cidade}"

class Empresa(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cnpj = models.CharField(max_length=18, unique=True)
    nomeFantasia = models.CharField(max_length=255)
    descricao = models.TextField(blank=True)
    endereco = models.OneToOneField(Endereco, on_delete=models.CASCADE, related_name='empresa')
    telefone = models.CharField(max_length=20)
    email = models.EmailField()
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nomeFantasia

class HorarioFuncionamento(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='horarios_funcionamento')
    diaSemana = models.IntegerField(choices=DiaSemana.choices)
    horaInicio = models.TimeField()
    horaFim = models.TimeField()

class CategoriaServico(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='categorias_servicos')
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)

    def __str__(self):
        return self.nome

class Servico(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    categoria = models.ForeignKey(CategoriaServico, on_delete=models.CASCADE, related_name='servicos')
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    duracaoMinutos = models.PositiveIntegerField()

    def __str__(self):
        return self.nome

class Atendente(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='atendentes')
    nome = models.CharField(max_length=255)
    especialidades = models.ManyToManyField(Servico, related_name='atendentes')

    def __str__(self):
        return self.nome

class HorarioAtendimento(models.Model):
    atendente = models.ForeignKey(Atendente, on_delete=models.CASCADE, related_name='disponibilidade')
    diaSemana = models.IntegerField(choices=DiaSemana.choices)
    horaInicio = models.TimeField()
    horaFim = models.TimeField()

class Agendamento(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dataHoraInicio = models.DateTimeField()
    dataHoraFim = models.DateTimeField()
    status = models.CharField(max_length=10, choices=StatusAgendamento.choices, default=StatusAgendamento.PENDENTE)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='agendamentos')
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='agendamentos')
    servico = models.ForeignKey(Servico, on_delete=models.CASCADE, related_name='agendamentos')
    atendente = models.ForeignKey(Atendente, on_delete=models.CASCADE, related_name='agendamentos')