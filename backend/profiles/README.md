# User Profiles & Business Information Module

## Overview
This module provides comprehensive user profile management and business information collection functionality for Zambian businesses. It seamlessly integrates with the authentication system to collect detailed business profiles and personal information.

## Features

### 👤 **Personal Information Management**
- **First & Last Name**: Separated personal name fields with auto-generated full name
- **Email & Phone**: Inherited from user authentication system
- **Profile Completion Tracking**: Real-time completion percentage calculation
- **Auto-profile Creation**: Profiles automatically created when users register

### 🏢 **Business Information Collection**
- **Business Name**: Company or business name
- **Business Type**: 12 predefined categories (retail, services, agriculture, etc.)
- **Business Location**: City/Town and Province in Zambia
- **Employee Count**: Optional employee range selection (1 to 100+)
- **Revenue Tracking**: Monthly revenue ranges in Zambian Kwacha (ZMW)

### 📊 **Profile Analytics**
- **Completion Percentage**: Calculate how complete a profile is
- **Missing Fields Detection**: Identify which fields need completion
- **Profile Summary**: Quick overview of user and business information
- **Business Location Formatting**: Auto-formatted location display

## API Endpoints

### Profile Management
```
GET    /api/profile/              - Get user profile information
PUT    /api/profile/update/       - Update user profile
PATCH  /api/profile/update/       - Partial profile update
GET    /api/profile/summary/      - Get profile summary
GET    /api/profile/completion/   - Check profile completion status
```

### Query Features
- Full profile data retrieval
- Partial updates support
- Completion tracking
- Missing fields identification

## Data Models

### UserProfile
- `user`: One-to-one with CustomUser (authentication)
- `first_name`: User's first name
- `last_name`: User's last name
- `full_name`: Auto-generated from first + last name (read-only)
- `business_name`: Name of the user's business
- `business_type`: Type of business (choices provided)
- `business_city`: City or town where business is located
- `business_province`: Province where business is located
- `employee_count`: Optional employee count range
- `monthly_revenue_range`: Optional revenue range in ZMW
- `is_complete`: Auto-calculated completion status
- `created_at`: Profile creation timestamp
- `updated_at`: Last update timestamp

#### Calculated Properties
- `email`: From related user account
- `phone`: From related user account
- `business_location`: Formatted "City, Province"
- `completion_percentage`: Percentage of required fields completed

## Business Type Options
- `retail`: Retail
- `services`: Services
- `agriculture`: Agriculture
- `manufacturing`: Manufacturing
- `technology`: Technology
- `hospitality`: Hospitality
- `healthcare`: Healthcare
- `education`: Education
- `finance`: Finance
- `construction`: Construction
- `transport`: Transport & Logistics
- `other`: Other

## Employee Count Ranges
- `1`: 1 employee
- `2-5`: 2-5 employees
- `6-10`: 6-10 employees
- `11-25`: 11-25 employees
- `26-50`: 26-50 employees
- `51-100`: 51-100 employees
- `100+`: 100+ employees

## Monthly Revenue Ranges (ZMW)
- `0-1000`: ZMW 0 - ZMW 1,000
- `1001-5000`: ZMW 1,001 - ZMW 5,000
- `5001-10000`: ZMW 5,001 - ZMW 10,000
- `10001-25000`: ZMW 10,001 - ZMW 25,000
- `25001-50000`: ZMW 25,001 - ZMW 50,000
- `50001-100000`: ZMW 50,001 - ZMW 100,000
- `100001-250000`: ZMW 100,001 - ZMW 250,000
- `250001-500000`: ZMW 250,001 - ZMW 500,000
- `500001+`: ZMW 500,001+

## Sample API Requests

### Get Profile Information
```http
GET /api/profile/
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
    "success": true,
    "message": "Profile retrieved successfully",
    "data": {
        "id": 1,
        "user": 1,
        "first_name": "John",
        "last_name": "Mwansa",
        "full_name": "John Mwansa",
        "business_name": "Mwansa General Store",
        "email": "john@example.com",
        "phone": "+260977123456",
        "business_type": "retail",
        "business_city": "Lusaka",
        "business_province": "Lusaka",
        "business_location": "Lusaka, Lusaka",
        "employee_count": "2-5",
        "monthly_revenue_range": "25001-50000",
        "is_complete": true,
        "completion_percentage": 100,
        "created_at": "2025-07-21T10:00:00Z",
        "updated_at": "2025-07-21T15:30:00Z"
    }
}
```

### Update Profile
```http
PUT /api/profile/update/
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
    "first_name": "John",
    "last_name": "Mwansa",
    "business_name": "Mwansa General Store",
    "business_type": "retail",
    "business_city": "Lusaka",
    "business_province": "Lusaka",
    "employee_count": "2-5",
    "monthly_revenue_range": "25001-50000"
}
```

### Partial Profile Update
```http
PATCH /api/profile/update/
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
    "business_name": "Mwansa Enterprises Ltd",
    "employee_count": "6-10"
}
```

