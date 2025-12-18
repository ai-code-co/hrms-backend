# Database Table Structure and Creation Process

## Overview
This HRMS (Human Resource Management System) backend uses Django's ORM with SQLite database (configurable to PostgreSQL via environment variables). Tables are created through Django's migration system.

---

## Table Structure

### 1. **auth_user** (Custom User Model)
**App:** `auth_app`  
**Model:** `User` (extends Django's `AbstractUser`)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BigAutoField | Primary Key | Auto-incrementing ID |
| `username` | CharField(150) | Unique, Required | Login username |
| `email` | EmailField | Unique, Required | User email address |
| `password` | CharField(128) | Required | Hashed password |
| `first_name` | CharField(150) | Required | First name |
| `last_name` | CharField(150) | Required | Last name |
| `is_verified` | BooleanField | Default: False | Email verification status |
| `is_first_login` | BooleanField | Default: True | First login flag |
| `is_active` | BooleanField | Default: True | Account active status |
| `is_staff` | BooleanField | Default: False | Admin access |
| `is_superuser` | BooleanField | Default: False | Superuser status |
| `last_login` | DateTimeField | Nullable | Last login timestamp |
| `date_joined` | DateTimeField | Auto | Account creation date |
| `groups` | ManyToMany | - | Permission groups |
| `user_permissions` | ManyToMany | - | User permissions |

**Additional Fields from AbstractUser:**
- All standard Django user fields are inherited

---

### 2. **departments_department**
**App:** `departments`  
**Model:** `Department`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BigAutoField | Primary Key | Auto-incrementing ID |
| `name` | CharField(100) | Unique, Indexed | Department name |
| `code` | CharField(20) | Unique, Nullable | Department code (e.g., IT, HR) |
| `description` | TextField | Optional | Department description |
| `manager` | ForeignKey | Nullable | Links to `employees_employee` |
| `is_active` | BooleanField | Default: True | Active status |
| `created_at` | DateTimeField | Auto | Creation timestamp |
| `updated_at` | DateTimeField | Auto | Last update timestamp |

**Indexes:**
- Index on `name`
- Index on `code`

**Relationships:**
- `manager` → `employees_employee` (One department can have one manager)
- Reverse: `employees` → Many employees belong to one department

---

### 3. **departments_designation**
**App:** `departments`  
**Model:** `Designation`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BigAutoField | Primary Key | Auto-incrementing ID |
| `name` | CharField(100) | Required | Job title name |
| `department` | ForeignKey | Required | Links to `departments_department` |
| `level` | IntegerField | Default: 1 | Hierarchy level (1-10) |
| `description` | TextField | Optional | Job description |
| `is_active` | BooleanField | Default: True | Active status |
| `created_at` | DateTimeField | Auto | Creation timestamp |
| `updated_at` | DateTimeField | Auto | Last update timestamp |

**Unique Constraints:**
- `(name, department)` - Same designation name can't exist twice in one department

**Indexes:**
- Composite index on `(department, level)`

**Relationships:**
- `department` → `departments_department` (Many designations belong to one department)
- Reverse: `employees` → Many employees have one designation

---

### 4. **employees_employee**
**App:** `employees`  
**Model:** `Employee`

#### Core Identification
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BigAutoField | Primary Key | Auto-incrementing ID |
| `employee_id` | CharField(50) | Unique, Indexed | Auto-generated ID (e.g., EMP20250001) |
| `user` | OneToOneField | Nullable | Links to `auth_user` for login |

#### Personal Information
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `first_name` | CharField(50) | Required | First name |
| `middle_name` | CharField(50) | Optional | Middle name |
| `last_name` | CharField(50) | Required | Last name |
| `date_of_birth` | DateField | Nullable | Date of birth |
| `gender` | CharField(20) | Choices | Male/Female/Other/Prefer Not to Say |
| `marital_status` | CharField(20) | Choices | Single/Married/Divorced/Widowed |
| `nationality` | CharField(50) | Optional | Nationality |
| `blood_group` | CharField(5) | Optional | Blood group |
| `photo` | ImageField | Nullable | Profile photo |

#### Contact Information
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `email` | EmailField | Unique, Indexed | Email address |
| `phone` | CharField(20) | Required | Phone number (validated) |
| `alternate_phone` | CharField(20) | Optional | Alternate phone |
| `address_line1` | CharField(200) | Required | Address line 1 |
| `address_line2` | CharField(200) | Optional | Address line 2 |
| `city` | CharField(50) | Required | City |
| `state` | CharField(50) | Required | State |
| `country` | CharField(50) | Default: 'India' | Country |
| `postal_code` | CharField(10) | Required | Postal code |

#### Professional Information
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `department` | ForeignKey | Required, PROTECT | Links to `departments_department` |
| `designation` | ForeignKey | Required, PROTECT | Links to `departments_designation` |
| `reporting_manager` | ForeignKey | Nullable | Self-referential (links to another Employee) |
| `employee_type` | CharField(20) | Choices, Default: 'full_time' | Full Time/Part Time/Contract/Intern/Consultant |
| `employment_status` | CharField(20) | Choices, Default: 'active' | Active/On Leave/Terminated/Suspended/Resigned |
| `joining_date` | DateField | Required | Joining date |
| `probation_end_date` | DateField | Nullable | Probation end date |
| `confirmation_date` | DateField | Nullable | Confirmation date |
| `work_location` | CharField(100) | Default: 'Office' | Work location |

#### Identification Documents
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `pan_number` | CharField(10) | Unique, Nullable | PAN card number |
| `aadhar_number` | CharField(12) | Unique, Nullable | Aadhar number |
| `passport_number` | CharField(20) | Unique, Nullable | Passport number |
| `driving_license` | CharField(20) | Optional | Driving license |

#### Financial Information
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `bank_name` | CharField(100) | Optional | Bank name |
| `account_number` | CharField(30) | Optional | Account number |
| `ifsc_code` | CharField(11) | Optional | IFSC code |
| `account_holder_name` | CharField(100) | Optional | Account holder name |

#### System Fields
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `is_active` | BooleanField | Default: True | Active status |
| `created_at` | DateTimeField | Auto | Creation timestamp |
| `updated_at` | DateTimeField | Auto | Last update timestamp |
| `created_by` | ForeignKey | Nullable | Links to `auth_user` (creator) |
| `updated_by` | ForeignKey | Nullable | Links to `auth_user` (last updater) |

**Indexes:**
- Index on `employee_id`
- Index on `email`
- Index on `employment_status`
- Composite index on `(department, designation)`

**Relationships:**
- `user` → `auth_user` (One-to-one: Employee linked to User account)
- `department` → `departments_department` (Many employees → one department)
- `designation` → `departments_designation` (Many employees → one designation)
- `reporting_manager` → `employees_employee` (Self-referential: Employee → Manager)
- `created_by` → `auth_user` (Many employees → one creator)
- `updated_by` → `auth_user` (Many employees → one updater)

**Special Features:**
- `employee_id` is auto-generated if not provided: Format `EMP{year}{4-digit-number}` (e.g., EMP20250001)

---

### 5. **employees_emergencycontact**
**App:** `employees`  
**Model:** `EmergencyContact`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BigAutoField | Primary Key | Auto-incrementing ID |
| `employee` | ForeignKey | Required | Links to `employees_employee` |
| `name` | CharField(100) | Required | Contact person name |
| `relationship` | CharField(50) | Required | Relationship (Spouse, Father, etc.) |
| `phone` | CharField(20) | Required | Phone number |
| `alternate_phone` | CharField(20) | Optional | Alternate phone |
| `email` | EmailField | Optional | Email address |
| `address` | TextField | Optional | Address |
| `is_primary` | BooleanField | Default: False | Primary contact flag |
| `created_at` | DateTimeField | Auto | Creation timestamp |
| `updated_at` | DateTimeField | Auto | Last update timestamp |

**Relationships:**
- `employee` → `employees_employee` (Many contacts → one employee)

**Special Features:**
- Only one contact per employee can be marked as `is_primary=True` (enforced in `save()` method)

---

### 6. **employees_education**
**App:** `employees`  
**Model:** `Education`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BigAutoField | Primary Key | Auto-incrementing ID |
| `employee` | ForeignKey | Required | Links to `employees_employee` |
| `level` | CharField(20) | Choices | High School/Diploma/Bachelor/Master/PhD/Certification/Other |
| `degree` | CharField(100) | Required | Degree name (e.g., B.Tech, MBA) |
| `field_of_study` | CharField(100) | Required | Field (e.g., Computer Science) |
| `institution` | CharField(200) | Required | School/University name |
| `start_date` | DateField | Nullable | Start date |
| `end_date` | DateField | Nullable | End date |
| `is_completed` | BooleanField | Default: True | Completion status |
| `percentage` | DecimalField(5,2) | Nullable | Percentage or CGPA |
| `grade` | CharField(10) | Optional | Grade |
| `description` | TextField | Optional | Additional details |
| `certificate` | FileField | Nullable | Certificate file |
| `created_at` | DateTimeField | Auto | Creation timestamp |
| `updated_at` | DateTimeField | Auto | Last update timestamp |

**Relationships:**
- `employee` → `employees_employee` (Many education records → one employee)

**Validation:**
- `end_date` cannot be before `start_date` (enforced in `clean()` method)

---

### 7. **employees_workhistory**
**App:** `employees`  
**Model:** `WorkHistory`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BigAutoField | Primary Key | Auto-incrementing ID |
| `employee` | ForeignKey | Required | Links to `employees_employee` |
| `company_name` | CharField(200) | Required | Previous company name |
| `job_title` | CharField(100) | Required | Job title |
| `department` | CharField(100) | Optional | Department name |
| `start_date` | DateField | Required | Start date |
| `end_date` | DateField | Nullable | End date |
| `is_current` | BooleanField | Default: False | Current job flag |
| `job_description` | TextField | Optional | Job description |
| `achievements` | TextField | Optional | Achievements |
| `reason_for_leaving` | TextField | Optional | Reason for leaving |
| `supervisor_name` | CharField(100) | Optional | Supervisor name |
| `supervisor_contact` | CharField(50) | Optional | Supervisor contact |
| `salary` | DecimalField(10,2) | Nullable | Last drawn salary |
| `created_at` | DateTimeField | Auto | Creation timestamp |
| `updated_at` | DateTimeField | Auto | Last update timestamp |

**Relationships:**
- `employee` → `employees_employee` (Many work history records → one employee)

**Validation:**
- `end_date` cannot be before `start_date` (enforced in `clean()` method)

---

## How Tables Are Created

### Django Migration System

Django uses a **migration system** to manage database schema changes. Here's how it works:

1. **Models Define Structure**: Tables are defined as Python classes in `models.py` files
2. **Migrations Generate SQL**: Django generates migration files that contain instructions to create/modify tables
3. **Migrations Apply Changes**: Running migrations executes SQL commands to create/update the database

### Migration Files Location

```
hrms-backend/
├── auth_app/
│   └── migrations/
│       ├── 0001_initial.py          # Creates auth_user table
│       ├── 0002_user_is_verified.py # Adds is_verified field
│       └── 0003_user_is_first_login.py # Adds is_first_login field
├── departments/
│   └── migrations/
│       ├── 0001_initial.py          # Creates Department, Designation tables
│       └── 0003_alter_department_*.py # Modifies Department table
└── employees/
    └── migrations/
        ├── 0001_initial.py          # Creates Employee, EmergencyContact, Education, WorkHistory tables
        └── 0002_alter_employee_*.py # Modifies Employee table fields
```

---

## When Tables Are Created

### Initial Setup (First Time)

**Step 1: Create Migration Files**
```bash
python manage.py makemigrations
```
This command:
- Scans all `models.py` files in installed apps
- Compares current models with existing migrations
- Generates new migration files if changes are detected

**Step 2: Apply Migrations**
```bash
python manage.py migrate
```
This command:
- Reads all migration files in order
- Executes SQL commands to create/modify tables
- Tracks applied migrations in `django_migrations` table

### Migration Execution Order

Django executes migrations in **dependency order**:

1. **Django Core Migrations** (auth, contenttypes, sessions, etc.)
2. **auth_app migrations** (0001_initial → 0002 → 0003)
3. **departments migrations** (0001_initial → 0002 → 0003)
4. **employees migrations** (0001_initial → 0002)

**Dependencies:**
- `employees` depends on `departments` (Employee has ForeignKey to Department)
- `employees` depends on `auth_app` (Employee has ForeignKey to User)
- `departments` depends on `employees` (Department.manager links to Employee - circular dependency handled)

### When Migrations Run

1. **During Development:**
   - After creating/modifying models
   - Run `makemigrations` → `migrate`

2. **During Deployment:**
   - Migrations run automatically if configured
   - Or manually: `python manage.py migrate`

3. **On Fresh Database:**
   - All migrations run in order
   - Creates all tables from scratch

4. **On Existing Database:**
   - Only unapplied migrations run
   - Django tracks which migrations have been applied

### Checking Migration Status

```bash
# See migration status
python manage.py showmigrations

# See SQL that will be executed
python manage.py sqlmigrate app_name migration_number
```

### Example: Creating Tables

When you run `python manage.py migrate` for the first time:

1. **Django creates system tables:**
   - `django_migrations` (tracks applied migrations)
   - `django_content_type` (content types)
   - `django_session` (sessions)
   - `auth_group`, `auth_permission` (permissions)

2. **Then creates your app tables:**
   - `auth_user` (custom user model)
   - `departments_department`
   - `departments_designation`
   - `employees_employee`
   - `employees_emergencycontact`
   - `employees_education`
   - `employees_workhistory`

3. **Creates indexes and constraints:**
   - Primary keys
   - Foreign key constraints
   - Unique constraints
   - Indexes (as defined in models)

---

## Database Configuration

**Current Setup:**
- **Database:** SQLite (default: `db.sqlite3`)
- **Configurable:** Can use PostgreSQL via `DATABASE_URL` environment variable
- **Location:** `config/settings.py` (line 147-149)

```python
DATABASES = {
    'default': dj_database_url.config(default='sqlite:///db.sqlite3')
}
```

**To Use PostgreSQL:**
Set `DATABASE_URL` environment variable:
```
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

---

## Summary

- **7 Main Tables** are created from 3 Django apps
- **Tables are created** through Django's migration system
- **Migrations run** when you execute `python manage.py migrate`
- **Order matters** - migrations execute in dependency order
- **Django tracks** which migrations have been applied
- **Tables persist** in the database file (`db.sqlite3` or PostgreSQL)

The migration system ensures your database schema stays in sync with your Django models, making it easy to version control and deploy database changes.

