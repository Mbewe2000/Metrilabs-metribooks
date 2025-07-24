'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/use-auth';
import { ProtectedRoute } from '@/components/protected-route';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { ArrowLeft, Lock, Mail, Phone, Key } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { authApi } from '@/lib/auth-api';

// Form schemas
const passwordChangeSchema = z.object({
  current_password: z.string().min(1, 'Current password is required'),
  new_password: z.string().min(8, 'Password must be at least 8 characters'),
  confirm_password: z.string().min(1, 'Please confirm your password'),
}).refine((data) => data.new_password === data.confirm_password, {
  message: "Passwords don't match",
  path: ["confirm_password"],
});

const emailUpdateSchema = z.object({
  new_email: z.string().email('Please enter a valid email address'),
  password: z.string().min(1, 'Password is required for security'),
});

const phoneUpdateSchema = z.object({
  new_phone: z.string().min(10, 'Please enter a valid phone number'),
  password: z.string().min(1, 'Password is required for security'),
});

const passwordResetSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
});

type PasswordChangeData = z.infer<typeof passwordChangeSchema>;
type EmailUpdateData = z.infer<typeof emailUpdateSchema>;
type PhoneUpdateData = z.infer<typeof phoneUpdateSchema>;
type PasswordResetData = z.infer<typeof passwordResetSchema>;

