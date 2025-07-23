# 📚 Metribooks - Complete Business Management Platform

**Metribooks** is a comprehensive business management platform designed specifically for small to medium businesses in Zambia. It provides complete solutions for user management, customer profiles, inventory tracking, service management, sales processing, and financial accounting with built-in ZRA compliance.

## 🚀 Platform Overview

Metribooks is a Django-based platform that integrates multiple business modules into a unified system, enabling businesses to manage all aspects of their operations from a single dashboard.

### 🎯 Key Features

✅ **Multi-Tenant Architecture** - Complete data isolation between businesses  
✅ **ZRA Compliance** - Built-in Zambian tax calculations and reporting  
✅ **REST API** - Complete API coverage for web and mobile applications  
✅ **Real-time Integration** - Automatic data synchronization between modules  
✅ **Comprehensive Testing** - 95+ automated tests ensuring reliability  
✅ **Production Ready** - Scalable architecture with security best practices  

---

## 📦 Module Architecture

### 🔐 Authentication Module
**Complete user management and security system**

- **Custom User Model** - Email/phone authentication support
- **JWT Tokens** - Secure API authentication with refresh tokens
- **Role-Based Access** - Admin and user permission management
- **Security Features** - Rate limiting, blacklisting, and session management

**API Endpoints:** Registration, Login, Logout, Password Management, Profile Updates

### 👤 Profiles Module  
**Customer and business profile management**

- **Customer Profiles** - Complete customer information and history
- **Business Categories** - Industry classification and subcategories
- **Profile Analytics** - Customer insights and relationship tracking
- **Data Validation** - Comprehensive profile data integrity

**API Endpoints:** Profile CRUD, Customer Management, Business Classification

### 📦 Inventory Module
**Complete inventory and product management**

- **Product Management** - SKU tracking, categorization, and pricing
- **Stock Control** - Real-time inventory levels and reorder alerts
- **Stock Adjustments** - Manual adjustments with audit trails
- **Multi-Unit Support** - Various units of measurement (kg, liters, pieces, etc.)
- **Category Management** - Predefined product categories with custom options

**API Endpoints:** Products, Categories, Stock Levels, Stock Adjustments, Inventory Reports

### 🛠️ Services Module
**Service delivery and worker management**

- **Service Catalog** - Hourly services, contracts, and gig work
- **Worker Management** - Service provider profiles and specializations
- **Service Records** - Complete service delivery tracking
- **Performance Analytics** - Service metrics and worker performance
- **Scheduling System** - Service appointment and availability management

**API Endpoints:** Services, Workers, Service Records, Analytics, Scheduling

### 💰 Sales Module
**Complete sales processing and management**

- **Point of Sale** - Quick sale processing with receipt generation
- **Customer Integration** - Links to customer profiles and history
- **Inventory Integration** - Automatic stock reduction and validation
- **Payment Methods** - Cash, bank transfer, mobile money support
- **Sales Analytics** - Revenue tracking, product performance, customer insights
- **Receipt Management** - Digital receipts with customer delivery

**API Endpoints:** Sales Processing, Sales History, Analytics, Receipts, Customer Sales

### 🧮 Accounting Module
**Comprehensive financial management with ZRA compliance**

- **Income Tracking** - Automatic income recording from sales and services
- **Expense Management** - Manual expense entry with categorization and recurring tracking
- **Asset Management** - Asset tracking with depreciation calculations
- **ZRA Turnover Tax** - Full 2025 tax compliance (K1,000 threshold, 5% rate)
- **Financial Reports** - P&L statements, cash flow, tax reports, and dashboards
- **Multi-Tenant Security** - Complete financial data isolation

**API Endpoints:** Expenses, Assets, Income, Tax Records, Financial Reports, Dashboard

---

## 🏗️ Technical Architecture

### **Technology Stack**
- **Backend:** Django 5.2.4 with Django REST Framework
- **Database:** SQLite (development) / PostgreSQL (production ready)
- **Authentication:** JWT with djangorestframework-simplejwt
- **Testing:** Django TestCase with 95+ automated tests
- **Documentation:** Comprehensive API documentation per module

### **Integration Architecture**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Layer     │    │   Business      │
│   Applications  │◄──►│   (Django REST) │◄──►│   Logic Layer   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Database      │    │   Signal        │
                       │   Layer         │    │   Integration   │
                       └─────────────────┘    └─────────────────┘
