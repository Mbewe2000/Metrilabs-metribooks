from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import transaction, IntegrityError
from decimal import Decimal
from datetime import date, time, timedelta

from .models import ServiceCategory, Service, Worker, ServiceRecord, WorkerPerformance

User = get_user_model()


class ServiceCategoryModelTest(TestCase):
    """Test ServiceCategory model"""
    
    def test_category_creation(self):
        """Test creating a service category"""
        category = ServiceCategory.objects.create(
            name='beauty_wellness',
            description='Beauty and wellness services'
        )
        
        self.assertEqual(category.name, 'beauty_wellness')
        self.assertEqual(category.description, 'Beauty and wellness services')
        self.assertTrue(category.created_at)
        self.assertEqual(str(category), 'beauty_wellness')
    
    def test_category_unique_name(self):
        """Test that category names must be unique"""
        ServiceCategory.objects.create(name='beauty_wellness')
        
        with self.assertRaises(Exception):  # Should raise IntegrityError
            ServiceCategory.objects.create(name='beauty_wellness')


class ServiceModelTest(TestCase):
    """Test Service model"""
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123'
        )
        # Get or create the category that signals created
        self.category, _ = ServiceCategory.objects.get_or_create(
            name='beauty_wellness',
            defaults={'description': 'Beauty and wellness services'}
        )
    
    def test_service_creation_hourly(self):
        """Test creating an hourly service"""
        service = Service.objects.create(
            user=self.user1,
            name='Haircut',
            description='Professional haircut service',
            category=self.category,
            pricing_type='hourly',
            hourly_rate=Decimal('50.00')
        )
        
        self.assertEqual(service.user, self.user1)
        self.assertEqual(service.name, 'Haircut')
        self.assertEqual(service.pricing_type, 'hourly')
        self.assertEqual(service.hourly_rate, Decimal('50.00'))
        self.assertTrue(service.is_active)
        self.assertEqual(str(service), f'Haircut ({self.user1.email})')
    
    def test_service_creation_fixed(self):
        """Test creating a fixed price service"""
        service = Service.objects.create(
            user=self.user1,
            name='Manicure',
            pricing_type='fixed',
            fixed_price=Decimal('25.00')
        )
        
        self.assertEqual(service.pricing_type, 'fixed')
        self.assertEqual(service.fixed_price, Decimal('25.00'))
    
    def test_service_creation_both(self):
        """Test creating a service with both pricing options"""
        service = Service.objects.create(
            user=self.user1,
            name='Cleaning Service',
            pricing_type='both',
            hourly_rate=Decimal('30.00'),
            fixed_price=Decimal('100.00')
        )
        
        self.assertEqual(service.pricing_type, 'both')
        self.assertEqual(service.hourly_rate, Decimal('30.00'))
        self.assertEqual(service.fixed_price, Decimal('100.00'))
    
    def test_service_user_isolation(self):
        """Test that services are isolated by user"""
        service1 = Service.objects.create(
            user=self.user1,
            name='User1 Service',
            pricing_type='fixed',
            fixed_price=Decimal('50.00')
        )
        service2 = Service.objects.create(
            user=self.user2,
            name='User2 Service',
            pricing_type='fixed',
            fixed_price=Decimal('75.00')
        )
        
        user1_services = Service.objects.filter(user=self.user1)
        user2_services = Service.objects.filter(user=self.user2)
        
        self.assertEqual(user1_services.count(), 1)
        self.assertEqual(user2_services.count(), 1)
        self.assertIn(service1, user1_services)
        self.assertIn(service2, user2_services)
        self.assertNotIn(service1, user2_services)
        self.assertNotIn(service2, user1_services)
    
    def test_service_display_price(self):
        """Test service price display formatting"""
        hourly_service = Service.objects.create(
            user=self.user1,
            name='Hourly Service',
            pricing_type='hourly',
            hourly_rate=Decimal('40.00')
        )
        
        fixed_service = Service.objects.create(
            user=self.user1,
            name='Fixed Service',
            pricing_type='fixed',
            fixed_price=Decimal('60.00')
        )
        
        both_service = Service.objects.create(
            user=self.user1,
            name='Both Service',
            pricing_type='both',
            hourly_rate=Decimal('35.00'),
            fixed_price=Decimal('120.00')
        )
        
        self.assertEqual(hourly_service.get_display_price(), 'ZMW 40.00/hour')
        self.assertEqual(fixed_service.get_display_price(), 'ZMW 60.00 (fixed)')
        self.assertEqual(both_service.get_display_price(), 'ZMW 35.00/hour or ZMW 120.00 (fixed)')
    
    def test_service_unique_name_per_user(self):
        """Test that service names must be unique per user but can be same across users"""
        # Create first service for user1
        service1 = Service.objects.create(
            user=self.user1,
            name='Haircut',
            pricing_type='fixed',
            fixed_price=Decimal('50.00')
        )
        
        # Same name for same user should fail
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Service.objects.create(
                    user=self.user1,
                    name='Haircut',
                    pricing_type='fixed',
                    fixed_price=Decimal('60.00')
                )
        
        # Different name for same user should succeed
        service2 = Service.objects.create(
            user=self.user1,
            name='Manicure',
            pricing_type='fixed',
            fixed_price=Decimal('30.00')
        )
        
        # Different user should be able to use same service name
        service3 = Service.objects.create(
            user=self.user2,
            name='Haircut',
            pricing_type='fixed',
            fixed_price=Decimal('55.00')
        )
        
        self.assertEqual(service3.name, 'Haircut')
        self.assertEqual(service3.user, self.user2)
        self.assertNotEqual(service1.id, service3.id)


