# Generated migration for User-Tenant relationship

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('protocolos', '0002_add_ownership_fields'),
    ]

    operations = [
        # Primeiro, adicionar campo tenant ao User através do perfil
        migrations.RunSQL(
            """
            ALTER TABLE auth_user ADD COLUMN tenant_id INTEGER;
            """,
            reverse_sql="""
            ALTER TABLE auth_user DROP COLUMN tenant_id;
            """
        ),
        
        # Adicionar foreign key constraint
        migrations.RunSQL(
            """
            ALTER TABLE auth_user 
            ADD CONSTRAINT auth_user_tenant_fk 
            FOREIGN KEY (tenant_id) REFERENCES protocolos_tenant(id) 
            ON DELETE SET NULL;
            """,
            reverse_sql="""
            ALTER TABLE auth_user DROP CONSTRAINT auth_user_tenant_fk;
            """
        ),
        
        # Atualizar usuários existentes com seus tenants
        migrations.RunPython(
            code=lambda apps, schema_editor: None,  # Será implementado via comando
            reverse_code=lambda apps, schema_editor: None,
        ),
    ]