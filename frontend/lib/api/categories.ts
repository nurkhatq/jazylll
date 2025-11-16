import apiClient from './client';

export interface Category {
  id: string;
  code: string;
  name_ru: string;
  name_kk: string;
  name_en: string;
  description_ru?: string;
  description_kk?: string;
  description_en?: string;
  icon_url?: string;
  salon_count: number;
}

export interface City {
  city: string;
  salon_count: number;
}

// Get all categories (PUBLIC)
export const getCategories = async (): Promise<Category[]> => {
  const response = await apiClient.get<Category[]>('/categories');
  return response.data;
};

// Get single category (PUBLIC)
export const getCategory = async (id: string): Promise<Category> => {
  const response = await apiClient.get<Category>(`/categories/${id}`);
  return response.data;
};

// Get cities with salons (PUBLIC)
export const getCities = async (categoryId?: string): Promise<City[]> => {
  const response = await apiClient.get<City[]>('/categories/cities/list', {
    params: categoryId ? { category_id: categoryId } : undefined,
  });
  return response.data;
};
