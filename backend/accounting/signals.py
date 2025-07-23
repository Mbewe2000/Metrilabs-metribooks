from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from decimal import Decimal
import logging
from datetime import date

logger = logging.getLogger('accounting')


@receiver(post_save, sender='sales.Sale')
def create_income_record_from_sale(sender, instance, created, **kwargs):
    """Create income record when a sale is completed"""
    from .models import IncomeRecord, TurnoverTaxRecord, FinancialSummary
    
    if created and instance.status == 'completed':
        with transaction.atomic():
            # Create income record
            income_record, created = IncomeRecord.objects.get_or_create(
                user=instance.user,
                sale_id=instance.id,
                defaults={
                    'source': 'sales',
                    'amount': instance.total_amount,
                    'income_date': instance.sale_date.date() if hasattr(instance.sale_date, 'date') else instance.sale_date,
                    'description': f"Sale #{instance.sale_number} - {instance.customer_name or 'Walk-in Customer'}"
                }
            )
            
            if created:
                logger.info(f"Income record created for sale {instance.sale_number}: K{instance.total_amount}")
                
                # Update or create turnover tax record for the month
                sale_date = instance.sale_date.date() if hasattr(instance.sale_date, 'date') else instance.sale_date
                update_monthly_tax_record(instance.user, sale_date, instance.total_amount)
                
                # Update financial summary
                update_monthly_financial_summary(instance.user, sale_date.year, sale_date.month)


@receiver(post_save, sender='services.WorkRecord')
def create_income_record_from_service(sender, instance, created, **kwargs):
    """Create income record when a service is completed and paid"""
    from .models import IncomeRecord, TurnoverTaxRecord, FinancialSummary
    
    if instance.payment_status == 'paid':
        with transaction.atomic():
            # Create or update income record
            income_record, created = IncomeRecord.objects.update_or_create(
                user=instance.user,
                service_record_id=instance.id,
                defaults={
                    'source': 'services',
                    'amount': instance.total_amount,
                    'income_date': instance.completed_date or instance.service_date,
                    'description': f"Service: {instance.service.name} - {instance.client_name or 'Client'}"
                }
            )
            
            if created:
                logger.info(f"Income record created for service {instance.service.name}: K{instance.total_amount}")
                
                # Update or create turnover tax record for the month
                service_date = instance.completed_date or instance.service_date
                update_monthly_tax_record(instance.user, service_date, instance.total_amount)
                
                # Update financial summary
                update_monthly_financial_summary(instance.user, service_date.year, service_date.month)


@receiver(post_delete, sender='sales.Sale')
def remove_income_record_from_sale(sender, instance, **kwargs):
    """Remove income record when a sale is deleted"""
    from .models import IncomeRecord
    
    try:
        income_record = IncomeRecord.objects.get(
            user=instance.user,
            sale_id=instance.id
        )
        
        sale_date = instance.sale_date.date() if hasattr(instance.sale_date, 'date') else instance.sale_date
        amount = income_record.amount
        
        income_record.delete()
        
        logger.info(f"Income record removed for deleted sale {instance.sale_number}: K{amount}")
        
        # Update turnover tax record for the month
        update_monthly_tax_record(instance.user, sale_date, -amount)
        
        # Update financial summary
        update_monthly_financial_summary(instance.user, sale_date.year, sale_date.month)
        
    except IncomeRecord.DoesNotExist:
        logger.warning(f"No income record found for deleted sale {instance.sale_number}")


def update_monthly_tax_record(user, transaction_date, amount):
    """Update or create monthly turnover tax record"""
    from .models import TurnoverTaxRecord
    
    year = transaction_date.year
    month = transaction_date.month
    
    # Get or create tax record for the month
    tax_record, created = TurnoverTaxRecord.objects.get_or_create(
        user=user,
        year=year,
        month=month,
        defaults={
            'total_revenue': Decimal('0.00')
        }
    )
    
    # Update total revenue
    tax_record.total_revenue += amount
    
    # Ensure total revenue doesn't go negative
    if tax_record.total_revenue < Decimal('0.00'):
        tax_record.total_revenue = Decimal('0.00')
    
    # Recalculate tax
    tax_record.calculate_tax()
    
    logger.info(f"Updated turnover tax record for {year}-{month:02d}: Revenue K{tax_record.total_revenue}, Tax K{tax_record.tax_due}")


def update_monthly_financial_summary(user, year, month):
    """Update or create monthly financial summary"""
    from .models import FinancialSummary
    
    # Get or create financial summary for the month
    summary, created = FinancialSummary.objects.get_or_create(
        user=user,
        year=year,
        month=month
    )
    
    # Recalculate summary
    summary.calculate_summary()
    
    logger.info(f"Updated financial summary for {year}-{month:02d}: Profit K{summary.net_profit}")


@receiver(post_save, sender='accounting.Expense')
def update_financial_summary_on_expense(sender, instance, created, **kwargs):
    """Update financial summary when expenses are added or modified"""
    if instance.payment_status == 'paid':
        expense_date = instance.expense_date
        update_monthly_financial_summary(instance.user, expense_date.year, expense_date.month)


@receiver(post_save, sender='accounting.Asset')
def update_financial_summary_on_asset(sender, instance, created, **kwargs):
    """Update financial summary when assets are added or modified"""
    purchase_date = instance.purchase_date
    update_monthly_financial_summary(instance.user, purchase_date.year, purchase_date.month)


# Signal to handle sale status changes
@receiver(post_save, sender='sales.Sale')
def handle_sale_status_change(sender, instance, created, **kwargs):
    """Handle changes in sale status"""
    from .models import IncomeRecord
    
    if not created:  # Only for updates, not new sales
        try:
            income_record = IncomeRecord.objects.get(
                user=instance.user,
                sale_id=instance.id
            )
            
            # If sale is cancelled or refunded, we might want to reverse the income
            if instance.status in ['cancelled', 'refunded']:
                # For now, we'll keep the income record but could add logic to handle refunds
                logger.info(f"Sale {instance.sale_number} status changed to {instance.status}")
                
        except IncomeRecord.DoesNotExist:
            # If sale status changed to completed, create income record
            if instance.status == 'completed':
                create_income_record_from_sale(sender, instance, False, **kwargs)


# Monthly task signal (can be triggered by a management command or cron job)
def calculate_monthly_summaries_for_user(user, year, month):
    """Calculate all monthly summaries for a specific user and month"""
    from .models import TurnoverTaxRecord, FinancialSummary
    
    # Calculate/update turnover tax
    try:
        tax_record = TurnoverTaxRecord.objects.get(user=user, year=year, month=month)
        tax_record.calculate_tax()
    except TurnoverTaxRecord.DoesNotExist:
        # Create tax record if it doesn't exist
        tax_record = TurnoverTaxRecord.objects.create(
            user=user,
            year=year,
            month=month,
            total_revenue=Decimal('0.00')
        )
        tax_record.calculate_tax()
    
    # Calculate/update financial summary
    summary, created = FinancialSummary.objects.get_or_create(
        user=user,
        year=year,
        month=month
    )
    summary.calculate_summary()
    
    logger.info(f"Monthly calculations completed for user {user.email} - {year}-{month:02d}")
    
    return tax_record, summary
