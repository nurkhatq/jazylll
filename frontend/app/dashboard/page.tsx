'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/useAuthStore';
import { getMySalons } from '@/lib/api/salons';
import { Users, Calendar, Star, BarChart, Building, Plus, Settings, Eye } from 'lucide-react';
import toast from 'react-hot-toast';

interface Salon {
  id: string;
  display_name: string;
  slug: string;
  is_active: boolean;
  rating: number;
  total_reviews: number;
}

export default function DashboardPage() {
  const { user, isAuthenticated } = useAuthStore();
  const router = useRouter();
  const [salons, setSalons] = useState<Salon[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSalon, setSelectedSalon] = useState<string>('');

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth/login');
      return;
    }

    if (user?.role === 'client') {
      router.push('/profile');
      return;
    }

    loadMySalons();
  }, [isAuthenticated, router]);

  const loadMySalons = async () => {
    try {
      setLoading(true);
      const data = await getMySalons();
      setSalons(data);
      if (data.length > 0) {
        setSelectedSalon(data[0].id);
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to load salons');
    } finally {
      setLoading(false);
    }
  };

  if (!isAuthenticated || !user) {
    return null;
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-gray-600">Loading dashboard...</div>
      </div>
    );
  }

  const currentSalon = salons.find((s) => s.id === selectedSalon);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Salon Dashboard</h1>
        <p className="text-gray-600 mt-2">
          Welcome back, {user.first_name || user.email}!
        </p>
      </div>

      {/* Salon Selector or Create New */}
      {salons.length === 0 ? (
        <div className="bg-white p-8 rounded-lg shadow mb-8 text-center">
          <Building className="mx-auto text-gray-400 mb-4" size={48} />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">No Salon Yet</h2>
          <p className="text-gray-600 mb-6">Create your first salon to get started</p>
          <button
            onClick={() => router.push('/dashboard/salons/create')}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 inline-flex items-center gap-2"
          >
            <Plus size={20} />
            <span>Create Salon</span>
          </button>
        </div>
      ) : (
        <>
          {/* Salon Selector */}
          <div className="bg-white p-4 rounded-lg shadow mb-8">
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-4 flex-1">
                <Building className="text-gray-600" size={24} />
                <select
                  value={selectedSalon}
                  onChange={(e) => setSelectedSalon(e.target.value)}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {salons.map((salon) => (
                    <option key={salon.id} value={salon.id}>
                      {salon.display_name}
                    </option>
                  ))}
                </select>
              </div>
              <button
                onClick={() => router.push('/dashboard/salons/create')}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 inline-flex items-center gap-2"
              >
                <Plus size={20} />
                <span>New Salon</span>
              </button>
            </div>
          </div>

          {currentSalon && (
            <>
              {/* Stats Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <div className="bg-white p-6 rounded-lg shadow">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-gray-500 text-sm">Total Bookings</p>
                      <p className="text-2xl font-bold text-gray-900">-</p>
                    </div>
                    <div className="bg-blue-100 p-3 rounded-full">
                      <Calendar className="text-blue-600" size={24} />
                    </div>
                  </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-gray-500 text-sm">Total Clients</p>
                      <p className="text-2xl font-bold text-gray-900">-</p>
                    </div>
                    <div className="bg-purple-100 p-3 rounded-full">
                      <Users className="text-purple-600" size={24} />
                    </div>
                  </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-gray-500 text-sm">Average Rating</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {currentSalon.rating.toFixed(1)}
                      </p>
                    </div>
                    <div className="bg-yellow-100 p-3 rounded-full">
                      <Star className="text-yellow-600" size={24} />
                    </div>
                  </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-gray-500 text-sm">Total Reviews</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {currentSalon.total_reviews}
                      </p>
                    </div>
                    <div className="bg-green-100 p-3 rounded-full">
                      <BarChart className="text-green-600" size={24} />
                    </div>
                  </div>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="bg-white p-6 rounded-lg shadow mb-8">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <button
                    onClick={() => router.push(`/dashboard/salons/${selectedSalon}/edit`)}
                    className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors"
                  >
                    <div className="text-center">
                      <Settings className="mx-auto text-blue-600 mb-2" size={32} />
                      <p className="font-medium">Salon Settings</p>
                    </div>
                  </button>

                  <button
                    onClick={() => router.push(`/dashboard/salons/${selectedSalon}/masters`)}
                    className="p-4 border-2 border-gray-200 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-colors"
                  >
                    <div className="text-center">
                      <Users className="mx-auto text-purple-600 mb-2" size={32} />
                      <p className="font-medium">Manage Masters</p>
                    </div>
                  </button>

                  <button
                    onClick={() => router.push(`/dashboard/salons/${selectedSalon}/services`)}
                    className="p-4 border-2 border-gray-200 rounded-lg hover:border-green-500 hover:bg-green-50 transition-colors"
                  >
                    <div className="text-center">
                      <BarChart className="mx-auto text-green-600 mb-2" size={32} />
                      <p className="font-medium">Services</p>
                    </div>
                  </button>

                  <button
                    onClick={() => router.push(`/salon/${currentSalon.slug}`)}
                    className="p-4 border-2 border-gray-200 rounded-lg hover:border-orange-500 hover:bg-orange-50 transition-colors"
                  >
                    <div className="text-center">
                      <Eye className="mx-auto text-orange-600 mb-2" size={32} />
                      <p className="font-medium">View Public Page</p>
                    </div>
                  </button>
                </div>
              </div>

              {/* Status */}
              <div className="bg-white p-6 rounded-lg shadow">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Salon Status</h2>
                <div className="flex items-center gap-4">
                  <div className={`px-4 py-2 rounded-lg ${currentSalon.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                    {currentSalon.is_active ? 'Active' : 'Inactive'}
                  </div>
                  <p className="text-gray-600">
                    Your salon is {currentSalon.is_active ? 'visible' : 'hidden'} in the catalog
                  </p>
                </div>
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}
