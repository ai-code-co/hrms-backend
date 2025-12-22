# Inventory Module 📦

## What is this?

The **Inventory Module** manages company assets and equipment:
- Laptops, monitors, keyboards
- Office furniture
- Mobile phones
- Other equipment

## Why do we need it?

- **Asset Tracking** - Know what assets company owns
- **Assignment** - Track who has what equipment
- **Maintenance** - Schedule and track repairs
- **Accountability** - Employees responsible for assigned items
- **Auditing** - Generate asset reports

## API Endpoints

### Base URL: `/api/inventory/`

### 1. List Assets
`GET /api/inventory/`

**Query Parameters:**
- `category` - laptop, monitor, phone, furniture, etc.
- `status` - available, assigned, maintenance, retired
- `assigned_to` - Filter by employee
- `search` - Search by name, serial number

**Response:**
```json
[
  {
    "id": 1,
    "name": "MacBook Pro 16\"",
    "category": "laptop",
    "serial_number": "C02XG0FDH7JY",
    "status": "assigned",
    "assigned_to": {
      "id": 5,
      "name": "John Doe",
      "employee_id": "EMP001"
    },
    "assigned_date": "2025-01-15",
    "purchase_date": "2024-12-01",
    "purchase_price": 2500.00,
    "warranty_expiry": "2027-12-01"
  }
]
```

### 2. Get Asset Details
`GET /api/inventory/{id}/`

### 3. Create Asset
`POST /api/inventory/` (Admin only)

```json
{
  "name": "Dell Monitor 27\"",
  "category": "monitor",
  "serial_number": "MON123456",
  "purchase_date": "2025-01-10",
  "purchase_price": 350.00,
  "warranty_expiry": "2028-01-10",
  "status": "available"
}
```

### 4. Assign Asset
`POST /api/inventory/{id}/assign/`

```json
{
  "employee_id": 10,
  "assigned_date": "2025-01-20",
  "notes": "Issued for remote work"
}
```

### 5. Return Asset
`POST /api/inventory/{id}/return/`

```json
{
  "return_date": "2025-06-15",
  "condition": "good",
  "notes": "Returned in good condition"
}
```

### 6. Mark for Maintenance
`POST /api/inventory/{id}/maintenance/`

### 7. Retire Asset
`POST /api/inventory/{id}/retire/`

## Asset Categories

- **Electronics**: laptop, desktop, monitor, keyboard, mouse, phone
- **Furniture**: desk, chair, cabinet
- **Accessories**: headphones, webcam, docking station
- **Other**: Any other equipment

## Asset Status

- **Available** - Ready to assign
- **Assigned** - Currently with an employee
- **Maintenance** - Under repair
- **Retired** - No longer in use

## Features

### Assignment History
Track complete lifecycle:
- Who had the asset
- When it was assigned/returned
- Condition at return

### Maintenance Tracking
- Schedule maintenance
- Track repair costs
- Maintenance history

### Depreciation
- Calculate asset value over time
- Generate depreciation reports

## Summary
Complete asset lifecycle management from purchase to retirement! 📦
