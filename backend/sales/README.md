# Sales Module

The Sales module is a comprehensive sales management system that handles sales transactions, inventory integration, and revenue tracking for the Metrilabs-metribooks application.

## Features

### Core Functionality
- **Sales Transaction Management**: Create, update, and track sales with automatic numbering
- **Mixed Product/Service Sales**: Support for selling both inventory products and services in a single transaction
- **Automatic Inventory Integration**: Real-time inventory updates when products are sold
- **Payment Processing**: Multiple payment methods with amount tracking and change calculation
- **Customer Management**: Optional customer information storage for each sale
- **Sales Analytics**: Dashboard with comprehensive sales metrics and reporting

### Business Logic
- **Automatic Sale Number Generation**: Format: `SL{YYYYMMDD}{XXXX}` (e.g., SL202507230001)
- **Real-time Inventory Updates**: Stock automatically reduced when products are sold
- **Audit Trail**: Complete inventory movement tracking with sale references
- **User Isolation**: Each user can only access their own sales data
- **Sale Status Management**: Pending, Completed, Cancelled, Refunded statuses
- **Flexible Pricing**: Support for discounts, taxes, and custom pricing

## Models

### Sale Model
The main sales record containing transaction details.

```python
class Sale(models.Model):
    # Core fields
    id = UUIDField(primary_key=True)  # UUID for security
    user = ForeignKey(User)  # Owner of the sale
    sale_number = CharField(max_length=50)  # Auto-generated unique number
    
    # Sale details
    sale_date = DateTimeField(default=timezone.now)
    customer_name = CharField(max_length=200, blank=True)
    customer_phone = CharField(max_length=20, blank=True)
    customer_email = EmailField(blank=True)
    
    # Financial details
    subtotal = DecimalField(max_digits=12, decimal_places=2)
    discount_amount = DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = DecimalField(max_digits=12, decimal_places=2)
    
    # Payment details
    payment_method = CharField(choices=PAYMENT_METHOD_CHOICES)
    payment_reference = CharField(max_length=100, blank=True)
    amount_paid = DecimalField(max_digits=12, decimal_places=2, default=0)
    change_amount = DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Status and metadata
    status = CharField(choices=STATUS_CHOICES, default='completed')
    notes = TextField(blank=True)
```

### SaleItem Model
Individual items within a sale (products or services).

```python
class SaleItem(models.Model):
    # Core fields
    id = UUIDField(primary_key=True)
    sale = ForeignKey(Sale, related_name='items')
    
    # Item details
    item_type = CharField(choices=[('product', 'Product'), ('service', 'Service')])
    product = ForeignKey(Product, null=True, blank=True)
    service = ForeignKey(Service, null=True, blank=True)
    item_name = CharField(max_length=200)  # Snapshot of name
    
    # Pricing
    quantity = DecimalField(max_digits=10, decimal_places=3)
    unit_price = DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = DecimalField(max_digits=5, decimal_places=2, default=0)
    total_price = DecimalField(max_digits=12, decimal_places=2)
```

## API Endpoints

### Sales Management

#### Create Sale
```http
POST /api/sales/sales/create/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "customer_name": "John Doe",
    "customer_phone": "+1234567890",
    "payment_method": "cash",
    "status": "completed",
    "tax_amount": "5.00",
    "discount_amount": "0.00",
    "amount_paid": "955.00",
    "change_amount": "5.00",
    "items": [
        {
            "item_type": "product",
            "product": "product-uuid",
            "quantity": "2.000",
            "unit_price": "400.00"
        },
        {
            "item_type": "service",
            "service": "service-uuid",
            "quantity": "1.000",
            "unit_price": "150.00"
        }
    ]
}
```

**Response:**
```json
{
    "success": true,
    "message": "Sale created successfully",
    "data": {
        "id": "sale-uuid",
        "sale_number": "SL202507230001",
        "sale_date": "2025-07-23T10:30:00Z",
        "customer_name": "John Doe",
        "subtotal": "950.00",
        "total_amount": "955.00",
        "status": "completed",
        "items": [...]
    }
}
```

#### List Sales
```http
GET /api/sales/sales/
Authorization: Bearer {access_token}

# Optional query parameters:
GET /api/sales/sales/?start_date=2025-07-01&end_date=2025-07-31
GET /api/sales/sales/?payment_method=cash
GET /api/sales/sales/?status=completed
GET /api/sales/sales/?customer_name=John
```

#### Get Sale Details
```http
GET /api/sales/sales/{sale_id}/
Authorization: Bearer {access_token}
```

#### Update Sale
```http
PUT /api/sales/sales/{sale_id}/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "customer_name": "Jane Doe",
    "customer_phone": "+9876543210",
    "notes": "Updated customer information"
}
```

#### Delete Sale
```http
DELETE /api/sales/sales/{sale_id}/
Authorization: Bearer {access_token}
```

**Note:** Only sales with status 'pending' or 'cancelled' can be deleted.

### Analytics Dashboard

#### Sales Dashboard
```http
GET /api/sales/dashboard/
Authorization: Bearer {access_token}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "today_sales": 5,
        "today_revenue": "2450.00",
        "this_week_sales": 23,
        "this_week_revenue": "12300.00",
        "this_month_sales": 89,
        "this_month_revenue": "45600.00",
        "recent_sales": [...],
        "payment_methods": {
            "cash": 12,
            "mobile_money": 8,
            "card": 3
        },
        "top_products": [...],
        "top_services": [...]
    }
}
```

## Payment Methods

The system supports the following payment methods:

