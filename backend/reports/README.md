# Reports and Analytics Module

A comprehensive Django app for advanced business reporting and analytics in the Metribooks system. This module aggregates data from all other modules to provide insightful business intelligence and reporting capabilities.

## Features

- **📊 Profit/Loss Reports**: Comprehensive income and expense analysis with profit margins
- **💰 Cash Flow Analysis**: Track money flow in and out of business operations
- **📈 Sales/Expense Trends**: Visual trend analysis with growth metrics and forecasting
- **🧾 Tax Compliance**: ZRA-compliant turnover tax calculations and reporting
- **📋 Business Overview**: Comprehensive dashboard with key performance indicators
- **⚡ Smart Caching**: Performance-optimized report generation with intelligent caching
- **📊 Business Metrics**: Track key performance indicators over time
- **📄 Report Templates**: Reusable report configurations with automation support

## Models

### ReportSnapshot
Stores cached report data for improved performance and historical comparisons.

**Key Fields:**
- `report_type`: Type of report (profit_loss, cash_flow, sales_trend, etc.)
- `period_start/period_end`: Reporting period
- `total_income/total_expenses/net_profit`: Financial metrics
- `total_sales_count/average_sale_value`: Sales metrics
- `total_service_hours/total_service_revenue`: Service metrics
- `taxable_income/turnover_tax_due`: Tax metrics
- `additional_data`: JSON field for flexible report data
- `is_cached`: Performance optimization flag

**Methods:**
- `get_profit_margin_percentage()`: Calculate profit margin as percentage
- `get_expense_ratio_percentage()`: Calculate expense ratio
- `get_tax_rate_percentage()`: Calculate effective tax rate

### ReportTemplate
Reusable report configurations for automated report generation.

**Key Fields:**
- `name/description`: Template identification
- `report_types`: List of report types to include
- `frequency`: Automation frequency (daily, weekly, monthly, etc.)
- `auto_generate`: Whether to automatically generate reports
- `include_*`: Boolean flags for module inclusion
- `email_recipients`: List of email addresses for automated delivery

### BusinessMetric
Track key business performance indicators over time.

**Key Fields:**
- `metric_type`: Type of metric (revenue_growth, profit_margin, etc.)
- `value/percentage_value`: Metric values
- `previous_period_value/change_percentage`: Comparison data
- `metadata`: Additional metric context

**Methods:**
- `get_trend_direction()`: Returns 'up', 'down', 'stable', or 'neutral'
- `is_positive_change()`: Determines if change is beneficial for business

## API Endpoints

### Report Generation
**Base URL: `/api/reports/`**

#### Core Report Generation
- `POST /generate/` - Generate any report type with caching support
- `GET /profit-loss/` - Quick Profit & Loss summary
- `GET /cash-flow/` - Quick Cash Flow overview
- `GET /sales-trends/` - Sales trend analysis
- `GET /expense-trends/` - Expense trend analysis
- `GET /tax-summary/` - Tax compliance summary
- `GET /business-overview/` - Comprehensive business dashboard

#### Analytics Dashboard
- `GET /dashboard/` - Complete analytics dashboard with growth metrics

### Report Management
- `GET /snapshots/` - List cached report snapshots
- `POST /snapshots/` - Create report snapshot
- `GET /snapshots/{id}/` - Get specific snapshot
- `DELETE /snapshots/{id}/` - Delete snapshot

#### Report Templates
- `GET /templates/` - List report templates
- `POST /templates/` - Create report template
- `GET /templates/{id}/` - Get template details
- `PUT /templates/{id}/` - Update template
- `POST /templates/{id}/generate_from_template/` - Generate reports from template

#### Business Metrics
- `GET /metrics/` - List business metrics
- `POST /metrics/` - Create business metric
- `GET /metrics/latest_metrics/` - Get latest value for each metric type
- `GET /metrics/metric_trends/` - Get trend data for specific metrics

## Query Parameters

### Date Filtering
- `start_date` - Start date for reporting period (YYYY-MM-DD)
- `end_date` - End date for reporting period (YYYY-MM-DD)
- `period_type` - For trends: 'daily', 'weekly', 'monthly'

### Report Generation
- `force_regenerate` - Force new report generation (ignore cache)
- `include_trends` - Include trend analysis
- `include_comparisons` - Include period comparisons

### Business Metrics
- `metric_type` - Filter by specific metric type
- `start_date/end_date` - Date range for metrics

## Report Types

