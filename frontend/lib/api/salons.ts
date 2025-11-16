import apiClient from './client';

export interface Salon {
  id: string;
  display_name: string;
  slug: string;
  description_ru?: string;
  logo_url?: string;
  cover_image_url?: string;
  rating: number;
  total_reviews: number;
  city?: string;
  is_promoted?: boolean;
}

export interface SalonDetails extends Salon {
  business_name: string;
  description_kk?: string;
  description_en?: string;
  email?: string;
  phone?: string;
  website_url?: string;
  social_links?: any;
  is_active: boolean;
  created_at: string;
}

export interface CatalogResponse {
  items: Salon[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

// Get catalog of salons (PUBLIC)
export const getSalons = async (params: {
  category_id: string;
  city?: string;
  search?: string;
  sort?: 'relevance' | 'rating' | 'recent';
  page?: number;
  per_page?: number;
}): Promise<CatalogResponse> => {
  const response = await apiClient.get<CatalogResponse>('/catalog/salons', { params });
  return response.data;
};

// Get salon public page (PUBLIC)
export const getSalonBySlug = async (slug: string): Promise<any> => {
  const response = await apiClient.get(`/catalog/salons/${slug}`);
  return response.data;
};

// Register click on salon
export const registerSalonClick = async (salonId: string) => {
  await apiClient.post(`/catalog/salons/${salonId}/click`);
};

// Create salon (requires auth)
export const createSalon = async (data: any): Promise<SalonDetails> => {
  const response = await apiClient.post<SalonDetails>('/salons', data);
  return response.data;
};

// Get my salon (requires auth)
export const getMySalon = async (salonId: string): Promise<SalonDetails> => {
  const response = await apiClient.get<SalonDetails>(`/salons/${salonId}`);
  return response.data;
};

// Update salon (requires auth)
export const updateSalon = async (salonId: string, data: any): Promise<SalonDetails> => {
  const response = await apiClient.patch<SalonDetails>(`/salons/${salonId}`, data);
  return response.data;
};

// Upload logo
export const uploadLogo = async (salonId: string, file: File) => {
  const formData = new FormData();
  formData.append('logo', file);
  const response = await apiClient.post(`/salons/${salonId}/logo`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

// Upload cover
export const uploadCover = async (salonId: string, file: File) => {
  const formData = new FormData();
  formData.append('cover', file);
  const response = await apiClient.post(`/salons/${salonId}/cover`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

// Get list of my salons
export const getMySalons = async (): Promise<SalonDetails[]> => {
  const response = await apiClient.get<SalonDetails[]>('/salons');
  return response.data;
};

// Branch management
export const createBranch = async (salonId: string, data: any) => {
  const response = await apiClient.post(`/salons/${salonId}/branches`, data);
  return response.data;
};

export const updateBranch = async (salonId: string, branchId: string, data: any) => {
  const response = await apiClient.patch(`/salons/${salonId}/branches/${branchId}`, data);
  return response.data;
};

export const deleteBranch = async (salonId: string, branchId: string) => {
  await apiClient.delete(`/salons/${salonId}/branches/${branchId}`);
};

// Service management
export const createService = async (salonId: string, data: any) => {
  const response = await apiClient.post(`/salons/${salonId}/services`, data);
  return response.data;
};

export const updateService = async (salonId: string, serviceId: string, data: any) => {
  const response = await apiClient.patch(`/salons/${salonId}/services/${serviceId}`, data);
  return response.data;
};

export const deleteService = async (salonId: string, serviceId: string) => {
  await apiClient.delete(`/salons/${salonId}/services/${serviceId}`);
};

// Master management
export const getSalonMasters = async (salonId: string, params?: any) => {
  const response = await apiClient.get(`/masters/salons/${salonId}/masters`, { params });
  return response.data;
};

export const inviteMaster = async (salonId: string, data: {
  email?: string;
  phone?: string;
  first_name: string;
  last_name: string;
  specialization?: string;
  branch_id?: string;
}) => {
  const response = await apiClient.post(`/masters/salons/${salonId}/masters/invite`, data);
  return response.data;
};

export const updateMaster = async (salonId: string, masterId: string, data: any) => {
  const response = await apiClient.patch(`/masters/salons/${salonId}/masters/${masterId}`, data);
  return response.data;
};

export const deactivateMaster = async (salonId: string, masterId: string) => {
  const response = await apiClient.patch(`/masters/salons/${salonId}/masters/${masterId}/deactivate`);
  return response.data;
};
