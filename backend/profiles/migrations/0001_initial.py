# Generated by Django 5.2.4 on 2025-07-21 18:14

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(help_text='Complete full name', max_length=255)),
                ('business_name', models.CharField(help_text='Name of your business', max_length=255)),
                ('business_type', models.CharField(choices=[('retail', 'Retail'), ('services', 'Services'), ('agriculture', 'Agriculture'), ('manufacturing', 'Manufacturing'), ('technology', 'Technology'), ('hospitality', 'Hospitality'), ('healthcare', 'Healthcare'), ('education', 'Education'), ('finance', 'Finance'), ('construction', 'Construction'), ('transport', 'Transport & Logistics'), ('other', 'Other')], help_text='Type of business you operate', max_length=20)),
                ('business_city', models.CharField(help_text='City or Town where business is located', max_length=100)),
                ('business_province', models.CharField(help_text='Province where business is located', max_length=100)),
                ('employee_count', models.CharField(blank=True, choices=[('1', '1 employee'), ('2-5', '2-5 employees'), ('6-10', '6-10 employees'), ('11-25', '11-25 employees'), ('26-50', '26-50 employees'), ('51-100', '51-100 employees'), ('100+', '100+ employees')], help_text='Number of employees in your business', max_length=10, null=True)),
                ('monthly_revenue_range', models.CharField(blank=True, choices=[('0-1000', 'ZMW 0 - ZMW 1,000'), ('1001-5000', 'ZMW 1,001 - ZMW 5,000'), ('5001-10000', 'ZMW 5,001 - ZMW 10,000'), ('10001-25000', 'ZMW 10,001 - ZMW 25,000'), ('25001-50000', 'ZMW 25,001 - ZMW 50,000'), ('50001-100000', 'ZMW 50,001 - ZMW 100,000'), ('100001-250000', 'ZMW 100,001 - ZMW 250,000'), ('250001-500000', 'ZMW 250,001 - ZMW 500,000'), ('500001+', 'ZMW 500,001+')], help_text='Monthly revenue range of your business', max_length=20, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_complete', models.BooleanField(default=False, help_text='Whether the profile has been completed')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Profile',
                'verbose_name_plural': 'User Profiles',
                'ordering': ['-created_at'],
            },
        ),
    ]
