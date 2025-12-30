# Leave Document Upload - Path Storage Approach

## Overview
Documents are uploaded to Cloudinary and only the **path** is stored in the database. The backend constructs the full URL when returning data.

## Architecture

### Database Storage
```
doc_link: "hrms/uploads/abc123.jpg"
```

### API Response
```json
{
  "doc_link": "hrms/uploads/abc123.jpg",
  "doc_link_url": "https://res.cloudinary.com/dhlyvqdoi/image/upload/hrms/uploads/abc123.jpg"
}
```

## Benefits

1. **Service Portability**: Easy to switch cloud providers
2. **Smaller Database**: Stores only path, not full URL
3. **Environment Flexibility**: Different base URLs for dev/prod
4. **Clean Data**: Service-agnostic storage

## Usage

### Step 1: Upload Document
```bash
POST /auth/upload-image/
Content-Type: multipart/form-data

image: <file>
```

**Response:**
```json
{
  "success": true,
  "url": "https://res.cloudinary.com/dhlyvqdoi/image/upload/v1767069022/hrms/uploads/abc123.jpg",
  "public_id": "hrms/uploads/abc123.jpg"
}
```

### Step 2: Apply for Leave with Path
```bash
POST /api/leaves/
Content-Type: application/json

{
  "leave_type": "Sick Leave",
  "from_date": "2025-01-20",
  "to_date": "2025-01-22",
  "no_of_days": 3.0,
  "reason": "Medical treatment",
  "doc_link": "hrms/uploads/abc123.jpg"  ← Use public_id from Step 1
}
```

### Step 3: Get Leave Details
```bash
GET /api/leaves/{id}/
```

**Response:**
```json
{
  "id": 123,
  "doc_link": "hrms/uploads/abc123.jpg",
  "doc_link_url": "https://res.cloudinary.com/dhlyvqdoi/image/upload/hrms/uploads/abc123.jpg",
  ...
}
```

## Frontend Usage

```javascript
// 1. Upload document
const uploadDoc = async (file) => {
  const formData = new FormData();
  formData.append('image', file);
  
  const response = await fetch('/auth/upload-image/', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
  });
  
  const data = await response.json();
  return data.public_id;  // Return path, not full URL
};

// 2. Apply for leave
const applyLeave = async (leaveData, docFile) => {
  let docPath = null;
  if (docFile) {
    docPath = await uploadDoc(docFile);
  }
  
  const response = await fetch('/api/leaves/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      ...leaveData,
      doc_link: docPath  // Send path only
    })
  });
  
  return await response.json();
};

// 3. Display document
const displayLeave = (leave) => {
  if (leave.doc_link_url) {
    return <img src={leave.doc_link_url} />;  // Use full URL from backend
  }
};
```

## Migration to Different Service

### Update Environment Variable
```bash
# Change from Cloudinary to S3
CLOUDINARY_BASE_URL=https://your-bucket.s3.amazonaws.com
```

### Migrate Files
```bash
# Copy all files from Cloudinary to S3
# Paths remain the same: hrms/uploads/abc123.jpg
```

### No Database Changes Needed!
The paths in database stay the same, backend automatically constructs new URLs.

## Configuration

### Environment Variables
```bash
# .env
CLOUDINARY_BASE_URL=https://res.cloudinary.com/dhlyvqdoi/image/upload

# For different environments
# Dev: https://dev-cloudinary.com/...
# Prod: https://prod-cloudinary.com/...
```

### Default (Hardcoded)
If `CLOUDINARY_BASE_URL` is not set, defaults to:
```
https://res.cloudinary.com/dhlyvqdoi/image/upload
```
