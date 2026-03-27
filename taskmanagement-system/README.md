# PayrollPro — Payroll Management System

A desktop payroll management system built with **Python** and **PyQt5**, using **SQLite** as the local database.

---

### Running the App

cd payroll_system
python main.py
```

---

## Project Structure

```
payroll_system/
├── main.py                        ← Entry point
├── payroll.db                     ← Auto-created SQLite database
├── attachments/                   ← Leave proof/attachment files
├── ui/
│   ├── login.ui
│   ├── admin_dashboard.ui
│   ├── employee_dashboard.ui
│   ├── add_employee.ui
│   ├── salary_manage.ui
│   ├── leave.ui
│   └── salary_report.ui
└── py/
    ├── database.py                ← DB setup & connection
    ├── login.py                   ← Login window
    ├── admin_dashboard.py         ← Admin main window
    ├── employee_dashboard.py      ← Employee main window
    ├── manage_employees.py        ← Employee CRUD
    ├── manage_salary.py           ← Salary management
    ├── leave_page.py              ← Leave requests
    ├── payslip_generator.py       ← Payslip generation & PDF export
    ├── salary_report.py           ← Salary reports & CSV export
    └── confirm_dialog.py          ← Reusable confirmation dialog
```

---

## Default Login Credentials

### Admin Account
| Field    | Value      |
|----------|------------|
| Role     | Admin      |
| Username | `admin`    |
| Password | `admin123` |

### Employee Accounts
Employee accounts are **auto-created** when an employee is added.

| Field    | Format                                     | Example   |
|----------|--------------------------------------------|-----------|
| Role     | Employee                                   |           |
| Username | `emp_id` in lowercase                      | `emp0042` |
| Password | `firstname` (lowercase) + last 4 of emp_id | `juan0042`|

---

## Database Tables

| Table            | Description                            |
|------------------|----------------------------------------|
| `employees`      | Employee personal and job information  |
| `users`          | Login credentials (admin + employees)  |
| `salary`         | Salary records per employee            |
| `payslips`       | Generated payslip records              |
| `leave_requests` | Leave applications with status         |

---

## Reset the Records
cd ~/Desktop/payroll_system
rm py/payroll.db
python main.py
