
import os
import django
import random
import datetime
import pymysql
# Mock version to satisfy Django's check
pymysql.version_info = (2, 2, 7, "final", 0)
pymysql.install_as_MySQLdb()
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from auth_app.models import User
from employees.models import Employee, Education, EmergencyContact, WorkHistory
from organizations.models import Company
from departments.models import Department, Designation
from attendance.models import Attendance, Timesheet, ManualAttendanceRequest
from django.contrib.auth.models import Group
from holidays.models import Holiday
from inventory.models import DeviceType, Device, DeviceAssignment
from leaves.models import Leave, LeaveQuota, LeaveBalance, RestrictedHoliday
from payroll.models import SalaryStructure, Payslip, PayrollConfig

def populate_all_data():
    print("🌱 Starting Comprehensive Data Population...")

    # --- 1. Company ---
    company, _ = Company.objects.get_or_create(name="HueHRMS", defaults={'slug': 'hue-hrms'})
    print(f"🏢 Company: {company.name}")

    # --- 2. Departments & Designations ---
    departments_data = {
        'Engineering': ['Software Engineer', 'Senior Engineer', 'CTO'],
        'HR': ['HR Executive', 'HR Manager'],
        'Sales': ['Sales Representative', 'Sales Manager']
    }
    dept_objs = {}
    desig_objs = {}
    for dept_name, roles in departments_data.items():
        dept, _ = Department.objects.get_or_create(name=dept_name, defaults={'code': dept_name[:3].upper()})
        dept_objs[dept_name] = dept
        for role in roles:
            desig, _ = Designation.objects.get_or_create(name=role, department=dept, defaults={'level': 1})
            desig_objs[role] = desig
    print("✅ Departments & Designations created.")

    # --- 3. Auth Groups ---
    groups = ['Admin', 'Manager', 'Employee']
    group_objs = {}
    for g_name in groups:
        grp, _ = Group.objects.get_or_create(name=g_name)
        group_objs[g_name] = grp
    print("✅ Auth Groups created.")

    # --- 4. Users & Employees ---
    specific_users = [
        {'username': 'admin', 'email': 'devpython549@gmail.com', 'first': 'Admin', 'last': 'User', 'group': 'Admin', 'is_staff': True, 'is_superuser': True},
        {'username': 'medha', 'email': 'medhavisharma11apr@gmail.com', 'first': 'Medhavi', 'last': 'Sharma', 'group': 'Manager', 'is_staff': False, 'is_superuser': False},
        {'username': 'jane.doe', 'email': 'jane.doe@company.com', 'first': 'Jane', 'last': 'Doe', 'group': 'Employee', 'is_staff': False, 'is_superuser': False},
        {'username': 'jane.doeerr', 'email': 'jane.doeerr@company.com', 'first': 'Janeerr', 'last': 'Doeerr', 'group': 'Employee', 'is_staff': False, 'is_superuser': False},
    ]

    for data in specific_users:
        # Get or Create User
        user, created = User.objects.get_or_create(
            username=data['username'],
            defaults={
                'email': data['email'],
                'first_name': data['first'],
                'last_name': data['last'],
                'is_staff': data['is_staff'],
                'is_superuser': data['is_superuser'],
                'is_active': True,
                'is_verified': True
            }
        )
        if created:
            user.set_password('password123')
            user.save()
            print(f"👤 Created User: {user.username}")
        else:
            print(f"ℹ️ User {user.username} exists. Checking relations...")

        # Add to Group
        if data['group'] in group_objs:
            user.groups.add(group_objs[data['group']])
        
        # Get or Create Employee
        dept_name = list(departments_data.keys())[0] # Default to first if needed
        role_name = departments_data[dept_name][0]
        
        join_date = datetime.date.today() - datetime.timedelta(days=30)
        
        emp, emp_created = Employee.objects.get_or_create(
            email=user.email,
            defaults={
                'user': user,
                'company': company,
                'employee_id': f"EMP{random.randint(1000, 9999)}",
                'first_name': user.first_name,
                'last_name': user.last_name,
                'department': dept_objs[dept_name],
                'designation': desig_objs[role_name],
                'date_of_birth': datetime.date(1990, 1, 1),
                'joining_date': join_date,
                'phone': f"98{random.randint(10000000, 99999999)}",
                'is_active': True
            }
        )
        if emp_created:
            print(f"   └── 👷 Created Employee: {emp.employee_id}")
        else:
            print(f"   └── 👷 Found Employee: {emp.employee_id}")
        
        # --- 5. Education ---
        if not Education.objects.filter(employee=emp).exists():
             Education.objects.create(
                employee=emp,
                level='bachelor',
                degree='B.Tech Computer Science',
                institution='Tech University',
                start_date=join_date - datetime.timedelta(days=365*4),
                end_date=join_date - datetime.timedelta(days=30),
                percentage=85.5
            )
             print(f"   └── 🎓 Added Education")

        # --- 6. Emergency & Work History ---
        if not EmergencyContact.objects.filter(employee=emp).exists():
            EmergencyContact.objects.create(
                employee=emp,
                name=f"Parent of {user.first_name}",
                relationship="Parent",
                phone=f"98{random.randint(10000000, 99999999)}",
                is_primary=True
            )
            print(f"   └── 🆘 Added Emergency Contact")

        if not WorkHistory.objects.filter(employee=emp).exists():
            WorkHistory.objects.create(
                employee=emp,
                company_name="Previous Corp",
                job_title="Junior Developer",
                start_date=join_date - datetime.timedelta(days=700),
                end_date=join_date - datetime.timedelta(days=60),
                is_current=False
            )
            print(f"   └── 💼 Added Work History")

        # --- 7. Attendance & Timesheets ---
        today = timezone.localdate()
        for i in range(7):
            date = today - datetime.timedelta(days=i)
            if date.weekday() < 5: # Weekdays only
                if not Attendance.objects.filter(employee=emp, date=date).exists():
                    in_time = timezone.now().replace(year=date.year, month=date.month, day=date.day, hour=9, minute=0, second=0)
                    out_time = in_time + datetime.timedelta(hours=9)
                    
                    Attendance.objects.create(
                        employee=emp,
                        date=date,
                        in_time=in_time,
                        out_time=out_time,
                        day_type='WORKING_DAY',
                        office_in_time=in_time,
                        office_out_time=out_time,
                        office_working_hours='09:00',
                    )
                    print(f"       └── 🕒 Added Attendance for {date}")
        
        if not Timesheet.objects.filter(employee=emp).exists():
            Timesheet.objects.create(
                employee=emp,
                start_date=today - datetime.timedelta(days=7),
                end_date=today,
                hours=45.0,
                status='approved'
            )
            print(f"   └── 📝 Added Timesheet")

        if not ManualAttendanceRequest.objects.filter(employee=emp).exists():
            ManualAttendanceRequest.objects.create(
                employee=emp,
                date=today - datetime.timedelta(days=2),
                entry_time=datetime.time(9, 30),
                exit_time=datetime.time(18, 30),
                reason="Forgot to punch in",
                status='pending'
            )
            print(f"   └── 📩 Added Manual Request")

    # --- 8. Holidays ---
    print("\n🗓️ Populating Holidays...")
    current_year = timezone.now().year
    holidays = [
        ("New Year's Day", f"{current_year}-01-01", "national"),
        ("Republic Day", f"{current_year}-01-26", "national"),
        ("Independence Day", f"{current_year}-08-15", "national"),
        ("Gandhi Jayanti", f"{current_year}-10-02", "national"),
        ("Christmas", f"{current_year}-12-25", "religious"),
    ]

    for name, date_str, h_type in holidays:
        Holiday.objects.get_or_create(
            name=name,
            date=date_str,
            defaults={
                'holiday_type': h_type,
                'description': f"{name} celebration",
                'country': 'India',
                'is_active': True
            }
        )
        print(f"   └── 🎉 Added Holiday: {name} ({date_str})")

    # --- 9. Inventory ---
    print("\n💻 Populating Inventory...")
    types = ['Laptop', 'Monitor', 'Mobile Phone', 'Mouse', 'Keyboard']
    type_objs = {}
    for t_name in types:
        dt, _ = DeviceType.objects.get_or_create(name=t_name, defaults={'is_active': True})
        type_objs[t_name] = dt
        
    # Assign Devices to Employees
    admin_user = User.objects.filter(is_superuser=True).first()
    employees = Employee.objects.all()
    
    for emp in employees:
        # Give each employee a Laptop
        laptop_serial = f"LPT-{emp.employee_id}-{random.randint(100,999)}"
        if not Device.objects.filter(serial_number=laptop_serial).exists():
            laptop, created = Device.objects.get_or_create(
                serial_number=laptop_serial,
                defaults={
                    'device_type': type_objs['Laptop'],
                    'brand': random.choice(['Apple', 'Dell', 'Lenovo']),
                    'model_name': 'ProBook X1',
                    'status': 'working',
                    'condition': 'good',
                    'employee': emp, # Currently assigned
                    'purchase_date': emp.joining_date,
                    'warranty_expiry': emp.joining_date + datetime.timedelta(days=365*3),
                    'is_active': True
                }
            )
            if created:
                print(f"   └── 💻 Assigned Laptop to {emp.first_name}: {laptop.serial_number}")
                
                # History Log
                DeviceAssignment.objects.create(
                    device=laptop,
                    employee=emp,
                    assigned_by=admin_user,
                    condition_at_assignment='new'
                )

    # --- 10. Leaves ---
    print("\n🍃 Populating Leaves...")
    
    # 1. Restricted Holidays
    rh_days = [
        ("Makar Sankranti", f"{current_year}-01-14"),
        ("Holi", f"{current_year}-03-14"),
        ("Raksha Bandhan", f"{current_year}-08-09"),
        ("Diwali", f"{current_year}-10-20"),
    ]
    for rh_name, rh_date in rh_days:
        RestrictedHoliday.objects.get_or_create(
            date=rh_date,
            defaults={'name': rh_name, 'is_active': True}
        )
        print(f"   └── 📅 Added RH: {rh_name}")

    # 2. Quotas & Balances for Employees
    for emp in employees:
        # Default Quota: 12 Casual, 12 Sick
        # Casual Leave
        LeaveQuota.objects.get_or_create(
            employee=emp,
            leave_type=Leave.LeaveType.CASUAL_LEAVE,
            effective_from=datetime.date(current_year, 1, 1),
            defaults={
                'monthly_quota': 1.0,
                'yearly_quota': 12.0,
                'rh_quota': 2
            }
        )
        # Sick Leave
        LeaveQuota.objects.get_or_create(
            employee=emp,
            leave_type=Leave.LeaveType.SICK_LEAVE,
            effective_from=datetime.date(current_year, 1, 1),
            defaults={
                'monthly_quota': 1.0,
                'yearly_quota': 12.0,
                'rh_quota': 0
            }
        )
        
        # Initialize Balance (Casual)
        LeaveBalance.objects.get_or_create(
            employee=emp,
            leave_type=Leave.LeaveType.CASUAL_LEAVE,
            year=current_year,
            defaults={
                'total_allocated': 12.0,
                'used': 0.0,
                'rh_allocated': 2
            }
        )
    print(f"   └── ✅ Quotas & Balances initialized for {employees.count()} employees")

    # 3. Create a Sample Leave Request
    sample_emp = Employee.objects.first()
    if sample_emp:
        l_date = datetime.date.today() + datetime.timedelta(days=5)
        if not Leave.objects.filter(employee=sample_emp, from_date=l_date).exists():
            Leave.objects.create(
                employee=sample_emp,
                leave_type=Leave.LeaveType.CASUAL_LEAVE,
                from_date=l_date,
                to_date=l_date,
                no_of_days=1.0,
                reason="Personal work",
                status=Leave.Status.APPROVED
            )
            print(f"   └── 🏖️ Created Sample Leave for {sample_emp.first_name}")

    # --- 11. Payroll ---
    print("\n💰 Populating Payroll...")
    
    # 1. Config
    PayrollConfig.objects.get_or_create(
        key="TAX_BRACKETS_2025",
        defaults={
            'value': {"0-5L": 0, "5L-10L": 5, "10L+": 10},
            'description': "Tax slabs for FY 2025"
        }
    )

    # 2. Salary Structures & Payslips
    for emp in employees:
        # Create Structure
        basic = 50000.00
        hra = 20000.00
        special = 15000.00
        gross = basic + hra + special
        epf = basic * 0.12 # 6000
        tds = gross * 0.10 # 8500
        epf = float(epf)
        tds = float(tds)
        
        SalaryStructure.objects.get_or_create(
            employee=emp,
            defaults={
                'basic_salary': basic,
                'hra': hra,
                'special_allowance': special,
                'medical_allowance': 1200.00,
                'conveyance_allowance': 1600.00,
                'epf': epf,
                'tds': tds,
                'is_active': True
            }
        )
        print(f"   └── 💳 Structure set for {emp.first_name}")

        # Create Payslip for last month
        last_month = datetime.date.today().replace(day=1) - datetime.timedelta(days=1)
        if not Payslip.objects.filter(employee=emp, month=last_month.month, year=last_month.year).exists():
            Payslip.objects.create(
                employee=emp,
                month=last_month.month,
                year=last_month.year,
                basic_salary=basic,
                hra=hra,
                medical_allowance=1200.00,
                conveyance_allowance=1600.00,
                special_allowance=special,
                total_earnings=gross + 2800, # Gross + Med + Conv
                epf=epf,
                tds=tds,
                total_deductions=epf + tds,
                net_salary=(gross + 2800) - (epf + tds),
                working_days=22,
                leaves_taken=1.0,
                status='paid'
            )
            print(f"   └── 📄 Generated Payslip for {last_month.strftime('%B %Y')}")

    print("\n🎉 FULL Data Population Complete!")

if __name__ == "__main__":
    populate_all_data()




# DATABASE_URL='mysql://231jcYH2kME1CNj.root:slTPhzvfRf2bny82@gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/test?ssl-mode=REQUIRED' python populate_tidb_all.py