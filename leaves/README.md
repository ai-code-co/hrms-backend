# Leaves Module - API Documentation

## Overview
The Leaves module provides a complete leave management system for the HRMS application. It includes day calculation, leave application, document upload functionality, and **comprehensive leave balance tracking**.

---

## Features

✅ **Working Day Calculator** - Automatically calculates working days, weekends, and holidays  
✅ **Leave Application** - Submit and manage leave requests  
✅ **Leave Balance Tracking** - Real-time balance validation and tracking  
✅ **Admin-Controlled Quotas** - HR sets monthly/yearly leave allocations  
✅ **Restricted Holidays (RH)** - Separate RH quota and tracking  
✅ **Carry Forward Support** - Unused leaves can be carried to next year  
✅ **Auto-Balance Updates** - Balance updates on approval/rejection  
✅ **Document Upload** - Attach supporting documents to leave requests  
✅ **Holiday Integration** - Integrates with the existing Holiday system  
✅ **JWT Authentication** - Secure, token-based authentication  
✅ **Admin Interface** - Full CRUD operations in Django Admin  

---

## API Endpoints

### Base URL
```
/api/leaves/
```

### Authentication
All endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

---

## 🛠 Testing with Swagger

For a step-by-step guide on how to authenticate and test these APIs using the Swagger UI, see the [Leaves API Testing Guide](file:///Users/medhavi/.gemini/antigravity/brain/7be0fa9d-509b-445c-a995-bb82f74f9db5/leaves_api_testing_guide.md).

---

## Endpoint Details

### 1. Calculate Working Days

**Endpoint:** `POST /api/leaves/`  
**Action Field:** `get_days_between_leaves`

Calculate the number of working days, weekends, and holidays between two dates.

**Request:**
```json
{
  "action": "get_days_between_leaves",
  "start_date": "2025-12-22",
  "end_date": "2025-12-30",
  "token": "<jwt_token>"
}
```

**Response:**
```json
{
  "error": 0,
  "data": {
    "start_date": "2025-12-22",
    "end_date": "2025-12-30",
    "working_days": 5,
    "holidays": 1,
    "weekends": 2,
    "days": [
      {
        "type": "weekend",
        "sub_type": "Sunday",
        "sub_sub_type": "",
        "full_date": "2025-12-22"
      },
      {
        "type": "working",
        "sub_type": "",
        "sub_sub_type": "",
        "full_date": "2025-12-23"
      }
    ],
    "message": ""
  }
}
```

**Alternative REST Endpoint:**
```
POST /api/leaves/calculate-days/
```

---

### 2. Apply for Leave

**Endpoint:** `POST /api/leaves/`  
**Action Field:** `apply_leave`

Submit a new leave request.

**Request:**
```json
{
  "action": "apply_leave",
  "from_date": "2025-12-22",
  "to_date": "2025-12-30",
  "no_of_days": 7,
  "reason": "out of town",
  "day_status": "",
  "leave_type": "Casual Leave",
  "late_reason": "",
  "doc_link": "",
  "rh_dates": [],
  "token": "<jwt_token>"
}
```

**Response:**
```json
{
  "error": 0,
  "data": {
    "message": "Leave applied.",
    "leave_id": 1
  }
}
```

**Alternative REST Endpoint:**
```
POST /api/leaves/submit-leave/
```

---

### 3. Upload Document

**Endpoint:** `POST /api/leaves/upload-doc/`  
**Content-Type:** `multipart/form-data`

Upload a supporting document for a leave request.

**Request:**
```
POST /api/leaves/upload-doc/
Content-Type: multipart/form-data

file: <file_object>
document_type: leave_doc
token: <jwt_token>
```

**Response:**
```json
{
  "error": 0,
  "message": "Uploaded successfully!!"
}
```

---

### 4. List User's Leaves

**Endpoint:** `GET /api/leaves/`

Retrieve all leave requests for the authenticated user.

**Response:**
```json
[
  {
    "id": 1,
    "from_date": "2025-12-22",
    "to_date": "2025-12-30",
    "no_of_days": 7.0,
    "reason": "out of town",
    "leave_type": "Casual Leave",
    "status": "Pending",
    "day_status": "",
    "late_reason": null,
    "doc_link": null,
    "rejection_reason": null,
    "created_at": "2025-12-21T14:30:00Z"
  }
]
```

---

### 5. Get Specific Leave

**Endpoint:** `GET /api/leaves/{id}/`

Retrieve details of a specific leave request.

---

### 6. Update Leave

**Endpoint:** `PUT /api/leaves/{id}/` or `PATCH /api/leaves/{id}/`

Update an existing leave request (if status is still Pending).

---

### 7. Delete Leave

**Endpoint:** `DELETE /api/leaves/{id}/`

Delete a leave request (if status is still Pending).

---

### 8. Get Leave Balance

**Endpoint:** `GET /api/leaves/balance/`

Retrieve current leave balance for the authenticated user.

**Response:**
```json
{
  "error": 0,
  "data": {
    "Casual Leave": {
      "allocated": 12.0,
      "used": 3.0,
      "pending": 1.0,
      "available": 8.0,
      "carried_forward": 2.0
    },
    "Sick Leave": {
      "allocated": 10.0,
      "used": 1.0,
      "pending": 0.0,
      "available": 9.0,
      "carried_forward": 0.0
    },
    "rh": {
      "allocated": 2,
      "used": 0,
      "available": 2
    }
  }
}
```

**Error Response (No Balance Configured):**
```json
{
  "error": 1,
  "message": "No leave balance configured. Please contact HR."
}
```

---

## Data Models

### Leave Model

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Primary key |
| `employee` | ForeignKey | Reference to Employee (not User) |
| `leave_type` | String | Type of leave (Casual, Sick, etc.) |
| `from_date` | Date | Start date |
| `to_date` | Date | End date |
| `no_of_days` | Decimal | Number of days |
| `reason` | Text | Reason for leave |
| `status` | String | Pending/Approved/Rejected/Cancelled |
| `day_status` | String | First Half/Second Half (optional) |
| `late_reason` | Text | Reason if applied late (optional) |
| `doc_link` | File | Supporting document (optional) |
| `rejection_reason` | Text | Reason if rejected (optional) |
| `rh_dates` | JSON | Restricted Holiday dates |
| `created_at` | DateTime | Creation timestamp |
| `updated_at` | DateTime | Last update timestamp |

> **Note:** As of 2025-12-22, Leave is connected to the `Employee` model, not directly to `User`. Users must have an employee profile to apply for leaves.

### Leave Types
- Casual Leave
- Sick Leave
- Earned Leave
- Unpaid Leave
- Maternity Leave
- Paternity Leave
- Other

### Leave Status
- Pending (default)
- Approved
- Rejected
- Cancelled

---

### LeaveQuota Model

Defines leave quotas configured by admin for each employee.

| Field | Type | Description |
|-------|------|-------------|
| `employee` | ForeignKey | Reference to Employee |
| `leave_type` | String | Type of leave |
| `monthly_quota` | Decimal | Leaves per month |
| `yearly_quota` | Decimal | Total leaves per year |
| `rh_quota` | Integer | Restricted Holidays allowed |
| `carry_forward_limit` | Decimal | Max leaves to carry forward |
| `effective_from` | Date | Quota start date |
| `effective_to` | Date | Quota end date (optional) |

### LeaveBalance Model

Tracks current leave balance for each employee per year.

| Field | Type | Description |
|-------|------|-------------|
| `employee` | ForeignKey | Reference to Employee |
| `leave_type` | String | Type of leave |
| `year` | Integer | Fiscal year |
| `total_allocated` | Decimal | Total quota + carry forward |
| `carried_forward` | Decimal | Leaves from previous year |
| `used` | Decimal | Approved leaves taken |
| `pending` | Decimal | Leaves pending approval |
| `available` | Decimal (computed) | Remaining balance |
| `rh_allocated` | Integer | RH days allocated |
| `rh_used` | Integer | RH days used |
| `rh_available` | Integer (computed) | RH days remaining |

### RestrictedHoliday Model

Defines available Restricted Holiday dates.

| Field | Type | Description |
|-------|------|-------------|
| `date` | Date | RH date |
| `name` | String | Holiday name |
| `description` | Text | Additional details |
| `is_active` | Boolean | Whether RH is available |

---

## Usage Examples

### Python (requests)

```python
import requests

BASE_URL = "http://localhost:8000/api/leaves/"
TOKEN = "your_jwt_token_here"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Calculate days
response = requests.post(BASE_URL, json={
    "action": "get_days_between_leaves",
    "start_date": "2025-12-22",
    "end_date": "2025-12-30"
}, headers=headers)

print(response.json())

# Apply for leave
response = requests.post(BASE_URL, json={
    "action": "apply_leave",
    "from_date": "2025-12-22",
    "to_date": "2025-12-30",
    "no_of_days": 7,
    "reason": "Personal work",
    "leave_type": "Casual Leave",
    "rh_dates": []
}, headers=headers)

print(response.json())
```

### cURL

```bash
# Calculate days
curl -X POST http://localhost:8000/api/leaves/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "get_days_between_leaves",
    "start_date": "2025-12-22",
    "end_date": "2025-12-30"
  }'

# Apply for leave
curl -X POST http://localhost:8000/api/leaves/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "apply_leave",
    "from_date": "2025-12-22",
    "to_date": "2025-12-30",
    "no_of_days": 7,
    "reason": "out of town",
    "leave_type": "Casual Leave",
    "rh_dates": []
  }'
```

---

## Business Logic

### Working Day Calculation
1. Iterates through each day between start and end dates
2. Checks if day is a weekend (Saturday=5, Sunday=6)
3. Checks if day is a holiday (queries Holiday model)
4. Categorizes each day as: working, weekend, or holiday
5. Returns detailed breakdown with counts

### Weekend Detection
- Saturday: `weekday() == 5`
- Sunday: `weekday() == 6`

### Holiday Integration
- Queries `Holiday` model for active holidays in date range
- Filters by `is_active=True`
- Checks `date` field against each day

### Leave Balance Validation
**On Leave Application:**
1. Check if employee has leave quota configured
2. Verify available balance >= requested days
3. If RH dates provided, check RH quota
4. Reject if insufficient balance

**On Leave Approval:**
1. Move days from `pending` to `used`
2. Deduct RH days if applicable
3. Update balance in real-time

**On Leave Rejection:**
1. Remove days from `pending`
2. Return balance to available pool

**On Leave Cancellation:**
1. Reverse `used` days
2. Return RH days if applicable

### Carry Forward Logic
- Unused leaves at year-end can be carried forward
- Maximum carry forward defined in `LeaveQuota.carry_forward_limit`
- Carried forward leaves added to next year's `total_allocated`

---

## Admin Interface

Access the admin panel at `/admin/` to:

### Leave Management
- View all leave requests
- Filter by status, leave type, or date
- Search by employee name or email
- Approve/reject leave requests
- Add rejection reasons

### Leave Quota Management
- Configure monthly/yearly quotas per employee
- Set RH allocations
- Define carry forward limits
- Set effective date ranges
- Bulk quota setup for multiple employees

### Leave Balance Tracking
- View current balances for all employees
- Filter by year and leave type
- Monitor usage and availability
- Read-only (auto-calculated)
- Export to CSV for reports

### Restricted Holiday Management
- Add/edit RH dates
- Mark RH as active/inactive
- View RH usage across employees

---

## Database Schema

```sql
CREATE TABLE leaves_leave (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    employee_id BIGINT NOT NULL,
    leave_type VARCHAR(50) NOT NULL,
    from_date DATE NOT NULL,
    to_date DATE NOT NULL,
    no_of_days DECIMAL(5,1) DEFAULT 1.0,
    reason TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'Pending',
    day_status VARCHAR(50),
    late_reason TEXT,
    doc_link VARCHAR(100),
    rejection_reason TEXT,
    rh_dates JSON,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES employees_employee(id)
);
```

> **Note:** Foreign key now references `employees_employee` table instead of `auth_app_user`.

---

## Testing

### Run Tests
```bash
python manage.py test leaves
```

### Verify Installation
```bash
python verify_leaves.py
```

Expected output:
```
✅ Model OK
✅ Database OK
✅ Holiday Integration OK
✅ URLs OK
```

---

## Deployment

### Local Development
```bash
# Run migrations
python manage.py migrate

# Start server
python manage.py runserver

# Access Swagger docs
http://localhost:8000/swagger/
```

### Production (Render)
```bash
# Commit changes
git add leaves/ config/settings.py config/urls.py
git commit -m "feat: implement leaves module"
git push origin feat/leaves

# Merge to deploy branch
git checkout feat/deploy-server
git merge feat/leaves
git push origin feat/deploy-server
```

Migrations will run automatically via the Start Command:
```bash
python manage.py migrate && gunicorn config.wsgi:application
```

---

## Error Handling

### Common Errors

**401 Unauthorized**
```json
{
  "detail": "Authentication credentials were not provided."
}
```
**Solution:** Include valid JWT token in Authorization header

**400 Bad Request**
```json
{
  "error": 1,
  "message": "start_date and end_date are required"
}
```
**Solution:** Provide all required fields

**400 Validation Error**
```json
{
  "error": 1,
  "message": "Validation failed",
  "errors": {
    "from_date": ["This field is required."]
  }
}
```
**Solution:** Check request payload against model schema

---

## Security

- ✅ JWT authentication required on all endpoints
- ✅ Users can only view/modify their own leaves
- ✅ File uploads validated and stored securely
- ✅ SQL injection protection via Django ORM
- ✅ CSRF protection enabled

---

## Performance

- Database queries optimized with `select_related()` and `prefetch_related()`
- Pagination enabled (20 items per page)
- Indexes on frequently queried fields
- Efficient date range queries

---

## Support

For issues or questions:
1. Check the verification report: `leaves_verification.md`
2. Review the implementation plan: `implementation_plan.md`
3. Test with the verification script: `verify_leaves.py`

---

## Version History

**v1.0.0** (2025-12-21)
- Initial release
- Working day calculator
- Leave application system
- Document upload
- Admin interface
- Full REST API support
- Action-based dispatch for legacy compatibility
