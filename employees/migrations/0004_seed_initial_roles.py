# Data migration to seed initial roles
from django.db import migrations


def create_initial_roles(apps, schema_editor):
    """Create initial roles: Admin, HR, Manager, Employee"""
    Role = apps.get_model('employees', 'Role')
    
    roles_data = [
        {
            'name': 'Admin',
            'code': 'ADMIN',
            'level': 100,
            'description': 'System Administrator with full access to all features',
            'can_view_all_employees': True,
            'can_create_employees': True,
            'can_edit_all_employees': True,
            'can_delete_employees': True,
            'can_view_subordinates': True,
            'can_approve_leave': True,
            'can_approve_timesheet': True,
            'is_active': True,
        },
        {
            'name': 'HR',
            'code': 'HR',
            'level': 80,
            'description': 'Human Resources with access to employee management',
            'can_view_all_employees': True,
            'can_create_employees': True,
            'can_edit_all_employees': True,
            'can_delete_employees': True,
            'can_view_subordinates': True,
            'can_approve_leave': True,
            'can_approve_timesheet': True,
            'is_active': True,
        },
        {
            'name': 'Manager',
            'code': 'MANAGER',
            'level': 50,
            'description': 'Manager with access to view and manage subordinates',
            'can_view_all_employees': False,
            'can_create_employees': False,
            'can_edit_all_employees': False,
            'can_delete_employees': False,
            'can_view_subordinates': True,
            'can_approve_leave': True,
            'can_approve_timesheet': True,
            'is_active': True,
        },
        {
            'name': 'Employee',
            'code': 'EMPLOYEE',
            'level': 10,
            'description': 'Regular employee with access to own profile only',
            'can_view_all_employees': False,
            'can_create_employees': False,
            'can_edit_all_employees': False,
            'can_delete_employees': False,
            'can_view_subordinates': False,
            'can_approve_leave': False,
            'can_approve_timesheet': False,
            'is_active': True,
        },
    ]
    
    for role_data in roles_data:
        Role.objects.get_or_create(
            code=role_data['code'],
            defaults=role_data
        )


def reverse_roles(apps, schema_editor):
    """Remove initial roles"""
    Role = apps.get_model('employees', 'Role')
    Role.objects.filter(name__in=['Admin', 'HR', 'Manager', 'Employee']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0003_role_employee_role'),
    ]

    operations = [
        migrations.RunPython(create_initial_roles, reverse_roles),
    ]

