"""
Management command to assign default roles to existing employees.

Usage:
    python manage.py assign_default_roles
    
    # Assign Employee role to all employees without roles
    python manage.py assign_default_roles
    
    # Assign specific role based on is_staff flag
    python manage.py assign_default_roles --assign-by-staff
"""
from django.core.management.base import BaseCommand
from employees.models import Employee, Role


class Command(BaseCommand):
    help = 'Assign default roles to existing employees'

    def add_arguments(self, parser):
        parser.add_argument(
            '--assign-by-staff',
            action='store_true',
            help='Assign Admin/HR role to staff users, Employee role to others',
        )
        parser.add_argument(
            '--default-role',
            type=str,
            default='Employee',
            help='Default role name to assign (default: Employee)',
        )

    def handle(self, *args, **options):
        assign_by_staff = options['assign_by_staff']
        default_role_name = options['default_role']

        # Get or create default role
        try:
            default_role = Role.objects.get(name=default_role_name)
        except Role.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f'Role with name "{default_role_name}" does not exist. '
                    'Please run migrations first to create initial roles.'
                )
            )
            return

        # Get Admin/HR roles for staff assignment
        admin_role = None
        hr_role = None
        if assign_by_staff:
            try:
                admin_role = Role.objects.get(name='Admin')
            except Role.DoesNotExist:
                pass
            try:
                hr_role = Role.objects.get(name='HR')
            except Role.DoesNotExist:
                pass

        # Get employees without roles
        employees_without_roles = Employee.objects.filter(role__isnull=True)
        total = employees_without_roles.count()

        if total == 0:
            self.stdout.write(
                self.style.SUCCESS('All employees already have roles assigned.')
            )
            return

        self.stdout.write(f'Found {total} employee(s) without roles.')

        assigned_count = 0
        for employee in employees_without_roles:
            role_to_assign = default_role

            # If assign_by_staff is enabled, check user's is_staff status
            if assign_by_staff and employee.user:
                if employee.user.is_superuser and admin_role:
                    role_to_assign = admin_role
                elif employee.user.is_staff and hr_role:
                    role_to_assign = hr_role

            employee.role = role_to_assign
            employee.save()
            assigned_count += 1

            self.stdout.write(
                f'  ✓ Assigned {role_to_assign.name} role to {employee.get_full_name()} '
                f'({employee.employee_id})'
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully assigned roles to {assigned_count} employee(s).'
            )
        )

