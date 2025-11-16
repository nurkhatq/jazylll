'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { getSalonBySlug } from '@/lib/api/salons';
import { getAvailableSlots, createBooking } from '@/lib/api/bookings';
import { Calendar, Clock, ArrowLeft, Check } from 'lucide-react';
import { useAuthStore } from '@/lib/store/useAuthStore';
import toast from 'react-hot-toast';

interface TimeSlot {
  slot_time: string;
  slot_end: string;
}

export default function BookingPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();

  const branchId = searchParams.get('branch');
  const serviceId = searchParams.get('service');
  const masterId = searchParams.get('master');

  const [salon, setSalon] = useState<any>(null);
  const [selectedDate, setSelectedDate] = useState<string>('');
  const [availableSlots, setAvailableSlots] = useState<TimeSlot[]>([]);
  const [selectedSlot, setSelectedSlot] = useState<TimeSlot | null>(null);
  const [notes, setNotes] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [bookingStep, setBookingStep] = useState<'date' | 'time' | 'confirm'>('date');

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth/login');
      return;
    }

    if (!branchId || !serviceId) {
      toast.error('Missing booking information');
      router.back();
      return;
    }

    loadSalonData();
  }, []);

  useEffect(() => {
    if (selectedDate && masterId) {
      loadAvailableSlots();
    }
  }, [selectedDate, masterId]);

  const loadSalonData = async () => {
    try {
      const salonData = await getSalonBySlug(params.slug as string);
      setSalon(salonData);
    } catch (error: any) {
      toast.error('Failed to load salon information');
      router.back();
    }
  };

  const loadAvailableSlots = async () => {
    if (!masterId || !selectedDate || !serviceId || !branchId) {
      return;
    }

    try {
      setLoading(true);
      const slots = await getAvailableSlots({
        master_id: masterId,
        date: selectedDate,
        service_id: serviceId,
        branch_id: branchId,
      });
      setAvailableSlots(slots);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to load available slots');
      setAvailableSlots([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDateSelect = (date: string) => {
    setSelectedDate(date);
    setSelectedSlot(null);
    setBookingStep('time');
  };

  const handleSlotSelect = (slot: TimeSlot) => {
    setSelectedSlot(slot);
    setBookingStep('confirm');
  };

  const handleConfirmBooking = async () => {
    if (!selectedDate || !selectedSlot || !serviceId || !branchId) {
      toast.error('Please complete all booking steps');
      return;
    }

    try {
      setLoading(true);

      const bookingData: any = {
        service_id: serviceId,
        branch_id: branchId,
        booking_date: selectedDate,
        start_time: selectedSlot.slot_time,
      };

      if (masterId) {
        bookingData.master_id = masterId;
      }

      if (notes.trim()) {
        bookingData.notes_from_client = notes.trim();
      }

      await createBooking(bookingData);

      toast.success('Booking created successfully!');
      router.push('/profile/bookings');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to create booking');
    } finally {
      setLoading(false);
    }
  };

  // Generate next 14 days for date selection
  const getNextDays = (count: number) => {
    const days = [];
    const today = new Date();

    for (let i = 0; i < count; i++) {
      const date = new Date(today);
      date.setDate(today.getDate() + i);
      days.push(date);
    }

    return days;
  };

  const formatDate = (date: Date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const formatDisplayDate = (date: Date) => {
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    });
  };

  if (!salon) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-gray-600">Loading...</div>
      </div>
    );
  }

  const selectedService = salon.services.find((s: any) => s.id === serviceId);
  const selectedBranch = salon.branches.find((b: any) => b.id === branchId);
  const selectedMaster = masterId
    ? salon.masters.find((m: any) => m.id === masterId)
    : null;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft size={20} />
          <span>Back</span>
        </button>

        <h1 className="text-3xl font-bold text-gray-900 mb-2">Book Appointment</h1>
        <p className="text-gray-600">{salon.name}</p>
      </div>

      {/* Booking Summary */}
      <div className="bg-white p-6 rounded-lg shadow mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Booking Details</h2>
        <div className="space-y-2 text-sm">
          {selectedService && (
            <div className="flex justify-between">
              <span className="text-gray-600">Service:</span>
              <span className="font-medium">{selectedService.name_ru}</span>
            </div>
          )}
          {selectedBranch && (
            <div className="flex justify-between">
              <span className="text-gray-600">Location:</span>
              <span className="font-medium">{selectedBranch.branch_name}</span>
            </div>
          )}
          {selectedMaster && (
            <div className="flex justify-between">
              <span className="text-gray-600">Master:</span>
              <span className="font-medium">
                {selectedMaster.first_name} {selectedMaster.last_name}
              </span>
            </div>
          )}
          {selectedService && (
            <>
              <div className="flex justify-between">
                <span className="text-gray-600">Duration:</span>
                <span className="font-medium">{selectedService.duration_minutes} min</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Price:</span>
                <span className="font-medium">{selectedService.price.toLocaleString()} ₸</span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Steps Progress */}
      <div className="flex items-center justify-center mb-8">
        <div className="flex items-center gap-4">
          <div
            className={`flex items-center gap-2 ${
              bookingStep === 'date' ? 'text-blue-600' : 'text-gray-400'
            }`}
          >
            {bookingStep !== 'date' && selectedDate ? (
              <Check className="text-green-600" size={20} />
            ) : (
              <span className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center">
                1
              </span>
            )}
            <span className="font-medium">Date</span>
          </div>

          <div className="w-12 h-0.5 bg-gray-300" />

          <div
            className={`flex items-center gap-2 ${
              bookingStep === 'time' ? 'text-blue-600' : 'text-gray-400'
            }`}
          >
            {bookingStep === 'confirm' && selectedSlot ? (
              <Check className="text-green-600" size={20} />
            ) : (
              <span
                className={`w-8 h-8 rounded-full ${
                  bookingStep === 'time' ? 'bg-blue-600 text-white' : 'bg-gray-300'
                } flex items-center justify-center`}
              >
                2
              </span>
            )}
            <span className="font-medium">Time</span>
          </div>

          <div className="w-12 h-0.5 bg-gray-300" />

          <div
            className={`flex items-center gap-2 ${
              bookingStep === 'confirm' ? 'text-blue-600' : 'text-gray-400'
            }`}
          >
            <span
              className={`w-8 h-8 rounded-full ${
                bookingStep === 'confirm' ? 'bg-blue-600 text-white' : 'bg-gray-300'
              } flex items-center justify-center`}
            >
              3
            </span>
            <span className="font-medium">Confirm</span>
          </div>
        </div>
      </div>

      {/* Date Selection */}
      {bookingStep === 'date' && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Calendar size={24} />
            Select Date
          </h2>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {getNextDays(14).map((date) => {
              const dateStr = formatDate(date);
              const isSelected = selectedDate === dateStr;

              return (
                <button
                  key={dateStr}
                  onClick={() => handleDateSelect(dateStr)}
                  className={`p-4 border-2 rounded-lg transition-colors ${
                    isSelected
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="text-center">
                    <p className="text-sm text-gray-600">{formatDisplayDate(date)}</p>
                  </div>
                </button>
              );
            })}
          </div>

          {!masterId && (
            <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-800">
                No master selected. Please go back and select a master to see available time slots.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Time Selection */}
      {bookingStep === 'time' && selectedDate && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Clock size={24} />
            Select Time
          </h2>

          {loading ? (
            <div className="text-center py-8 text-gray-600">Loading available slots...</div>
          ) : availableSlots.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-600">No available slots for this date</p>
              <button
                onClick={() => setBookingStep('date')}
                className="mt-4 text-blue-600 hover:text-blue-700"
              >
                Choose another date
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-3 md:grid-cols-5 gap-3">
              {availableSlots.map((slot) => {
                const isSelected = selectedSlot?.slot_time === slot.slot_time;

                return (
                  <button
                    key={slot.slot_time}
                    onClick={() => handleSlotSelect(slot)}
                    className={`p-3 border-2 rounded-lg transition-colors ${
                      isSelected
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="text-center">
                      <p className="font-medium">{slot.slot_time.slice(0, 5)}</p>
                    </div>
                  </button>
                );
              })}
            </div>
          )}

          <div className="mt-4 flex gap-2">
            <button
              onClick={() => setBookingStep('date')}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Back to Date
            </button>
          </div>
        </div>
      )}

      {/* Confirmation */}
      {bookingStep === 'confirm' && selectedDate && selectedSlot && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Confirm Booking</h2>

          <div className="space-y-4 mb-6">
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-600 mb-1">Date</p>
                  <p className="font-medium">
                    {new Date(selectedDate).toLocaleDateString('en-US', {
                      weekday: 'long',
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                    })}
                  </p>
                </div>
                <div>
                  <p className="text-gray-600 mb-1">Time</p>
                  <p className="font-medium">
                    {selectedSlot.slot_time.slice(0, 5)} - {selectedSlot.slot_end.slice(0, 5)}
                  </p>
                </div>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Notes (Optional)
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Any special requests or notes for the salon..."
              />
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={() => setBookingStep('time')}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Back
            </button>
            <button
              onClick={handleConfirmBooking}
              disabled={loading}
              className="flex-1 bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating Booking...' : 'Confirm Booking'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
