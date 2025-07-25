# Generated by Django 5.2.4 on 2025-07-23 13:00

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
import uuid
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AssetCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('fixed_assets', 'Fixed Assets'), ('current_assets', 'Current Assets'), ('intangible_assets', 'Intangible Assets'), ('equipment', 'Equipment & Machinery'), ('vehicles', 'Vehicles'), ('furniture', 'Furniture & Fixtures'), ('buildings', 'Buildings & Property'), ('technology', 'Technology & Software'), ('other', 'Other Assets')], max_length=50, unique=True)),
                ('description', models.TextField(blank=True, help_text='Category description')),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name_plural': 'Asset Categories',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ExpenseCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('operational', 'Operational'), ('staff', 'Staff & Salaries'), ('utilities', 'Utilities'), ('transport', 'Transport'), ('marketing', 'Marketing & Advertising'), ('equipment', 'Equipment & Tools'), ('professional', 'Professional Services'), ('rent', 'Rent & Facilities'), ('insurance', 'Insurance'), ('loan_payments', 'Loan Payments'), ('taxes', 'Taxes & Fees'), ('other', 'Other')], max_length=50, unique=True)),
                ('description', models.TextField(blank=True, help_text='Category description')),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name_plural': 'Expense Categories',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Asset',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='Asset name/description', max_length=200)),
                ('purchase_value', models.DecimalField(decimal_places=2, help_text='Original purchase price in Kwacha', max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('current_value', models.DecimalField(blank=True, decimal_places=2, help_text='Current estimated value in Kwacha', max_digits=12, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('purchase_date', models.DateField(help_text='Date asset was purchased')),
                ('status', models.CharField(choices=[('active', 'Active'), ('disposed', 'Disposed'), ('damaged', 'Damaged'), ('under_repair', 'Under Repair')], default='active', max_length=20)),
                ('disposal_date', models.DateField(blank=True, help_text='Date asset was disposed', null=True)),
                ('vendor', models.CharField(blank=True, help_text='Vendor/supplier name', max_length=200)),
                ('serial_number', models.CharField(blank=True, help_text='Serial/model number', max_length=100)),
                ('location', models.CharField(blank=True, help_text='Asset location', max_length=200)),
                ('notes', models.TextField(blank=True, help_text='Additional notes')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assets', to=settings.AUTH_USER_MODEL)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='accounting.assetcategory')),
            ],
            options={
                'ordering': ['-purchase_date', 'name'],
                'indexes': [models.Index(fields=['user', 'category'], name='accounting__user_id_6fac79_idx'), models.Index(fields=['user', 'status'], name='accounting__user_id_7604f8_idx'), models.Index(fields=['user', 'purchase_date'], name='accounting__user_id_2484f3_idx')],
            },
        ),
        migrations.CreateModel(
            name='Expense',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='Expense description', max_length=200)),
                ('amount', models.DecimalField(decimal_places=2, help_text='Expense amount in Kwacha', max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('expense_type', models.CharField(choices=[('one_time', 'One-time Expense'), ('recurring', 'Recurring Expense')], default='one_time', max_length=20)),
                ('recurrence', models.CharField(blank=True, choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('annually', 'Annually')], help_text='For recurring expenses only', max_length=20, null=True)),
                ('expense_date', models.DateField(default=django.utils.timezone.now, help_text='Date expense was incurred')),
                ('due_date', models.DateField(blank=True, help_text='Payment due date', null=True)),
                ('payment_date', models.DateField(blank=True, help_text='Date payment was made', null=True)),
                ('payment_status', models.CharField(choices=[('paid', 'Paid'), ('unpaid', 'Unpaid'), ('overdue', 'Overdue'), ('partial', 'Partially Paid')], default='unpaid', max_length=20)),
                ('vendor', models.CharField(blank=True, help_text='Vendor/supplier name', max_length=200)),
                ('reference_number', models.CharField(blank=True, help_text='Invoice/receipt number', max_length=100)),
                ('notes', models.TextField(blank=True, help_text='Additional notes')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='expenses', to=settings.AUTH_USER_MODEL)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='accounting.expensecategory')),
            ],
            options={
                'ordering': ['-expense_date', '-created_at'],
                'indexes': [models.Index(fields=['user', 'expense_date'], name='accounting__user_id_0d3703_idx'), models.Index(fields=['user', 'category'], name='accounting__user_id_0ef467_idx'), models.Index(fields=['user', 'payment_status'], name='accounting__user_id_37af3e_idx')],
            },
        ),
        migrations.CreateModel(
            name='FinancialSummary',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('year', models.IntegerField()),
                ('month', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(12)])),
                ('total_income', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('total_expenses', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('net_profit', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('total_assets', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('turnover_tax_due', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('calculated_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='financial_summaries', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-year', '-month'],
                'indexes': [models.Index(fields=['user', 'year', 'month'], name='accounting__user_id_1c1778_idx')],
                'unique_together': {('user', 'year', 'month')},
            },
        ),
        migrations.CreateModel(
            name='IncomeRecord',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('source', models.CharField(choices=[('sales', 'Sales Revenue'), ('services', 'Service Income'), ('other', 'Other Income')], max_length=20)),
                ('amount', models.DecimalField(decimal_places=2, help_text='Income amount in Kwacha', max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('income_date', models.DateField(help_text='Date income was earned')),
                ('description', models.CharField(help_text='Income description', max_length=200)),
                ('sale_id', models.UUIDField(blank=True, help_text='Reference to sale record', null=True)),
                ('service_record_id', models.UUIDField(blank=True, help_text='Reference to service record', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='income_records', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-income_date', '-created_at'],
                'indexes': [models.Index(fields=['user', 'income_date'], name='accounting__user_id_7780fd_idx'), models.Index(fields=['user', 'source'], name='accounting__user_id_a01fc2_idx')],
            },
        ),
        migrations.CreateModel(
            name='TurnoverTaxRecord',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('year', models.IntegerField(help_text='Tax year')),
                ('month', models.IntegerField(help_text='Tax month (1-12)', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(12)])),
                ('total_revenue', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Total monthly revenue in Kwacha', max_digits=12)),
                ('tax_free_threshold', models.DecimalField(decimal_places=2, default=Decimal('1000.00'), help_text='Monthly tax-free threshold (K1,000)', max_digits=12)),
                ('taxable_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Amount subject to tax', max_digits=12)),
                ('tax_rate', models.DecimalField(decimal_places=2, default=Decimal('5.00'), help_text='Tax rate percentage', max_digits=5)),
                ('tax_due', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Total turnover tax due', max_digits=12)),
                ('payment_status', models.CharField(choices=[('pending', 'Pending'), ('paid', 'Paid'), ('overdue', 'Overdue')], default='pending', max_length=20)),
                ('payment_date', models.DateField(blank=True, null=True)),
                ('payment_reference', models.CharField(blank=True, help_text='ZRA payment reference', max_length=100)),
                ('calculated_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tax_records', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-year', '-month'],
                'indexes': [models.Index(fields=['user', 'year', 'month'], name='accounting__user_id_c89a36_idx'), models.Index(fields=['user', 'payment_status'], name='accounting__user_id_b30a2c_idx')],
                'unique_together': {('user', 'year', 'month')},
            },
        ),
    ]
