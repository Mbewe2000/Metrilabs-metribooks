# Employees Module

A simple Django app for managing designated employees in the Metribooks system.

## Features

- Employee management with basic fields (ID, name, phone, employment type, pay)
- Support for both full-time and part-time employees
- RESTful API endpoints for CRUD operations
- Integration ready for services module (task assignment) and accounting module (expenses)
- Admin interface for easy management
- Search and filtering capabilities

## Models

### Employee
- `employee_id`: Unique identifier for the employee
- `employee_name`: Full name of the employee
- `phone_number`: Contact phone number with validation
- `employment_type`: Either 'full_time' or 'part_time'
- `pay`: Pay rate (hourly for part-time, salary for full-time)
- `is_active`: Whether the employee is currently active
- `date_hired`: Date when the employee was hired
- `created_at`/`updated_at`: Timestamp fields

## API Endpoints

### Base URL: `/api/employees/`

- `GET /employees/` - List all employees
- `POST /employees/` - Create a new employee
- `GET /employees/{id}/` - Get specific employee details
- `PUT /employees/{id}/` - Update employee (full update)
- `PATCH /employees/{id}/` - Partial update employee
- `DELETE /employees/{id}/` - Delete employee

### Custom Endpoints
- `GET /employees/active_employees/` - Get all active employees
- `GET /employees/full_time_employees/` - Get all full-time employees
- `GET /employees/part_time_employees/` - Get all part-time employees
- `PATCH /employees/{id}/activate/` - Activate an employee
- `PATCH /employees/{id}/deactivate/` - Deactivate an employee

## Query Parameters

- `search` - Search by employee_id, employee_name, or phone_number
- `employment_type` - Filter by employment type (full_time/part_time)
- `is_active` - Filter by active status (true/false)
- `ordering` - Order by employee_name, date_hired, or pay

## Usage Examples

### Create Employee
```json
POST /api/employees/
{
    "employee_id": "EMP001",
    "employee_name": "John Doe",
    "phone_number": "+1234567890",
    "employment_type": "full_time",
    "pay": 5000.00
}
```

### Search Employees
```
GET /api/employees/?search=john
GET /api/employees/?employment_type=part_time
GET /api/employees/?is_active=true
```

## Integration Points

### With Services Module (Future)
- Employees can be assigned to tasks/services
- Foreign key relationship: `Task.assigned_employee -> Employee`

### With Accounting Module
- Employee pay can be tracked as expenses
- Integration for payroll processing
- Expense categorization by employee

## Installation

1. Add 'employees' to INSTALLED_APPS in settings.py
2. Add URL pattern to main urls.py: `path('api/employees/', include('employees.urls'))`
3. Run migrations: `python manage.py makemigrations employees && python manage.py migrate`

## Admin Interface

The Employee model is registered with Django admin with:
- List view showing key fields
- Filtering by employment type, active status, and hire date
- Search functionality
- Organized fieldsets for better UX
