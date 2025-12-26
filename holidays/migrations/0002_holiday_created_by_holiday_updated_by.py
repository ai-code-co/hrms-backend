import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

def add_holiday_tracking_robust(apps, schema_editor):
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        # created_by
        try:
            cursor.execute("ALTER TABLE holidays_holiday ADD COLUMN created_by_id bigint unsigned NULL")
        except Exception as e:
            if "1060" in str(e): pass
            else: raise e
        
        try:
            cursor.execute("ALTER TABLE holidays_holiday ADD CONSTRAINT holidays_holiday_created_by_id_fk FOREIGN KEY (created_by_id) REFERENCES auth_app_user(id)")
        except Exception as e:
            if "Duplicate" in str(e) or "121" in str(e) or "1061" in str(e): pass
            else: raise e

        # updated_by
        try:
            cursor.execute("ALTER TABLE holidays_holiday ADD COLUMN updated_by_id bigint unsigned NULL")
        except Exception as e:
            if "1060" in str(e): pass
            else: raise e
        
        try:
            cursor.execute("ALTER TABLE holidays_holiday ADD CONSTRAINT holidays_holiday_updated_by_id_fk FOREIGN KEY (updated_by_id) REFERENCES auth_app_user(id)")
        except Exception as e:
            if "Duplicate" in str(e) or "121" in str(e) or "1061" in str(e): pass
            else: raise e

def remove_holiday_tracking_robust(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('holidays', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(add_holiday_tracking_robust, remove_holiday_tracking_robust),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='holiday',
                    name='created_by',
                    field=models.ForeignKey(blank=True, help_text='User who created this holiday', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_holidays', to=settings.AUTH_USER_MODEL),
                ),
                migrations.AddField(
                    model_name='holiday',
                    name='updated_by',
                    field=models.ForeignKey(blank=True, help_text='User who last updated this holiday', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_holidays', to=settings.AUTH_USER_MODEL),
                ),
            ]
        ),
    ]
