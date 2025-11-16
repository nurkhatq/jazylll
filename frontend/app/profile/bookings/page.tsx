'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getMyBookings, cancelBooking, createReview } from '@/lib/api/bookings';
import { useAuthStore } from '@/lib/store/useAuthStore';
import { Calendar, Clock, MapPin, User, Star, X } from 'lucide-react';
import toast from 'react-hot-toast';

interface Booking {
  id: string;
  booking_date: string;
  start_time: string;
  end_time: string;
  final_price: number;
  status: string;
  notes_from_client?: string;
  master: {
    id: string;
    first_name: string;
    last_name: string;
    photo_url?: string;
  };
  service: {
    id: string;
    name_ru: string;
  };
  branch: {
    id: string;
    branch_name: string;
    city: string;
    address: string;
  };
  salon: {
    id: string;
    name: string;
    slug: string;
  };
}

export default function BookingsPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [selectedBooking, setSelectedBooking] = useState<Booking | null>(null);
  const [rating, setRating] = useState(5);
  const [reviewText, setReviewText] = useState('');

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth/login');
      return;
    }

    loadBookings();
  }, [filter]);

  const loadBookings = async () => {
    try {
      setLoading(true);
      const statusFilter = filter === 'all' ? undefined : filter;
      const data = await getMyBookings(statusFilter);
      setBookings(data);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to load bookings');
    } finally {
      setLoading(false);
    }
  };

  const handleCancelBooking = async (bookingId: string) => {
    if (!confirm('Are you sure you want to cancel this booking?')) {
      return;
    }

    try {
      await cancelBooking(bookingId);
      toast.success('Booking cancelled successfully');
      loadBookings();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to cancel booking');
    }
  };

  const handleOpenReviewModal = (booking: Booking) => {
    setSelectedBooking(booking);
    setRating(5);
    setReviewText('');
    setShowReviewModal(true);
  };

  const handleSubmitReview = async () => {
    if (!selectedBooking) return;

    try {
      await createReview({
        booking_id: selectedBooking.id,
        salon_id: selectedBooking.salon.id,
        master_id: selectedBooking.master.id,
        rating,
        review_text: reviewText.trim() || undefined,
      });

      toast.success('Review submitted successfully!');
      setShowReviewModal(false);
      loadBookings();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to submit review');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'confirmed':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'completed':
        return 'bg-blue-100 text-blue-800';
      case 'cancelled_by_client':
      case 'cancelled_by_salon':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    return status.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
  };

  const canCancel = (booking: Booking) => {
    return ['pending', 'confirmed'].includes(booking.status);
  };

  const canReview = (booking: Booking) => {
    return booking.status === 'completed';
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-gray-600">Loading bookings...</div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">My Bookings</h1>
        <p className="text-gray-600">View and manage your appointments</p>
      </div>

      {/* Filter Tabs */}
      <div className="mb-6 border-b border-gray-200">
        <nav className="flex gap-4">
          {[
            { value: 'all', label: 'All Bookings' },
            { value: 'pending', label: 'Pending' },
            { value: 'confirmed', label: 'Confirmed' },
            { value: 'completed', label: 'Completed' },
          ].map((tab) => (
            <button
              key={tab.value}
              onClick={() => setFilter(tab.value)}
              className={`px-4 py-2 border-b-2 transition-colors ${
                filter === tab.value
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Bookings List */}
      {bookings.length === 0 ? (
        <div className="text-center py-12">
          <Calendar className="mx-auto text-gray-400 mb-4" size={48} />
          <p className="text-gray-600 mb-4">No bookings found</p>
          <button
            onClick={() => router.push('/catalog')}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
          >
            Browse Salons
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {bookings.map((booking) => (
            <div key={booking.id} className="bg-white p-6 rounded-lg shadow">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-1">
                    {booking.salon.name}
                  </h3>
                  <span
                    className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(
                      booking.status
                    )}`}
                  >
                    {getStatusText(booking.status)}
                  </span>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-gray-900">
                    {booking.final_price.toLocaleString()} ₸
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-gray-700">
                    <Calendar size={18} />
                    <span>
                      {new Date(booking.booking_date).toLocaleDateString('en-US', {
                        weekday: 'long',
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                      })}
                    </span>
                  </div>

                  <div className="flex items-center gap-2 text-gray-700">
                    <Clock size={18} />
                    <span>
                      {booking.start_time.slice(0, 5)} - {booking.end_time.slice(0, 5)}
                    </span>
                  </div>

                  <div className="flex items-center gap-2 text-gray-700">
                    <MapPin size={18} />
                    <span>
                      {booking.branch.branch_name}, {booking.branch.city}
                    </span>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-start gap-2">
                    <User size={18} className="mt-0.5 text-gray-700" />
                    <div>
                      <p className="text-gray-700">
                        {booking.master.first_name} {booking.master.last_name}
                      </p>
                      <p className="text-sm text-gray-600">{booking.service.name_ru}</p>
                    </div>
                  </div>

                  {booking.notes_from_client && (
                    <div className="text-sm">
                      <p className="text-gray-600 font-medium">Notes:</p>
                      <p className="text-gray-700">{booking.notes_from_client}</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-3 pt-4 border-t border-gray-200">
                <button
                  onClick={() => router.push(`/salon/${booking.salon.slug}`)}
                  className="px-4 py-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                >
                  View Salon
                </button>

                {canReview(booking) && (
                  <button
                    onClick={() => handleOpenReviewModal(booking)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Leave Review
                  </button>
                )}

                {canCancel(booking) && (
                  <button
                    onClick={() => handleCancelBooking(booking.id)}
                    className="px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors ml-auto"
                  >
                    Cancel Booking
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Review Modal */}
      {showReviewModal && selectedBooking && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold text-gray-900">Leave a Review</h3>
              <button
                onClick={() => setShowReviewModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={24} />
              </button>
            </div>

            <div className="mb-4">
              <p className="text-gray-700 mb-2">{selectedBooking.salon.name}</p>
              <p className="text-sm text-gray-600">
                {selectedBooking.master.first_name} {selectedBooking.master.last_name} -{' '}
                {selectedBooking.service.name_ru}
              </p>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">Rating</label>
              <div className="flex gap-2">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    onClick={() => setRating(star)}
                    className="focus:outline-none"
                  >
                    <Star
                      size={32}
                      className={
                        star <= rating
                          ? 'text-yellow-400 fill-yellow-400'
                          : 'text-gray-300'
                      }
                    />
                  </button>
                ))}
              </div>
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Review (Optional)
              </label>
              <textarea
                value={reviewText}
                onChange={(e) => setReviewText(e.target.value)}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Share your experience..."
              />
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setShowReviewModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmitReview}
                className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700"
              >
                Submit Review
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