- **cash**: Cash payment
- **mobile_money**: Mobile money transfer
- **bank_transfer**: Bank transfer
- **card**: Card payment (credit/debit)
- **credit**: Credit/Account payment
- **other**: Other payment methods

## Sale Statuses

- **completed**: Sale completed successfully
- **pending**: Sale created but not yet completed
- **cancelled**: Sale cancelled
- **refunded**: Sale refunded

## Inventory Integration

### Automatic Stock Updates
When a product sale is created:
1. Product inventory is automatically reduced by the sold quantity
2. A `StockMovement` record is created for audit trail
3. Sale totals are automatically calculated

### Inventory Restoration
When a sale item is deleted:
1. Product inventory is automatically restored
2. A reverse `StockMovement` record is created
3. Sale totals are recalculated

### Stock Movement Records
```python
StockMovement.objects.create(
    product=product,
    movement_type='sale',  # or 'return' for deletions
    quantity=-2,  # Negative for outbound, positive for inbound
    quantity_before=10,
    quantity_after=8,
    reference_number='SL202507230001',
    notes='Sale #SL202507230001 - Product Name',
    created_by=user
)
```

## Usage Examples

### Creating a Product Sale
```python
from sales.models import Sale, SaleItem
from inventory.models import Product

# Create sale
sale = Sale.objects.create(
    user=request.user,
    customer_name='John Doe',
    payment_method='cash',
    subtotal=Decimal('800.00'),
    total_amount=Decimal('800.00')
)

# Add product item
product = Product.objects.get(id=product_id)
SaleItem.objects.create(
    sale=sale,
    item_type='product',
    product=product,
    item_name=product.name,
    quantity=Decimal('2.000'),
    unit_price=product.selling_price,
    total_price=Decimal('800.00')
)

# Inventory is automatically updated via signals
```

### Creating a Service Sale
```python
from services.models import Service

# Add service item
service = Service.objects.get(id=service_id)
SaleItem.objects.create(
    sale=sale,
    item_type='service',
    service=service,
    item_name=service.name,
    quantity=Decimal('1.000'),
    unit_price=service.fixed_price,
    total_price=service.fixed_price
)
```

### Mixed Product and Service Sale
```python
# Create sale with both products and services
sale_data = {
    'customer_name': 'Customer Name',
    'payment_method': 'cash',
    'items': [
        {
            'item_type': 'product',
            'product': product.id,
            'quantity': '1.000',
            'unit_price': '500.00'
        },
        {
            'item_type': 'service',
            'service': service.id,
            'quantity': '1.000',
            'unit_price': '100.00'
        }
    ]
}

# Use API endpoint to create
response = client.post('/api/sales/sales/create/', sale_data)
```

## Signals and Automatic Processing

### Sale Item Signals
The module uses Django signals for automatic processing:

```python
@receiver(post_save, sender=SaleItem)
def sale_item_post_save(sender, instance, created, **kwargs):
    # Recalculate sale totals
    # Update inventory for products
    # Create stock movement records

@receiver(post_delete, sender=SaleItem)
def sale_item_post_delete(sender, instance, **kwargs):
    # Recalculate sale totals
    # Restore inventory for products
    # Create reverse stock movement records
```

## Security Features

### User Isolation
- Users can only access their own sales
- All API endpoints filter by `request.user`
- Database queries include user-based filtering

### Authentication
- JWT token-based authentication required
- Rate limiting on sale creation (100 requests/hour per user)
- Proper permission checks on all endpoints

### Data Validation
- Input validation on all fields
- Stock availability checks before sale creation
- Proper error handling and user feedback

## Testing

The module includes comprehensive tests:
- **15 Core Tests**: Model validation, signals, business logic
- **11 API Tests**: Endpoint functionality, authentication, user isolation

Run tests:
```bash
# Run all sales tests
python manage.py test sales

# Run specific test categories
python manage.py test sales.tests        # Core functionality tests
python manage.py test sales.test_api     # API endpoint tests
```

## Installation and Setup

1. **Add to INSTALLED_APPS**:
```python
INSTALLED_APPS = [
    # ... other apps
    'sales',
]
```

2. **Run Migrations**:
```bash
python manage.py makemigrations sales
python manage.py migrate
```

3. **Add URL Configuration**:
```python
# urls.py
urlpatterns = [
    # ... other URLs
    path('api/sales/', include('sales.urls')),
]
```

4. **Configure Logging** (optional):
```python
LOGGING = {
    'loggers': {
        'sales': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

## Dependencies

- **Django**: Web framework
- **Django REST Framework**: API functionality
- **django-ratelimit**: Rate limiting
- **Inventory Module**: Product management and stock tracking
- **Services Module**: Service management
- **Authentication Module**: User management and JWT tokens

## Performance Considerations

- Uses database transactions for data consistency
- Efficient queryset operations with select_related/prefetch_related
- UUID primary keys for security and distributed systems
- Indexed fields for common queries (user, sale_date, payment_method)

## Future Enhancements

- **Receipts**: PDF receipt generation
- **Returns**: Formal return/refund processing
- **Invoicing**: Invoice generation for B2B sales
- **Reporting**: Advanced analytics and custom reports
- **Multi-currency**: Support for multiple currencies
- **Loyalty Programs**: Customer loyalty point systems

## Support

For issues, questions, or contributions:
- Create issues in the project repository
- Follow the existing code patterns and test coverage
- Ensure all tests pass before submitting changes

---

**Version**: 1.0.0  
**Last Updated**: July 23, 2025  
**Django Version**: 5.2.4  
**DRF Version**: 3.15.2
