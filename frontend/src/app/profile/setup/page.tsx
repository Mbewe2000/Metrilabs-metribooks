'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/use-auth';
import { ProtectedRoute } from '@/components/protected-route';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Building2, User, MapPin, Users, ArrowLeft } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { profileApi } from '@/lib/profile-api';

// Business type options with subcategories
const BUSINESS_TYPES = {
  food_beverage: {
    label: 'Food & Beverage',
    subcategories: [
      { value: 'fast_food', label: 'Fast Food' },
      { value: 'catering', label: 'Catering' },
      { value: 'restaurant_dine_in', label: 'Restaurant/Dine-In' },
      { value: 'takeaway', label: 'Takeaway' },
      { value: 'bakery', label: 'Bakery' },
      { value: 'bar_drinks', label: 'Bar/Drinks' },
      { value: 'other', label: 'Other' },
    ]
  },
  retail: {
    label: 'Retail',
    subcategories: [
      { value: 'grocery', label: 'Grocery' },
      { value: 'electronics', label: 'Electronics' },
      { value: 'clothing_accessories', label: 'Clothing & Accessories' },
      { value: 'hardware_tools', label: 'Hardware & Tools' },
      { value: 'furniture', label: 'Furniture' },
      { value: 'other', label: 'Other' },
    ]
  },
  beauty: {
    label: 'Beauty',
    subcategories: [
      { value: 'hair_salon', label: 'Hair Salon' },
      { value: 'barber_shop', label: 'Barber Shop' },
      { value: 'spa_massage', label: 'Spa & Massage' },
      { value: 'cosmetics_retail', label: 'Cosmetics Retail' },
      { value: 'mobile_beauty_services', label: 'Mobile Beauty Services' },
      { value: 'other', label: 'Other' },
    ]
  },
  health_wellness: {
    label: 'Health & Wellness',
    subcategories: [
      { value: 'pharmacy', label: 'Pharmacy' },
      { value: 'fitness_instructor', label: 'Fitness Instructor' },
      { value: 'gym', label: 'Gym' },
      { value: 'herbal_medicine', label: 'Herbal Medicine' },
      { value: 'physiotherapy', label: 'Physiotherapy' },
      { value: 'other', label: 'Other' },
    ]
  },
  services: {
    label: 'Services',
    subcategories: [
      { value: 'cleaning', label: 'Cleaning' },
      { value: 'transport_delivery', label: 'Transport & Delivery' },
      { value: 'repairs', label: 'Repairs (phone, auto, etc.)' },
      { value: 'consultancy', label: 'Consultancy' },
      { value: 'tailoring', label: 'Tailoring' },
      { value: 'other', label: 'Other' },
    ]
  }
};

const EMPLOYEE_COUNT_OPTIONS = [
  { value: '1', label: '1 employee' },
  { value: '2-5', label: '2-5 employees' },
  { value: '6-10', label: '6-10 employees' },
  { value: '11-25', label: '11-25 employees' },
  { value: '26-50', label: '26-50 employees' },
  { value: '51-100', label: '51-100 employees' },
  { value: '100+', label: '100+ employees' },
];

const REVENUE_RANGE_OPTIONS = [
  { value: '0-1000', label: 'ZMW 0 - ZMW 1,000' },
  { value: '1001-5000', label: 'ZMW 1,001 - ZMW 5,000' },
  { value: '5001-10000', label: 'ZMW 5,001 - ZMW 10,000' },
  { value: '10001-25000', label: 'ZMW 10,001 - ZMW 25,000' },
  { value: '25001-50000', label: 'ZMW 25,001 - ZMW 50,000' },
  { value: '50001-100000', label: 'ZMW 50,001 - ZMW 100,000' },
  { value: '100001-250000', label: 'ZMW 100,001 - ZMW 250,000' },
  { value: '250001-500000', label: 'ZMW 250,001 - ZMW 500,000' },
  { value: '500001+', label: 'ZMW 500,001+' },
];

const ZAMBIAN_PROVINCES = [
  'Central Province',
  'Copperbelt Province',
  'Eastern Province',
  'Luapula Province',
  'Lusaka Province',
  'Muchinga Province',
  'Northern Province',
  'North-Western Province',
  'Southern Province',
  'Western Province'
];

// Form validation schema
const profileSchema = z.object({
  first_name: z.string().min(1, 'First name is required'),
  last_name: z.string().min(1, 'Last name is required'),
  business_name: z.string().min(1, 'Business name is required'),
  business_type: z.enum(['food_beverage', 'retail', 'beauty', 'health_wellness', 'services']),
  business_subcategory: z.string().optional(),
  business_city: z.string().min(1, 'City is required'),
  business_province: z.string().min(1, 'Province is required'),
  employee_count: z.string().optional(),
  monthly_revenue_range: z.string().optional(),
});

type ProfileFormData = z.infer<typeof profileSchema>;

