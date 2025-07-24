'use client';

import { useAuth } from '@/hooks/use-auth';
import { ProtectedRoute } from '@/components/protected-route';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { User, Building2, LogOut } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function DashboardPage() {
  const { user, userProfile, logout } = useAuth();
  const router = useRouter();

  const handleLogout = async () => {
    try {
      await logout();
      router.push('/auth/login');
    } catch (error) {
      console.error('Logout failed:', error);
      router.push('/auth/login');
    }
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center">
                <h1 className="text-2xl font-bold text-gray-900">Metribooks</h1>
              </div>
              <div className="flex items-center space-x-4">
                <span className="text-sm text-gray-700">
                  Welcome, {user?.email}
                </span>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={handleLogout}
                  className="flex items-center"
                >
                  <LogOut className="h-4 w-4 mr-2" />
                  Logout
                </Button>
              </div>
            </div>
          </div>
        </header>

        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <div className="px-4 py-6 sm:px-0">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              
              {/* Welcome Card */}
              <Card className="col-span-full">
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <User className="h-5 w-5 mr-2" />
                    Welcome to Metribooks
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <p className="text-gray-600">
                      Your complete business management platform for Zambian SMEs
                    </p>
                    <div className="grid grid-cols-2 gap-4 mt-4">
                      <div>
                        <p className="text-sm text-gray-500">Email</p>
                        <p className="font-medium">{user?.email}</p>
                      </div>
                      {user?.phone && (
                        <div>
                          <p className="text-sm text-gray-500">Phone</p>
                          <p className="font-medium">{user?.phone}</p>
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Business Profile Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Building2 className="h-5 w-5 mr-2" />
                    Business Profile
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {userProfile ? (
                    <div className="space-y-2">
                      <div>
                        <p className="font-medium text-lg">
                          {userProfile.business_name || 'Business name not set'}
                        </p>
                        <p className="text-sm text-gray-500">
                          Owner: {userProfile.first_name || 'N/A'} {userProfile.last_name || 'N/A'}
                        </p>
                      </div>
                      {userProfile.business_type && (
                        <p className="text-sm text-gray-600">
                          {userProfile.business_type.replace('_', ' ').charAt(0).toUpperCase() + 
                           userProfile.business_type.replace('_', ' ').slice(1)}
                        </p>
                      )}
                      {userProfile.business_city && userProfile.business_province && (
                        <p className="text-sm text-gray-600">
                          {userProfile.business_city}, {userProfile.business_province}
                        </p>
                      )}
                      <div className="flex items-center justify-between mt-3">
                        <div className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                          userProfile.is_complete 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {userProfile.is_complete ? 'Complete' : 'Incomplete'}
                        </div>
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => router.push('/profile/setup')}
                        >
                          Edit Profile
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-4">
                      <p className="text-gray-600 mb-3">No business profile found</p>
                      <Button 
                        size="sm" 
                        className="bg-blue-600 hover:bg-blue-700"
                        onClick={() => router.push('/profile/setup')}
                      >
                        Create Profile
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Quick Actions Card */}
              <Card>
                <CardHeader>
                  <CardTitle>Quick Actions</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <Button variant="outline" className="w-full justify-start">
                      Record Sale
                    </Button>
                    <Button variant="outline" className="w-full justify-start">
                      Add Expense
                    </Button>
                    <Button variant="outline" className="w-full justify-start">
                      View Reports
                    </Button>
                    <Button 
                      variant="outline" 
                      className="w-full justify-start"
                      onClick={() => router.push('/settings/security')}
                    >
                      Security Settings
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {/* System Status Card */}
              <Card>
                <CardHeader>
                  <CardTitle>System Status</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Authentication</span>
                      <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm">API Connection</span>
                      <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm">ZRA Compliance</span>
                      <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
}