```

### **Module Integration**
- **Sales → Accounting:** Automatic income recording and tax calculations
- **Services → Accounting:** Service revenue tracking and financial integration
- **Inventory → Sales:** Stock validation and automatic reductions
- **Profiles → All Modules:** Customer data integration across platform
- **Authentication → All Modules:** Secure access control and user isolation

---

## 🇿🇲 ZRA Compliance Features

### **2025 Turnover Tax Implementation**
- **Threshold:** K1,000 monthly tax-free allowance
- **Rate:** 5% on revenue exceeding threshold  
- **Annual Limit:** K5,000,000 annual turnover eligibility
- **Automatic Calculations:** Real-time tax calculations with sales integration
- **Compliance Reporting:** ZRA-ready tax reports and summaries

### **Tax Calculation Example**
```
Monthly Sales: K8,000
Tax-free Threshold: K1,000
Taxable Amount: K8,000 - K1,000 = K7,000
Turnover Tax: 5% × K7,000 = K350
```

---

## 🚀 Installation & Setup

### **Prerequisites**
- Python 3.8+
- Django 5.2.4
- Virtual environment (recommended)

### **Quick Start**

1. **Clone Repository**
   ```bash
   git clone https://github.com/Mbewe2000/Metrilabs-metribooks.git
   cd Metrilabs-metribooks/backend
   ```

2. **Setup Virtual Environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Database Setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create Superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start Development Server**
   ```bash
   python manage.py runserver
   ```

7. **Access Admin Panel**
   ```
   http://localhost:8000/admin/
   ```

---

## 📊 Testing & Quality Assurance

### **Test Coverage**
- **Authentication:** 16 tests - User registration, login, JWT tokens, security
- **Profiles:** 15 tests - Profile management, business categories, validation  
- **Inventory:** 15 tests - Products, stock control, adjustments, categories
- **Services:** 17 tests - Service management, workers, records, analytics
- **Sales:** 32 tests - Sales processing, integration, analytics, receipts
- **Accounting:** 19 tests - Financial management, ZRA compliance, integration

**Total: 95+ Tests | Status: ✅ All Passing**

### **Run Tests**
```bash
# Run all tests
python manage.py test

# Run specific module tests
python manage.py test authentication
python manage.py test accounting
python manage.py test sales

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

---

## 🔌 API Documentation

### **Base URL**
```
http://localhost:8000/api/
```

### **Authentication**
All API endpoints require JWT authentication:
```bash
# Get token
POST /api/auth/login/
{
    "email": "user@example.com",
    "password": "password"
}

# Use token in headers
Authorization: Bearer <access_token>
```

### **Module Endpoints**

#### **Authentication** (`/api/auth/`)
```
POST /register/          # User registration
POST /login/             # User login
POST /logout/            # User logout
PUT  /change-password/   # Change password
GET  /profile/           # Get user profile
```

#### **Profiles** (`/api/`)
```
GET    /profiles/        # List customer profiles
POST   /profiles/        # Create customer profile
GET    /profiles/{id}/   # Get specific profile
PUT    /profiles/{id}/   # Update profile
DELETE /profiles/{id}/   # Delete profile
```

#### **Inventory** (`/api/inventory/`)
```
GET    /products/        # List products
POST   /products/        # Create product
GET    /categories/      # List categories
POST   /products/{id}/adjust-stock/  # Adjust stock
GET    /dashboard/       # Inventory dashboard
```

#### **Services** (`/api/services/`)
```
GET    /services/        # List services
POST   /services/        # Create service
GET    /workers/         # List workers
GET    /records/         # Service records
GET    /dashboard/       # Services dashboard
```

#### **Sales** (`/api/sales/`)
```
GET    /sales/           # List sales
POST   /sales/create/    # Create sale
GET    /analytics/       # Sales analytics
GET    /dashboard/       # Sales dashboard
POST   /sales/{id}/receipt/  # Generate receipt
```

#### **Accounting** (`/api/accounting/`)
```
GET    /expenses/        # List expenses
POST   /expenses/        # Create expense
GET    /assets/          # List assets
GET    /reports/profit-loss/     # P&L report
GET    /reports/dashboard/       # Financial dashboard
GET    /turnover-tax/    # Tax calculations
```

---

## 🔒 Security Features

### **Authentication & Authorization**
- JWT-based authentication with refresh tokens
- Rate limiting on sensitive endpoints
- User session management and blacklisting
- Role-based access control

