import { apiClient } from './api-client';
import { UserProfile } from '@/types';

export interface CreateProfileData {
  first_name: string;
  last_name: string;
  business_name: string;
  business_type: string;
  business_subcategory?: string;
  business_city: string;
  business_province: string;
  employee_count?: string;
  monthly_revenue_range?: string;
}

export type UpdateProfileData = Partial<CreateProfileData>;

export interface ProfileCompletion {
  completion_percentage: number;
  missing_fields: string[];
  is_complete: boolean;
}

// Backend response wrapper interface
interface BackendResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

export const profileApi = {
  // Get user profile
  getProfile: async (): Promise<UserProfile> => {
    const response = await apiClient.get('/profile/');
    return response.data as UserProfile;
  },

  // Create user profile
  createProfile: async (data: CreateProfileData): Promise<UserProfile> => {
    const response = await apiClient.put('/profile/update/', data);
    const backendResponse = response.data as BackendResponse<UserProfile>;
    return backendResponse.data;
  },

  // Update user profile
  updateProfile: async (data: UpdateProfileData): Promise<UserProfile> => {
    const response = await apiClient.put('/profile/update/', data);
    const backendResponse = response.data as BackendResponse<UserProfile>;
    return backendResponse.data;
  },

  // Partial update user profile
  partialUpdateProfile: async (data: UpdateProfileData): Promise<UserProfile> => {
    const response = await apiClient.patch('/profile/update/', data);
    const backendResponse = response.data as BackendResponse<UserProfile>;
    return backendResponse.data;
  },

  // Get profile summary
  getProfileSummary: async (): Promise<UserProfile> => {
    const response = await apiClient.get('/profile/summary/');
    return response.data as UserProfile;
  },

  // Get profile completion status
  getProfileCompletion: async (): Promise<ProfileCompletion> => {
    const response = await apiClient.get('/profile/completion/');
    return response.data as ProfileCompletion;
  },
};
