from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Cria grupos de usuários e permissões personalizadas'

    def handle(self, *args, **options):
        # Criar grupos
        admin_group, created = Group.objects.get_or_create(name='Administradores')
        gerente_group, created = Group.objects.get_or_create(name='Gerentes')
        atendente_group, created = Group.objects.get_or_create(name='Atendentes')
        cliente_group, created = Group.objects.get_or_create(name='Clientes')

        # Importar modelos
        from protocolos.models import Cliente, Empresa, Atendente, Agendamento, Servico, CategoriaServico, Tenant

        # Permissões para Administradores (acesso total)
        admin_permissions = Permission.objects.all()
        admin_group.permissions.set(admin_permissions)

        # Permissões para Gerentes (gestão da empresa)
        gerente_permissions = []
        for model in [Empresa, Atendente, Servico, CategoriaServico, Cliente, Agendamento]:
            content_type = ContentType.objects.get_for_model(model)
            perms = Permission.objects.filter(content_type=content_type)
            gerente_permissions.extend(perms)
        gerente_group.permissions.set(gerente_permissions)

        # Permissões para Atendentes (visualizar e gerenciar agendamentos e clientes)
        atendente_permissions = []
        for model in [Cliente, Agendamento]:
            content_type = ContentType.objects.get_for_model(model)
            perms = Permission.objects.filter(content_type=content_type)
            atendente_permissions.extend(perms)
        
        # Adicionar permissão de visualização para Serviços
        content_type = ContentType.objects.get_for_model(Servico)
        view_servico = Permission.objects.filter(content_type=content_type, codename='view_servico')
        atendente_permissions.extend(view_servico)
        
        atendente_group.permissions.set(atendente_permissions)

        # Permissões para Clientes (apenas visualizar seus próprios agendamentos)
        cliente_permissions = []
        content_type = ContentType.objects.get_for_model(Agendamento)
        view_agendamento = Permission.objects.filter(content_type=content_type, codename='view_agendamento')
        cliente_permissions.extend(view_agendamento)
        cliente_group.permissions.set(cliente_permissions)

        self.stdout.write(
            self.style.SUCCESS('Grupos e permissões criados com sucesso!')
        )