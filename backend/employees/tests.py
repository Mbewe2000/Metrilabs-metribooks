from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Employee

User = get_user_model()


class EmployeeModelTest(TestCase):
    """Test cases for Employee model"""
    
    def setUp(self):
        self.employee_data = {
            'employee_id': 'EMP001',
            'employee_name': 'John Doe',
            'phone_number': '+1234567890',
            'employment_type': 'full_time',
            'pay': 5000.00
        }
    
    def test_create_employee(self):
        """Test creating an employee"""
        employee = Employee.objects.create(**self.employee_data)
        self.assertEqual(employee.employee_id, 'EMP001')
        self.assertEqual(employee.employee_name, 'John Doe')
        self.assertTrue(employee.is_active)
        self.assertTrue(employee.is_full_time)
        self.assertFalse(employee.is_part_time)
    
    def test_employee_str_representation(self):
        """Test string representation of employee"""
        employee = Employee.objects.create(**self.employee_data)
        expected_str = f"{employee.employee_id} - {employee.employee_name}"
        self.assertEqual(str(employee), expected_str)
    
    def test_unique_employee_id(self):
        """Test that employee_id must be unique"""
        Employee.objects.create(**self.employee_data)
        with self.assertRaises(Exception):
            Employee.objects.create(**self.employee_data)
    
    def test_part_time_employee(self):
        """Test creating a part-time employee"""
        self.employee_data['employment_type'] = 'part_time'
        employee = Employee.objects.create(**self.employee_data)
        self.assertTrue(employee.is_part_time)
        self.assertFalse(employee.is_full_time)


class EmployeeAPITest(APITestCase):
    """Test cases for Employee API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.employee_data = {
            'employee_id': 'EMP001',
            'employee_name': 'John Doe',
            'phone_number': '+1234567890',
            'employment_type': 'full_time',
            'pay': 5000.00
        }
        self.employee = Employee.objects.create(**self.employee_data)
    
    def test_get_employees_list(self):
        """Test retrieving list of employees"""
        url = reverse('employee-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_create_employee_via_api(self):
        """Test creating employee via API"""
        url = reverse('employee-list')
        new_employee_data = {
            'employee_id': 'EMP002',
            'employee_name': 'Jane Smith',
            'phone_number': '+1987654321',
            'employment_type': 'part_time',
            'pay': 25.00
        }
        response = self.client.post(url, new_employee_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Employee.objects.count(), 2)
    
    def test_get_employee_detail(self):
        """Test retrieving specific employee"""
        url = reverse('employee-detail', kwargs={'pk': self.employee.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['employee_id'], 'EMP001')