class WorkerModelTest(TestCase):
    """Test Worker model"""
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123'
        )
        self.service = Service.objects.create(
            user=self.user1,
            name='Haircut',
            pricing_type='fixed',
            fixed_price=Decimal('50.00')
        )
    
    def test_worker_creation(self):
        """Test creating a worker"""
        worker = Worker.objects.create(
            user=self.user1,
            name='John Doe',
            employee_id='EMP001',
            phone='+260771234567',
            email='john@example.com',
            is_owner=False,
            hired_date=date.today()
        )
        
        self.assertEqual(worker.user, self.user1)
        self.assertEqual(worker.name, 'John Doe')
        self.assertEqual(worker.employee_id, 'EMP001')
        self.assertFalse(worker.is_owner)
        self.assertTrue(worker.is_active)
        self.assertEqual(str(worker), 'John Doe')
    
    def test_owner_worker(self):
        """Test creating an owner worker"""
        owner = Worker.objects.create(
            user=self.user1,
            name='Business Owner',
            is_owner=True
        )
        
        self.assertTrue(owner.is_owner)
        self.assertEqual(str(owner), 'Business Owner (Owner)')
    
    def test_worker_user_isolation(self):
        """Test that workers are isolated by user"""
        # Note: User creation signals already create owner workers
        # Let's check that existing workers plus new ones are isolated
        initial_user1_count = Worker.objects.filter(user=self.user1).count()
        initial_user2_count = Worker.objects.filter(user=self.user2).count()
        
        worker1 = Worker.objects.create(
            user=self.user1,
            name='User1 Employee'
        )
        worker2 = Worker.objects.create(
            user=self.user2,
            name='User2 Employee'
        )
        
        user1_workers = Worker.objects.filter(user=self.user1)
        user2_workers = Worker.objects.filter(user=self.user2)
        
        self.assertEqual(user1_workers.count(), initial_user1_count + 1)
        self.assertEqual(user2_workers.count(), initial_user2_count + 1)
        self.assertIn(worker1, user1_workers)
        self.assertIn(worker2, user2_workers)
        self.assertNotIn(worker1, user2_workers)
        self.assertNotIn(worker2, user1_workers)
    
    def test_worker_services_assignment(self):
        """Test assigning services to workers"""
        service2 = Service.objects.create(
            user=self.user1,
            name='Manicure',
            pricing_type='fixed',
            fixed_price=Decimal('25.00')
        )
        
        worker = Worker.objects.create(
            user=self.user1,
            name='Jane Doe'
        )
        
        worker.services.add(self.service, service2)
        
        self.assertEqual(worker.services.count(), 2)
        self.assertIn(self.service, worker.services.all())
        self.assertIn(service2, worker.services.all())
        self.assertEqual(worker.get_services_list(), 'Haircut, Manicure')
    
    def test_worker_unique_name_per_user(self):
        """Test that worker names must be unique per user but can be same across users"""
        # Create first worker for user1
        worker1 = Worker.objects.create(
            user=self.user1,
            name='Test Employee'
        )
        
        # Same name for same user should fail
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Worker.objects.create(
                    user=self.user1,
                    name='Test Employee'
                )
        
        # Different name for same user should succeed
        worker2 = Worker.objects.create(
            user=self.user1,
            name='Another Employee'
        )
        
        # Different user should be able to use same worker name
        worker3 = Worker.objects.create(
            user=self.user2,
            name='Test Employee'
        )
        
        self.assertEqual(worker3.name, 'Test Employee')
        self.assertEqual(worker3.user, self.user2)
        self.assertNotEqual(worker1.id, worker3.id)