### 1. Profit & Loss Reports
Comprehensive income statement analysis.

**Includes:**
- Sales revenue from all sources
- Service revenue tracking
- Categorized expense breakdown
- Gross and net profit calculations
- Profit margin percentages
- Transaction count and averages

### 2. Cash Flow Reports
Track actual money movement in business operations.

**Includes:**
- Cash inflows (sales, services, other income)
- Cash outflows (expenses, assets, taxes)
- Net cash flow calculation
- Daily breakdown for trend analysis

### 3. Sales Trend Analysis
Visual and statistical sales performance analysis.

**Includes:**
- Configurable period analysis (daily, weekly, monthly)
- Growth rate calculations
- Best/worst performing periods
- Trend direction indicators

### 4. Expense Trend Analysis
Track and analyze spending patterns.

**Includes:**
- Expense category breakdowns
- Period-over-period comparisons
- Spending pattern identification
- Budget variance analysis

### 5. Tax Summary Reports
**ZRA-compliant turnover tax reporting.**

**Features:**
- **Automatic tax calculations** based on 2025 ZRA regulations
- **K1,000 monthly tax-free allowance** application
- **5% turnover tax rate** on taxable income
- **Annual eligibility checking** (K5M turnover limit)
- Monthly breakdown with compliance status
- Tax payment scheduling

### 6. Business Overview Dashboard
Comprehensive business health dashboard.

**Includes:**
- Key financial metrics summary
- Operational performance indicators
- Growth rate calculations
- Top performing products/services
- Comparative analysis with previous periods

## Integration Points

### With Sales Module
- **Revenue Integration**: Automatic sales revenue aggregation
- **Transaction Analysis**: Sales count and average value tracking
- **Product Performance**: Top-selling product identification

### With Services Module
- **Service Revenue**: Service income aggregation
- **Performance Metrics**: Service utilization and profitability
- **Employee Performance**: Service provider analysis

### With Accounting Module
- **Expense Integration**: Complete expense category analysis
- **Income Tracking**: Multi-source income aggregation
- **Tax Compliance**: Automated ZRA turnover tax calculations
- **Asset Analysis**: Asset purchase and depreciation impact

### With Inventory Module
- **Product Analysis**: Inventory turnover and profitability
- **Cost Analysis**: Product cost impact on profit margins

### With Employees Module
- **Service Assignment**: Employee service performance
- **Cost Analysis**: Employee cost impact on profitability

## Usage Examples

### Generate Profit & Loss Report
```bash
GET /api/reports/profit-loss/?start_date=2025-07-01&end_date=2025-07-31
```

### Generate Sales Trends
```bash
GET /api/reports/sales-trends/?start_date=2025-01-01&end_date=2025-07-31&period_type=monthly
```

### Create Report Template
```json
POST /api/reports/templates/
{
    "name": "Monthly Business Review",
    "description": "Comprehensive monthly analysis",
    "report_types": ["profit_loss", "cash_flow", "tax_summary"],
    "frequency": "monthly",
    "auto_generate": true,
    "include_sales": true,
    "include_services": true,
    "include_expenses": true,
    "email_recipients": ["owner@business.com"]
}
```

### Generate Custom Report
```json
POST /api/reports/generate/
{
    "report_type": "business_overview",
    "period_start": "2025-07-01",
    "period_end": "2025-07-31",
    "force_regenerate": false,
    "include_trends": true
}
```

### Get Analytics Dashboard
```bash
GET /api/reports/dashboard/
```

## ZRA Tax Compliance

### 2025 Turnover Tax Implementation
The Reports module includes comprehensive ZRA compliance features:

**Tax Calculation Logic:**
```python
# Monthly calculation
monthly_revenue = sales + services + other_income
tax_free_allowance = K1,000
taxable_income = max(monthly_revenue - tax_free_allowance, 0)
turnover_tax = taxable_income * 5%
```

**Compliance Features:**
- **Automatic threshold application**: K1,000 monthly allowance
- **Rate calculation**: 5% on taxable income
- **Annual eligibility**: Monitors K5M annual turnover limit
- **Monthly breakdowns**: Detailed tax calculations per month
- **Compliance status**: Real-time eligibility checking

## Performance Features

### Smart Caching System
- **Automatic Caching**: Reports are cached for improved performance
- **Cache Invalidation**: Smart cache updates when underlying data changes
- **Force Regeneration**: Option to bypass cache for fresh data

