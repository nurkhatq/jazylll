import apiClient from './client';

export interface TimeSlot {
  slot_time: string;
  slot_end: string;
}

export interface Booking {
  id: string;
  booking_date: string;
  start_time: string;
  end_time: string;
  final_price: number;
  status: string;
  notes_from_client?: string;
  master: any;
  service: any;
  branch: any;
}

// Get available time slots
export const getAvailableSlots = async (params: {
  master_id: string;
  date: string;
  service_id: string;
  branch_id: string;
}): Promise<TimeSlot[]> => {
  const response = await apiClient.get<TimeSlot[]>(`/bookings/masters/${params.master_id}/available-slots`, {
    params: {
      date: params.date,
      service_id: params.service_id,
      branch_id: params.branch_id,
    },
  });
  return response.data;
};

// Create booking
export const createBooking = async (data: {
  master_id: string;
  service_id: string;
  branch_id: string;
  booking_date: string;
  start_time: string;
  notes_from_client?: string;
}): Promise<Booking> => {
  const response = await apiClient.post<Booking>('/bookings', data);
  return response.data;
};

// Get my bookings
export const getMyBookings = async (status?: string): Promise<Booking[]> => {
  const response = await apiClient.get<Booking[]>('/bookings', {
    params: status ? { status } : undefined,
  });
  return response.data;
};

// Get booking details
export const getBooking = async (id: string): Promise<Booking> => {
  const response = await apiClient.get<Booking>(`/bookings/${id}`);
  return response.data;
};

// Cancel booking
export const cancelBooking = async (id: string) => {
  await apiClient.patch(`/bookings/${id}`, { status: 'cancelled_by_client' });
};

// Create review
export const createReview = async (data: {
  booking_id: string;
  salon_id: string;
  master_id?: string;
  rating: number;
  review_text?: string;
  review_photos?: string[];
}) => {
  const response = await apiClient.post('/bookings/reviews', data);
  return response.data;
};

// Get reviews
export const getReviews = async (params: {
  salon_id?: string;
  master_id?: string;
  rating?: number;
  sort?: 'recent' | 'highest_rated' | 'lowest_rated';
  page?: number;
  per_page?: number;
}) => {
  const response = await apiClient.get('/bookings/reviews', { params });
  return response.data;
};