export default function ProfileSetupPage() {
  const { user, userProfile, refreshUserData } = useAuth();
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      first_name: userProfile?.first_name || '',
      last_name: userProfile?.last_name || '',
      business_name: userProfile?.business_name || '',
      business_type: userProfile?.business_type || undefined,
      business_subcategory: userProfile?.business_subcategory || '',
      business_city: userProfile?.business_city || '',
      business_province: userProfile?.business_province || '',
      employee_count: userProfile?.employee_count || '',
      monthly_revenue_range: userProfile?.monthly_revenue_range || '',
    },
  });

  const watchedBusinessType = watch('business_type');

  const onSubmit = async (data: ProfileFormData) => {
    setIsLoading(true);
    try {
      // Create or update profile using the API
      await profileApi.createProfile(data);
      
      // Refresh user profile data
      await refreshUserData();
      
      // Redirect to dashboard
      router.push('/dashboard');
    } catch (error) {
      console.error('Profile setup failed:', error);
      // TODO: Add proper error handling/notification
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow">
          <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => router.back()}
                  className="mr-4"
                >
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back
                </Button>
                <h1 className="text-2xl font-bold text-gray-900">Complete Your Profile</h1>
              </div>
              <div className="text-sm text-gray-500">
                Welcome, {user?.email}
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-3xl mx-auto py-6 sm:px-6 lg:px-8">
          <div className="px-4 py-6 sm:px-0">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              
              {/* Personal Information */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <User className="h-5 w-5 mr-2" />
                    Personal Information
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="first_name" className="block text-sm font-medium text-gray-700 mb-1">
                        First Name *
                      </label>
                      <Input
                        id="first_name"
                        {...register('first_name')}
                        placeholder="Enter your first name"
                        className={errors.first_name ? 'border-red-500' : ''}
                      />
                      {errors.first_name && (
                        <p className="text-sm text-red-500 mt-1">{errors.first_name.message}</p>
                      )}
                    </div>
                    <div>
                      <label htmlFor="last_name" className="block text-sm font-medium text-gray-700 mb-1">
                        Last Name *
                      </label>
                      <Input
                        id="last_name"
                        {...register('last_name')}
                        placeholder="Enter your last name"
                        className={errors.last_name ? 'border-red-500' : ''}
                      />
                      {errors.last_name && (
                        <p className="text-sm text-red-500 mt-1">{errors.last_name.message}</p>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Business Information */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Building2 className="h-5 w-5 mr-2" />
                    Business Information
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label htmlFor="business_name" className="block text-sm font-medium text-gray-700 mb-1">
                      Business Name *
                    </label>
                    <Input
                      id="business_name"
                      {...register('business_name')}
                      placeholder="Enter your business name"
                      className={errors.business_name ? 'border-red-500' : ''}
                    />
                    {errors.business_name && (
                      <p className="text-sm text-red-500 mt-1">{errors.business_name.message}</p>
                    )}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="business_type" className="block text-sm font-medium text-gray-700 mb-1">
                        Business Type *
                      </label>
                      <select
                        {...register('business_type')}
                        className={`w-full p-2 border rounded-md ${errors.business_type ? 'border-red-500' : 'border-gray-300'}`}
                        onChange={(e) => {
                          setValue('business_type', e.target.value as keyof typeof BUSINESS_TYPES);
                          setValue('business_subcategory', '');
                        }}
                      >
                        <option value="">Select business type</option>
                        {Object.entries(BUSINESS_TYPES).map(([key, type]) => (
                          <option key={key} value={key}>
                            {type.label}
                          </option>
                        ))}
                      </select>
                      {errors.business_type && (
                        <p className="text-sm text-red-500 mt-1">{errors.business_type.message}</p>
                      )}
                    </div>

                    {watchedBusinessType && (
                      <div>
                        <label htmlFor="business_subcategory" className="block text-sm font-medium text-gray-700 mb-1">
                          Business Subcategory
                        </label>
                        <select
                          {...register('business_subcategory')}
                          className="w-full p-2 border border-gray-300 rounded-md"
                        >
                          <option value="">Select subcategory</option>
                          {BUSINESS_TYPES[watchedBusinessType as keyof typeof BUSINESS_TYPES]?.subcategories.map((subcat) => (
                            <option key={subcat.value} value={subcat.value}>
                              {subcat.label}
                            </option>
                          ))}
                        </select>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Location Information */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <MapPin className="h-5 w-5 mr-2" />
                    Business Location
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="business_city" className="block text-sm font-medium text-gray-700 mb-1">
                        City/Town *
                      </label>
                      <Input
                        id="business_city"
                        {...register('business_city')}
                        placeholder="e.g., Lusaka, Kitwe, Ndola"
                        className={errors.business_city ? 'border-red-500' : ''}
                      />
                      {errors.business_city && (
                        <p className="text-sm text-red-500 mt-1">{errors.business_city.message}</p>
                      )}
                    </div>
                    <div>
                      <label htmlFor="business_province" className="block text-sm font-medium text-gray-700 mb-1">
                        Province *
                      </label>
                      <select
                        {...register('business_province')}
                        className={`w-full p-2 border rounded-md ${errors.business_province ? 'border-red-500' : 'border-gray-300'}`}
                      >
                        <option value="">Select province</option>
                        {ZAMBIAN_PROVINCES.map((province) => (
                          <option key={province} value={province}>
                            {province}
                          </option>
                        ))}
                      </select>
                      {errors.business_province && (
                        <p className="text-sm text-red-500 mt-1">{errors.business_province.message}</p>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Optional Business Details */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Users className="h-5 w-5 mr-2" />
                    Business Details (Optional)
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="employee_count" className="block text-sm font-medium text-gray-700 mb-1">
                        Number of Employees
                      </label>
                      <select
                        {...register('employee_count')}
                        className="w-full p-2 border border-gray-300 rounded-md"
                      >
                        <option value="">Select employee count</option>
                        {EMPLOYEE_COUNT_OPTIONS.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label htmlFor="monthly_revenue_range" className="block text-sm font-medium text-gray-700 mb-1">
                        Monthly Revenue Range
                      </label>
                      <select
                        {...register('monthly_revenue_range')}
                        className="w-full p-2 border border-gray-300 rounded-md"
                      >
                        <option value="">Select revenue range</option>
                        {REVENUE_RANGE_OPTIONS.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Submit Button */}
              <div className="flex justify-end space-x-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => router.push('/dashboard')}
                >
                  Skip for Now
                </Button>
                <Button
                  type="submit"
                  disabled={isLoading}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  {isLoading ? 'Saving...' : 'Complete Profile'}
                </Button>
              </div>
            </form>
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
}