### Signal Integration
- **Real-time Updates**: Business metrics update automatically when data changes
- **Background Processing**: Non-blocking metric calculations
- **Data Consistency**: Ensures report accuracy across module updates

## Business Metrics Tracking

### Supported Metrics
- **Revenue Growth Rate**: Period-over-period revenue changes
- **Profit Margin**: Net profit as percentage of revenue
- **Customer Acquisition**: New customer tracking (future feature)
- **Average Order Value**: Sales transaction averages
- **Expense Ratio**: Expenses as percentage of revenue
- **Inventory Turnover**: Stock movement efficiency (future feature)
- **Service Utilization**: Service capacity usage
- **Tax Efficiency**: Effective tax rate monitoring

### Trend Analysis
- **Direction Indicators**: Up, down, stable, neutral trends
- **Change Calculations**: Percentage changes from previous periods
- **Positive/Negative Assessment**: Business impact evaluation

## Installation

1. **Add to INSTALLED_APPS**:
```python
INSTALLED_APPS = [
    # ... other apps
    'reports',
]
```

2. **Add URL pattern**:
```python
path('api/reports/', include('reports.urls')),
```

3. **Run migrations**:
```bash
python manage.py makemigrations reports
python manage.py migrate
```

4. **Configure logging** (optional):
```python
LOGGING = {
    'loggers': {
        'reports': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
    }
}
```

## Admin Interface

The Reports module includes comprehensive Django admin integration:

### Report Snapshots
- **Visual Indicators**: Color-coded profit margins
- **Filter Options**: By report type, date, user
- **Bulk Operations**: Delete multiple snapshots

### Report Templates
- **Template Management**: Create and manage reusable templates
- **Automation Control**: Enable/disable auto-generation
- **Email Configuration**: Manage report distribution

### Business Metrics
- **Trend Visualization**: Visual trend indicators
- **Performance Tracking**: Change percentage displays
- **Metric Analysis**: Detailed metric breakdowns

## Testing

The module includes comprehensive test coverage:

- **Model Tests**: Data integrity and calculations
- **API Tests**: All endpoint functionality
- **Integration Tests**: Cross-module data aggregation
- **Performance Tests**: Caching and optimization
- **Tax Compliance Tests**: ZRA calculation accuracy

Run tests:
```bash
python manage.py test reports
```

## Business Use Cases

### Small Retail Business
- **Daily Sales Tracking**: Monitor daily revenue patterns
- **Expense Management**: Track operational costs
- **Tax Compliance**: Automated ZRA turnover tax calculations
- **Profit Analysis**: Weekly/monthly profit assessments

### Service-Based Business
- **Service Performance**: Track service revenue and utilization
- **Employee Productivity**: Service provider performance analysis
- **Cash Flow Management**: Monitor service payment patterns
- **Growth Tracking**: Service expansion analysis

### Mixed Business Operations
- **Comprehensive Reporting**: Combined sales and service analysis
- **Cost Allocation**: Product vs. service cost analysis
- **Performance Optimization**: Identify most profitable activities
- **Strategic Planning**: Data-driven business decisions

## Future Enhancements

### Planned Features
- **Customer Analytics**: Customer lifetime value and acquisition metrics
- **Inventory Optimization**: Stock level and turnover analysis
- **Forecasting Models**: Predictive analytics for revenue and expenses
- **Export Capabilities**: PDF and Excel report exports
- **Email Automation**: Scheduled report delivery
- **Advanced Visualizations**: Charts and graphs for trend analysis

### Integration Roadmap
- **Customer Module**: When implemented, full customer analytics
- **Advanced Inventory**: Enhanced inventory performance metrics
- **Multi-Currency**: Support for multiple currency reporting
- **Comparative Analysis**: Industry benchmark comparisons

## API Rate Limits

For performance and security:
- **Report Generation**: 20 requests per minute per user
- **Quick Reports**: 30 requests per minute per user
- **Dashboard Access**: 10 requests per minute per user
- **Analytics**: 20 requests per minute per user

## Security Features

- **User Isolation**: Complete data separation between users
- **Authentication Required**: All endpoints require valid JWT tokens
- **Permission Checks**: User-specific data access only
- **Data Validation**: Comprehensive input validation
- **Error Handling**: Secure error responses without data leakage

The Reports and Analytics module provides a comprehensive business intelligence solution specifically designed for small to medium businesses in Zambia, with built-in ZRA tax compliance and multi-module data integration.
