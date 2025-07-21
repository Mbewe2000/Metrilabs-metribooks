# Custom Authentication System with DRF-JWT

This project implements a custom Django authentication system that supports login with both email and phone numbers, using Django REST Framework with JWT tokens and CORS support for web and mobile applications.

## Features

✅ **Custom User Model** - Supports both email and phone authentication
✅ **JWT Authentication** - Using djangorestframework-simplejwt
✅ **CORS Support** - Configured for web and mobile app integration
✅ **Complete Auth Views** - Registration, Login, Logout, Change Password, Reset Password
✅ **Admin Interface** - Custom admin for user management
✅ **API Documentation** - Complete endpoint documentation

## Project Structure

```
backend/
├── authentication/                 # Authentication app
│   ├── models.py                  # CustomUser model
│   ├── serializers.py             # API serializers
│   ├── views.py                   # Authentication views
│   ├── urls.py                    # Authentication URLs
│   ├── admin.py                   # Admin configuration
│   ├── backends.py                # Custom authentication backend
│   └── migrations/                # Database migrations
├── backend/                       # Main project settings
│   ├── settings.py                # Django settings with JWT/CORS config
│   ├── urls.py                    # Main URL configuration
│   └── ...
├── manage.py                      # Django management script
├── requirements.txt               # Python dependencies
├── API_DOCUMENTATION.md           # Complete API documentation
└── test_auth_api.py              # API testing script
```

## Installation & Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

3. **Create Superuser** (Optional)
   ```bash
   python manage.py createsuperuser
   ```

4. **Start Development Server**
   ```bash
   python manage.py runserver
   ```

## API Endpoints

All authentication endpoints are available at `/api/auth/`:

- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login  
- `POST /api/auth/logout/` - User logout
- `PUT /api/auth/change-password/` - Change password
- `POST /api/auth/reset-password/` - Request password reset
- `POST /api/auth/reset-password-confirm/` - Confirm password reset
- `GET/PUT /api/auth/profile/` - User profile
- `POST /api/auth/token/refresh/` - Refresh JWT token

## Configuration

### JWT Settings
- Access token lifetime: 60 minutes
- Refresh token lifetime: 7 days
- Tokens are automatically rotated and blacklisted on logout

### CORS Settings
Currently configured for:
- `http://localhost:3000` (React)
- `http://localhost:8080` (Vue)

Update `CORS_ALLOWED_ORIGINS` in `settings.py` for your frontend URLs.

### Custom User Model
The `CustomUser` model supports:
- Email authentication (optional)
- Phone number authentication (optional)
- Standard user fields (first_name, last_name, etc.)
- Email/phone verification flags
- At least one of email or phone is required

## Usage Examples

### Registration
```python
import requests

data = {
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
