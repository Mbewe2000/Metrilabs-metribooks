# Services Module

A comprehensive Django app for managing services, work assignments, and employee performance tracking in the Metribooks system.

## Features

- **Service Management**: Define business services with hourly or fixed pricing
- **Service Categories**: Organize services into categories (Beauty, Labor, Consultancy, etc.)
- **Employee Assignment**: Assign services to employees or track owner work
- **Work Recording**: Record work hours, tasks, and automatically calculate payments
- **Performance Reports**: Generate summaries for employees and services
- **Integration**: Seamlessly connects with employees and accounting modules

## Models

### ServiceCategory
- `name`: Category name (e.g., "Beauty Services", "Labor", "Consultancy")
- `description`: Optional category description

### Service
- `name`: Service name (e.g., "Haircut", "Cleaning", "Delivery")
- `category`: Foreign key to ServiceCategory
- `pricing_type`: 'hourly' or 'fixed'
- `hourly_rate`: Rate per hour in ZMW (for hourly services)
- `fixed_price`: Fixed price in ZMW (for fixed-price services)
- `description`: Optional service description
- `is_active`: Whether service is currently offered

### WorkRecord
- `worker_type`: 'employee' or 'owner'
- `employee`: Foreign key to Employee (if worker_type is 'employee')
- `owner_name`: Owner name (if worker_type is 'owner')
- `service`: Foreign key to Service
- `date_of_work`: Date when work was performed
- `hours_worked`: Hours worked (for hourly services)
- `quantity`: Number of services performed (for fixed-price services)
- `total_amount`: Auto-calculated total payment
- `notes`: Optional work notes

## API Endpoints

### Service Categories
**Base URL: `/api/services/categories/`**
- `GET /categories/` - List all categories
- `POST /categories/` - Create new category
- `GET /categories/{id}/` - Get category details
- `PUT/PATCH /categories/{id}/` - Update category
- `DELETE /categories/{id}/` - Delete category

### Services
**Base URL: `/api/services/services/`**
- `GET /services/` - List all services
- `POST /services/` - Create new service
- `GET /services/{id}/` - Get service details
- `PUT/PATCH /services/{id}/` - Update service
- `DELETE /services/{id}/` - Delete service

#### Custom Service Endpoints
- `GET /services/active_services/` - Get all active services
- `GET /services/hourly_services/` - Get all hourly services
- `GET /services/fixed_price_services/` - Get all fixed-price services

### Work Records
**Base URL: `/api/services/work-records/`**
- `GET /work-records/` - List all work records
- `POST /work-records/` - Create new work record
- `GET /work-records/{id}/` - Get work record details
- `PUT/PATCH /work-records/{id}/` - Update work record
- `DELETE /work-records/{id}/` - Delete work record

#### Custom Work Record Endpoints
- `GET /work-records/today_records/` - Get today's work records
- `GET /work-records/this_week_records/` - Get this week's work records
- `GET /work-records/employee_summary/` - Get employee performance summary
- `GET /work-records/service_report/` - Get service performance report

## Query Parameters

### Services
- `search` - Search by service name or description
- `is_active` - Filter by active status (true/false)
- `pricing_type` - Filter by pricing type (hourly/fixed)
- `category` - Filter by category ID
- `ordering` - Order by name, created_at, hourly_rate, fixed_price

### Work Records
- `search` - Search by service name, employee name, owner name, or notes
- `worker_type` - Filter by worker type (employee/owner)
- `employee` - Filter by employee ID
- `service` - Filter by service ID
- `start_date` - Filter by start date (YYYY-MM-DD)
- `end_date` - Filter by end date (YYYY-MM-DD)
- `ordering` - Order by date_of_work, total_amount, created_at

## Usage Examples

### Create Service Category
```json
POST /api/services/categories/
{
    "name": "Beauty Services",
    "description": "Hair, nails, and beauty treatments"
}
```

### Create Hourly Service
```json
POST /api/services/services/
{
    "name": "Hair Washing",
    "category": 1,
    "pricing_type": "hourly",
    "hourly_rate": "25.00",
    "description": "Professional hair washing service"
}
```

### Create Fixed-Price Service
```json
POST /api/services/services/
{
    "name": "Haircut",
    "category": 1,
    "pricing_type": "fixed",
    "fixed_price": "50.00",
    "description": "Standard haircut service"
}
```

### Record Employee Work (Hourly)
```json
POST /api/services/work-records/
{
    "worker_type": "employee",
    "employee": 1,
    "service": 1,
    "date_of_work": "2025-07-23",
    "hours_worked": "3.5",
    "notes": "Regular cleaning service"
}
```

### Record Owner Work (Fixed Price)
```json
POST /api/services/work-records/
{
    "worker_type": "owner",
    "owner_name": "Business Owner",
    "service": 2,
    "date_of_work": "2025-07-23",
    "quantity": 2,
    "notes": "Performed 2 haircuts"
}
```

### Get Employee Summary
```
GET /api/services/work-records/employee_summary/?start_date=2025-07-01&end_date=2025-07-31
```

### Get Service Report
```
GET /api/services/work-records/service_report/?start_date=2025-07-01&end_date=2025-07-31
```

## Integration Points

### With Employees Module
- **Foreign Key Relationship**: `WorkRecord.employee -> Employee`
- **Employee Assignment**: Services can be assigned to specific employees
- **Performance Tracking**: Track which employees perform which services

### With Accounting Module (Future)
- **Expense Integration**: Work records can be linked to expense entries
- **Payroll Processing**: Employee work hours can feed into payroll calculations
- **Revenue Tracking**: Service income can be categorized and tracked
- **Cost Analysis**: Compare service revenue vs. employee costs

### With Future Modules
- **Customer Management**: Link work records to specific customers
- **Inventory**: Track materials used in services
- **Scheduling**: Integration with appointment/booking systems

## Reports & Analytics

### Employee Performance Summary
- Total hours worked
- Total earnings
- Number of tasks completed
- Services performed
- Date range filtering

### Service Performance Report
- Total revenue per service
- Number of tasks completed
- Total hours (for hourly services)
- Average revenue per task
- Service popularity ranking

## Installation

1. Add 'services' to INSTALLED_APPS in settings.py
2. Add URL pattern to main urls.py: `path('api/services/', include('services.urls'))`
3. Run migrations: `python manage.py makemigrations services && python manage.py migrate`
4. Ensure 'employees' app is installed and migrated first

## Admin Interface

All models are registered with Django admin:
- **ServiceCategory**: Basic category management
- **Service**: Comprehensive service management with pricing controls
- **WorkRecord**: Work record management with calculated totals and worker information

## Business Use Cases

### Beauty Salon
- Services: Haircut (ZMW 50), Manicure (ZMW 30), Hair Washing (ZMW 25/hour)
- Employees: Hair stylists, nail technicians
- Tracking: Daily services performed, employee earnings

### Cleaning Service
- Services: House Cleaning (ZMW 40/hour), Office Cleaning (ZMW 35/hour)
- Employees: Cleaning staff
- Tracking: Hours worked per location, total earnings

### Tailoring Shop
- Services: Shirt Tailoring (ZMW 80), Dress Making (ZMW 150), Alterations (ZMW 30/hour)
- Mixed: Owner and employee work
- Tracking: Pieces completed, time spent on custom work
