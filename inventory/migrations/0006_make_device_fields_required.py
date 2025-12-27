# Generated manually

from django.db import migrations, models

def populate_null_device_fields(apps, schema_editor):
    Device = apps.get_model('inventory', 'Device')
    
    # 1. Handle Serial Numbers (must be unique)
    for i, device in enumerate(Device.objects.filter(serial_number__isnull=True), 1):
        device.serial_number = f"SN-TEMP-{device.id}-{i}"
        device.save()
        
    # 2. Handle Internal Serial Numbers (must be unique)
    for i, device in enumerate(Device.objects.filter(internal_serial_number__isnull=True), 1):
        device.internal_serial_number = f"ISN-TEMP-{device.id}-{i}"
        device.save()
        
    # 3. Handle Purchase Price
    Device.objects.filter(purchase_price__isnull=True).update(purchase_price=0.00)

class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0005_device_invoice_image_device_device_image'),
    ]

    operations = [
        # Step 1: Populate NULL values with placeholder data
        migrations.RunPython(populate_null_device_fields, reverse_code=migrations.RunPython.noop),
        
        # Step 2: Now apply the required constraints
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
