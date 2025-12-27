# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0003_devicetype_default_warranty_months_devicetype_icon_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='devicetype',
            name='prefix',
        ),
        migrations.AddField(
            model_name='device',
            name='internal_serial_number',
            field=models.CharField(blank=True, help_text='Internal Serial No.', max_length=100, null=True, unique=True),
        ),
        migrations.AddIndex(
            model_name='device',
            index=models.Index(fields=['internal_serial_number'], name='inventory_de_interna_idx'),
        ),
    ]

