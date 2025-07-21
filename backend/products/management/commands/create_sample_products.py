from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from products.models import ProductCategory, Product, ProductInventory, StockMovement
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample product data for testing'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating sample product data...'))
        
        # Create sample categories
        categories_data = [
            {'name': 'Beverages', 'description': 'Drinks and beverages'},
            {'name': 'Electronics', 'description': 'Electronic devices and accessories'},
            {'name': 'Services', 'description': 'Service-based offerings'},
            {'name': 'Food Items', 'description': 'Food products and groceries'},
            {'name': 'Household Items', 'description': 'Home and household products'},
            {'name': 'Agriculture', 'description': 'Agricultural products and supplies'},
        ]
        
        # Get or create superuser for created_by field
        try:
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                admin_user = User.objects.create_superuser(
                    email='admin@metribooks.com',
                    password='admin123',
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating admin user: {e}'))
            return
        
        categories = {}
        for cat_data in categories_data:
            category, created = ProductCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'description': cat_data['description'],
                    'created_by': admin_user
                }
            )
            categories[cat_data['name']] = category
            if created:
                self.stdout.write(f'Created category: {category.name}')
        
        # Create sample products
        products_data = [
            # Beverages
            {
                'name': 'Coca Cola 500ml',
                'category': 'Beverages',
                'selling_price': Decimal('8.50'),
                'cost_price': Decimal('6.00'),
                'unit_of_measure': 'bottle',
                'description': 'Coca Cola soft drink 500ml bottle',
                'initial_stock': Decimal('100'),
                'reorder_level': Decimal('20'),
            },
            {
                'name': 'Mosi Lager 750ml',
                'category': 'Beverages',
                'selling_price': Decimal('15.00'),
                'cost_price': Decimal('12.00'),
                'unit_of_measure': 'bottle',
                'description': 'Local Zambian beer 750ml bottle',
                'initial_stock': Decimal('50'),
                'reorder_level': Decimal('15'),
            },
            
            # Electronics
            {
                'name': 'Samsung Galaxy A54',
                'category': 'Electronics',
                'selling_price': Decimal('3500.00'),
                'cost_price': Decimal('3000.00'),
                'unit_of_measure': 'each',
                'description': 'Samsung Galaxy A54 smartphone',
                'initial_stock': Decimal('10'),
                'reorder_level': Decimal('3'),
            },
            {
                'name': 'USB Cable Type-C',
                'category': 'Electronics',
                'selling_price': Decimal('45.00'),
                'cost_price': Decimal('30.00'),
                'unit_of_measure': 'each',
                'description': 'USB Type-C charging cable',
                'initial_stock': Decimal('25'),
                'reorder_level': Decimal('10'),
            },
            
            # Food Items
            {
                'name': 'Mealie Meal 25kg',
                'category': 'Food Items',
                'selling_price': Decimal('180.00'),
                'cost_price': Decimal('150.00'),
                'unit_of_measure': 'bag',
                'description': 'White maize meal 25kg bag',
                'initial_stock': Decimal('30'),
                'reorder_level': Decimal('10'),
            },
            {
                'name': 'Rice 2kg',
                'category': 'Food Items',
                'selling_price': Decimal('65.00'),
                'cost_price': Decimal('50.00'),
                'unit_of_measure': 'pack',
                'description': 'Long grain white rice 2kg pack',
                'initial_stock': Decimal('40'),
                'reorder_level': Decimal('15'),
            },
            
            # Services
            {
                'name': 'Mobile Money Transfer',
                'category': 'Services',
                'selling_price': Decimal('5.00'),
                'cost_price': Decimal('2.00'),
                'unit_of_measure': 'each',
                'description': 'Mobile money transfer service',
                'initial_stock': Decimal('0'),  # Services don't have stock
                'reorder_level': None,
            },
            
            # Agriculture
            {
                'name': 'Fertilizer NPK 50kg',
                'category': 'Agriculture',
                'selling_price': Decimal('450.00'),
                'cost_price': Decimal('380.00'),
                'unit_of_measure': 'bag',
                'description': 'NPK fertilizer 50kg bag',
                'initial_stock': Decimal('20'),
                'reorder_level': Decimal('5'),
            },
        ]
        
        for product_data in products_data:
            category = categories[product_data['category']]
            
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                category=category,
                defaults={
                    'selling_price': product_data['selling_price'],
                    'cost_price': product_data['cost_price'],
                    'unit_of_measure': product_data['unit_of_measure'],
                    'description': product_data['description'],
                    'created_by': admin_user,
                }
            )
            
            if created:
                self.stdout.write(f'Created product: {product.name}')
                
                # Set up inventory
                inventory = product.inventory
                inventory.quantity_in_stock = product_data['initial_stock']
                inventory.reorder_level = product_data['reorder_level']
                inventory.save()
                
                # Create opening stock movement if there's initial stock
                if product_data['initial_stock'] > 0:
                    StockMovement.objects.create(
                        product=product,
                        movement_type='opening_stock',
                        quantity=product_data['initial_stock'],
                        quantity_before=Decimal('0'),
                        quantity_after=product_data['initial_stock'],
                        notes='Initial stock setup',
                        created_by=admin_user,
                    )
                    self.stdout.write(f'Set initial stock: {product_data["initial_stock"]} {product.unit_of_measure} for {product.name}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created sample data:\n'
                f'- {ProductCategory.objects.count()} categories\n'
                f'- {Product.objects.count()} products\n'
                f'- {StockMovement.objects.count()} stock movements'
            )
        )
