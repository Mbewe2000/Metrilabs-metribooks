# Services Module

The Services module is a comprehensive Django application that provides service management capabilities for businesses. It enables users to define services, manage workers, track service records, and monitor performance metrics with complete user isolation and security.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Models](#models)
- [API Endpoints](#api-endpoints)
- [Authentication & Security](#authentication--security)
- [Testing](#testing)
- [Installation & Setup](#installation--setup)
- [Usage Examples](#usage-examples)
- [Performance & Analytics](#performance--analytics)

## Overview

The Services module supports various business types including:
- **Service Providers**: Hair salons, cleaning services, repair shops
- **Consultancies**: Legal, accounting, IT consulting
- **Labor Services**: Construction, handyman, delivery services
- **Professional Services**: Photography, design, tutoring

## Features

### Core Functionality
- ✅ **Service Management**: Create and manage different types of services with flexible pricing
- ✅ **Worker Management**: Track employees, contractors, and their service assignments
- ✅ **Service Records**: Log completed services with time tracking and payment status
- ✅ **Performance Analytics**: Monitor worker performance and business metrics
- ✅ **User Isolation**: Complete data separation between different businesses
- ✅ **Payment Tracking**: Track pending, partial, and completed payments

### Pricing Models
- **Hourly Rate**: Services charged by the hour
- **Fixed Price**: One-time fee services
- **Hybrid**: Services that can be charged either way

### Security Features
- JWT token authentication
- Rate limiting on API endpoints
- User data isolation
- Comprehensive error handling
- Audit logging

## Models

### ServiceCategory
Global categories for organizing services.
```python
- name: Category name (unique)
- description: Optional description
- created_at: Timestamp
```

### Service
User-specific service definitions.
```python
- user: Foreign key to User (isolated per user)
- name: Service name (unique per user)
- description: Optional service description
- category: Foreign key to ServiceCategory
- pricing_type: 'hourly', 'fixed', or 'both'
- hourly_rate: Decimal field for hourly services
- fixed_price: Decimal field for fixed services
- estimated_hours: Expected duration
- is_active: Service availability status
```

### Worker
Employee/contractor management.
```python
- user: Foreign key to User (isolated per user)
- name: Worker name (unique per user)
- email: Optional contact email
- phone: Optional contact phone
- role: Worker role/title
- hourly_rate: Worker's hourly rate
- is_owner: Boolean for business owner
- is_active: Worker availability status
- services: Many-to-many with Service
```

### ServiceRecord
Individual service transaction records.
```python
- user: Foreign key to User (isolated per user)
- service: Foreign key to Service
- worker: Foreign key to Worker
- client_name: Customer name
- client_contact: Customer contact info
- start_time: Service start timestamp
- end_time: Service completion timestamp
- hours_worked: Auto-calculated duration
- hourly_rate_used: Rate applied for this service
- fixed_price_used: Fixed amount charged
- total_amount: Auto-calculated total
- payment_status: 'pending', 'partial', 'completed'
- amount_paid: Amount received
- notes: Additional service notes
```

### WorkerPerformance
Performance tracking and analytics.
```python
- user: Foreign key to User
- worker: Foreign key to Worker
- month: Performance month
- year: Performance year
- services_completed: Number of services
- total_hours: Total hours worked
- total_revenue: Total revenue generated
- average_rating: Customer satisfaction
```

## API Endpoints

All endpoints require JWT authentication and follow RESTful conventions.

### Service Categories
```
GET /api/services/categories/          # List all categories
```

### Service Management
```
GET    /api/services/services/         # List user's services
POST   /api/services/services/create/  # Create new service
GET    /api/services/services/{id}/    # Get service details
PUT    /api/services/services/{id}/    # Update service
DELETE /api/services/services/{id}/    # Delete service
```

### Worker Management
```
GET    /api/services/workers/          # List user's workers
POST   /api/services/workers/create/   # Create new worker
GET    /api/services/workers/{id}/     # Get worker details
PUT    /api/services/workers/{id}/     # Update worker
DELETE /api/services/workers/{id}/     # Delete worker
```

### Service Records
```
GET    /api/services/records/          # List user's service records
POST   /api/services/records/create/   # Create new record
GET    /api/services/records/{id}/     # Get record details
PUT    /api/services/records/{id}/     # Update record
DELETE /api/services/records/{id}/     # Delete record
```

### Payment Management
```
POST /api/services/records/{id}/update-payment/  # Update payment status
```

### Reports & Analytics
```
GET /api/services/dashboard/                # Dashboard summary
GET /api/services/reports/summary/          # Service records summary
GET /api/services/reports/performance/      # Worker performance report
```

## Authentication & Security

### JWT Authentication
All API endpoints require valid JWT tokens:
```http
Authorization: Bearer <your-jwt-token>
```

### Rate Limiting
- Service creation: 50 requests per hour per user
- Worker creation: 30 requests per hour per user
- Record creation: 100 requests per hour per user

### User Isolation
Every data model is isolated by user. Users can only access their own:
- Services
- Workers
- Service records
- Performance data

### Error Handling
Standardized error responses:
```json
{
    "success": false,
    "message": "Error description",
    "errors": ["Detailed error messages"]
}
```

## Testing

Comprehensive test suite with 29 tests covering:

### Model Tests (23 tests)
- Service category creation and constraints
- Service creation with different pricing models
- Worker management and service assignments
- Service record calculations and validations
- Performance metric generation
- Django signals testing
- User isolation verification

### API Tests (6 tests)
- Authentication and authorization
- CRUD operations for all endpoints
- User data isolation
- Dashboard functionality
- Security validation

### Running Tests
```bash
# Run all services tests
python manage.py test services

# Run only model tests
python manage.py test services.tests

# Run only API tests
python manage.py test services.test_api

# Run with verbose output
python manage.py test services -v 2
```

## Installation & Setup

### 1. Dependencies
Ensure these packages are installed:
```python
# In requirements.txt
django>=5.2.4
djangorestframework>=3.15.2
djangorestframework-simplejwt>=5.3.0
django-ratelimit>=4.1.0
```

### 2. Django Settings
Add to `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    # ... other apps
    'rest_framework',
    'rest_framework_simplejwt',
    'services',
]
```

### 3. URL Configuration
Include in main `urls.py`:
```python
urlpatterns = [
    # ... other patterns
    path('api/services/', include('services.urls')),
]
```

### 4. Database Migration
```bash
python manage.py makemigrations services
python manage.py migrate
```

### 5. Signal Setup
Signals are automatically configured to:
- Create default service categories for new users
- Update worker performance when service records change

## Usage Examples

### Creating a Service
```python
# POST /api/services/services/create/
{
    "name": "Haircut",
    "description": "Professional haircut service",
    "category": 1,
    "pricing_type": "both",
    "hourly_rate": "25.00",
    "fixed_price": "30.00",
    "estimated_hours": "1.00"
}
```

### Creating a Worker
```python
# POST /api/services/workers/create/
{
    "name": "John Smith",
    "email": "john@example.com",
    "phone": "+1234567890",
    "role": "Senior Stylist",
    "hourly_rate": "20.00",
    "is_owner": false,
    "services": [1, 2, 3]
}
```

### Recording a Service
```python
# POST /api/services/records/create/
{
    "service": 1,
    "worker": 1,
    "client_name": "Jane Doe",
    "client_contact": "jane@example.com",
    "start_time": "2025-07-23T10:00:00Z",
    "end_time": "2025-07-23T11:30:00Z",
    "hourly_rate_used": "25.00",
    "payment_status": "pending",
    "notes": "Customer requested styling tips"
}
```

### Query Parameters
Services list supports filtering:
```
GET /api/services/services/?category=beauty&is_active=true&search=haircut
```

## Performance & Analytics

### Dashboard Metrics
The dashboard endpoint provides:
- Total active services
- Total active workers
- Service records summary (today, this week, this month)
- Revenue totals and averages
- Top performing workers
- Payment status breakdown

### Worker Performance
Track individual worker metrics:
- Services completed per month
- Total hours worked
- Revenue generated
- Average customer ratings
- Performance trends

### Service Records Summary
Comprehensive reporting with filters:
- Date range filtering
- Payment status breakdown
- Revenue analysis
- Client activity tracking

## File Structure

```
services/
├── __init__.py
├── admin.py              # Django admin configuration
├── apps.py              # App configuration
├── models.py            # Data models
├── serializers.py       # DRF serializers
├── signals.py           # Django signals
├── tests.py             # Model tests
├── test_api.py          # API tests
├── urls.py              # URL routing
├── views.py             # API views
├── migrations/          # Database migrations
└── README.md            # This file
```

## Support & Contributing

For issues, feature requests, or contributions:
1. Check existing test coverage
2. Add tests for new features
3. Ensure all tests pass
4. Follow Django and DRF best practices
5. Maintain user isolation security

## License

This module is part of the MetriBooks project and follows the project's licensing terms.
