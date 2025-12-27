import os
import django
import random
import pymysql
pymysql.version_info = (2, 2, 1, "final", 0)
pymysql.install_as_MySQLdb()
from datetime import date, timedelta, datetime
from django.utils import timezone
from decimal import Decimal
from django.db.models.signals import post_save, pre_save

# Utility to disable signals for speed
class DisableSignals(object):
    def __init__(self, disabled_signals=None):
        self.stashed_signals = disabled_signals or [pre_save, post_save]
        self.disabled_signals = []

    def __enter__(self):
        for signal in self.stashed_signals:
            self.disabled_signals.append(signal.receivers)
            signal.receivers = []

    def __exit__(self, exc_type, exc_val, exc_tb):
        for i, signal in enumerate(self.stashed_signals):
            signal.receivers = self.disabled_signals[i]

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from auth_app.models import User
from organizations.models import Company
from departments.models import Department, Designation
from employees.models import Employee
from leaves.models import Leave
from attendance.models import Attendance, Timesheet, ManualAttendanceRequest
from inventory.models import DeviceType, Device, DeviceAssignment
from payroll.models import SalaryStructure, Payslip

def populate_db():
    print("🚀 Starting Comprehensive Database Population...")

    # 1. Companies
    co1, _ = Company.objects.get_or_create(id=1, defaults={'name': 'Excellence Tech', 'slug': 'excellence-tech'})
    co2, _ = Company.objects.get_or_create(id=2, defaults={'name': 'SuccesPoint', 'slug': 'succespoint'})
    print("✅ Companies synced.")

    # 2. Departments
    dept_hr, _ = Department.objects.get_or_create(id=1, defaults={'name': 'Human Resources', 'code': 'HR'})
    dept_eng, _ = Department.objects.get_or_create(id=2, defaults={'name': 'Engineering', 'code': 'ENG'})
    print("✅ Departments synced.")

    # 3. Designations
    des_mgr, _ = Designation.objects.get_or_create(id=1, defaults={'name': 'HR Manager', 'department': dept_hr, 'level': 5})
    des_dev, _ = Designation.objects.get_or_create(id=2, defaults={'name': 'Senior Developer', 'department': dept_eng, 'level': 3})
    print("✅ Designations synced.")

    # 4. Users (Restore priority accounts)
    users_data = [
        {
            'id': 1,
            'password': 'pbkdf2_sha256$1200000$KPGo4KF1S3FDaaRmoPCFtF$w03IEcTzyrGrup96D5MjFykLN8pLBcrDAekPjOTVj7o=',
            'username': 'admin',
            'first_name': 'admin',
            'last_name': 'admin',
            'email': 'devpython549@gmail.com',
            'is_superuser': True,
            'is_staff': True,
            'is_active': True,
            'is_verified': False,
            'is_first_login': True
        },
        {
            'id': 2,
            'password': 'pbkdf2_sha256$1200000$DfUSHqqSl5Z3RRQHyyuiE3$bZqcSOMhngXIP/vK+Us0iLtEg+Iyl2GUNVOczYQub0g=',
            'username': 'medha',
            'first_name': 'mukund',
            'last_name': 'sharma',
            'email': 'medhavisharma11apr@gmail.com',
            'is_superuser': False,
            'is_staff': False,
            'is_active': True,
            'is_verified': True,
            'is_first_login': False
        },
        {
            'id': 3,
            'password': 'pbkdf2_sha256$1200000$A9AvRV1F7crjekkVvSDry4$HPwOJm5pOOLwMe1q5yo8xHNNA5DIkve2yhjdwHLC+WQ=',
            'username': 'jane.doe',
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane.doe@company.com',
            'is_superuser': False,
            'is_staff': False,
            'is_active': False,
            'is_verified': False,
            'is_first_login': True
        },
        {
            'id': 4,
            'password': 'pbkdf2_sha256$1200000$eUVcCD4Q3zBqWqyL87CNM2$chIgwRzvWfi/Qk/nuOcF7Ypc3YFGlsNcOgmiQwOAgWA=',
            'username': 'jane.doeerr',
            'first_name': 'Janeerr',
            'last_name': 'Doeerr',
            'email': 'jane.doeerr@company.com',
            'is_superuser': False,
            'is_staff': False,
            'is_active': False,
            'is_verified': False,
            'is_first_login': True
        }
    ]

    for u_data in users_data:
        User.objects.update_or_create(id=u_data['id'], defaults=u_data)
    print("✅ Users restored.")

    # 5. Employees mapping
    user_configs = [
        {'id': 1, 'username': 'admin', 'company': co1, 'dept': dept_hr, 'des': des_mgr},
        {'id': 2, 'username': 'medha', 'company': co1, 'dept': dept_eng, 'des': des_dev},
        {'id': 3, 'username': 'jane.doe', 'company': co2, 'dept': dept_hr, 'des': des_mgr},
        {'id': 4, 'username': 'jane.doeerr', 'company': co2, 'dept': dept_eng, 'des': des_dev},
    ]

    employees = []
    for config in user_configs:
        try:
            user = User.objects.get(id=config['id'])
            emp, created = Employee.objects.get_or_create(
                user=user,
                defaults={
                    'first_name': user.first_name or user.username,
                    'last_name': user.last_name or 'User',
                    'email': user.email,
                    'company': config['company'],
                    'department': config['dept'],
                    'designation': config['des'],
                    'joining_date': date.today() - timedelta(days=365),
                    'employment_status': 'active',
                    'is_active': True,
                    'country': 'India',
                    'phone': getattr(user, 'phone_number', '1234567890') or '1234567890'
                }
            )
            employees.append(emp)
            if created: print(f"✅ Created Employee Profile for {user.username}")
        except User.DoesNotExist:
            print(f"⚠️ User with ID {config['id']} ({config['username']}) not found. Skipping...")

    if not employees:
        print("❌ No employees found/created. Stopping.")
        return

    # 5. Salary Structures
    for emp in employees:
        SalaryStructure.objects.update_or_create(
            employee=emp,
            defaults={
                'basic_salary': Decimal('50000.00'),
                'hra': Decimal('20000.00'),
                'medical_allowance': Decimal('2000.00'),
                'conveyance_allowance': Decimal('1600.00'),
                'special_allowance': Decimal('5000.00'),
                'epf': Decimal('1800.00'),
                'tds': Decimal('1000.00'),
            }
        )
    print("✅ Salary Structures synced.")

    # 6. Attendance (Last 30 days)
    print("⏳ Populating Attendance records...")
    today = date.today()
    for emp in employees:
        for i in range(30):
            d = today - timedelta(days=i)
            # Skip Sundays
            if d.weekday() == 6: continue
            
            # 80% chance of being present
            if random.random() > 0.2:
                in_dt = timezone.make_aware(datetime.combine(d, datetime.min.time().replace(hour=9, minute=random.randint(0, 30))))
                out_dt = timezone.make_aware(datetime.combine(d, datetime.min.time().replace(hour=18, minute=random.randint(0, 30))))
                
                Attendance.objects.update_or_create(
                    employee=emp,
                    date=d,
                    defaults={
                        'in_time': in_dt,
                        'out_time': out_dt,
                        'office_in_time': in_dt,
                        'office_out_time': out_dt,
                        'day_type': 'WORKING_DAY',
                    }
                )

    # 7. Leaves
    print("⏳ Populating Leave records...")
    for emp in employees:
        Leave.objects.get_or_create(
            employee=emp,
            reason="Family Function",
            from_date=today + timedelta(days=10),
            to_date=today + timedelta(days=12),
            defaults={
                'leave_type': 'Casual Leave',
                'no_of_days': 3,
                'status': 'Pending'
            }
        )

    # 8. Inventory
    dt_laptop, _ = DeviceType.objects.get_or_create(name='Laptop', defaults={'description': 'Work Laptops'})
    dt_phone, _ = DeviceType.objects.get_or_create(name='Mobile Phone', defaults={'description': 'Company Phones'})
    
    for i, emp in enumerate(employees):
        dev, _ = Device.objects.get_or_create(
            serial_number=f"SN-{emp.id}-{i}",
            defaults={
                'device_type': dt_laptop,
                'brand': random.choice(['Dell', 'Apple', 'HP', 'Lenovo']),
                'model_name': 'Professional Series',
                'status': 'working',
                'employee': emp
            }
        )
        DeviceAssignment.objects.get_or_create(
            device=dev,
            employee=emp,
            defaults={
                'assigned_by': User.objects.get(id=1), # Admin
                'notes': 'Initial assignment'
            }
        )
    print("✅ Inventory synced.")

    # 9. Payroll (Previous Month Payslip)
    prev_month_date = today.replace(day=1) - timedelta(days=1)
    for emp in employees:
        Payslip.objects.update_or_create(
            employee=emp,
            month=prev_month_date.month,
            year=prev_month_date.year,
            defaults={
                'basic_salary': Decimal('50000.00'),
                'hra': Decimal('20000.00'),
                'medical_allowance': Decimal('2000.00'),
                'conveyance_allowance': Decimal('1600.00'),
                'special_allowance': Decimal('5000.00'),
                'total_earnings': Decimal('78600.00'),
                'total_deductions': Decimal('2800.00'),
                'net_salary': Decimal('75800.00'),
                'working_days': 22,
                'status': 'paid'
            }
        )
    print("✅ Payroll records (Payslips) synced.")

    print("\n🎉 ALL TEST DATA POPULATED SUCCESSFULLY!")

if __name__ == "__main__":
    with DisableSignals():
        populate_db()
