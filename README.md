 # 🧑‍💼 HRMS — Human Resource Management System  
### Built with Django · EAV Model · Custom Admin (Jazzmin)

This project is a modular Human Resource Management System (HRMS) built using **Django** and the **Entity–Attribute–Value (EAV)** model.  
It provides a flexible and scalable way to manage employee data, dynamic attributes, attendance, and more.

---

## 🚀 Features

### ✅ Core Features
- Employee Management  
- Dynamic Attributes using **EAV Model**  
- Custom Django Admin (Jet Theme)  
- Department & Role Management  
- Attendance Management  
- Login Authentication (Superuser / Staff)

### 🎨 UI Features
- Beautiful Jazzmin Admin Panel  
- Custom Fonts, Icons & Dashboard Layout  
- Dark/Light Mode Support  
- Reordered Menus & Navigation

---

## 🏗️ Tech Stack

| Component | Technology |
|----------|------------|
| Backend | Django 5.x |
| Admin UI | Jet |
| Database | SQLite (default) / PostgreSQL (optional) |
| Dynamic Attributes | django-eav2 |
| Environment | Python 3.10+ |

---

## 📦 Project Structure

HRMS_EAV/
│── hrms/ # Main Django project
│── employees/ # Employee app
│── attendance/ # Attendance app (optional)
│── templates/ # Custom templates (if needed)
│── static/ # Static files
│── venv/ # Virtual environment (ignored in Git)
│── manage.py
│── requirements.txt
│── README.md


## 🛠️ Installation

### 1️⃣ Clone the Repository

```bash
git clone <your-repo-url>
cd HRMS_EAV

### 1️⃣ Clone the Repository

python3 -m venv venv
source venv/bin/activate   # macOS/Linux
# venv\Scripts\activate    # Windows

3️⃣ Install Dependencies

pip install -r requirements.txt

4️⃣ Run Migrations
python manage.py makemigrations
python manage.py migrate

6️⃣ Run Server
python manage.py runserver

Visit the admin panel:

👉 http://127.0.0.1:8000/admin/