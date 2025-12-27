# Generated manually

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0003_devicetype_default_warranty_months_devicetype_icon_and_more'),
    ]

    operations = [
        # 1. Handle "prefix" removal idempotently
        migrations.SeparateDatabaseAndState(
            database_operations=[
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
                    reverse_sql=""
                ),
            ],
            state_operations=[
                migrations.RemoveField(
                    model_name='devicetype',
                    name='prefix',
                ),
            ]
        ),
        
        # 2. Add "internal_serial_number" without unique constraint first (TiDB compatibility)
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # Add column if not exists
                migrations.RunSQL(
                    sql="""
                    SET @dbname = DATABASE();
                    SET @tablename = 'inventory_device';
                    SET @columnname = 'internal_serial_number';
                    SET @preparedStatement = (SELECT IF(
                        (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                         WHERE TABLE_SCHEMA = @dbname
                           AND TABLE_NAME = @tablename
                           AND COLUMN_NAME = @columnname) = 0,
                        'ALTER TABLE inventory_device ADD COLUMN internal_serial_number varchar(100) NULL',
                        'SELECT 1'
                    ));
                    PREPARE stmt FROM @preparedStatement;
                    EXECUTE stmt;
                    DEALLOCATE PREPARE stmt;
                    """,
                    reverse_sql=""
                ),
                # Add unique index if not exists
                migrations.RunSQL(
                    sql="""
                    SET @dbname = DATABASE();
                    SET @tablename = 'inventory_device';
                    SET @indexname = 'inventory_device_internal_serial_number_unique';
                    SET @preparedStatement = (SELECT IF(
                        (SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
                         WHERE TABLE_SCHEMA = @dbname
                           AND TABLE_NAME = @tablename
                           AND INDEX_NAME = @indexname) = 0,
                        'ALTER TABLE inventory_device ADD UNIQUE INDEX inventory_device_internal_serial_number_unique (internal_serial_number)',
                        'SELECT 1'
                    ));
                    PREPARE stmt FROM @preparedStatement;
                    EXECUTE stmt;
                    DEALLOCATE PREPARE stmt;
                    """,
                    reverse_sql=""
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='device',
                    name='internal_serial_number',
                    field=models.CharField(blank=True, help_text='Internal Serial No.', max_length=100, null=True, unique=True),
                ),
            ]
        ),
        
        # 3. Add non-unique index if not exists
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    SET @dbname = DATABASE();
                    SET @tablename = 'inventory_device';
                    SET @indexname = 'inventory_de_interna_idx';
                    SET @preparedStatement = (SELECT IF(
                        (SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
                         WHERE TABLE_SCHEMA = @dbname
                           AND TABLE_NAME = @tablename
                           AND INDEX_NAME = @indexname) = 0,
                        'ALTER TABLE inventory_device ADD INDEX inventory_de_interna_idx (internal_serial_number)',
                        'SELECT 1'
                    ));
                    PREPARE stmt FROM @preparedStatement;
                    EXECUTE stmt;
                    DEALLOCATE PREPARE stmt;
                    """,
                    reverse_sql=""
                ),
            ],
            state_operations=[
                migrations.AddIndex(
                    model_name='device',
                    index=models.Index(fields=['internal_serial_number'], name='inventory_de_interna_idx'),
                ),
            ]
        ),
    ]
