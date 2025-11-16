'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { getSalonBySlug } from '@/lib/api/salons';
import { getReviews } from '@/lib/api/bookings';
import { Star, MapPin, Clock, Phone, Mail, Calendar } from 'lucide-react';
import { useAuthStore } from '@/lib/store/useAuthStore';
import toast from 'react-hot-toast';

interface Master {
  id: string;
  first_name: string;
  last_name: string;
  specialization?: string;
  photo_url?: string;
  rating?: number;
}

interface Service {
  id: string;
  name_ru: string;
  name_kk: string;
  name_en: string;
  description_ru?: string;
  price: number;
  duration_minutes: number;
}

interface Branch {
  id: string;
  branch_name: string;
  city: string;
  address: string;
  phone?: string;
  email?: string;
  working_hours?: any;
}

interface Salon {
  id: string;
  name: string;
  slug: string;
  description_ru?: string;
  logo_url?: string;
  cover_photo_url?: string;
  rating?: number;
  review_count: number;
  branches: Branch[];
  services: Service[];
  masters: Master[];
}

interface Review {
  id: string;
  rating: number;
  review_text?: string;
  review_photos?: string[];
  created_at: string;
  client: {
    first_name?: string;
    last_name?: string;
  };
  master?: {
    first_name: string;
    last_name: string;
  };
  salon_response?: string;
}

