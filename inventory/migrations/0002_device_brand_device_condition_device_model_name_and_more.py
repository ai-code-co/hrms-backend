import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

def add_inventory_fields_robust(apps, schema_editor):
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        fields = [
            ("inventory_device", "brand", "varchar(100) NOT NULL DEFAULT ''"),
            ("inventory_device", "condition", "varchar(20) NOT NULL DEFAULT 'good'"),
            ("inventory_device", "model_name", "varchar(200) NOT NULL DEFAULT ''"),
            ("inventory_deviceassignment", "condition_at_assignment", "varchar(20) NOT NULL DEFAULT ''"),
            ("inventory_deviceassignment", "condition_at_return", "varchar(20) NOT NULL DEFAULT ''"),
            ("inventory_deviceassignment", "returned_to_id", "bigint unsigned NULL"),
        ]
        
        for table, col, defn in fields:
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {defn}")
            except Exception as e:
                if "1060" in str(e): pass
                else: raise e

        # Constraint
        try:
            cursor.execute("ALTER TABLE inventory_deviceassignment ADD CONSTRAINT inventory_deviceassignment_returned_to_id_fk FOREIGN KEY (returned_to_id) REFERENCES auth_app_user(id)")
        except Exception as e:
            if "Duplicate" in str(e) or "121" in str(e) or "1061" in str(e): pass
            else: raise e

        # Indexes
        try:
            cursor.execute("CREATE INDEX inventory_d_status_458222_idx ON inventory_device(status)")
        except Exception as e:
            if "Duplicate" in str(e) or "1061" in str(e): pass
            else: raise e

        try:
            cursor.execute("CREATE INDEX inventory_d_returne_eb4ff9_idx ON inventory_deviceassignment(returned_date)")
        except Exception as e:
            if "Duplicate" in str(e) or "1061" in str(e): pass
            else: raise e

def remove_inventory_fields_robust(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0004_employee_slack_user_id'),
        ('inventory', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(add_inventory_fields_robust, remove_inventory_fields_robust),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='device',
                    name='brand',
                    field=models.CharField(blank=True, help_text='Brand/Manufacturer', max_length=100),
                ),
                migrations.AddField(
                    model_name='device',
                    name='condition',
                    field=models.CharField(choices=[('new', 'New'), ('excellent', 'Excellent'), ('good', 'Good'), ('fair', 'Fair'), ('poor', 'Poor')], default='good', help_text='Physical condition of the device', max_length=20),
                ),
                migrations.AddField(
                    model_name='device',
                    name='model_name',
                    field=models.CharField(blank=True, help_text='Model name/number of the device', max_length=200),
                ),
                migrations.AddField(
                    model_name='deviceassignment',
                    name='condition_at_assignment',
                    field=models.CharField(blank=True, choices=[('new', 'New'), ('excellent', 'Excellent'), ('good', 'Good'), ('fair', 'Fair'), ('poor', 'Poor')], help_text='Device condition when assigned', max_length=20),
                ),
                migrations.AddField(
                    model_name='deviceassignment',
                    name='condition_at_return',
                    field=models.CharField(blank=True, choices=[('new', 'New'), ('excellent', 'Excellent'), ('good', 'Good'), ('fair', 'Fair'), ('poor', 'Poor')], help_text='Device condition when returned', max_length=20),
                ),
                migrations.AddField(
                    model_name='deviceassignment',
                    name='returned_to',
                    field=models.ForeignKey(blank=True, help_text='Admin who received the returned device', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='device_returns_received', to=settings.AUTH_USER_MODEL),
                ),
                migrations.AddIndex(
                    model_name='device',
                    index=models.Index(fields=['status'], name='inventory_d_status_458222_idx'),
                ),
                migrations.AddIndex(
                    model_name='deviceassignment',
                    index=models.Index(fields=['returned_date'], name='inventory_d_returne_eb4ff9_idx'),
                ),
            ]
        ),
    ]
