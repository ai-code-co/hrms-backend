# Generated manually

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0003_devicetype_default_warranty_months_devicetype_icon_and_more'),
    ]

    operations = [
        # Use SeparateDatabaseAndState to handle "prefix" removal idempotently
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # Only drop if it exists (MySQL style)
                migrations.RunSQL(
                    sql="""
                    SET @dbname = DATABASE();
                    SET @tablename = 'inventory_devicetype';
                    SET @columnname = 'prefix';
                    SET @preparedStatement = (SELECT IF(
                        (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                         WHERE TABLE_SCHEMA = @dbname
                           AND TABLE_NAME = @tablename
                           AND COLUMN_NAME = @columnname) > 0,
                        'ALTER TABLE inventory_devicetype DROP COLUMN prefix',
                        'SELECT 1'
                    ));
                    PREPARE stmt FROM @preparedStatement;
                    EXECUTE stmt;
                    DEALLOCATE PREPARE stmt;
                    """,
                    reverse_sql="ALTER TABLE inventory_devicetype ADD COLUMN prefix varchar(10) DEFAULT ''"
                ),
            ],
            state_operations=[
                migrations.RemoveField(
                    model_name='devicetype',
                    name='prefix',
                ),
            ]
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
