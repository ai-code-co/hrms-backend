# Payroll Module

The Payroll module manages employee salary structures, generates monthly payslips, and handles payroll-related configurations. It is synchronized with the Holidays and Leaves modules to account for working days and unpaid leaves.

## Models

### 1. SalaryStructure
Defines the components of an employee's monthly salary.
- **Fields**: Basic Salary, HRA, Medical Allowance, Conveyance Allowance, Special Allowance, EPF, TDS, etc.

### 2. Payslip
Stores historical records of generated monthly payments.
- **Fields**: Monthly breakdown of earnings, deductions, net salary, and attendance summary.

### 3. PayrollConfig
Generic key-value store for HR/Payroll settings (e.g., late day limits, Restricted Holiday rules).

## API Endpoints

### 1. Get User Salary Info
Returns the current salary structure and payslip history for the authenticated user.
- **Endpoint**: `GET /api/payroll/user-salary-info/`
- **Response Structure**:
```json
{
  "error": 0,
  "data": {
    "id": "695",
    "name": "Medhavi",
    "email": "medhavi@example.com",
    "salary_details": [...],
    "payslip_history": [...]
  }
}
```

### 2. Get Generic Configuration
Returns HR configurations.
- **Endpoint**: `GET /api/payroll/generic-configuration/`
- **Response Structure**:
```json
{
  "error": false,
  "data": {
    "attendance_late_days": 4,
    "rh_config": {...}
  }
}
```

## Calculation Logic
The module synchronizes with:
- **Leaves**: Approved `Unpaid Leave` records result in salary deductions.
    - **Formula**: `Daily Rate = Gross Salary / Days in Month`
    - **Deduction**: `Unpaid Leaves * Daily Rate`
- **Holidays**: Public holidays are counted as paid days.
- **Designation/Level**: Can be used to determine components if needed.

## Testing Deductions
To test how leaves affect salary:
1. Apply and **approve** an "Unpaid Leave" for an employee in the Admin panel.
2. Call the `GET /api/payroll/user-salary-info/` API.
3. Observe the `current_month_preview` object in the response. It will show the updated `net_salary` and the `unpaid_leave_deduction` details.
