# Leaves Module - API Documentation

## Overview
The Leaves module provides a complete leave management system for the HRMS application. It includes day calculation, leave application, and document upload functionality.

---

## Features

✅ **Working Day Calculator** - Automatically calculates working days, weekends, and holidays  
✅ **Leave Application** - Submit and manage leave requests  
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

## Data Models

### Leave Model

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Primary key |
| `employee` | ForeignKey | Reference to User |
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

---

## Admin Interface

Access the admin panel at `/admin/` to:
- View all leave requests
- Filter by status, leave type, or date
- Search by employee name or email
- Approve/reject leave requests
- Add rejection reasons

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
    FOREIGN KEY (employee_id) REFERENCES auth_user(id)
);
```

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