### Check Profile Completion
```http
GET /api/profile/completion/
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
    "success": true,
    "message": "Profile completion status retrieved successfully",
    "data": {
        "is_complete": false,
        "completion_percentage": 75,
        "missing_fields": ["employee_count"]
    }
}
```

### Get Profile Summary
```http
GET /api/profile/summary/
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
    "success": true,
    "message": "Profile summary retrieved successfully",
    "data": {
        "id": 1,
        "first_name": "John",
        "last_name": "Mwansa",
        "full_name": "John Mwansa",
        "business_name": "Mwansa General Store",
        "email": "john@example.com",
        "phone": "+260977123456",
        "business_type": "retail",
        "business_location": "Lusaka, Lusaka",
        "is_complete": true
    }
}
```

## Admin Interface Features

### User Admin Integration
- **Business Name Display**: Shows business name in user list
- **Full Name Display**: Shows complete name from profile
- **Profile Information Section**: Dedicated section in user edit page
- **Search Integration**: Search users by business name and personal names
- **Read-only Display**: Profile info shown as read-only in user admin

### Profile Admin
- **Comprehensive View**: All profile fields organized in logical sections
- **Auto-calculated Fields**: Full name, completion status shown as read-only
- **Search & Filter**: Search by names, business info, and location
- **Metadata Tracking**: Creation and update timestamps
- **User Integration**: Links to related user account

#### Admin Sections
1. **User Information**: Email, phone (from auth system)
2. **Personal Information**: First name, last name, auto-generated full name
3. **Business Information**: Business name
4. **Business Details**: Type, location, employee count, revenue
5. **Status & Dates**: Completion status and timestamps

## Security Features
- **Rate Limiting**: Profile updates limited to 10 requests/minute
- **Authentication Required**: All endpoints require valid JWT token
- **Input Validation**: Comprehensive server-side validation
- **Audit Trail**: Complete logging of profile operations
- **Data Protection**: Personal information properly secured

## Auto-Profile Creation
Profiles are automatically created when users register through Django signals:
- New user registration triggers profile creation
- Existing users get profiles created on first access
- Ensures every user has a profile record

## Profile Completion Logic

### Required Fields (for completion)
1. First Name
2. Last Name
3. Business Name
4. Business Type
5. Business City
6. Business Province

### Optional Fields
1. Employee Count
2. Monthly Revenue Range

### Completion Calculation
- **Total Fields**: 8 (6 required + 2 optional)
- **Percentage**: (Completed Fields / Total Fields) × 100
- **Status**: `is_complete` = true when all required fields are filled

## Validation Rules

### Personal Information
- **First Name**: Cannot be empty, trimmed automatically
- **Last Name**: Cannot be empty, trimmed automatically
- **Full Name**: Auto-generated, read-only

### Business Information
- **Business Name**: Cannot be empty, trimmed automatically
- **Business Type**: Must be one of predefined choices
- **Business City**: Cannot be empty, trimmed automatically
- **Business Province**: Cannot be empty, trimmed automatically

### Optional Fields
- **Employee Count**: Must be valid choice if provided
- **Revenue Range**: Must be valid choice if provided

## Integration with Authentication
The profiles module seamlessly integrates with the custom authentication system:

- **Email/Phone**: Retrieved from `CustomUser` model
- **User Relationship**: One-to-one relationship with `CustomUser`
- **Admin Display**: User admin shows business name and full name from profile
- **Automatic Creation**: Profiles created via Django signals

## Rate Limiting
- **Profile Retrieval**: 20 requests/minute
- **Profile Updates**: 10 requests/minute
- **Profile Summary**: 20 requests/minute
- **Completion Check**: 10 requests/minute

## Error Handling
All endpoints return standardized error responses:

```json
{
    "success": false,
    "message": "Error message",
    "errors": {
        "field_name": ["Specific validation error"]
    }
}
```

## Future Enhancements
- **Profile Photos**: Add user/business photo upload capability
- **Business Documents**: Attach business registration documents
- **Multiple Locations**: Support for multi-location businesses
- **Business Verification**: Email/phone verification for businesses
- **Profile Templates**: Pre-filled profiles for common business types
- **Analytics**: Business profile analytics and insights
- **Integration**: Connect with accounting and inventory modules

## Usage Examples

### Initial Profile Setup
1. User registers through authentication system
2. Profile automatically created with empty fields
3. User completes personal information (name)
4. User fills business details (name, type, location)
5. Optional: Add employee count and revenue range

### Profile Management
1. Check completion status regularly
2. Update business information as it changes
3. Monitor missing fields for complete profiles
4. Use profile summary for quick overviews

### Admin Management
1. View all user profiles in admin interface
2. Search users by business name or personal name
3. Monitor profile completion across user base
4. Manage business information centrally

## Getting Started
1. Profiles module is automatically available after migration
2. Profiles created automatically when users register
3. Access via API endpoints with JWT authentication
4. Manage through Django admin interface
5. Integrate with frontend for user profile forms

This module provides essential business profile functionality for Zambian enterprises, with comprehensive data collection and management capabilities.
