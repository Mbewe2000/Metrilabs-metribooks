from rest_framework import serializers
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Sale, SaleItem, SalesReport
from inventory.models import Product
from services.models import Service


class SaleItemSerializer(serializers.ModelSerializer):
    """Serializer for sale items"""
    item_name = serializers.CharField(read_only=True)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = SaleItem
        fields = [
            'id', 'item_type', 'product', 'service', 'item_name',
            'quantity', 'unit_price', 'discount_amount', 'total_price', 'notes'
        ]
    
    def validate(self, data):
        """Validate sale item data"""
        item_type = data.get('item_type')
        product = data.get('product')
        service = data.get('service')
        
        # Ensure correct item type selection
        if item_type == 'product' and not product:
            raise serializers.ValidationError("Product must be selected when item_type is 'product'")
        if item_type == 'service' and not service:
            raise serializers.ValidationError("Service must be selected when item_type is 'service'")
        
        # Ensure mutually exclusive selection
        if product and service:
            raise serializers.ValidationError("Cannot select both product and service for the same item")
        
        # Validate quantity against inventory for products
        if item_type == 'product' and product:
            # All products now have inventory tracking via signals
            if hasattr(product, 'inventory') and data.get('quantity', 0) > product.current_stock:
                raise serializers.ValidationError(
                    f"Insufficient stock for {product.name}. Available: {product.current_stock}"
                )
        
        return data


class SaleItemCreateSerializer(SaleItemSerializer):
    """Serializer for creating sale items"""
    
    def validate_unit_price(self, value):
        """Validate unit price"""
        if value <= 0:
            raise serializers.ValidationError("Unit price must be greater than 0")
        return value
    
    def validate_quantity(self, value):
        """Validate quantity"""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0")
        return value


class SaleSerializer(serializers.ModelSerializer):
    """Serializer for sales (read operations)"""
    items = SaleItemSerializer(many=True, read_only=True)
    balance_due = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    is_fully_paid = serializers.BooleanField(read_only=True)
    sale_number = serializers.CharField(read_only=True)
    
    class Meta:
        model = Sale
        fields = [
            'id', 'sale_number', 'sale_date', 'customer_name', 'customer_phone', 'customer_email',
            'subtotal', 'discount_amount', 'tax_amount', 'total_amount',
            'payment_method', 'payment_reference', 'amount_paid', 'change_amount',
            'status', 'notes', 'items', 'balance_due', 'is_fully_paid',
            'created_at', 'updated_at'
        ]


class SaleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating sales"""
    items = SaleItemCreateSerializer(many=True, write_only=True)
    sale_number = serializers.CharField(read_only=True)  # Auto-generated field
    
    class Meta:
        model = Sale
        fields = [
            'id', 'sale_number', 'sale_date', 'customer_name', 'customer_phone', 'customer_email',
            'discount_amount', 'tax_amount', 'payment_method', 'payment_reference',
            'amount_paid', 'change_amount', 'status', 'notes', 'items'
        ]
    
    def validate_items(self, value):
        """Validate that at least one item is provided"""
        if not value:
            raise serializers.ValidationError("At least one item must be provided")
        return value
    
    def validate_amount_paid(self, value):
        """Validate amount paid"""
        if value < 0:
            raise serializers.ValidationError("Amount paid cannot be negative")
        return value
    
    @transaction.atomic
    def create(self, validated_data):
        """Create sale with items and update inventory"""
        items_data = validated_data.pop('items')
        user = self.context['request'].user
        
        # Calculate totals
        subtotal = Decimal('0.00')
        total_discount = validated_data.get('discount_amount', Decimal('0.00'))
        
        # Calculate subtotal from items
        for item_data in items_data:
            quantity = item_data['quantity']
            unit_price = item_data['unit_price']
            item_discount = item_data.get('discount_amount', Decimal('0.00'))
            line_total = (quantity * unit_price) - item_discount
            subtotal += line_total
        
        # Calculate final total
        tax_amount = validated_data.get('tax_amount', Decimal('0.00'))
        total_amount = subtotal + tax_amount - total_discount
        
        if total_amount <= 0:
            raise serializers.ValidationError("Total amount must be greater than 0")
        
        # Create sale
        sale = Sale.objects.create(
            user=user,
            subtotal=subtotal,
            total_amount=total_amount,
            **validated_data
        )
        
        # Create sale items - inventory will be updated by signals
        for item_data in items_data:
            SaleItem.objects.create(sale=sale, **item_data)
        
        return sale


class SaleUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating sales (limited fields)"""
    
    class Meta:
        model = Sale
        fields = [
            'customer_name', 'customer_phone', 'customer_email',
            'payment_method', 'payment_reference', 'amount_paid',
            'change_amount', 'status', 'notes'
        ]
    
    def validate_amount_paid(self, value):
        """Validate amount paid doesn't exceed total"""
        if value < 0:
            raise serializers.ValidationError("Amount paid cannot be negative")
        return value


class SalesReportSerializer(serializers.ModelSerializer):
    """Serializer for sales reports"""
    
    class Meta:
        model = SalesReport
        fields = [
            'id', 'report_type', 'period_start', 'period_end',
            'total_sales', 'total_revenue', 'total_discounts', 'total_tax',
            'payment_method_breakdown', 'top_products', 'top_services',
            'generated_at'
        ]


class DashboardSummarySerializer(serializers.Serializer):
    """Serializer for sales dashboard summary"""
    today_sales = serializers.IntegerField()
    today_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    this_week_sales = serializers.IntegerField()
    this_week_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    this_month_sales = serializers.IntegerField()
    this_month_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # Recent sales
    recent_sales = SaleSerializer(many=True)
    
    # Payment method breakdown
    payment_methods = serializers.JSONField()
    
    # Top selling items
    top_products = serializers.JSONField()
    top_services = serializers.JSONField()


class SalesSummarySerializer(serializers.Serializer):
    """Serializer for sales summary with filters"""
    total_sales = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_discount = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_tax = serializers.DecimalField(max_digits=12, decimal_places=2)
    average_sale_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    # Breakdown by payment method
    payment_breakdown = serializers.JSONField()
    
    # Daily/weekly/monthly breakdown
    period_breakdown = serializers.JSONField()