class ServiceRecordModelTest(TestCase):
    """Test ServiceRecord model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpass123'
        )
        self.service = Service.objects.create(
            user=self.user,
            name='Haircut',
            pricing_type='both',
            hourly_rate=Decimal('50.00'),
            fixed_price=Decimal('30.00')
        )
        self.worker = Worker.objects.create(
            user=self.user,
            name='Barber John'
        )
        self.worker.services.add(self.service)
    
    def test_service_record_hourly(self):
        """Test creating an hourly service record"""
        record = ServiceRecord.objects.create(
            user=self.user,
            worker=self.worker,
            service=self.service,
            date_performed=date.today(),
            hours_worked=Decimal('2.5'),
            used_fixed_price=False,
            hourly_rate_used=Decimal('50.00'),
            customer_name='John Customer',
            total_amount=Decimal('125.00')
        )
        
        self.assertEqual(record.user, self.user)
        self.assertEqual(record.worker, self.worker)
        self.assertEqual(record.service, self.service)
        self.assertEqual(record.hours_worked, Decimal('2.5'))
        self.assertFalse(record.used_fixed_price)
        self.assertEqual(record.total_amount, Decimal('125.00'))
        self.assertEqual(record.payment_status, 'pending')
        self.assertEqual(record.amount_paid, Decimal('0.00'))
    
    def test_service_record_fixed(self):
        """Test creating a fixed price service record"""
        record = ServiceRecord.objects.create(
            user=self.user,
            worker=self.worker,
            service=self.service,
            date_performed=date.today(),
            used_fixed_price=True,
            fixed_price_used=Decimal('30.00'),
            customer_name='Jane Customer',
            total_amount=Decimal('30.00')
        )
        
        self.assertTrue(record.used_fixed_price)
        self.assertEqual(record.fixed_price_used, Decimal('30.00'))
        self.assertEqual(record.total_amount, Decimal('30.00'))
    
    def test_service_record_auto_calculation(self):
        """Test automatic calculation of total amount"""
        record = ServiceRecord(
            user=self.user,
            worker=self.worker,
            service=self.service,
            date_performed=date.today(),
            hours_worked=Decimal('3.0'),
            used_fixed_price=False,
            hourly_rate_used=Decimal('40.00')
        )
        
        # Total amount should be auto-calculated on save
        record.save()
        
        self.assertEqual(record.total_amount, Decimal('120.00'))  # 3.0 * 40.00
    
    def test_service_record_time_calculation(self):
        """Test automatic calculation of hours from start/end time"""
        record = ServiceRecord(
            user=self.user,
            worker=self.worker,
            service=self.service,
            date_performed=date.today(),
            start_time=time(9, 0),  # 9:00 AM
            end_time=time(11, 30),  # 11:30 AM
            used_fixed_price=False,
            hourly_rate_used=Decimal('50.00')
        )
        
        record.save()
        
        self.assertEqual(record.hours_worked, Decimal('2.50'))  # 2.5 hours
        
        # Calculate total amount after hours are calculated
        if not record.total_amount:
            record.calculate_total_amount()
            record.save()
        
        self.assertEqual(record.total_amount, Decimal('125.00'))  # 2.5 * 50.00
    
    def test_service_record_payment_properties(self):
        """Test payment-related properties"""
        record = ServiceRecord.objects.create(
            user=self.user,
            worker=self.worker,
            service=self.service,
            date_performed=date.today(),
            used_fixed_price=True,
            fixed_price_used=Decimal('100.00'),
            total_amount=Decimal('100.00'),
            amount_paid=Decimal('60.00')
        )
        
        self.assertEqual(record.remaining_balance, Decimal('40.00'))
        self.assertFalse(record.is_fully_paid)
        
        # Test full payment
        record.amount_paid = Decimal('100.00')
        record.save()
        
        self.assertEqual(record.remaining_balance, Decimal('0.00'))
        self.assertTrue(record.is_fully_paid)
    
    def test_service_record_payment_status_update(self):
        """Test payment status updates"""
        record = ServiceRecord.objects.create(
            user=self.user,
            worker=self.worker,
            service=self.service,
            date_performed=date.today(),
            used_fixed_price=True,
            fixed_price_used=Decimal('100.00'),
            total_amount=Decimal('100.00')
        )
        
        # Test pending status
        record.update_payment_status()
        self.assertEqual(record.payment_status, 'pending')
        
        # Test partial payment
        record.amount_paid = Decimal('50.00')
        record.update_payment_status()
        self.assertEqual(record.payment_status, 'partially_paid')
        
        # Test full payment
        record.amount_paid = Decimal('100.00')
        record.update_payment_status()
        self.assertEqual(record.payment_status, 'paid')


class WorkerPerformanceModelTest(TestCase):
    """Test WorkerPerformance model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpass123'
        )
        self.service1 = Service.objects.create(
            user=self.user,
            name='Haircut',
            pricing_type='hourly',
            hourly_rate=Decimal('50.00')
        )
        self.service2 = Service.objects.create(
            user=self.user,
            name='Manicure',
            pricing_type='fixed',
            fixed_price=Decimal('25.00')
        )
        self.worker = Worker.objects.create(
            user=self.user,
            name='Test Worker'
        )
        self.worker.services.add(self.service1, self.service2)
    
    def test_performance_generation(self):
        """Test generating worker performance data"""
        today = date.today()
        
        # Create some service records
        ServiceRecord.objects.create(
            user=self.user,
            worker=self.worker,
            service=self.service1,
            date_performed=today,
            hours_worked=Decimal('2.0'),
            used_fixed_price=False,
            hourly_rate_used=Decimal('50.00'),
            total_amount=Decimal('100.00')
        )
        
        ServiceRecord.objects.create(
            user=self.user,
            worker=self.worker,
            service=self.service2,
            date_performed=today,
            used_fixed_price=True,
            fixed_price_used=Decimal('25.00'),
            total_amount=Decimal('25.00')
        )
        
        ServiceRecord.objects.create(
            user=self.user,
            worker=self.worker,
            service=self.service1,
            date_performed=today,
            hours_worked=Decimal('1.5'),
            used_fixed_price=False,
            hourly_rate_used=Decimal('50.00'),
            total_amount=Decimal('75.00')
        )
        
        # Generate performance
        performance = WorkerPerformance.generate_for_period(
            self.user, today.year, today.month
        )
        
        self.assertIsNotNone(performance)
        self.assertEqual(performance.worker, self.worker)
        self.assertEqual(performance.year, today.year)
        self.assertEqual(performance.month, today.month)
        self.assertEqual(performance.total_services_performed, 3)
        self.assertEqual(performance.total_hours_worked, Decimal('3.50'))  # 2.0 + 1.5
        self.assertEqual(performance.total_revenue_generated, Decimal('200.00'))  # 100 + 25 + 75
        self.assertEqual(performance.average_hourly_rate, Decimal('50.00'))  # Only hourly services
        
        # Check services breakdown
        self.assertIn('Haircut', performance.services_breakdown)
        self.assertIn('Manicure', performance.services_breakdown)
        self.assertEqual(performance.services_breakdown['Haircut'], 2)
        self.assertEqual(performance.services_breakdown['Manicure'], 1)
    
    def test_performance_string_representation(self):
        """Test performance string representation"""
        performance = WorkerPerformance.objects.create(
            user=self.user,
            worker=self.worker,
            year=2025,
            month=7
        )
        
        self.assertEqual(str(performance), 'Test Worker - 2025-07')


