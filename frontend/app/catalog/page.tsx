'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { getSalons, Salon } from '@/lib/api/salons';
import { getCities, City } from '@/lib/api/categories';
import Link from 'next/link';
import { Star, MapPin, Filter } from 'lucide-react';
import toast from 'react-hot-toast';

export default function CatalogPage() {
  const searchParams = useSearchParams();
  const categoryId = searchParams.get('category') || '';

  const [salons, setSalons] = useState<Salon[]>([]);
  const [cities, setCities] = useState<City[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCity, setSelectedCity] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    if (categoryId) {
      loadSalons();
      loadCities();
    }
  }, [categoryId, selectedCity, search, page]);

  const loadSalons = async () => {
    try {
      setLoading(true);
      const response = await getSalons({
        category_id: categoryId,
        city: selectedCity || undefined,
        search: search || undefined,
        page,
        per_page: 12,
      });

      setSalons(response.items);
      setTotalPages(response.total_pages);
    } catch (error) {
      toast.error('Failed to load salons');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const loadCities = async () => {
    try {
      const data = await getCities(categoryId);
      setCities(data);
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Filters */}
      <div className="bg-white p-6 rounded-lg shadow mb-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search
            </label>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search salons..."
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              City
            </label>
            <select
              value={selectedCity}
              onChange={(e) => setSelectedCity(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Cities</option>
              {cities.map((city) => (
                <option key={city.city} value={city.city}>
                  {city.city} ({city.salon_count})
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={loadSalons}
              className="w-full px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center justify-center"
            >
              <Filter size={20} className="mr-2" />
              Apply Filters
            </button>
          </div>
        </div>
      </div>

      {/* Results */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="bg-white rounded-lg shadow animate-pulse">
              <div className="h-48 bg-gray-200"></div>
              <div className="p-4">
                <div className="h-6 bg-gray-200 rounded mb-2"></div>
                <div className="h-4 bg-gray-200 rounded w-2/3"></div>
              </div>
            </div>
          ))}
        </div>
      ) : salons.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg">No salons found</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {salons.map((salon) => (
              <Link
                key={salon.id}
                href={`/salon/${salon.slug}`}
                className="bg-white rounded-lg shadow hover:shadow-xl transition-shadow overflow-hidden"
              >
                <div className="relative h-48 bg-gradient-to-r from-blue-400 to-purple-400">
                  {salon.cover_image_url ? (
                    <img
                      src={salon.cover_image_url}
                      alt={salon.display_name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="flex items-center justify-center h-full">
                      <span className="text-6xl">💇</span>
                    </div>
                  )}

                  {salon.is_promoted && (
                    <div className="absolute top-2 right-2 bg-yellow-400 text-yellow-900 px-2 py-1 rounded text-xs font-semibold">
                      Promoted
                    </div>
                  )}
                </div>

                <div className="p-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {salon.display_name}
                  </h3>

                  <div className="flex items-center text-sm text-gray-600 mb-2">
                    <Star className="text-yellow-400 fill-current" size={16} />
                    <span className="ml-1 font-medium">{salon.rating.toFixed(1)}</span>
                    <span className="mx-1">•</span>
                    <span>{salon.total_reviews} reviews</span>
                  </div>

                  {salon.city && (
                    <div className="flex items-center text-sm text-gray-600">
                      <MapPin size={16} />
                      <span className="ml-1">{salon.city}</span>
                    </div>
                  )}
                </div>
              </Link>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center mt-8 space-x-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 bg-white border border-gray-300 rounded-md disabled:opacity-50"
              >
                Previous
              </button>

              <span className="px-4 py-2 bg-white border border-gray-300 rounded-md">
                Page {page} of {totalPages}
              </span>

              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-4 py-2 bg-white border border-gray-300 rounded-md disabled:opacity-50"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
