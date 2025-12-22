# Holidays Module 🎉

## What is this?

The **Holidays Module** manages company holidays and observances:
- Public holidays
- Company-specific holidays
- Restricted holidays (RH)
- Regional holidays

## Why do we need it?

- **Leave Calculation** - Exclude holidays when calculating working days
- **Planning** - Employees know when office is closed
- **Compliance** - Follow regional holiday calendars
- **Flexibility** - Manage different holiday sets for different locations

## API Endpoints

### Base URL: `/api/holidays/`

### 1. List Holidays
`GET /api/holidays/`

**Query Parameters:**
- `year` - Filter by year (e.g., 2025)
- `month` - Filter by month (1-12)
- `is_active` - Filter active holidays
- `holiday_type` - public, restricted, company

**Response:**
```json
[
  {
    "id": 1,
    "name": "New Year's Day",
    "date": "2025-01-01",
    "holiday_type": "public",
    "description": "New Year celebration",
    "is_active": true
  },
  {
    "id": 2,
    "name": "Diwali",
    "date": "2025-10-24",
    "holiday_type": "restricted",
    "description": "Festival of Lights",
    "is_active": true
  }
]
```

### 2. Get Holiday Details
`GET /api/holidays/{id}/`

### 3. Create Holiday
`POST /api/holidays/` (Admin only)

```json
{
  "name": "Independence Day",
  "date": "2025-08-15",
  "holiday_type": "public",
  "description": "National Holiday",
  "is_active": true
}
```

### 4. Update Holiday
`PATCH /api/holidays/{id}/` (Admin only)

### 5. Delete Holiday
`DELETE /api/holidays/{id}/` (Admin only)

### 6. Get Holidays by Year
`GET /api/holidays/?year=2025`

### 7. Get Upcoming Holidays
`GET /api/holidays/upcoming/`

Returns next 10 upcoming holidays

## Holiday Types

1. **Public Holidays** - Office closed for everyone
2. **Restricted Holidays (RH)** - Optional, employees can choose
3. **Company Holidays** - Company-specific observances
4. **Regional Holidays** - Location-specific

## Integration

Used by:
- **Leaves Module** - Calculate working days
- **Attendance Module** - Mark holiday attendance
- **Payroll Module** - Holiday pay calculations

## Summary
Centralized holiday management for accurate leave and attendance tracking! 🎉