class ServiceSignalsTest(TestCase):
    """Test service-related signals"""
    
    def test_user_setup_signal(self):
        """Test that new users get default setup"""
        user = User.objects.create_user(
            email='newuser@example.com',
            password='testpass123'
        )
        
        # Check that default categories were created
        categories = ServiceCategory.objects.all()
        self.assertGreater(categories.count(), 0)
        
        # Check that expected categories exist
        expected_categories = ['labor', 'beauty_wellness', 'cleaning', 'repairs']
        for category_name in expected_categories:
            self.assertTrue(
                ServiceCategory.objects.filter(name=category_name).exists(),
                f"Category {category_name} should exist"
            )
        
        # Check that owner worker was created
        owner_worker = Worker.objects.filter(user=user, is_owner=True).first()
        self.assertIsNotNone(owner_worker)
        self.assertTrue(owner_worker.is_owner)
        self.assertTrue(owner_worker.is_active)
        self.assertIn('Owner', owner_worker.name)
    
    def test_performance_update_signal(self):
        """Test that performance is updated when service records are created"""
        user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123'
        )
        service = Service.objects.create(
            user=user,
            name='Test Service',
            pricing_type='fixed',
            fixed_price=Decimal('50.00')
        )
        worker = Worker.objects.create(
            user=user,
            name='Test Worker'
        )
        worker.services.add(service)
        
        today = date.today()
        
        # Create a service record (should trigger performance update)
        ServiceRecord.objects.create(
            user=user,
            worker=worker,
            service=service,
            date_performed=today,
            used_fixed_price=True,
            fixed_price_used=Decimal('50.00'),
            total_amount=Decimal('50.00')
        )
        
        # Check that performance record was created
        performance = WorkerPerformance.objects.filter(
            user=user,
            worker=worker,
            year=today.year,
            month=today.month
        ).first()
        
        self.assertIsNotNone(performance)
        self.assertEqual(performance.total_services_performed, 1)
        self.assertEqual(performance.total_revenue_generated, Decimal('50.00'))
