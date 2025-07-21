# Product Management & Inventory Tracking Module

## Overview
This module provides comprehensive product management and inventory tracking functionality for Zambian businesses, with full support for Zambian Kwacha (ZMW) currency.

## Features

### 🏷️ **Product Management**
- **Add, Edit, Delete Products**: Full CRUD operations for product management
- **Product Categories**: Organize products into categories (Beverages, Electronics, Services, etc.)
- **Pricing in ZMW**: Set selling prices and optional cost prices in Zambian Kwacha
- **Auto-generated SKU**: Automatic SKU generation based on category and product name
- **Active/Inactive Status**: Enable/disable products without deletion

### 📦 **Inventory Tracking**
- **Real-time Stock Levels**: View current stock quantities in real-time
- **Opening Stock**: Manually input initial stock for each product
- **Stock Adjustments**: Manually add or reduce stock (restocking, theft, damage)
- **Reorder Levels**: Set optional reorder levels for low stock alerts
- **Multiple Units**: Support for various units (Each, Kg, Liter, etc.)

### 📋 **Stock Movement History**
- **Complete Audit Trail**: Track every stock movement with full history
- **Movement Types**: Manual in/out, opening stock, restock, adjustments, damage, theft
- **Reference Numbers**: Auto-generated reference numbers for tracking
- **User Attribution**: Track who made each stock movement
- **Notes**: Optional notes for each movement

### 📊 **Reports & Analytics**
- **Stock Summary Report**: Overview of all products with quantities and values
- **Low Stock Alerts**: Identify products that need restocking
- **Inventory Valuation**: Calculate total inventory value based on cost prices
- **Category Breakdown**: Analyze inventory by product categories

## API Endpoints

### Product Categories
```
GET    /api/categories/              - List all categories
POST   /api/categories/              - Create new category
GET    /api/categories/{id}/         - Get category details
PUT    /api/categories/{id}/         - Update category
DELETE /api/categories/{id}/         - Delete category
```

### Products
```
GET    /api/products/                - List all products
POST   /api/products/                - Create new product
GET    /api/products/{id}/           - Get product details
PUT    /api/products/{id}/           - Update product
DELETE /api/products/{id}/           - Delete product
```

#### Query Parameters for Products:
- `?category=<id>` - Filter by category
- `?is_active=true/false` - Filter by active status
- `?search=<term>` - Search by name or SKU
- `?low_stock=true` - Show only low stock products

### Inventory Management
```
GET    /api/inventory/{product_id}/  - Get inventory details
PUT    /api/inventory/{product_id}/  - Update inventory settings
```

### Stock Movements
```
GET    /api/stock-movements/         - List stock movements
POST   /api/stock-movements/         - Create stock movement
```

#### Query Parameters for Stock Movements:
- `?product=<id>` - Filter by product
- `?movement_type=<type>` - Filter by movement type
- `?date_from=YYYY-MM-DD` - Filter by start date
- `?date_to=YYYY-MM-DD` - Filter by end date

### Reports
```
GET    /api/reports/inventory-summary/     - Stock summary report
GET    /api/reports/low-stock-alerts/      - Low stock alerts
GET    /api/reports/inventory-valuation/   - Inventory valuation report
```

## Data Models

### ProductCategory
- `name`: Category name (unique)
- `description`: Optional description
- `is_active`: Active status
- `active_products_count`: Calculated field

### Product
- `name`: Product name
- `category`: Foreign key to ProductCategory
- `description`: Optional description
- `selling_price`: Price in ZMW (required)
- `cost_price`: Cost price in ZMW (optional)
- `unit_of_measure`: Unit type (each, kg, liter, etc.)
- `sku`: Auto-generated or manual SKU
- `is_active`: Active status
- Calculated fields: `profit_margin`, `current_stock`, `is_low_stock`

### ProductInventory
- `product`: One-to-one with Product
- `quantity_in_stock`: Current stock quantity
- `reorder_level`: Optional reorder threshold
- `last_restocked`: Last restock date
- Calculated fields: `is_low_stock`, `stock_value_cost`, `stock_value_selling`

### StockMovement
- `product`: Foreign key to Product
- `movement_type`: Type of movement (manual_in, manual_out, etc.)
- `quantity`: Quantity moved (positive for in, negative for out)
- `quantity_before`: Stock before movement
- `quantity_after`: Stock after movement
- `reference_number`: Auto-generated reference
- `notes`: Optional notes
- `created_by`: User who made the movement

## Movement Types
- `opening_stock`: Initial stock setup
- `manual_in`: Manual stock increase
- `manual_out`: Manual stock decrease
- `restock`: Restocking from supplier
- `adjustment`: Stock adjustment/correction
- `damage`: Damaged or expired items
- `theft`: Theft or loss
- `sale`: Sale transaction (for future sales integration)
- `return`: Product return
- `transfer`: Stock transfer

## Sample API Requests

### Create Product Category
```json
POST /api/categories/
{
    "name": "Beverages",
    "description": "Drinks and beverages",
    "is_active": true
}
```

### Create Product
```json
POST /api/products/
{
    "name": "Coca Cola 500ml",
    "category": 1,
    "selling_price": "8.50",
    "cost_price": "6.00",
    "unit_of_measure": "bottle",
    "description": "Coca Cola soft drink 500ml bottle",
    "is_active": true
}
```

### Create Stock Movement
```json
POST /api/stock-movements/
{
    "product": 1,
    "movement_type": "opening_stock",
    "quantity": "100.000",
    "notes": "Initial stock setup"
}
```

### Update Inventory Settings
```json
PUT /api/inventory/1/
{
    "reorder_level": "20.000"
}
```

## Admin Interface Features

### Product Admin
- List view with stock status indicators
- Inline inventory management
- Profit margin calculations
- Stock value displays
- Search and filtering

### Inventory Admin
- Visual stock status indicators
- Stock value calculations
- Reorder level management
- Read-only for safety

### Stock Movement Admin
- Movement direction indicators
- Complete audit trail
- Reference number tracking
- Read-only to prevent tampering

## Security Features
- **Rate Limiting**: API endpoints are rate-limited to prevent abuse
- **Authentication**: All endpoints require authentication
- **Audit Trail**: Complete logging of all operations
- **Data Validation**: Comprehensive input validation
- **Stock Protection**: Prevents negative stock situations

## Usage Examples

### Setting Up Products
1. Create product categories (Beverages, Electronics, etc.)
2. Add products with pricing and details
3. Set initial stock levels using opening stock movements
4. Configure reorder levels for low stock alerts

### Daily Operations
1. Use stock movements to record restocking
2. Adjust stock for damaged/expired items
3. Monitor low stock alerts
4. Generate inventory reports

### Reporting
1. Run inventory summary for complete overview
2. Check low stock alerts daily
3. Generate valuation reports for accounting
4. Review stock movement history for auditing

## Rate Limits
- Category operations: 20-30 requests/minute
- Product operations: 15-30 requests/minute
- Stock movements: 30 requests/minute
- Reports: 10-15 requests/minute

## Future Enhancements
- Integration with sales module for automatic stock reduction
- Barcode scanning support
- Multi-location inventory tracking
- Supplier management
- Purchase order integration
- Advanced analytics and forecasting

## Getting Started
1. Run migrations: `python manage.py migrate`
2. Create sample data: `python manage.py create_sample_products`
3. Access admin interface to manage products
4. Use API endpoints for frontend integration

This module provides a solid foundation for inventory management in Zambian businesses, with room for future enhancements and integrations.
