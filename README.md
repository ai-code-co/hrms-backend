# 🧑‍💼 HRMS — Human Resource Management System  
### Built with Django · Multi-tenant · Slack Integration

This project is a modular Human Resource Management System (HRMS) built using **Django**. It supports **Multi-tenancy**, allowing multiple organizations to manage their HR operations independently within the same system, including per-company Slack notification workflows.

---

## 🚀 Features

### ✅ Core Features
- **Multi-tenant Support**: Manage multiple companies/organizations independently.
- **Employee Management**: Comprehensive profiles with document tracking.
- **Dynamic Attributes**: Flexible data modeling.
- **Attendance Management**: Check-in/out tracking with automatic Slack alerts.
- **Leave & Timesheet Management**: Interactive Slack-based approval workflows.
- **Payroll**: Automated payslip generation and distribution.

### 🔔 Slack Integration (Multi-tenant)
- **Automatic Notifications**: Real-time alerts for leave, attendance, and payroll.
- **Interactive Actions**: Approve or reject requests directly from Slack.
- **Event-based Logging**: Update attendance via Slack keywords (e.g., `#standup`).
- **Dynamic Configuration**: Configure Slack tokens and channels per organization in the Admin panel.

---

## 🏗️ Tech Stack

| Component | Technology |
|----------|------------|
| Backend | Django 6.0 |
| REST API | Django REST Framework (DRF) |
| Slack SDK | slack-sdk |
| Admin UI | Jet Theme |
| Database | MySQL / TiDB / SQLite |
| Environment | Python 3.13+ |

---

## 📦 Project Structure

```text
HRMS/
│── organizations/  # Multi-tenancy Management
│── employees/      # Employee profiles & Company mapping
│── attendance/     # Attendance tracking & Timesheets
│── leaves/         # Leave management logic
│── payroll/        # Salary & Payslip generation
│── notifications/  # Slack Service & Webhook handlers
│── auth_app/       # Custom User model & Auth logic
│── config/         # System settings
```

## 🛠️ Installation

### 1️⃣ Clone the Repository

```bash
git clone <your-repo-url>
cd HRMS
```

### 2️⃣ Set up Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate   # macOS/Linux
# venv\Scripts\activate    # Windows
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Environment Setup
Create a `.env` file from the provided template and configure your database and Slack credentials.

### 5️⃣ Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6️⃣ Run Server
```bash
python manage.py runserver
```

### 7️⃣ Initial Setup
1. Create a Superuser: `python manage.py createsuperuser`
2. Visit the Admin Panel at [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
3. Create a **Company** record.
4. Add a **Slack Configuration** for that company.
5. Assign **Employees** to the company to enable notifications.