# Inventory Management Module

This module provides comprehensive product inventory management capabilities for the Metrilabs-metribooks platform. Each user has their own isolated inventory system.

## Features

### 🔹 Product Management
- **Add, Edit, Delete Products**: Complete CRUD operations for products
- **Product Categories**: Organize products into predefined categories (no services)
- **Pricing Management**: Set selling prices and optional cost prices
- **SKU Management**: Optional product codes for better organization
- **Unit of Measure**: Support for various units (Each, Kg, Liter, etc.)
- **Product Status**: Active/Inactive status control

### 🔹 Inventory Tracking
- **Real-time Stock Levels**: View current stock quantities
- **Manual Stock Adjustments**: Add or remove stock manually
- **Opening Stock**: Set initial inventory levels
- **Auto Stock Reduction**: Automatic reduction when sales are recorded (future sales module)
- **Reorder Levels**: Set minimum stock levels for alerts

### 🔹 Stock Movement History
- **Complete Audit Trail**: Track all stock movements
- **Movement Types**: Opening stock, manual in/out, sales, returns, adjustments, damage, theft
- **Reference Numbers**: Link movements to invoices, receipts, etc.
- **User Attribution**: Track who performed each movement
- **Detailed Notes**: Add context to stock movements

### 🔹 Stock Alerts
- **Low Stock Alerts**: Automatic alerts when stock falls below reorder level
- **Out of Stock Alerts**: Immediate alerts when stock reaches zero
- **Alert Management**: Mark alerts as resolved
- **Real-time Monitoring**: Continuous stock level monitoring

### 🔹 Reports & Dashboard
- **Stock Summary Report**: Overview of all products and their stock levels
- **Inventory Valuation Report**: Calculate total inventory value
- **Low Stock Report**: Products requiring attention
- **Dashboard Metrics**: Key inventory statistics and trends

## Database Models

### Product
- **User Isolation**: Each product belongs to a specific user
- **Basic Info**: Name, SKU, description, category
- **Pricing**: Selling price, cost price (optional)
- **Measurement**: Unit of measure
- **Status**: Active/inactive flag

### ProductCategory
- **Predefined Categories**: Food & Beverage, Electronics, Clothing, etc.
- **Global Categories**: Shared across all users but products are user-specific

### Inventory
- **One-to-One with Product**: Each product has one inventory record
- **Stock Tracking**: Current quantity, reorder level, opening stock
- **Timestamps**: Track when stock was last updated

### StockMovement
- **Complete Audit**: Every stock change is recorded
- **Movement Types**: Various categories of stock changes
- **Before/After Quantities**: Track exact changes
- **User Attribution**: Who made the change

### StockAlert
- **Automated Alerts**: System-generated low stock warnings
- **Resolution Tracking**: Mark alerts as resolved
- **Alert Types**: Low stock vs out of stock

## API Endpoints

### Product Management
```
GET    /api/inventory/products/                    # List all user's products
POST   /api/inventory/products/create/             # Create new product
GET    /api/inventory/products/{id}/               # Get product details
PUT    /api/inventory/products/{id}/               # Update product
DELETE /api/inventory/products/{id}/               # Delete product
```

### Inventory Management
```
POST   /api/inventory/products/{id}/adjust-stock/  # Manual stock adjustment
```

### Stock Movements
```
GET    /api/inventory/stock-movements/             # List stock movements
```

### Categories
```
GET    /api/inventory/categories/                  # List product categories
```

### Alerts
```
GET    /api/inventory/alerts/                      # List stock alerts
POST   /api/inventory/alerts/{id}/resolve/         # Resolve alert
```

### Reports & Dashboard
```
GET    /api/inventory/dashboard/                   # Inventory dashboard data
GET    /api/inventory/reports/stock-summary/       # Stock summary report
GET    /api/inventory/reports/valuation/           # Inventory valuation report
```

## User Isolation & Security

### Complete User Isolation
- **Product Ownership**: Each product belongs to a specific user
- **Query Filtering**: All queries automatically filter by current user
- **Admin Interface**: Non-superusers only see their own data
- **API Security**: JWT authentication required for all endpoints

### Rate Limiting
- **Product Creation**: 50 products per hour per user
- **Product Updates**: 100 updates per hour per user
- **Stock Adjustments**: 200 adjustments per hour per user
- **Dashboard Access**: 100 requests per hour per user

### Audit Trail
- **Stock Movements**: Every change logged with user attribution
- **Comprehensive Logging**: All actions logged for security
- **Change History**: Complete history of all inventory changes

## Product Categories

### Available Categories
1. **Food & Beverage**: Restaurant supplies, packaged foods, drinks
2. **Electronics**: Computers, phones, accessories
3. **Clothing & Accessories**: Apparel, shoes, jewelry
4. **Health & Beauty**: Cosmetics, medications, wellness products
5. **Home & Garden**: Furniture, appliances, gardening supplies
6. **Books & Stationery**: Publications, office supplies
7. **Sports & Outdoor**: Equipment, gear, recreational items
8. **Automotive**: Car parts, accessories, maintenance items
9. **Toys & Games**: Children's toys, board games, puzzles
10. **Other**: Miscellaneous products

## Units of Measure

### Supported Units
- **Count**: Each, Dozen, Pair, Set
- **Weight**: Kilogram, Gram
- **Volume**: Liter, Milliliter
- **Length**: Meter, Centimeter
- **Packaging**: Pack, Box, Bottle, Can, Bag

## Stock Movement Types

### Movement Categories
- **Opening Stock**: Initial inventory setup
- **Stock In (Manual)**: Manual additions to inventory
- **Stock Out (Manual)**: Manual removals from inventory
- **Sale (Auto)**: Automatic reduction from sales (future)
- **Return**: Product returns increasing stock
- **Adjustment**: Corrections to stock levels
- **Damage**: Damaged or expired products
- **Theft**: Lost or stolen inventory

## Integration with Authentication System

### Automatic Setup
- **Signal-Based Creation**: Inventory setup when user registers
- **Default Categories**: Predefined categories created automatically
- **Profile Integration**: Links with user profile system

### User Management
- **JWT Authentication**: Secure API access
- **Permission-Based Access**: Role-based permissions
- **Multi-User Support**: Isolated inventories per user

## Future Enhancements

### Planned Features
- **Sales Integration**: Automatic stock reduction from sales
- **Purchase Orders**: Supplier management and ordering
- **Barcode Support**: Barcode scanning for products
- **Batch/Lot Tracking**: Track product batches
- **Supplier Management**: Vendor information and relationships
- **Advanced Analytics**: Predictive analytics and trends

## Getting Started

### 1. Product Setup
1. Access the inventory module via API or admin interface
2. Create product categories (auto-created on user registration)
3. Add your first products with initial stock levels
4. Set reorder levels for automatic alerts

### 2. Daily Operations
1. Use stock adjustment endpoints for manual changes
2. Monitor dashboard for low stock alerts
3. Review stock movement history for audit purposes
4. Generate reports for business insights

### 3. Best Practices
- Set appropriate reorder levels for all products
- Use descriptive SKUs for better organization
- Include cost prices for accurate valuation reports
- Regularly review and resolve stock alerts
- Use reference numbers for stock movements

This inventory module provides a solid foundation for product and stock management while maintaining complete user isolation and comprehensive audit trails.
