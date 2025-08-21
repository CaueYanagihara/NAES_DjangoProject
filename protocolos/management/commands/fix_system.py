from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from protocolos.models import Tenant, UserProfile
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Corrige problemas do sistema: cria profiles, associa tenants e configura grupos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix-all',
            action='store_true',
            help='Corrige todos os problemas automaticamente',
        )
        parser.add_argument(
            '--create-profiles',
            action='store_true',
            help='Cria profiles para usuários sem profile',
        )
        parser.add_argument(
            '--associate-tenants',
            action='store_true',
            help='Associa usuários aos seus tenants',
        )
        parser.add_argument(
            '--setup-groups',
            action='store_true',
            help='Configura grupos e permissões',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔧 Iniciando correção do sistema...'))
        
        if options['fix_all'] or options['create_profiles']:
            self.create_user_profiles()
        
        if options['fix_all'] or options['associate_tenants']:
            self.associate_tenants()
        
        if options['fix_all'] or options['setup_groups']:
            self.setup_groups()
        
        self.stdout.write(self.style.SUCCESS('✅ Correção do sistema concluída!'))

    def create_user_profiles(self):
        """Cria profiles para usuários que não têm"""
        self.stdout.write('📝 Criando profiles de usuários...')
        
        users_without_profile = User.objects.filter(profile__isnull=True)
        created_count = 0
        
        for user in users_without_profile:
            UserProfile.objects.create(user=user)
            created_count += 1
            self.stdout.write(f'  ✓ Profile criado para {user.username}')
        
        self.stdout.write(
            self.style.SUCCESS(f'📝 {created_count} profiles criados.')
        )

    def associate_tenants(self):
        """Associa usuários aos tenants baseado no owner"""
        self.stdout.write('🏢 Associando usuários aos tenants...')
        
        associated_count = 0
        
        # Associar owners aos seus tenants
        for tenant in Tenant.objects.all():
            if tenant.owner and not tenant.owner.tenant:
                tenant.owner.set_tenant(tenant)
                associated_count += 1
                self.stdout.write(f'  ✓ {tenant.owner.username} associado ao tenant {tenant.nome}')
        
        # Para usuários sem tenant, criar um automático se eles tiverem dados relacionados
        users_without_tenant = User.objects.filter(profile__tenant__isnull=True)
        
        for user in users_without_tenant:
            # Verificar se usuário tem dados (clientes, agendamentos, etc.)
            from protocolos.models import Cliente, Agendamento
            
            has_clients = Cliente.objects.filter(created_by=user).exists()
            has_appointments = Agendamento.objects.filter(created_by=user).exists()
            
            if has_clients or has_appointments:
                # Criar tenant automático
                base_slug = slugify(user.username)
                slug = base_slug
                counter = 1
                
                while Tenant.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                
                tenant = Tenant.objects.create(
                    nome=f"Organização de {user.get_full_name() or user.username}",
                    slug=slug,
                    owner=user
                )
                
                user.set_tenant(tenant)
                associated_count += 1
                self.stdout.write(f'  ✓ Tenant automático criado para {user.username}')
        
        self.stdout.write(
            self.style.SUCCESS(f'🏢 {associated_count} associações realizadas.')
        )

    def setup_groups(self):
        """Configura grupos e adiciona usuários apropriados"""
        self.stdout.write('👥 Configurando grupos...')
        
        # Criar grupos se não existirem
        groups_to_create = ['Administradores', 'Gerentes', 'Atendentes', 'Clientes']
        created_groups = 0
        
        for group_name in groups_to_create:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                created_groups += 1
                self.stdout.write(f'  ✓ Grupo {group_name} criado')
        
        # Adicionar owners de tenant como Administradores
        admin_group = Group.objects.get(name='Administradores')
        added_admins = 0
        
        for tenant in Tenant.objects.all():
            if tenant.owner and not tenant.owner.groups.filter(name='Administradores').exists():
                tenant.owner.groups.add(admin_group)
                added_admins += 1
                self.stdout.write(f'  ✓ {tenant.owner.username} adicionado como Administrador')
        
        # Adicionar superusers como Administradores se não estiverem
        for user in User.objects.filter(is_superuser=True):
            if not user.groups.filter(name='Administradores').exists():
                user.groups.add(admin_group)
                self.stdout.write(f'  ✓ Superuser {user.username} adicionado como Administrador')
        
        self.stdout.write(
            self.style.SUCCESS(f'👥 {created_groups} grupos criados, {added_admins} administradores configurados.')
        )

    def verify_system(self):
        """Verifica se o sistema está funcionando corretamente"""
        self.stdout.write('🔍 Verificando sistema...')
        
        issues = []
        
        # Verificar users sem profile
        users_without_profile = User.objects.filter(profile__isnull=True).count()
        if users_without_profile > 0:
            issues.append(f'{users_without_profile} usuários sem profile')
        
        # Verificar tenant owners sem tenant associado
        orphaned_owners = 0
        for tenant in Tenant.objects.all():
            if tenant.owner and not tenant.owner.tenant:
                orphaned_owners += 1
        
        if orphaned_owners > 0:
            issues.append(f'{orphaned_owners} owners sem tenant associado')
        
        # Verificar usuários sem grupo
        users_without_groups = User.objects.filter(groups__isnull=True, is_active=True).count()
        if users_without_groups > 0:
            issues.append(f'{users_without_groups} usuários sem grupos')
        
        if issues:
            self.stdout.write(self.style.WARNING('⚠️  Problemas encontrados:'))
            for issue in issues:
                self.stdout.write(f'  - {issue}')
        else:
            self.stdout.write(self.style.SUCCESS('✅ Sistema verificado - tudo funcionando!'))
        
        return len(issues) == 0