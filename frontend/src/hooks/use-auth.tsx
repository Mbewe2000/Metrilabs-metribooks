'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, UserProfile } from '@/types';
import { authApi } from '@/lib/auth-api';
import { apiClient } from '@/lib/api-client';

interface AuthContextType {
  user: User | null;
  userProfile: UserProfile | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: {
    email?: string;
    phone?: string;
    password: string;
    password_confirm: string;
  }) => Promise<void>;
  logout: () => Promise<void>;
  refreshUserData: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = !!user;

  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        const tokens = apiClient.getTokens();
        if (tokens) {
          await refreshUserData();
        }
      } catch (error) {
        console.error('Auth check failed:', error);
        apiClient.logout();
      } finally {
        setIsLoading(false);
      }
    };

    checkAuthStatus();
  }, []);

  const refreshUserData = async () => {
    try {
      const [userData, profileData] = await Promise.all([
        authApi.getProfile(),
        authApi.getUserProfile().catch(() => null), // Profile might not exist yet
      ]);
      
      setUser(userData);
      setUserProfile(profileData);
    } catch (error) {
      console.error('Failed to refresh user data:', error);
      throw error;
    }
  };

  const login = async (email: string, password: string) => {
    try {
      setIsLoading(true);
      console.log('Attempting login with:', { email_or_phone: email }); // Debug log
      
      const response = await authApi.login({ email_or_phone: email, password });
      
      apiClient.setTokens(response.tokens);
      setUser(response.user);
      
      // Try to get user profile
      try {
        const profileData = await authApi.getUserProfile();
        setUserProfile(profileData);
      } catch {
        // Profile doesn't exist yet, which is fine for new users
        console.log('User profile not found, will need to create one');
      }
    } catch (error) {
      console.error('Login failed:', error);
      
      // Extract meaningful error message
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response: { data: unknown } };
        if (axiosError.response?.data) {
          const errorData = axiosError.response.data as Record<string, unknown>;
          
          // Handle validation errors
          if (errorData.email_or_phone) {
            throw new Error('Email or phone number is required');
          }
          if (errorData.password) {
            throw new Error('Password is required');
          }
          if (errorData.non_field_errors) {
            const errors = errorData.non_field_errors as string[];
            throw new Error(errors[0] || 'Invalid credentials');
          }
          if (errorData.detail) {
            throw new Error(errorData.detail as string);
          }
        }
      }
      
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (data: {
    email?: string;
    phone?: string;
    password: string;
    password_confirm: string;
  }) => {
    try {
      setIsLoading(true);
      const response = await authApi.register(data);
      
      apiClient.setTokens(response.tokens);
      setUser(response.user);
      setUserProfile(null); // New user won't have a profile yet
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } catch (error) {
      console.error('Logout API call failed:', error);
    } finally {
      apiClient.logout();
      setUser(null);
      setUserProfile(null);
    }
  };

  const value: AuthContextType = {
    user,
    userProfile,
    isLoading,
    isAuthenticated,
    login,
    register,
    logout,
    refreshUserData,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
