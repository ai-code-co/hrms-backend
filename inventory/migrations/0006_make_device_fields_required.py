# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0005_device_invoice_image_device_device_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='device',
            name='serial_number',
            field=models.CharField(help_text='Device serial number', max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='device',
            name='internal_serial_number',
            field=models.CharField(help_text='Internal Serial No.', max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='device',
            name='purchase_price',
            field=models.DecimalField(decimal_places=2, help_text='Purchase price of the device', max_digits=10),
        ),
    ]

