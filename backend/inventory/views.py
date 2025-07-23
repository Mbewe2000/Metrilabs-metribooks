from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q, Sum, Count, Case, When, DecimalField, F
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from decimal import Decimal
import logging

from .models import Product, ProductCategory, Inventory, StockMovement, StockAlert
from .serializers import (
    ProductSerializer,
    ProductCreateUpdateSerializer,
    ProductCategorySerializer,
    StockMovementSerializer,
    StockAdjustmentSerializer,
    StockAlertSerializer,
    ProductSummarySerializer,
    InventorySerializer
)

# Get logger
logger = logging.getLogger('inventory')


# ===============================
# Product Management Views
# ===============================

class ProductListView(generics.ListAPIView):
    """List all products for the authenticated user"""
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Product.objects.filter(user=self.request.user).select_related(
            'category', 'inventory'
        ).prefetch_related('stock_movements')
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__name=category)
        
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
        
        # Filter by stock status
        stock_status = self.request.query_params.get('stock_status')
        if stock_status == 'low_stock':
            queryset = queryset.filter(
                inventory__quantity_in_stock__lte=F('inventory__reorder_level')
            )
        elif stock_status == 'out_of_stock':
            queryset = queryset.filter(inventory__quantity_in_stock=0)
        
        return queryset.order_by('name')


