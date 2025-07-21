from rest_framework import serializers
from .models import ProductCategory, Product, ProductInventory, StockMovement
from decimal import Decimal


class ProductCategorySerializer(serializers.ModelSerializer):
    active_products_count = serializers.ReadOnlyField()

    class Meta:
        model = ProductCategory
        fields = [
            'id',
            'name',
            'description',
            'is_active',
            'active_products_count',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Category name cannot be empty.")
        return value.strip()


class ProductInventorySerializer(serializers.ModelSerializer):
    is_low_stock = serializers.ReadOnlyField()
    stock_value_cost = serializers.ReadOnlyField()
    stock_value_selling = serializers.ReadOnlyField()

    class Meta:
        model = ProductInventory
        fields = [
            'id',
            'quantity_in_stock',
            'reorder_level',
            'last_restocked',
            'is_low_stock',
            'stock_value_cost',
            'stock_value_selling',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    inventory = ProductInventorySerializer(read_only=True)
    profit_margin = serializers.ReadOnlyField()
    profit_amount = serializers.ReadOnlyField()
    current_stock = serializers.ReadOnlyField()
    stock_value = serializers.ReadOnlyField()
    is_low_stock = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'category',
            'category_name',
            'description',
            'selling_price',
            'cost_price',
            'unit_of_measure',
            'sku',
            'is_active',
            'inventory',
            'profit_margin',
            'profit_amount',
            'current_stock',
            'stock_value',
            'is_low_stock',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['sku', 'created_at', 'updated_at']

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Product name cannot be empty.")
        return value.strip()

    def validate_selling_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Selling price must be greater than 0.")
        return value

    def validate_cost_price(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Cost price cannot be negative.")
        return value

    def validate(self, data):
        # Check if cost price is not higher than selling price
        cost_price = data.get('cost_price')
        selling_price = data.get('selling_price')
        
        if cost_price and selling_price and cost_price > selling_price:
            raise serializers.ValidationError({
                'cost_price': 'Cost price cannot be higher than selling price.'
            })
        
        return data


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating products"""
    
    class Meta:
        model = Product
        fields = [
            'name',
            'category',
            'description',
            'selling_price',
            'cost_price',
            'unit_of_measure',
            'sku',
            'is_active'
        ]

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Product name cannot be empty.")
        return value.strip()

    def validate_selling_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Selling price must be greater than 0.")
        return value

    def validate_cost_price(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Cost price cannot be negative.")
        return value


class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            'id',
            'product',
            'product_name',
            'product_sku',
            'movement_type',
            'quantity',
            'quantity_before',
            'quantity_after',
            'reference_number',
            'notes',
            'created_at',
            'created_by',
            'created_by_name'
        ]
        read_only_fields = ['quantity_before', 'quantity_after', 'reference_number', 'created_at', 'created_by']


class StockMovementCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating stock movements"""
    
    class Meta:
        model = StockMovement
        fields = [
            'product',
            'movement_type',
            'quantity',
            'reference_number',
            'notes'
        ]

    def validate_quantity(self, value):
        if value == 0:
            raise serializers.ValidationError("Quantity cannot be zero.")
        return value

    def validate(self, data):
        product = data.get('product')
        quantity = data.get('quantity')
        movement_type = data.get('movement_type')
        
        # For stock out movements, check if sufficient stock is available
        if quantity < 0:
            current_stock = product.current_stock
            if abs(quantity) > current_stock:
                raise serializers.ValidationError({
                    'quantity': f'Insufficient stock. Current stock: {current_stock} {product.unit_of_measure}'
                })
        
        return data


class InventoryReportSerializer(serializers.Serializer):
    """Serializer for inventory reports"""
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    category_name = serializers.CharField()
    sku = serializers.CharField()
    unit_of_measure = serializers.CharField()
    quantity_in_stock = serializers.DecimalField(max_digits=12, decimal_places=3)
    reorder_level = serializers.DecimalField(max_digits=12, decimal_places=3, allow_null=True)
    selling_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    cost_price = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    stock_value_cost = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    stock_value_selling = serializers.DecimalField(max_digits=12, decimal_places=2)
    is_low_stock = serializers.BooleanField()
    last_restocked = serializers.DateTimeField(allow_null=True)


class LowStockAlertSerializer(serializers.Serializer):
    """Serializer for low stock alerts"""
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    category_name = serializers.CharField()
    sku = serializers.CharField()
    current_stock = serializers.DecimalField(max_digits=12, decimal_places=3)
    reorder_level = serializers.DecimalField(max_digits=12, decimal_places=3)
    unit_of_measure = serializers.CharField()
    shortage = serializers.DecimalField(max_digits=12, decimal_places=3)


class InventoryValuationSerializer(serializers.Serializer):
    """Serializer for inventory valuation report"""
    total_products = serializers.IntegerField()
    total_stock_value_cost = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_stock_value_selling = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_potential_profit = serializers.DecimalField(max_digits=15, decimal_places=2)
    categories_breakdown = serializers.ListField()
    low_stock_count = serializers.IntegerField()