export default function SalonDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [salon, setSalon] = useState<Salon | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedBranch, setSelectedBranch] = useState<string>('');
  const [selectedService, setSelectedService] = useState<string>('');
  const [selectedMaster, setSelectedMaster] = useState<string>('');

  useEffect(() => {
    if (params.slug) {
      loadSalonData();
    }
  }, [params.slug]);

  const loadSalonData = async () => {
    try {
      setLoading(true);
      const salonData = await getSalonBySlug(params.slug as string);
      setSalon(salonData);

      // Set default selections
      if (salonData.branches.length > 0) {
        setSelectedBranch(salonData.branches[0].id);
      }

      // Load reviews
      const reviewsData = await getReviews({ salon_id: salonData.id, page: 1, per_page: 10 });
      setReviews(reviewsData.items || []);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to load salon');
    } finally {
      setLoading(false);
    }
  };

  const handleBookNow = () => {
    if (!isAuthenticated) {
      toast.error('Please login to book an appointment');
      router.push('/auth/login');
      return;
    }

    if (!selectedBranch || !selectedService) {
      toast.error('Please select a branch and service');
      return;
    }

    router.push(
      `/salon/${params.slug}/book?branch=${selectedBranch}&service=${selectedService}&master=${selectedMaster}`
    );
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-gray-600">Loading...</div>
      </div>
    );
  }

  if (!salon) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-gray-600">Salon not found</div>
      </div>
    );
  }

  const selectedServiceData = salon.services.find((s) => s.id === selectedService);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Cover Photo */}
      {salon.cover_photo_url && (
        <div className="relative h-64 md:h-96 rounded-lg overflow-hidden mb-8">
          <img
            src={salon.cover_photo_url}
            alt={salon.name}
            className="w-full h-full object-cover"
          />
        </div>
      )}

      {/* Salon Header */}
      <div className="flex items-start gap-6 mb-8">
        {salon.logo_url && (
          <img
            src={salon.logo_url}
            alt={salon.name}
            className="w-24 h-24 rounded-lg object-cover"
          />
        )}
        <div className="flex-1">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">{salon.name}</h1>
          {salon.rating && (
            <div className="flex items-center gap-2 mb-2">
              <div className="flex items-center">
                <Star className="text-yellow-400 fill-yellow-400" size={20} />
                <span className="ml-1 font-semibold">{salon.rating.toFixed(1)}</span>
              </div>
              <span className="text-gray-600">({salon.review_count} reviews)</span>
            </div>
          )}
          {salon.description_ru && (
            <p className="text-gray-600 mt-2">{salon.description_ru}</p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-8">
          {/* Branches */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Locations</h2>
            <div className="space-y-4">
              {salon.branches.map((branch) => (
                <div
                  key={branch.id}
                  className={`p-4 border-2 rounded-lg cursor-pointer transition-colors ${
                    selectedBranch === branch.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => setSelectedBranch(branch.id)}
                >
                  <h3 className="font-medium text-gray-900 mb-2">{branch.branch_name}</h3>
                  <div className="space-y-1 text-sm text-gray-600">
                    <div className="flex items-center gap-2">
                      <MapPin size={16} />
                      <span>
                        {branch.city}, {branch.address}
                      </span>
                    </div>
                    {branch.phone && (
                      <div className="flex items-center gap-2">
                        <Phone size={16} />
                        <span>{branch.phone}</span>
                      </div>
                    )}
                    {branch.email && (
                      <div className="flex items-center gap-2">
                        <Mail size={16} />
                        <span>{branch.email}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Services */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Services</h2>
            <div className="space-y-3">
              {salon.services.map((service) => (
                <div
                  key={service.id}
                  className={`p-4 border-2 rounded-lg cursor-pointer transition-colors ${
                    selectedService === service.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => setSelectedService(service.id)}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900">{service.name_ru}</h3>
                      {service.description_ru && (
                        <p className="text-sm text-gray-600 mt-1">{service.description_ru}</p>
                      )}
                      <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
                        <div className="flex items-center gap-1">
                          <Clock size={16} />
                          <span>{service.duration_minutes} min</span>
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-semibold text-gray-900">
                        {service.price.toLocaleString()} ₸
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Masters */}
          {salon.masters.length > 0 && (
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Our Masters</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {salon.masters.map((master) => (
                  <div
                    key={master.id}
                    className={`p-4 border-2 rounded-lg cursor-pointer transition-colors ${
                      selectedMaster === master.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() =>
                      setSelectedMaster(selectedMaster === master.id ? '' : master.id)
                    }
                  >
                    <div className="flex items-center gap-3">
                      {master.photo_url ? (
                        <img
                          src={master.photo_url}
                          alt={`${master.first_name} ${master.last_name}`}
                          className="w-16 h-16 rounded-full object-cover"
                        />
                      ) : (
                        <div className="w-16 h-16 rounded-full bg-gray-200 flex items-center justify-center">
                          <span className="text-gray-600 font-medium">
                            {master.first_name[0]}
                            {master.last_name[0]}
                          </span>
                        </div>
                      )}
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900">
                          {master.first_name} {master.last_name}
                        </h3>
                        {master.specialization && (
                          <p className="text-sm text-gray-600">{master.specialization}</p>
                        )}
                        {master.rating && (
                          <div className="flex items-center gap-1 mt-1">
                            <Star className="text-yellow-400 fill-yellow-400" size={14} />
                            <span className="text-sm font-medium">{master.rating.toFixed(1)}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <p className="text-sm text-gray-500 mt-3">
                {selectedMaster ? 'Master selected' : 'Optional: Select a preferred master'}
              </p>
            </div>
          )}

          {/* Reviews */}
          {reviews.length > 0 && (
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Reviews</h2>
              <div className="space-y-4">
                {reviews.map((review) => (
                  <div key={review.id} className="border-b border-gray-200 pb-4 last:border-0">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <p className="font-medium text-gray-900">
                          {review.client.first_name || 'Anonymous'}{' '}
                          {review.client.last_name || ''}
                        </p>
                        {review.master && (
                          <p className="text-sm text-gray-600">
                            Master: {review.master.first_name} {review.master.last_name}
                          </p>
                        )}
                      </div>
                      <div className="flex items-center gap-1">
                        <Star className="text-yellow-400 fill-yellow-400" size={16} />
                        <span className="font-medium">{review.rating}</span>
                      </div>
                    </div>
                    {review.review_text && (
                      <p className="text-gray-700 mb-2">{review.review_text}</p>
                    )}
                    {review.review_photos && review.review_photos.length > 0 && (
                      <div className="flex gap-2 mb-2">
                        {review.review_photos.map((photo, index) => (
                          <img
                            key={index}
                            src={photo}
                            alt={`Review photo ${index + 1}`}
                            className="w-20 h-20 object-cover rounded"
                          />
                        ))}
                      </div>
                    )}
                    <p className="text-xs text-gray-500">
                      {new Date(review.created_at).toLocaleDateString()}
                    </p>
                    {review.salon_response && (
                      <div className="mt-2 pl-4 border-l-2 border-gray-300">
                        <p className="text-sm font-medium text-gray-900">Salon Response:</p>
                        <p className="text-sm text-gray-700">{review.salon_response}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Booking Sidebar */}
        <div className="lg:col-span-1">
          <div className="bg-white p-6 rounded-lg shadow sticky top-4">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Book Appointment</h2>

            <div className="space-y-4">
              {!selectedBranch && (
                <p className="text-sm text-gray-600">Please select a location</p>
              )}

              {!selectedService && selectedBranch && (
                <p className="text-sm text-gray-600">Please select a service</p>
              )}

              {selectedService && selectedServiceData && (
                <div className="border border-gray-200 rounded-lg p-4">
                  <p className="text-sm text-gray-600 mb-1">Selected Service</p>
                  <p className="font-medium text-gray-900">{selectedServiceData.name_ru}</p>
                  <div className="flex justify-between items-center mt-2">
                    <span className="text-sm text-gray-600">
                      {selectedServiceData.duration_minutes} min
                    </span>
                    <span className="font-semibold text-gray-900">
                      {selectedServiceData.price.toLocaleString()} ₸
                    </span>
                  </div>
                </div>
              )}

              <button
                onClick={handleBookNow}
                disabled={!selectedBranch || !selectedService}
                className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
              >
                <Calendar size={20} />
                <span>Book Now</span>
              </button>

              {!isAuthenticated && (
                <p className="text-xs text-gray-500 text-center">
                  You need to login to book an appointment
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
