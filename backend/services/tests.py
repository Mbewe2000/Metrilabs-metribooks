from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from decimal import Decimal
from datetime import date
from django.contrib.auth import get_user_model
from .models import ServiceCategory, Service, WorkRecord
from employees.models import Employee

User = get_user_model()


class ServiceModelTest(TestCase):
    """Test cases for Service models"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = ServiceCategory.objects.create(
            name="Beauty Services",
            description="Hair, nails, and beauty treatments"
        )
        
        self.hourly_service = Service.objects.create(
            name="Hair Washing",
            category=self.category,
            pricing_type='hourly',
            hourly_rate=Decimal('25.00')
        )
        
        self.fixed_service = Service.objects.create(
            name="Haircut",
            category=self.category,
            pricing_type='fixed',
            fixed_price=Decimal('50.00')
        )
        
        self.employee = Employee.objects.create(
            employee_id='EMP001',
            employee_name='Jane Doe',
            phone_number='+1234567890',
            employment_type='full_time',
            pay=Decimal('3000.00')
        )
    
    def test_service_creation(self):
        """Test creating services"""
        self.assertEqual(self.hourly_service.name, "Hair Washing")
        self.assertEqual(self.hourly_service.pricing_type, 'hourly')
        self.assertEqual(self.hourly_service.hourly_rate, Decimal('25.00'))
        
        self.assertEqual(self.fixed_service.name, "Haircut")
        self.assertEqual(self.fixed_service.pricing_type, 'fixed')
        self.assertEqual(self.fixed_service.fixed_price, Decimal('50.00'))
    
    def test_service_price_display(self):
        """Test service price display property"""
        self.assertEqual(self.hourly_service.price_display, "ZMW 25.00/hour")
        self.assertEqual(self.fixed_service.price_display, "ZMW 50.00")
    
    def test_work_record_hourly_calculation(self):
        """Test work record total calculation for hourly service"""
        work_record = WorkRecord.objects.create(
            user=self.user,
            worker_type='employee',
            employee=self.employee,
            service=self.hourly_service,
            date_of_work=date.today(),
            hours_worked=Decimal('3.5')
        )
        
        expected_total = Decimal('25.00') * Decimal('3.5')
        self.assertEqual(work_record.total_amount, expected_total)
    
    def test_work_record_fixed_calculation(self):
        """Test work record total calculation for fixed service"""
        work_record = WorkRecord.objects.create(
            user=self.user,
            worker_type='employee',
            employee=self.employee,
            service=self.fixed_service,
            date_of_work=date.today(),
            quantity=2
        )
        
        expected_total = Decimal('50.00') * 2
        self.assertEqual(work_record.total_amount, expected_total)
    
    def test_work_record_owner_type(self):
        """Test work record with owner worker type"""
        work_record = WorkRecord.objects.create(
            user=self.user,
            worker_type='owner',
            owner_name='Business Owner',
            service=self.fixed_service,
            date_of_work=date.today(),
            quantity=1
        )
        
        self.assertEqual(work_record.get_worker_name(), 'Business Owner')
        self.assertEqual(work_record.worker_type, 'owner')


class ServiceAPITest(APITestCase):
    """Test cases for Service API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.category = ServiceCategory.objects.create(
            name="Beauty Services"
        )
        
        self.service = Service.objects.create(
            name="Haircut",
            category=self.category,
            pricing_type='fixed',
            fixed_price=Decimal('50.00')
        )
        
        self.employee = Employee.objects.create(
            employee_id='EMP_API_001',
            employee_name='Jane Doe',
            phone_number='+1234567890',
            employment_type='full_time',
            pay=Decimal('3000.00')
        )
    
    def test_get_services_list(self):
        """Test retrieving list of services"""
        url = reverse('service-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_create_service_via_api(self):
        """Test creating service via API"""
        url = reverse('service-list')
        service_data = {
            'name': 'Manicure',
            'category': self.category.id,
            'pricing_type': 'fixed',
            'fixed_price': '30.00'
        }
        response = self.client.post(url, service_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Service.objects.count(), 2)
    
    def test_create_work_record_via_api(self):
        """Test creating work record via API"""
        url = reverse('workrecord-list')
        work_data = {
            'worker_type': 'employee',
            'employee': self.employee.id,
            'service': self.service.id,
            'date_of_work': date.today().isoformat(),
            'quantity': 1
        }
        response = self.client.post(url, work_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(WorkRecord.objects.count(), 1)
    
    def test_employee_summary_endpoint(self):
        """Test employee work summary endpoint"""
        # Create a work record
        WorkRecord.objects.create(
            user=self.user,
            worker_type='employee',
            employee=self.employee,
            service=self.service,
            date_of_work=date.today(),
            quantity=1
        )
        
        url = reverse('workrecord-employee-performance')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
