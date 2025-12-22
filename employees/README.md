# Employees Module 👥

## What is this?

The **Employees Module** is the core HR database that stores all employee information including:
- Personal details
- Employment information
- Emergency contacts
- Education history
- Work experience

> [!NOTE]
> **Automatic Creation:** Employee profiles are now automatically created when an Admin creates a User account via the Authentication module. Only additional details (docs, banking, education) need to be added manually later.

## Why do we need it?

- **Central Database** - Single source of truth for all employee data
- **Complete Profiles** - Track everything from joining to exit
- **Compliance** - Store required documents and information
- **Reporting** - Generate employee reports and analytics

## API Endpoints

### Base URL: `/api/employees/`

### 1. List Employees
`GET /api/employees/`

**Query Parameters:**
- `department` - Filter by department
- `designation` - Filter by designation
- `employment_status` - active, on_leave, terminated, etc.
- `search` - Search by name, email, employee_id

**Response:**
```json
[
  {
    "id": 1,
    "employee_id": "EMP001",
    "full_name": "John Doe",
    "email": "john@company.com",
    "phone": "+1234567890",
    "department": "Engineering",
    "designation": "Software Engineer",
    "employment_status": "active",
    "joining_date": "2025-01-01"
  }
]
```

### 2. Get Employee Details
`GET /api/employees/{id}/`

**Response:** Complete employee profile with emergency contacts, education, and work history

### 3. Create Employee
`POST /api/employees/` (Admin only)

**Note:** This endpoint is typically used for bulk imports or manual entries. For new hires, use the `POST /api/auth/users/` endpoint to create both the User and Employee profile simultaneously.

### 4. Update Employee
`PATCH /api/employees/{id}/` (Admin only)

### 5. Get My Profile
`GET /api/employees/me/`

Returns logged-in user's employee profile

### 6. Get Subordinates
`GET /api/employees/{id}/subordinates/`

Returns all employees reporting to this employee

### 7. Add Emergency Contact
`POST /api/employees/{id}/emergency-contacts/`

### 8. Add Education
`POST /api/employees/{id}/educations/`

### 9. Add Work History
`POST /api/employees/{id}/work-histories/`

## Models

### Employee
- Personal: name, DOB, gender, blood group
- Contact: email, phone, address
- Employment: employee_id, department, designation, joining_date
- Documents: PAN, Aadhar, passport
- Banking: account details

### EmergencyContact
- name, relationship, phone, email
- is_primary flag

### Education
- degree, institution, field_of_study
- start_date, end_date, grade

### WorkHistory
- company_name, job_title
- start_date, end_date
- responsibilities, last_salary

## Summary
Complete employee lifecycle management from onboarding to exit! 👥