class ProductCreateView(generics.CreateAPIView):
    """Create a new product"""
    serializer_class = ProductCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @method_decorator(ratelimit(key='user', rate='50/h', method='POST'))
    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                response = super().create(request, *args, **kwargs)
                
                logger.info(f"Product created by user: {request.user.email}")
                return Response({
                    'success': True,
                    'message': 'Product created successfully',
                    'data': response.data
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"Error creating product for user {request.user.email}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error creating product',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a product"""
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Product.objects.filter(user=self.request.user).select_related(
            'category', 'inventory'
        )
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ProductCreateUpdateSerializer
        return ProductSerializer
    
    @method_decorator(ratelimit(key='user', rate='100/h', method=['PUT', 'PATCH']))
    def update(self, request, *args, **kwargs):
        try:
            response = super().update(request, *args, **kwargs)
            logger.info(f"Product updated by user: {request.user.email}")
            return Response({
                'success': True,
                'message': 'Product updated successfully',
                'data': response.data
            })
        except Exception as e:
            logger.error(f"Error updating product for user {request.user.email}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error updating product',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def destroy(self, request, *args, **kwargs):
        from django.http import Http404
        
        try:
            instance = self.get_object()
            product_name = instance.name
            instance.delete()
            
            logger.info(f"Product '{product_name}' deleted by user: {request.user.email}")
            return Response({
                'success': True,
                'message': 'Product deleted successfully'
            })
        except Http404:
            # Let the Http404 exception bubble up naturally to return 404
            raise
        except Exception as e:
            logger.error(f"Error deleting product for user {request.user.email}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error deleting product',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===============================
# Inventory Management Views
# ===============================

class StockAdjustmentView(APIView):
    """Manually adjust stock levels"""
    permission_classes = [permissions.IsAuthenticated]
    
    @method_decorator(ratelimit(key='user', rate='200/h', method='POST'))
    def post(self, request, product_id):
        try:
            product = get_object_or_404(
                Product.objects.select_related('inventory'),
                id=product_id,
                user=request.user
            )
            
            serializer = StockAdjustmentSerializer(
                data=request.data,
                context={'product': product}
            )
            
            if serializer.is_valid():
                with transaction.atomic():
                    adjustment_type = serializer.validated_data['adjustment_type']
                    quantity = serializer.validated_data['quantity']
                    movement_type = serializer.validated_data['movement_type']
                    reference_number = serializer.validated_data.get('reference_number', '')
                    notes = serializer.validated_data.get('notes', '')
                    
                    # Get current inventory
                    inventory = product.inventory
                    quantity_before = inventory.quantity_in_stock
                    
                    # Calculate new quantity
                    if adjustment_type == 'add':
                        movement_quantity = quantity
                    else:  # remove
                        movement_quantity = -quantity
                    
                    quantity_after = quantity_before + movement_quantity
                    
                    # Update inventory
                    inventory.quantity_in_stock = quantity_after
                    inventory.save()
                    
                    # Create stock movement record
                    StockMovement.objects.create(
                        product=product,
                        movement_type=movement_type,
                        quantity=movement_quantity,
                        quantity_before=quantity_before,
                        quantity_after=quantity_after,
                        reference_number=reference_number,
                        notes=notes,
                        created_by=request.user
                    )
                    
                    # Check for stock alerts
                    self._check_stock_alerts(product)
                    
                    logger.info(
                        f"Stock adjusted for {product.name}: {adjustment_type} {quantity} "
                        f"by user: {request.user.email}"
                    )
                    
                    return Response({
                        'success': True,
                        'message': f'Stock {adjustment_type}ed successfully',
                        'data': {
                            'product_name': product.name,
                            'quantity_before': quantity_before,
                            'quantity_after': quantity_after,
                            'adjustment': movement_quantity
                        }
                    })
            
            return Response({
                'success': False,
                'message': 'Invalid data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error adjusting stock for user {request.user.email}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error adjusting stock',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _check_stock_alerts(self, product):
        """Check and create stock alerts if needed"""
        inventory = product.inventory
        current_stock = inventory.quantity_in_stock
        
        # Check for out of stock
        if current_stock <= 0:
            StockAlert.objects.get_or_create(
                product=product,
                alert_type='out_of_stock',
                is_resolved=False,
                defaults={
                    'current_stock': current_stock,
                    'reorder_level': inventory.reorder_level
                }
            )
        # Check for low stock
        elif inventory.reorder_level and current_stock <= inventory.reorder_level:
            StockAlert.objects.get_or_create(
                product=product,
                alert_type='low_stock',
                is_resolved=False,
                defaults={
                    'current_stock': current_stock,
                    'reorder_level': inventory.reorder_level
                }
            )


# ===============================
# Stock Movement Views
# ===============================

class StockMovementListView(generics.ListAPIView):
    """List stock movements"""
    serializer_class = StockMovementSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = StockMovement.objects.filter(
            product__user=self.request.user
        ).select_related('product', 'created_by')
        
        # Filter by product
        product_id = self.request.query_params.get('product_id')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        # Filter by movement type
        movement_type = self.request.query_params.get('movement_type')
        if movement_type:
            queryset = queryset.filter(movement_type=movement_type)
        
        return queryset.order_by('-created_at')


# ===============================
# Category Management Views
# ===============================

class ProductCategoryListView(generics.ListCreateAPIView):
    """List and create product categories"""
    serializer_class = ProductCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ProductCategory.objects.filter(is_active=True).order_by('name')


# ===============================
# Alert Management Views
# ===============================

class StockAlertListView(generics.ListAPIView):
    """List stock alerts"""
    serializer_class = StockAlertSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = StockAlert.objects.filter(
            product__user=self.request.user
        ).select_related('product', 'product__category')
        
        # Filter by resolved status
        is_resolved = self.request.query_params.get('is_resolved')
        if is_resolved is not None:
            queryset = queryset.filter(is_resolved=is_resolved.lower() == 'true')
        
        # Filter by alert type
        alert_type = self.request.query_params.get('alert_type')
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)
        
        return queryset.order_by('-created_at')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def resolve_stock_alert(request, alert_id):
    """Resolve a stock alert"""
    try:
        alert = get_object_or_404(
            StockAlert,
            id=alert_id,
            product__user=request.user
        )
        
        alert.is_resolved = True
        alert.resolved_at = timezone.now()
        alert.save()
        
        logger.info(f"Stock alert resolved by user: {request.user.email}")
        
        return Response({
            'success': True,
            'message': 'Alert resolved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error resolving alert for user {request.user.email}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error resolving alert',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===============================
# Dashboard & Reports Views
# ===============================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@ratelimit(key='user', rate='100/h', method='GET')
def inventory_dashboard(request):
    """Get inventory dashboard data"""
    try:
        user = request.user
        
        # Basic counts
        total_products = Product.objects.filter(user=user, is_active=True).count()
        total_categories = ProductCategory.objects.filter(
            products__user=user,
            is_active=True
        ).distinct().count()
        
        # Stock alerts
        low_stock_count = StockAlert.objects.filter(
            product__user=user,
            alert_type='low_stock',
            is_resolved=False
        ).count()
        
        out_of_stock_count = StockAlert.objects.filter(
            product__user=user,
            alert_type='out_of_stock',
            is_resolved=False
        ).count()
        
        # Inventory value
        products_with_cost = Product.objects.filter(
            user=user,
            is_active=True,
            cost_price__isnull=False
        ).select_related('inventory')
        
        total_cost_value = sum(
            (product.current_stock * product.cost_price)
            for product in products_with_cost
        )
        
        total_selling_value = sum(
            (product.current_stock * product.selling_price)
            for product in Product.objects.filter(user=user, is_active=True).select_related('inventory')
        )
        
        # Recent stock movements
        recent_movements = StockMovementSerializer(
            StockMovement.objects.filter(
                product__user=user
            ).select_related('product', 'created_by').order_by('-created_at')[:10],
            many=True
        ).data
        
        # Low stock products
        low_stock_products = ProductSummarySerializer(
            Product.objects.filter(
                user=user,
                is_active=True,
                inventory__quantity_in_stock__lte=F('inventory__reorder_level')
            ).select_related('category', 'inventory')[:10],
            many=True
        ).data
        
        return Response({
            'success': True,
            'data': {
                'summary': {
                    'total_products': total_products,
                    'total_categories': total_categories,
                    'low_stock_count': low_stock_count,
                    'out_of_stock_count': out_of_stock_count,
                    'total_cost_value': total_cost_value,
                    'total_selling_value': total_selling_value,
                },
                'recent_movements': recent_movements,
                'low_stock_products': low_stock_products,
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard data for user {request.user.email}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error getting dashboard data',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@ratelimit(key='user', rate='50/h', method='GET')
def stock_summary_report(request):
    """Get stock summary report"""
    try:
        user = request.user
        
        products = Product.objects.filter(
            user=user,
            is_active=True
        ).select_related('category', 'inventory').order_by('name')
        
        report_data = []
        for product in products:
            inventory = product.inventory
            report_data.append({
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'category': product.category.get_name_display() if product.category else 'Uncategorized',
                'unit': product.get_unit_of_measure_display(),
                'current_stock': inventory.quantity_in_stock,
                'reorder_level': inventory.reorder_level,
                'selling_price': product.selling_price,
                'cost_price': product.cost_price,
                'stock_value_cost': product.stock_value,
                'stock_value_selling': product.selling_value,
                'stock_status': inventory.stock_status,
                'last_updated': inventory.last_stock_update,
            })
        
        return Response({
            'success': True,
            'data': report_data
        })
        
    except Exception as e:
        logger.error(f"Error generating stock report for user {request.user.email}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error generating stock report',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@ratelimit(key='user', rate='30/h', method='GET')
def inventory_valuation_report(request):
    """Get inventory valuation report"""
    try:
        user = request.user
        
        # Get products with cost prices
        products = Product.objects.filter(
            user=user,
            is_active=True,
            cost_price__isnull=False
        ).select_related('category', 'inventory').order_by('category__name', 'name')
        
        report_data = []
        category_totals = {}
        
        for product in products:
            inventory = product.inventory
            stock_value = product.stock_value or 0
            category_name = product.category.get_name_display() if product.category else 'Uncategorized'
            
            report_data.append({
                'product_name': product.name,
                'category': category_name,
                'current_stock': inventory.quantity_in_stock,
                'cost_price': product.cost_price,
                'total_value': stock_value,
            })
            
            # Add to category totals
            if category_name not in category_totals:
                category_totals[category_name] = 0
            category_totals[category_name] += stock_value
        
        total_value = sum(category_totals.values())
        
        return Response({
            'success': True,
            'data': {
                'products': report_data,
                'category_totals': category_totals,
                'total_inventory_value': total_value,
                'currency': 'ZMW'
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating valuation report for user {request.user.email}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error generating valuation report',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
