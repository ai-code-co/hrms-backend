# Generated manually for timesheet submission feature

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0010_attendance_lunch_end_time_and_more'),
        ('auth_app', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name='attendance',
                    name='tracker_screenshot',
                    field=models.FileField(blank=True, help_text='Tracker screenshot for work from home', null=True, upload_to='attendance/uploads/timesheetDocuments/'),
                ),
                migrations.AddField(
                    model_name='attendance',
                    name='timesheet_status',
                    field=models.CharField(choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')], default='PENDING', help_text='Timesheet approval status', max_length=20),
                ),
                migrations.AddField(
                    model_name='attendance',
                    name='timesheet_submitted_at',
                    field=models.DateTimeField(blank=True, help_text='When timesheet was submitted', null=True),
                ),
                migrations.AddField(
                    model_name='attendance',
                    name='timesheet_approved_by',
                    field=models.ForeignKey(blank=True, help_text='Admin who approved/rejected the timesheet', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_timesheets', to='auth_app.user'),
                ),
                migrations.AddField(
                    model_name='attendance',
                    name='timesheet_approved_at',
                    field=models.DateTimeField(blank=True, help_text='When timesheet was approved/rejected', null=True),
                ),
                migrations.AddField(
                    model_name='attendance',
                    name='timesheet_admin_notes',
                    field=models.TextField(blank=True, help_text='Admin notes (required for rejection, optional for approval)'),
                ),
            ]
        ),
    ]

