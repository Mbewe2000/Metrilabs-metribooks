from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Sum, F, Q, Value, Case, When
from django.db.models.functions import Coalesce
from django.db import transaction
from django.utils import timezone
from django_ratelimit.core import is_ratelimited
from decimal import Decimal
import logging

from .models import ProductCategory, Product, ProductInventory, StockMovement
from .serializers import (
    ProductCategorySerializer,
    ProductSerializer,
    ProductCreateUpdateSerializer,
    ProductInventorySerializer,
    StockMovementSerializer,
    StockMovementCreateSerializer,
    InventoryReportSerializer,
    LowStockAlertSerializer,
    InventoryValuationSerializer
)

# Get logger
logger = logging.getLogger('products')


# Product Category Views
class ProductCategoryListCreateView(generics.ListCreateAPIView):
    """List all categories or create a new category"""
    serializer_class = ProductCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ProductCategory.objects.all()

    def perform_create(self, serializer):
        # Rate limiting check
        if is_ratelimited(self.request, group='category_create', key='ip', rate='20/m', method='POST'):
            logger.warning(f"Rate limit exceeded for category creation by IP: {self.request.META.get('REMOTE_ADDR')}")
            return Response({
                'success': False,
                'message': 'Rate limit exceeded. Please try again later.',
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        serializer.save(created_by=self.request.user)
        logger.info(f"Category created: {serializer.instance.name} by user: {self.request.user.email}")


class ProductCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a category"""
    serializer_class = ProductCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = ProductCategory.objects.all()

    def perform_update(self, serializer):
        # Rate limiting check
        if is_ratelimited(self.request, group='category_update', key='ip', rate='30/m', method='PUT'):
            logger.warning(f"Rate limit exceeded for category update by IP: {self.request.META.get('REMOTE_ADDR')}")
            return Response({
                'success': False,
                'message': 'Rate limit exceeded. Please try again later.',
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        serializer.save()
        logger.info(f"Category updated: {serializer.instance.name} by user: {self.request.user.email}")

    def perform_destroy(self, instance):
        # Check if category has products
        if instance.products.exists():
            logger.warning(f"Attempt to delete category with products: {instance.name} by user: {self.request.user.email}")
            return Response({
                'success': False,
                'message': 'Cannot delete category that contains products. Move or delete products first.',
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"Category deleted: {instance.name} by user: {self.request.user.email}")
        instance.delete()


# Product Views
class ProductListCreateView(generics.ListCreateAPIView):
    """List all products or create a new product"""
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProductCreateUpdateSerializer
        return ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.select_related('category', 'inventory').all()
        
        # Filter by category
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Search by name or SKU
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(sku__icontains=search)
            )
        
        # Filter by low stock
        low_stock = self.request.query_params.get('low_stock')
        if low_stock == 'true':
            queryset = queryset.filter(
                inventory__reorder_level__isnull=False,
                inventory__quantity_in_stock__lte=F('inventory__reorder_level')
            )
        
        return queryset

    def perform_create(self, serializer):
        # Rate limiting check
        if is_ratelimited(self.request, group='product_create', key='ip', rate='15/m', method='POST'):
            logger.warning(f"Rate limit exceeded for product creation by IP: {self.request.META.get('REMOTE_ADDR')}")
            return Response({
                'success': False,
                'message': 'Rate limit exceeded. Please try again later.',
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        with transaction.atomic():
            product = serializer.save(created_by=self.request.user)
            # Create inventory record for the product
            ProductInventory.objects.create(product=product)
            logger.info(f"Product created: {product.name} by user: {self.request.user.email}")


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a product"""
    permission_classes = [permissions.IsAuthenticated]
    queryset = Product.objects.select_related('category', 'inventory').all()

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ProductCreateUpdateSerializer
        return ProductSerializer

    def perform_update(self, serializer):
        # Rate limiting check
        if is_ratelimited(self.request, group='product_update', key='ip', rate='30/m', method='PUT'):
            logger.warning(f"Rate limit exceeded for product update by IP: {self.request.META.get('REMOTE_ADDR')}")
            return Response({
                'success': False,
                'message': 'Rate limit exceeded. Please try again later.',
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        serializer.save()
        logger.info(f"Product updated: {serializer.instance.name} by user: {self.request.user.email}")

    def perform_destroy(self, instance):
        # Check if product has stock movements
        if instance.stock_movements.exists():
            logger.warning(f"Attempt to delete product with stock movements: {instance.name} by user: {self.request.user.email}")
            return Response({
                'success': False,
                'message': 'Cannot delete product with stock movement history. Deactivate instead.',
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"Product deleted: {instance.name} by user: {self.request.user.email}")
        instance.delete()


# Inventory Views
class ProductInventoryUpdateView(generics.RetrieveUpdateAPIView):
    """Update product inventory settings"""
    serializer_class = ProductInventorySerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = ProductInventory.objects.select_related('product').all()
    lookup_field = 'product_id'

    def perform_update(self, serializer):
        # Rate limiting check
        if is_ratelimited(self.request, group='inventory_update', key='ip', rate='20/m', method='PUT'):
            logger.warning(f"Rate limit exceeded for inventory update by IP: {self.request.META.get('REMOTE_ADDR')}")
            return Response({
                'success': False,
                'message': 'Rate limit exceeded. Please try again later.',
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        serializer.save()
        logger.info(f"Inventory updated for product: {serializer.instance.product.name} by user: {self.request.user.email}")


# Stock Movement Views
class StockMovementListCreateView(generics.ListCreateAPIView):
    """List all stock movements or create a new movement"""
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return StockMovementCreateSerializer
        return StockMovementSerializer

    def get_queryset(self):
        queryset = StockMovement.objects.select_related('product', 'created_by').all()
        
        # Filter by product
        product_id = self.request.query_params.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        # Filter by movement type
        movement_type = self.request.query_params.get('movement_type')
        if movement_type:
            queryset = queryset.filter(movement_type=movement_type)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        return queryset

    def perform_create(self, serializer):
        # Rate limiting check
        if is_ratelimited(self.request, group='stock_movement', key='ip', rate='30/m', method='POST'):
            logger.warning(f"Rate limit exceeded for stock movement by IP: {self.request.META.get('REMOTE_ADDR')}")
            return Response({
                'success': False,
                'message': 'Rate limit exceeded. Please try again later.',
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        with transaction.atomic():
            product = serializer.validated_data['product']
            quantity = serializer.validated_data['quantity']
            
            # Get or create inventory
            inventory, created = ProductInventory.objects.get_or_create(product=product)
            
            # Record before and after quantities
            quantity_before = inventory.quantity_in_stock
            quantity_after = quantity_before + quantity
            
            # Ensure stock doesn't go negative
            if quantity_after < 0:
                logger.warning(f"Attempt to create negative stock for product: {product.name} by user: {self.request.user.email}")
                return Response({
                    'success': False,
                    'message': f'Insufficient stock. Current stock: {quantity_before} {product.unit_of_measure}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update inventory
            inventory.quantity_in_stock = quantity_after
            if quantity > 0:  # Stock in
                inventory.last_restocked = timezone.now()
            inventory.save()
            
            # Create stock movement record
            movement = serializer.save(
                created_by=self.request.user,
                quantity_before=quantity_before,
                quantity_after=quantity_after
            )
            
            logger.info(f"Stock movement created: {movement.movement_type} {quantity} for {product.name} by user: {self.request.user.email}")


# Report Views
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def inventory_summary_report(request):
    """Get comprehensive inventory summary report"""
    try:
        # Rate limiting check
        if is_ratelimited(request, group='reports', key='ip', rate='10/m', method='GET'):
            logger.warning(f"Rate limit exceeded for inventory report by IP: {request.META.get('REMOTE_ADDR')}")
            return Response({
                'success': False,
                'message': 'Rate limit exceeded. Please try again later.',
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Get all products with inventory data
        products = Product.objects.select_related('category', 'inventory').filter(is_active=True)
        
        report_data = []
        for product in products:
            inventory = getattr(product, 'inventory', None)
            if inventory:
                report_data.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'category_name': product.category.name,
                    'sku': product.sku or '',
                    'unit_of_measure': product.unit_of_measure,
                    'quantity_in_stock': inventory.quantity_in_stock,
                    'reorder_level': inventory.reorder_level,
                    'selling_price': product.selling_price,
                    'cost_price': product.cost_price,
                    'stock_value_cost': inventory.stock_value_cost,
                    'stock_value_selling': inventory.stock_value_selling,
                    'is_low_stock': inventory.is_low_stock,
                    'last_restocked': inventory.last_restocked,
                })
        
        serializer = InventoryReportSerializer(report_data, many=True)
        logger.info(f"Inventory summary report generated for user: {request.user.email}")
        
        return Response({
            'success': True,
            'message': 'Inventory summary report generated successfully',
            'data': serializer.data,
            'total_products': len(report_data)
        })
        
    except Exception as e:
        logger.error(f"Error generating inventory report for user {request.user.email}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error generating inventory report',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def low_stock_alerts(request):
    """Get low stock alerts"""
    try:
        # Rate limiting check
        if is_ratelimited(request, group='reports', key='ip', rate='15/m', method='GET'):
            logger.warning(f"Rate limit exceeded for low stock alerts by IP: {request.META.get('REMOTE_ADDR')}")
            return Response({
                'success': False,
                'message': 'Rate limit exceeded. Please try again later.',
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Get products with low stock
        low_stock_products = Product.objects.select_related('category', 'inventory').filter(
            is_active=True,
            inventory__reorder_level__isnull=False,
            inventory__quantity_in_stock__lte=F('inventory__reorder_level')
        )
        
        alerts_data = []
        for product in low_stock_products:
            inventory = product.inventory
            shortage = inventory.reorder_level - inventory.quantity_in_stock
            alerts_data.append({
                'product_id': product.id,
                'product_name': product.name,
                'category_name': product.category.name,
                'sku': product.sku or '',
                'current_stock': inventory.quantity_in_stock,
                'reorder_level': inventory.reorder_level,
                'unit_of_measure': product.unit_of_measure,
                'shortage': shortage,
            })
        
        serializer = LowStockAlertSerializer(alerts_data, many=True)
        logger.info(f"Low stock alerts generated for user: {request.user.email}")
        
        return Response({
            'success': True,
            'message': 'Low stock alerts generated successfully',
            'data': serializer.data,
            'total_alerts': len(alerts_data)
        })
        
    except Exception as e:
        logger.error(f"Error generating low stock alerts for user {request.user.email}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error generating low stock alerts',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def inventory_valuation_report(request):
    """Get inventory valuation report"""
    try:
        # Rate limiting check
        if is_ratelimited(request, group='reports', key='ip', rate='10/m', method='GET'):
            logger.warning(f"Rate limit exceeded for valuation report by IP: {request.META.get('REMOTE_ADDR')}")
            return Response({
                'success': False,
                'message': 'Rate limit exceeded. Please try again later.',
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Get valuation data
        products = Product.objects.select_related('category', 'inventory').filter(is_active=True)
        
        total_stock_value_cost = Decimal('0.00')
        total_stock_value_selling = Decimal('0.00')
        categories_breakdown = {}
        low_stock_count = 0
        
        for product in products:
            inventory = getattr(product, 'inventory', None)
            if inventory:
                # Calculate values
                cost_value = inventory.stock_value_cost or Decimal('0.00')
                selling_value = inventory.stock_value_selling or Decimal('0.00')
                
                total_stock_value_cost += cost_value
                total_stock_value_selling += selling_value
                
                # Category breakdown
                category_name = product.category.name
                if category_name not in categories_breakdown:
                    categories_breakdown[category_name] = {
                        'category': category_name,
                        'products_count': 0,
                        'total_cost_value': Decimal('0.00'),
                        'total_selling_value': Decimal('0.00'),
                    }
                
                categories_breakdown[category_name]['products_count'] += 1
                categories_breakdown[category_name]['total_cost_value'] += cost_value
                categories_breakdown[category_name]['total_selling_value'] += selling_value
                
                # Low stock check
                if inventory.is_low_stock:
                    low_stock_count += 1
        
        report_data = {
            'total_products': products.count(),
            'total_stock_value_cost': total_stock_value_cost,
            'total_stock_value_selling': total_stock_value_selling,
            'total_potential_profit': total_stock_value_selling - total_stock_value_cost,
            'categories_breakdown': list(categories_breakdown.values()),
            'low_stock_count': low_stock_count,
        }
        
        serializer = InventoryValuationSerializer(report_data)
        logger.info(f"Inventory valuation report generated for user: {request.user.email}")
        
        return Response({
            'success': True,
            'message': 'Inventory valuation report generated successfully',
            'data': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Error generating valuation report for user {request.user.email}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error generating inventory valuation report',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
