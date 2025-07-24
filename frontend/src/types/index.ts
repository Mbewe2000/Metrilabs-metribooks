// Authentication Types
export interface User {
  id: number;
  email?: string;
  phone?: string;
  date_joined: string;
  email_verified: boolean;
  phone_verified: boolean;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface LoginCredentials {
  email_or_phone: string;
  password: string;
}

export interface RegisterData {
  email?: string;
  phone?: string;
  password: string;
  password_confirm: string;
}

export interface AuthResponse {
  user: User;
  tokens: AuthTokens;
  message: string;
}

// Profile Types
export interface UserProfile {
  id: string;
  first_name: string;
  last_name: string;
  full_name: string;
  business_name: string;
  business_type: 'food_beverage' | 'retail' | 'beauty' | 'health_wellness' | 'services';
  business_subcategory?: string;
  business_city: string;
  business_province: string;
  employee_count?: string;
  monthly_revenue_range?: string;
  is_complete: boolean;
  created_at: string;
  updated_at: string;
}

// Product/Inventory Types
export interface Product {
  id: number;
  name: string;
  sku?: string;
  description?: string;
  selling_price: string;
  cost_price?: string;
  current_stock: number;
  reorder_level: number;
  unit: string;
  category: ProductCategory;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProductCategory {
  id: number;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

// Sales Types
export interface Sale {
  id: string;
  sale_number: string;
  sale_date: string;
  customer_name?: string;
  customer_phone?: string;
  subtotal: string;
  discount_amount: string;
  tax_amount: string;
  total_amount: string;
  payment_method: 'cash' | 'bank_transfer' | 'mobile_money';
  payment_status: 'pending' | 'completed' | 'cancelled';
  items: SaleItem[];
  created_at: string;
}

export interface SaleItem {
  id: number;
  product: Product;
  quantity: number;
  unit_price: string;
  total_price: string;
}

// Service Types
export interface Service {
  id: number;
  name: string;
  pricing_type: 'hourly' | 'fixed';
  hourly_rate?: string;
  fixed_price?: string;
  description?: string;
  category?: ServiceCategory;
  is_active: boolean;
}

export interface ServiceCategory {
  id: number;
  name: string;
  description?: string;
}

export interface Employee {
  id: number;
  first_name: string;
  last_name: string;
  email?: string;
  phone?: string;
  position: string;
  employment_type: 'full_time' | 'part_time' | 'contract';
  hourly_rate?: string;
  monthly_salary?: string;
  hire_date: string;
  is_active: boolean;
}

export interface WorkRecord {
  id: number;
  service: Service;
  worker_type: 'employee' | 'owner';
  owner_name?: string;
  employee?: Employee;
  date_of_work: string;
  hours_worked?: string;
  quantity: number;
  total_amount: string;
  notes?: string;
}

// Accounting Types
export interface Expense {
  id: string;
  name: string;
  amount: string;
  expense_type: 'one_time' | 'recurring';
  category: ExpenseCategory;
  expense_date: string;
  payment_method: string;
  payment_status: 'pending' | 'paid' | 'overdue';
  vendor?: string;
  notes?: string;
}

export interface ExpenseCategory {
  id: number;
  name: string;
  description?: string;
}

export interface IncomeRecord {
  id: string;
  source: 'sales' | 'services' | 'other';
  amount: string;
  income_date: string;
  description: string;
}

// Reports Types
export interface ProfitLossReport {
  period_start: string;
  period_end: string;
  total_income: string;
  sales_revenue: string;
  service_revenue: string;
  other_income: string;
  total_expenses: string;
  gross_profit: string;
  net_profit: string;
  profit_margin: string;
  expense_breakdown: ExpenseBreakdown[];
}

export interface ExpenseBreakdown {
  category: string;
  amount: string;
  percentage: string;
}

// Dashboard Types
export interface DashboardMetrics {
  total_sales_today: string;
  total_revenue_month: string;
  total_expenses_month: string;
  net_profit_month: string;
  sales_count_today: number;
  low_stock_items: number;
  pending_payments: number;
}

// API Response Types
export interface ApiResponse<T> {
  data?: T;
  message?: string;
  error?: string;
  errors?: Record<string, string[]>;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
