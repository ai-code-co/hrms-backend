from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0011_add_timesheet_fields'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='attendance',
            name='seconds_actual_working_time',
        ),
        migrations.RemoveField(
            model_name='attendance',
            name='is_day_before_joining',
        ),
        migrations.AlterField(
            model_name='attendance',
            name='day_type',
            field=models.CharField(
                choices=[
                    ('WORKING_DAY', 'Working Day'),
                    ('HALF_DAY', 'Half Day'),
                    ('LEAVE_DAY', 'Leave Day'),
                    ('HOLIDAY', 'Holiday'),
                    ('WEEKEND_OFF', 'Weekend Off'),
                    ('HYBRID_DAY', 'Hybrid Day'),
                ],
                default='WORKING_DAY',
                help_text='Type of day',
                max_length=20,
            ),
        ),
    ]









