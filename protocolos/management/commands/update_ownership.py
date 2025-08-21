from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from protocolos.models import Cliente, Agendamento

User = get_user_model()

class Command(BaseCommand):
    help = 'Atualiza registros existentes de Cliente e Agendamento com campos de propriedade'

    def add_arguments(self, parser):
        parser.add_argument(
            '--admin-user',
            type=str,
            help='Username do administrador que será definido como criador dos registros órfãos',
            default='admin'
        )

    def handle(self, *args, **options):
        admin_username = options['admin_user']
        
        try:
            admin_user = User.objects.get(username=admin_username)
        except User.DoesNotExist:
            # Tentar pegar o primeiro superuser
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                self.stdout.write(
                    self.style.ERROR(f'Usuário administrador "{admin_username}" não encontrado e nenhum superuser existe.')
                )
                return

        # Atualizar clientes sem created_by
        clientes_updated = Cliente.objects.filter(created_by__isnull=True).update(created_by=admin_user)
        self.stdout.write(
            self.style.SUCCESS(f'Atualizados {clientes_updated} clientes com o criador: {admin_user.username}')
        )

        # Atualizar agendamentos sem created_by
        agendamentos_updated = Agendamento.objects.filter(created_by__isnull=True).update(created_by=admin_user)
        self.stdout.write(
            self.style.SUCCESS(f'Atualizados {agendamentos_updated} agendamentos com o criador: {admin_user.username}')
        )

        # Estatísticas finais
        total_clientes = Cliente.objects.count()
        total_agendamentos = Agendamento.objects.count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n--- Resumo ---\n'
                f'Total de clientes: {total_clientes}\n'
                f'Total de agendamentos: {total_agendamentos}\n'
                f'Todos os registros agora possuem informação de criador.'
            )
        )