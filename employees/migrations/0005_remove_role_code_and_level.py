# Generated migration to remove code and level fields from Role model
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0004_seed_initial_roles'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='role',
            name='code',
        ),
        migrations.RemoveField(
            model_name='role',
            name='level',
        ),
        migrations.AlterModelOptions(
            name='role',
            options={'ordering': ['name'], 'verbose_name': 'Role', 'verbose_name_plural': 'Roles'},
        ),
    ]

