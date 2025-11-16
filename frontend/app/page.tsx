'use client';

import { useEffect, useState } from 'react';
import { getCategories, Category } from '@/lib/api/categories';
import Link from 'next/link';
import { Search, MapPin, Star, TrendingUp } from 'lucide-react';
import toast from 'react-hot-toast';

export default function Home() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const data = await getCategories();
      setCategories(data);
    } catch (error) {
      toast.error('Failed to load categories');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="text-center">
            <h1 className="text-5xl font-bold mb-6">
              Find Your Perfect Beauty Salon
            </h1>
            <p className="text-xl mb-8 text-blue-100">
              Book appointments at the best salons in your city
            </p>

            <div className="max-w-2xl mx-auto bg-white rounded-lg p-2 flex items-center">
              <Search className="text-gray-400 ml-3" />
              <input
                type="text"
                placeholder="Search for services or salons..."
                className="flex-1 px-4 py-3 text-gray-900 outline-none"
              />
              <button className="bg-blue-600 text-white px-8 py-3 rounded-md hover:bg-blue-700 font-medium">
                Search
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Categories Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Browse by Category
          </h2>
          <p className="text-gray-600">
            Choose a category to find salons near you
          </p>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-white rounded-xl p-6 shadow-sm animate-pulse">
                <div className="w-16 h-16 bg-gray-200 rounded-full mb-4"></div>
                <div className="h-6 bg-gray-200 rounded mb-2"></div>
                <div className="h-4 bg-gray-200 rounded w-2/3"></div>
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {categories.map((category) => (
              <Link
                key={category.id}
                href={`/catalog?category=${category.id}`}
                className="bg-white rounded-xl p-6 shadow-sm hover:shadow-lg transition-all duration-300 border-2 border-transparent hover:border-blue-500 group"
              >
                <div className="flex flex-col items-center text-center">
                  <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                    <span className="text-2xl">
                      {category.icon_url || '💇'}
                    </span>
                  </div>

                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {category.name_en}
                  </h3>

                  <p className="text-sm text-gray-600 mb-3">
                    {category.description_en?.substring(0, 60)}...
                  </p>

                  <div className="flex items-center text-sm text-blue-600 font-medium">
                    <span>{category.salon_count} salons</span>
                    <TrendingUp size={16} className="ml-1" />
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Features Section */}
      <div className="bg-gray-50 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <MapPin className="text-blue-600" size={32} />
              </div>
              <h3 className="text-xl font-semibold mb-2">Find Nearby</h3>
              <p className="text-gray-600">
                Discover salons in your neighborhood
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Star className="text-purple-600" size={32} />
              </div>
              <h3 className="text-xl font-semibold mb-2">Top Rated</h3>
              <p className="text-gray-600">
                Book with highly-rated professionals
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold mb-2">Easy Booking</h3>
              <p className="text-gray-600">
                Book appointments in just a few clicks
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
