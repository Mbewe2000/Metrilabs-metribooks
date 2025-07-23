from rest_framework import serializers
from decimal import Decimal
from .models import Product, ProductCategory, Inventory, StockMovement, StockAlert


class ProductCategorySerializer(serializers.ModelSerializer):
    """Serializer for product categories"""
    
    display_name = serializers.CharField(source='get_name_display', read_only=True)
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductCategory
        fields = [
            'id',
            'name',
            'display_name',
            'description',
            'is_active',
            'product_count',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_product_count(self, obj):
        """Get count of products in this category"""
        return obj.products.filter(is_active=True).count()


class InventorySerializer(serializers.ModelSerializer):
    """Serializer for inventory information"""
    
    stock_status = serializers.CharField(read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Inventory
        fields = [
            'quantity_in_stock',
            'reorder_level',
            'opening_stock',
            'stock_status',
            'is_low_stock',
            'last_stock_update',
            'created_at'
        ]
        read_only_fields = ['last_stock_update', 'created_at']


class ProductSerializer(serializers.ModelSerializer):
    """Detailed serializer for products"""
    
    category_name = serializers.CharField(source='category.get_name_display', read_only=True)
    unit_display = serializers.CharField(source='get_unit_of_measure_display', read_only=True)
    profit_margin = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    current_stock = serializers.DecimalField(max_digits=12, decimal_places=3, read_only=True)
    stock_value = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    selling_value = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    inventory = InventorySerializer(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'sku',
            'description',
            'category',
            'category_name',
            'selling_price',
            'cost_price',
            'unit_of_measure',
            'unit_display',
            'profit_margin',
            'current_stock',
            'stock_value',
            'selling_value',
            'is_active',
            'inventory',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_sku(self, value):
        """Validate SKU uniqueness per user"""
        if value:
            user = self.context['request'].user
            queryset = Product.objects.filter(user=user, sku=value)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError("SKU must be unique for your products.")
        return value
    
    def validate(self, data):
        """Validate selling price vs cost price"""
        selling_price = data.get('selling_price')
        cost_price = data.get('cost_price')
        
        if cost_price and selling_price and cost_price > selling_price:
            raise serializers.ValidationError(
                "Cost price cannot be higher than selling price."
            )
        
        return data


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating products"""
    
    # Initial stock setup
    opening_stock = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=Decimal('0'),
        min_value=Decimal('0'),
        write_only=True,
        help_text="Initial stock quantity"
    )
    reorder_level = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        required=False,
        min_value=Decimal('0'),
        write_only=True,
        help_text="Minimum stock level for alerts"
    )
    
    class Meta:
        model = Product
        fields = [
            'name',
            'sku',
            'description',
            'category',
            'selling_price',
            'cost_price',
            'unit_of_measure',
            'opening_stock',
            'reorder_level',
            'is_active'
        ]
    
    def validate_sku(self, value):
        """Validate SKU uniqueness per user"""
        if value:
            user = self.context['request'].user
            queryset = Product.objects.filter(user=user, sku=value)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError("SKU must be unique for your products.")
        return value
    
    def create(self, validated_data):
        """Create product with initial inventory"""
        opening_stock = validated_data.pop('opening_stock', 0)
        reorder_level = validated_data.pop('reorder_level', None)
        
        # Set user from request
        validated_data['user'] = self.context['request'].user
        
        # Create product
        product = Product.objects.create(**validated_data)
        
        # Check if inventory already exists (might be created by signal)
        try:
            inventory = Inventory.objects.get(product=product)
            # Update existing inventory with provided values
            inventory.quantity_in_stock = opening_stock
            inventory.opening_stock = opening_stock
            if reorder_level is not None:
                inventory.reorder_level = reorder_level
            inventory.save()
        except Inventory.DoesNotExist:
            # Create inventory record if it doesn't exist
            inventory_data = {
                'product': product,
                'quantity_in_stock': opening_stock,
                'opening_stock': opening_stock,
            }
            if reorder_level is not None:
                inventory_data['reorder_level'] = reorder_level
            
            inventory = Inventory.objects.create(**inventory_data)
        
        # Create opening stock movement if there's initial stock
        if opening_stock > 0:
            StockMovement.objects.create(
                product=product,
                movement_type='opening_stock',
                quantity=opening_stock,
                quantity_before=0,
                quantity_after=opening_stock,
                notes='Initial stock entry',
                created_by=self.context['request'].user
            )
        
        return product
    
    def update(self, instance, validated_data):
        """Update product (inventory updates handled separately)"""
        # Remove inventory fields for product update
        validated_data.pop('opening_stock', None)
        validated_data.pop('reorder_level', None)
        
        return super().update(instance, validated_data)


class StockMovementSerializer(serializers.ModelSerializer):
    """Serializer for stock movements"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    movement_type_display = serializers.CharField(source='get_movement_type_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    is_inbound = serializers.BooleanField(read_only=True)
    is_outbound = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = StockMovement
        fields = [
            'id',
            'product',
            'product_name',
            'movement_type',
            'movement_type_display',
            'quantity',
            'quantity_before',
            'quantity_after',
            'reference_number',
            'notes',
            'is_inbound',
            'is_outbound',
            'created_by_name',
            'created_at'
        ]
        read_only_fields = [
            'quantity_before',
            'quantity_after',
            'created_by_name',
            'created_at'
        ]


class StockAdjustmentSerializer(serializers.Serializer):
    """Serializer for manual stock adjustments"""
    
    adjustment_type = serializers.ChoiceField(
        choices=['add', 'remove'],
        help_text="Whether to add or remove stock"
    )
    quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        min_value=Decimal('0.001'),
        help_text="Quantity to add or remove"
    )
    movement_type = serializers.ChoiceField(
        choices=StockMovement.MOVEMENT_TYPE_CHOICES,
        help_text="Type of stock movement"
    )
    reference_number = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Reference number"
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Additional notes"
    )
    
    def validate(self, data):
        """Validate stock adjustment"""
        product = self.context['product']
        adjustment_type = data['adjustment_type']
        quantity = data['quantity']
        
        if adjustment_type == 'remove':
            current_stock = product.current_stock
            if quantity > current_stock:
                raise serializers.ValidationError(
                    f"Cannot remove {quantity} units. Only {current_stock} units available in stock."
                )
        
        return data


class StockAlertSerializer(serializers.ModelSerializer):
    """Serializer for stock alerts"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    alert_type_display = serializers.CharField(source='get_alert_type_display', read_only=True)
    category_name = serializers.CharField(source='product.category.get_name_display', read_only=True)
    
    class Meta:
        model = StockAlert
        fields = [
            'id',
            'product',
            'product_name',
            'category_name',
            'alert_type',
            'alert_type_display',
            'current_stock',
            'reorder_level',
            'is_resolved',
            'resolved_at',
            'created_at'
        ]
        read_only_fields = ['created_at', 'resolved_at']


class ProductSummarySerializer(serializers.ModelSerializer):
    """Simple serializer for product summaries"""
    
    category_name = serializers.CharField(source='category.get_name_display', read_only=True)
    current_stock = serializers.DecimalField(max_digits=12, decimal_places=3, read_only=True)
    stock_value = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    stock_status = serializers.CharField(source='inventory.stock_status', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'sku',
            'category_name',
            'selling_price',
            'current_stock',
            'stock_value',
            'stock_status',
            'is_active'
        ]
