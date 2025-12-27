# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0004_remove_devicetype_prefix_add_device_internal_serial_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='invoice_image',
            field=models.ImageField(blank=True, help_text='Image of the purchase invoice', null=True, upload_to='devices/invoices/'),
        ),
        migrations.AddField(
            model_name='device',
            name='device_image',
            field=models.ImageField(blank=True, help_text='Image of the device', null=True, upload_to='devices/images/'),
        ),
    ]

