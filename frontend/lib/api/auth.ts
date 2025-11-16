import apiClient from './client';

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  user: {
    id: string;
    email?: string;
    phone?: string;
    first_name?: string;
    last_name?: string;
    role: string;
  };
}

// Request verification code for phone auth
export const requestVerificationCode = async (phone: string, language = 'en') => {
  const response = await apiClient.post('/auth/request-code', { phone, language });
  return response.data;
};

// Verify code and login
export const verifyCode = async (phone: string, code: string): Promise<LoginResponse> => {
  const response = await apiClient.post<LoginResponse>('/auth/verify-code', { phone, code });
  return response.data;
};

// Google OAuth login
export const googleLogin = async (idToken: string): Promise<LoginResponse> => {
  const response = await apiClient.post<LoginResponse>('/auth/google', { id_token: idToken });
  return response.data;
};

// Refresh token
export const refreshToken = async (refreshToken: string): Promise<LoginResponse> => {
  const response = await apiClient.post<LoginResponse>('/auth/refresh', {
    refresh_token: refreshToken,
  });
  return response.data;
};

// Logout
export const logout = async () => {
  await apiClient.post('/auth/logout');
};