### **Data Protection**
- Multi-tenant data isolation
- SQL injection protection via Django ORM
- CORS configuration for secure frontend integration
- Input validation and sanitization

### **Financial Security**
- Complete audit trails for all financial transactions
- User-specific data encryption
- ZRA compliance with tamper-proof calculations
- Secure financial report generation

---

## 🌟 Business Benefits

### **For Small Businesses**
- **Complete Solution:** All business operations in one platform
- **Cost Effective:** Reduces need for multiple software subscriptions
- **ZRA Compliant:** Automatic tax calculations and reporting
- **Easy to Use:** Intuitive API design for custom frontend development

### **For Developers**
- **REST API First:** Complete API coverage for any frontend framework
- **Modular Design:** Each module can be used independently
- **Comprehensive Testing:** Production-ready with extensive test coverage
- **Documentation:** Complete API documentation and examples

### **For Zambian Market**
- **Local Compliance:** Built-in ZRA turnover tax calculations
- **Currency Support:** Zambian Kwacha (ZMW) native support
- **Business Categories:** Pre-configured for Zambian business types
- **Scalable:** Supports growth from small business to enterprise

---

## 🛠️ Development Roadmap

### **Current Status: Production Ready ✅**
All core modules implemented and tested with complete integration.

### **Future Enhancements**
- **Mobile App:** React Native mobile application
- **Advanced Reporting:** Balance sheets, cash flow statements
- **Multi-Currency:** USD and other currency support
- **Bank Integration:** Automatic transaction import
- **Invoice Generation:** PDF invoice creation
- **Backup & Recovery:** Automated backup systems

---

## 📞 Support & Documentation

### **Module Documentation**
Each module includes comprehensive README files:
- `authentication/README.md` - Authentication system guide
- `profiles/README.md` - Profile management guide  
- `inventory/README.md` - Inventory system guide
- `services/README.md` - Service management guide
- `sales/README.md` - Sales processing guide
- `accounting/README.md` - Financial management guide

### **API Testing**
Use the included test script for API validation:
```bash
python test_auth_api.py
```

### **Getting Help**
- Check module-specific README files for detailed documentation
- Review test files for usage examples
- Examine admin interface for data management examples

---

## 📄 License

This project is developed by Metrilabs for business management solutions in Zambia.

---

## 🏆 Project Stats

- **Lines of Code:** 10,000+
- **Test Coverage:** 95+ tests
- **Modules:** 6 integrated modules
- **API Endpoints:** 50+ endpoints
- **Documentation:** Complete API and user guides
- **Status:** Production Ready ✅

**Metribooks - Empowering Zambian Businesses with Complete Digital Solutions** 🇿🇲
    "email": "user@example.com",
    "phone": "+1234567890",
    "password": "securepassword123",
    "password_confirm": "securepassword123",
    "first_name": "John",
    "last_name": "Doe"
}

response = requests.post("http://localhost:8000/api/auth/register/", json=data)
```

### Login
```python
# Login with email
data = {
    "email_or_phone": "user@example.com",
    "password": "securepassword123"
}

# Or login with phone
data = {
    "email_or_phone": "+1234567890",
    "password": "securepassword123"
}

response = requests.post("http://localhost:8000/api/auth/login/", json=data)
tokens = response.json()["tokens"]
```

### Authenticated Requests
```python
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get("http://localhost:8000/api/auth/profile/", headers=headers)
```

## Testing

Run the included test script to verify all endpoints:

```bash
python test_auth_api.py
```

## Security Notes

1. **Secret Key** - Change the `SECRET_KEY` in production
2. **Debug Mode** - Set `DEBUG = False` in production
3. **CORS Origins** - Update `CORS_ALLOWED_ORIGINS` for production domains
4. **HTTPS** - Use HTTPS in production for secure token transmission
5. **Password Reset** - Implement proper email/SMS services for production

## Dependencies

- Django 5.2.4
- djangorestframework 3.15.2
- djangorestframework-simplejwt 5.3.0
- django-cors-headers 4.4.0

## Mobile App Integration

For mobile apps, use the JWT tokens in the Authorization header:
```
Authorization: Bearer <access_token>
```

The API returns both access and refresh tokens. Store the refresh token securely and use it to get new access tokens when they expire.

## Web App Integration

For web applications, you can store JWT tokens in:
- HTTP-only cookies (recommended for web)
- localStorage (less secure but simpler)
- sessionStorage (cleared on tab close)

Remember to handle token refresh automatically in your frontend application.
