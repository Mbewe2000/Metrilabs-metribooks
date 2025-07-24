import { apiClient } from '@/lib/api-client';
import { 
  LoginCredentials, 
  RegisterData, 
  AuthResponse, 
  User, 
  UserProfile 
} from '@/types';

// Backend response wrapper interface
interface BackendResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

export const authApi = {
  // User Authentication
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/login/', credentials);
    return response.data;
  },

  async register(data: RegisterData): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/register/', data);
    return response.data;
  },

  async logout(): Promise<void> {
    const tokens = apiClient.getTokens();
    if (tokens?.refresh) {
      try {
        await apiClient.post('/auth/logout/', {
          refresh_token: tokens.refresh
        });
      } catch (error) {
        // Even if API logout fails, we still want to clear local tokens
        console.warn('Logout API call failed, but clearing local tokens:', error);
      }
    }
    apiClient.logout();
  },

  async refreshToken(): Promise<{ access: string }> {
    const response = await apiClient.post<{ access: string }>('/auth/token/refresh/');
    return response.data;
  },

  async changePassword(data: { current_password: string; new_password: string }): Promise<{ message: string }> {
    const response = await apiClient.put<{ message: string }>('/auth/change-password/', {
      old_password: data.current_password,
      new_password: data.new_password,
      new_password_confirm: data.new_password,
    });
    return response.data;
  },

  async resetPassword(email: string): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>('/auth/reset-password/', { email_or_phone: email });
    return response.data;
  },

  async resetPasswordConfirm(data: {
    uidb64: string;
    token: string;
    new_password: string;
  }): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>('/auth/reset-password-confirm/', data);
    return response.data;
  },

  // User Profile
  async getProfile(): Promise<User> {
    const response = await apiClient.get<User>('/auth/profile/');
    return response.data;
  },

  async updateProfile(data: Partial<User>): Promise<User> {
    const response = await apiClient.patch<User>('/auth/profile/', data);
    return response.data;
  },

  // Business Profile
  async getUserProfile(): Promise<UserProfile> {
    const response = await apiClient.get('/profile/');
    // Backend wraps response in {success, message, data} format
    const backendResponse = response.data as BackendResponse<UserProfile>;
    return backendResponse.data;
  },

  async updateUserProfile(data: Partial<UserProfile>): Promise<UserProfile> {
    const response = await apiClient.patch<UserProfile>('/profile/update/', data);
    return response.data;
  },

  // Security Operations  
  async updateEmail(data: {
    new_email: string;
    password: string;
  }): Promise<User> {
    const response = await apiClient.patch<User>('/auth/update-email/', data);
    return response.data;
  },

  async updatePhone(data: {
    new_phone: string;
    password: string;
  }): Promise<User> {
    const response = await apiClient.patch<User>('/auth/update-phone/', data);
    return response.data;
  },

  async getProfileSummary(): Promise<{
    profile: UserProfile;
    completion_percentage: number;
    missing_fields: string[];
  }> {
    const response = await apiClient.get<{
      profile: UserProfile;
      completion_percentage: number;
      missing_fields: string[];
    }>('/profile/summary/');
    return response.data;
  },

  async getBusinessSubcategories(): Promise<Record<string, string[]>> {
    const response = await apiClient.get<Record<string, string[]>>('/business/subcategories/');
    return response.data;
  },
};