export default function SecuritySettingsPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [activeSection, setActiveSection] = useState<string>('password');
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Password Change Form
  const passwordForm = useForm<PasswordChangeData>({
    resolver: zodResolver(passwordChangeSchema),
  });

  // Email Update Form
  const emailForm = useForm<EmailUpdateData>({
    resolver: zodResolver(emailUpdateSchema),
    defaultValues: {
      new_email: user?.email || '',
    },
  });

  // Phone Update Form
  const phoneForm = useForm<PhoneUpdateData>({
    resolver: zodResolver(phoneUpdateSchema),
    defaultValues: {
      new_phone: user?.phone || '',
    },
  });

  // Password Reset Form
  const resetForm = useForm<PasswordResetData>({
    resolver: zodResolver(passwordResetSchema),
    defaultValues: {
      email: user?.email || '',
    },
  });

  const onPasswordChange = async (data: PasswordChangeData) => {
    setIsLoading(true);
    setMessage(null);
    try {
      await authApi.changePassword({
        current_password: data.current_password,
        new_password: data.new_password,
      });
      
      setMessage({ type: 'success', text: 'Password changed successfully!' });
      passwordForm.reset();
    } catch (error) {
      console.error('Password change failed:', error);
      setMessage({ type: 'error', text: 'Failed to change password. Please check your current password.' });
    } finally {
      setIsLoading(false);
    }
  };

  const onEmailUpdate = async (data: EmailUpdateData) => {
    setIsLoading(true);
    setMessage(null);
    try {
      await authApi.updateEmail({
        new_email: data.new_email,
        password: data.password,
      });
      
      setMessage({ type: 'success', text: 'Email updated successfully!' });
      emailForm.reset();
      // Refresh user data to update the UI
      window.location.reload();
    } catch (error) {
      console.error('Email update failed:', error);
      setMessage({ type: 'error', text: 'Failed to update email. Please check your password.' });
    } finally {
      setIsLoading(false);
    }
  };

  const onPhoneUpdate = async (data: PhoneUpdateData) => {
    setIsLoading(true);
    setMessage(null);
    try {
      await authApi.updatePhone({
        new_phone: data.new_phone,
        password: data.password,
      });
      
      setMessage({ type: 'success', text: 'Phone number updated successfully!' });
      phoneForm.reset();
      // Refresh user data to update the UI
      window.location.reload();
    } catch (error) {
      console.error('Phone update failed:', error);
      setMessage({ type: 'error', text: 'Failed to update phone number. Please check your password.' });
    } finally {
      setIsLoading(false);
    }
  };

  const onPasswordReset = async (data: PasswordResetData) => {
    setIsLoading(true);
    setMessage(null);
    try {
      await authApi.resetPassword(data.email);
      
      setMessage({ type: 'success', text: 'Password reset email sent! Check your inbox.' });
      resetForm.reset();
    } catch (error) {
      console.error('Password reset failed:', error);
      setMessage({ type: 'error', text: 'Failed to send reset email. Please try again.' });
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
                <h1 className="text-2xl font-bold text-gray-900">Security Settings</h1>
              </div>
              <div className="text-sm text-gray-500">
                {user?.email}
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-3xl mx-auto py-6 sm:px-6 lg:px-8">
          <div className="px-4 py-6 sm:px-0">
            
            {/* Message Display */}
            {message && (
              <div className={`mb-6 p-4 rounded-md ${
                message.type === 'success' 
                  ? 'bg-green-50 text-green-800 border border-green-200' 
                  : 'bg-red-50 text-red-800 border border-red-200'
              }`}>
                {message.text}
              </div>
            )}

            {/* Navigation Tabs */}
            <div className="flex space-x-1 mb-6 bg-gray-100 p-1 rounded-lg">
              <button
                onClick={() => setActiveSection('password')}
                className={`flex-1 flex items-center justify-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  activeSection === 'password'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Lock className="h-4 w-4 mr-2" />
                Change Password
              </button>
              <button
                onClick={() => setActiveSection('email')}
                className={`flex-1 flex items-center justify-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  activeSection === 'email'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Mail className="h-4 w-4 mr-2" />
                Update Email
              </button>
              <button
                onClick={() => setActiveSection('phone')}
                className={`flex-1 flex items-center justify-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  activeSection === 'phone'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Phone className="h-4 w-4 mr-2" />
                Update Phone
              </button>
              <button
                onClick={() => setActiveSection('reset')}
                className={`flex-1 flex items-center justify-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  activeSection === 'reset'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Key className="h-4 w-4 mr-2" />
                Reset Password
              </button>
            </div>

            {/* Change Password Section */}
            {activeSection === 'password' && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Lock className="h-5 w-5 mr-2" />
                    Change Password
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <form onSubmit={passwordForm.handleSubmit(onPasswordChange)} className="space-y-4">
                    <div>
                      <label htmlFor="current_password" className="block text-sm font-medium text-gray-700 mb-1">
                        Current Password *
                      </label>
                      <Input
                        id="current_password"
                        type="password"
                        {...passwordForm.register('current_password')}
                        placeholder="Enter your current password"
                        className={passwordForm.formState.errors.current_password ? 'border-red-500' : ''}
                      />
                      {passwordForm.formState.errors.current_password && (
                        <p className="text-sm text-red-500 mt-1">
                          {passwordForm.formState.errors.current_password.message}
                        </p>
                      )}
                    </div>

                    <div>
                      <label htmlFor="new_password" className="block text-sm font-medium text-gray-700 mb-1">
                        New Password *
                      </label>
                      <Input
                        id="new_password"
                        type="password"
                        {...passwordForm.register('new_password')}
                        placeholder="Enter your new password"
                        className={passwordForm.formState.errors.new_password ? 'border-red-500' : ''}
                      />
                      {passwordForm.formState.errors.new_password && (
                        <p className="text-sm text-red-500 mt-1">
                          {passwordForm.formState.errors.new_password.message}
                        </p>
                      )}
                    </div>

                    <div>
                      <label htmlFor="confirm_password" className="block text-sm font-medium text-gray-700 mb-1">
                        Confirm New Password *
                      </label>
                      <Input
                        id="confirm_password"
                        type="password"
                        {...passwordForm.register('confirm_password')}
                        placeholder="Confirm your new password"
                        className={passwordForm.formState.errors.confirm_password ? 'border-red-500' : ''}
                      />
                      {passwordForm.formState.errors.confirm_password && (
                        <p className="text-sm text-red-500 mt-1">
                          {passwordForm.formState.errors.confirm_password.message}
                        </p>
                      )}
                    </div>

                    <div className="flex justify-end">
                      <Button
                        type="submit"
                        disabled={isLoading}
                        className="bg-blue-600 hover:bg-blue-700"
                      >
                        {isLoading ? 'Changing...' : 'Change Password'}
                      </Button>
                    </div>
                  </form>
                </CardContent>
              </Card>
            )}

            {/* Update Email Section */}
            {activeSection === 'email' && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Mail className="h-5 w-5 mr-2" />
                    Update Email Address
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
                    <p className="text-sm text-blue-800">
                      <strong>Current Email:</strong> {user?.email}
                    </p>
                  </div>
                  <form onSubmit={emailForm.handleSubmit(onEmailUpdate)} className="space-y-4">
                    <div>
                      <label htmlFor="new_email" className="block text-sm font-medium text-gray-700 mb-1">
                        New Email Address *
                      </label>
                      <Input
                        id="new_email"
                        type="email"
                        {...emailForm.register('new_email')}
                        placeholder="Enter your new email address"
                        className={emailForm.formState.errors.new_email ? 'border-red-500' : ''}
                      />
                      {emailForm.formState.errors.new_email && (
                        <p className="text-sm text-red-500 mt-1">
                          {emailForm.formState.errors.new_email.message}
                        </p>
                      )}
                    </div>

                    <div>
                      <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                        Confirm Password *
                      </label>
                      <Input
                        id="password"
                        type="password"
                        {...emailForm.register('password')}
                        placeholder="Enter your password for security"
                        className={emailForm.formState.errors.password ? 'border-red-500' : ''}
                      />
                      {emailForm.formState.errors.password && (
                        <p className="text-sm text-red-500 mt-1">
                          {emailForm.formState.errors.password.message}
                        </p>
                      )}
                    </div>

                    <div className="flex justify-end">
                      <Button
                        type="submit"
                        disabled={isLoading}
                        className="bg-blue-600 hover:bg-blue-700"
                      >
                        {isLoading ? 'Updating...' : 'Update Email'}
                      </Button>
                    </div>
                  </form>
                </CardContent>
              </Card>
            )}

            {/* Update Phone Section */}
            {activeSection === 'phone' && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Phone className="h-5 w-5 mr-2" />
                    Update Phone Number
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
                    <p className="text-sm text-blue-800">
                      <strong>Current Phone:</strong> {user?.phone || 'Not set'}
                    </p>
                  </div>
                  <form onSubmit={phoneForm.handleSubmit(onPhoneUpdate)} className="space-y-4">
                    <div>
                      <label htmlFor="new_phone" className="block text-sm font-medium text-gray-700 mb-1">
                        New Phone Number *
                      </label>
                      <Input
                        id="new_phone"
                        type="tel"
                        {...phoneForm.register('new_phone')}
                        placeholder="Enter your new phone number"
                        className={phoneForm.formState.errors.new_phone ? 'border-red-500' : ''}
                      />
                      {phoneForm.formState.errors.new_phone && (
                        <p className="text-sm text-red-500 mt-1">
                          {phoneForm.formState.errors.new_phone.message}
                        </p>
                      )}
                    </div>

                    <div>
                      <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                        Confirm Password *
                      </label>
                      <Input
                        id="password"
                        type="password"
                        {...phoneForm.register('password')}
                        placeholder="Enter your password for security"
                        className={phoneForm.formState.errors.password ? 'border-red-500' : ''}
                      />
                      {phoneForm.formState.errors.password && (
                        <p className="text-sm text-red-500 mt-1">
                          {phoneForm.formState.errors.password.message}
                        </p>
                      )}
                    </div>

                    <div className="flex justify-end">
                      <Button
                        type="submit"
                        disabled={isLoading}
                        className="bg-blue-600 hover:bg-blue-700"
                      >
                        {isLoading ? 'Updating...' : 'Update Phone'}
                      </Button>
                    </div>
                  </form>
                </CardContent>
              </Card>
            )}

            {/* Password Reset Section */}
            {activeSection === 'reset' && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Key className="h-5 w-5 mr-2" />
                    Reset Password
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                    <p className="text-sm text-yellow-800">
                      This will send a password reset link to your email address. You&apos;ll be logged out after requesting a reset.
                    </p>
                  </div>
                  <form onSubmit={resetForm.handleSubmit(onPasswordReset)} className="space-y-4">
                    <div>
                      <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                        Email Address *
                      </label>
                      <Input
                        id="email"
                        type="email"
                        {...resetForm.register('email')}
                        placeholder="Enter your email address"
                        className={resetForm.formState.errors.email ? 'border-red-500' : ''}
                      />
                      {resetForm.formState.errors.email && (
                        <p className="text-sm text-red-500 mt-1">
                          {resetForm.formState.errors.email.message}
                        </p>
                      )}
                    </div>

                    <div className="flex justify-end">
                      <Button
                        type="submit"
                        disabled={isLoading}
                        className="bg-red-600 hover:bg-red-700"
                      >
                        {isLoading ? 'Sending...' : 'Send Reset Email'}
                      </Button>
                    </div>
                  </form>
                </CardContent>
              </Card>
            )}

          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
}
