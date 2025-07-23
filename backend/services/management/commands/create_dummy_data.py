from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import random
from datetime import datetime, timedelta

from services.models import ServiceCategory, Service, Worker, ServiceRecord, WorkerPerformance
from profiles.models import UserProfile

User = get_user_model()


class Command(BaseCommand):
    help = 'Create dummy data for the services module'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing services data before creating new data',
        )
        parser.add_argument(
            '--users',
            type=int,
            default=3,
            help='Number of demo users to create (default: 3)',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing services data...')
            ServiceRecord.objects.all().delete()
            WorkerPerformance.objects.all().delete()
            Worker.objects.all().delete()
            Service.objects.all().delete()
            # Don't delete ServiceCategory as they might be shared
            self.stdout.write(self.style.SUCCESS('Cleared existing data'))

        # Create service categories if they don't exist
        self.create_service_categories()
        
        # Create demo users and their data
        num_users = options['users']
        for i in range(num_users):
            self.create_user_data(i + 1)

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created dummy data for {num_users} users'
            )
        )

    def create_service_categories(self):
        """Create service categories"""
        categories = [
            ('Beauty & Personal Care', 'Hair salons, spas, nail services'),
            ('Home Services', 'Cleaning, maintenance, repairs'),
            ('Professional Services', 'Consulting, legal, accounting'),
            ('Health & Wellness', 'Massage, fitness training, therapy'),
            ('Automotive', 'Car wash, repairs, maintenance'),
            ('Education', 'Tutoring, training, workshops'),
            ('Technology', 'IT support, web development, repairs'),
            ('Food Services', 'Catering, meal prep, delivery'),
        ]

        for name, description in categories:
            category, created = ServiceCategory.objects.get_or_create(
                name=name,
                defaults={'description': description}
            )
            if created:
                self.stdout.write(f'Created category: {name}')

    def create_user_data(self, user_num):
        """Create a demo user with services, workers, and records"""
        
        # Business profiles
        business_profiles = [
            {
                'email': f'salon.owner{user_num}@example.com',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'business_name': 'Elegant Hair Studio',
                'business_type': 'Beauty Salon',
                'services': [
                    ('Haircut', 'Professional haircuts for all hair types', 'Beauty & Personal Care', 'both', 25.00, 30.00),
                    ('Hair Styling', 'Special occasion styling', 'Beauty & Personal Care', 'both', 30.00, 45.00),
                    ('Hair Coloring', 'Professional hair coloring service', 'Beauty & Personal Care', 'fixed', None, 80.00),
                    ('Manicure', 'Professional nail care', 'Beauty & Personal Care', 'fixed', None, 25.00),
                    ('Pedicure', 'Foot care and nail service', 'Beauty & Personal Care', 'fixed', None, 35.00),
                ],
                'workers': [
                    ('Sarah Johnson', 'sarah.j@salon.com', '+1234567890', True, [0, 1, 2]),
                    ('Maria Rodriguez', 'maria.r@salon.com', '+1234567891', False, [0, 1]),
                    ('Lisa Chen', 'lisa.c@salon.com', '+1234567892', False, [3, 4]),
                ]
            },
            {
                'email': f'cleaning.owner{user_num}@example.com',
                'first_name': 'Michael',
                'last_name': 'Thompson',
                'business_name': 'SparkleClean Services',
                'business_type': 'Cleaning Service',
                'services': [
                    ('House Cleaning', 'Complete residential cleaning', 'Home Services', 'both', 25.00, 80.00),
                    ('Office Cleaning', 'Commercial office cleaning', 'Home Services', 'hourly', 30.00, None),
                    ('Deep Cleaning', 'Thorough deep cleaning service', 'Home Services', 'fixed', None, 150.00),
                    ('Window Cleaning', 'Interior and exterior windows', 'Home Services', 'fixed', None, 50.00),
                    ('Carpet Cleaning', 'Professional carpet cleaning', 'Home Services', 'fixed', None, 120.00),
                ],
                'workers': [
                    ('Michael Thompson', 'michael.t@sparkle.com', '+1234567893', True, [0, 1, 2]),
                    ('James Wilson', 'james.w@sparkle.com', '+1234567894', False, [0, 1, 3]),
                    ('Anna Garcia', 'anna.g@sparkle.com', '+1234567895', False, [2, 4]),
                ]
            },
            {
                'email': f'consultant.owner{user_num}@example.com',
                'first_name': 'David',
                'last_name': 'Kim',
                'business_name': 'KimTech Consulting',
                'business_type': 'IT Consulting',
                'services': [
                    ('IT Consultation', 'Technology consulting services', 'Professional Services', 'hourly', 75.00, None),
                    ('Website Development', 'Custom website creation', 'Technology', 'fixed', None, 2500.00),
                    ('System Setup', 'Computer and network setup', 'Technology', 'both', 60.00, 300.00),
                    ('Tech Support', 'Technical support services', 'Technology', 'hourly', 50.00, None),
                    ('Training Session', 'Software training sessions', 'Education', 'both', 80.00, 200.00),
                ],
                'workers': [
                    ('David Kim', 'david.k@kimtech.com', '+1234567896', True, [0, 1, 2, 4]),
                    ('Robert Lee', 'robert.l@kimtech.com', '+1234567897', False, [1, 2]),
                    ('Jennifer Park', 'jennifer.p@kimtech.com', '+1234567898', False, [2, 3, 4]),
                ]
            }
        ]

        # Select profile based on user number
        profile = business_profiles[(user_num - 1) % len(business_profiles)]
        if user_num > len(business_profiles):
            # Modify email for additional users
            profile['email'] = f'user{user_num}@example.com'
            profile['first_name'] = f'User{user_num}'
            profile['last_name'] = 'Demo'

        # Create user
        user, user_created = User.objects.get_or_create(
            email=profile['email'],
            defaults={
                'is_active': True,
            }
        )
        if user_created:
            user.set_password('demo123!')
            user.save()
            self.stdout.write(f'Created user: {user.email}')
        else:
            self.stdout.write(f'User already exists: {user.email}')
            
        # Create user profile if it doesn't exist
        user_profile, profile_created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'first_name': profile['first_name'],
                'last_name': profile['last_name'],
                'business_name': profile['business_name'],
                'business_type': 'services',  # Default to services type
                'business_city': 'Lusaka',
                'business_province': 'Lusaka',
            }
        )
        if profile_created:
            self.stdout.write(f'  Created profile for: {profile["first_name"]} {profile["last_name"]}')
        else:
            self.stdout.write(f'  Profile already exists for: {user.email}')

        # Create services
        services = []
        for service_data in profile['services']:
            name, description, category_name, pricing_type, hourly_rate, fixed_price = service_data
            
            category = ServiceCategory.objects.get(name=category_name)
            
            service, service_created = Service.objects.get_or_create(
                user=user,
                name=name,
                defaults={
                    'description': description,
                    'category': category,
                    'pricing_type': pricing_type,
                    'hourly_rate': hourly_rate,
                    'fixed_price': fixed_price,
                    'is_active': True,
                }
            )
            services.append(service)
            if service_created:
                self.stdout.write(f'  Created service: {name}')
            else:
                self.stdout.write(f'  Service already exists: {name}')

        # Create workers
        workers = []
        for worker_data in profile['workers']:
            name, email, phone, is_owner, service_indices = worker_data
            
            worker, worker_created = Worker.objects.get_or_create(
                user=user,
                name=name,
                defaults={
                    'email': email,
                    'phone': phone,
                    'is_owner': is_owner,
                    'is_active': True,
                }
            )
            
            if worker_created:
                # Assign services to worker
                worker_services = [services[i] for i in service_indices]
                worker.services.set(worker_services)
                self.stdout.write(f'  Created worker: {name}')
            else:
                self.stdout.write(f'  Worker already exists: {name}')
            
            workers.append(worker)

        # Create service records (last 30 days)
        self.create_service_records(user, services, workers)

    def create_service_records(self, user, services, workers):
        """Create sample service records for the last 30 days"""
        
        # Sample client names
        clients = [
            ('Alice Brown', 'alice.brown@email.com'),
            ('Bob Davis', 'bob.davis@email.com'),
            ('Carol Wilson', 'carol.wilson@email.com'),
            ('Dan Miller', 'dan.miller@email.com'),
            ('Eva Martinez', 'eva.martinez@email.com'),
            ('Frank Johnson', 'frank.johnson@email.com'),
            ('Grace Lee', 'grace.lee@email.com'),
            ('Henry Taylor', 'henry.taylor@email.com'),
            ('Ivy Chen', 'ivy.chen@email.com'),
            ('Jack Smith', 'jack.smith@email.com'),
        ]

        payment_statuses = ['pending', 'paid', 'partially_paid']
        
        # Create 20-40 service records per user
        num_records = random.randint(20, 40)
        
        for _ in range(num_records):
            # Random date in last 30 days
            days_ago = random.randint(0, 30)
            record_date = timezone.now().date() - timedelta(days=days_ago)
            
            # Random service and worker
            service = random.choice(services)
            # Filter workers who can perform this service
            available_workers = [w for w in workers if service in w.services.all()]
            if not available_workers:
                continue
            worker = random.choice(available_workers)
            
            # Random client
            client_name, client_contact = random.choice(clients)
            
            # Generate realistic start time (9 AM to 6 PM)
            start_hour = random.randint(9, 17)
            start_minute = random.choice([0, 15, 30, 45])
            start_time = datetime.combine(record_date, datetime.min.time().replace(hour=start_hour, minute=start_minute))
            
            # Calculate end time and pricing based on service
            if service.pricing_type == 'hourly':
                # For hourly services, work 0.5 to 4 hours
                hours_worked = round(random.uniform(0.5, 4.0), 2)
                end_time = start_time + timedelta(hours=hours_worked)
                hourly_rate_used = service.hourly_rate
                fixed_price_used = None
                used_fixed_price = False
                total_amount = Decimal(str(hours_worked)) * Decimal(str(hourly_rate_used))
            elif service.pricing_type == 'fixed':
                # For fixed services, use typical duration
                hours_worked = round(random.uniform(1.0, 3.0), 2)
                end_time = start_time + timedelta(hours=hours_worked)
                hourly_rate_used = None
                fixed_price_used = service.fixed_price
                used_fixed_price = True
                total_amount = Decimal(str(fixed_price_used))
            else:  # both
                # 70% chance of using fixed price, 30% hourly
                if random.random() < 0.7:
                    hours_worked = round(random.uniform(1.0, 3.0), 2)
                    end_time = start_time + timedelta(hours=hours_worked)
                    hourly_rate_used = None
                    fixed_price_used = service.fixed_price
                    used_fixed_price = True
                    total_amount = Decimal(str(fixed_price_used))
                else:
                    hours_worked = round(random.uniform(0.5, 4.0), 2)
                    end_time = start_time + timedelta(hours=hours_worked)
                    hourly_rate_used = service.hourly_rate
                    fixed_price_used = None
                    used_fixed_price = False
                    total_amount = Decimal(str(hours_worked)) * Decimal(str(hourly_rate_used))

            # Payment status and amount paid
            payment_status = random.choice(payment_statuses)
            if payment_status == 'paid':
                amount_paid = total_amount
            elif payment_status == 'partially_paid':
                partial_rate = Decimal(str(round(random.uniform(0.3, 0.8), 2)))
                amount_paid = (total_amount * partial_rate).quantize(Decimal('0.01'))
            else:  # pending
                amount_paid = Decimal('0.00')

            # Create service record
            ServiceRecord.objects.create(
                user=user,
                service=service,
                worker=worker,
                customer_name=client_name,
                date_performed=record_date,
                start_time=start_time.time(),
                end_time=end_time.time(),
                hours_worked=hours_worked,
                used_fixed_price=used_fixed_price,
                hourly_rate_used=hourly_rate_used,
                fixed_price_used=fixed_price_used,
                total_amount=total_amount,
                payment_status=payment_status,
                amount_paid=amount_paid,
                notes=random.choice([
                    'Great service, client very satisfied',
                    'Regular customer, no issues',
                    'Client requested follow-up appointment',
                    'Excellent work quality',
                    'Customer referred by previous client',
                    '',  # Some records without notes
                ])
            )

        self.stdout.write(f'  Created {num_records} service records for {user.email}')
