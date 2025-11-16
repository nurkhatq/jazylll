'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/useAuthStore';
import { User, Mail, Phone, Calendar, LogOut, Settings } from 'lucide-react';
import toast from 'react-hot-toast';

export default function ProfilePage() {
  const router = useRouter();
  const { user, isAuthenticated, clearAuth } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth/login');
    }
  }, [isAuthenticated]);

  const handleLogout = () => {
    clearAuth();
    toast.success('Logged out successfully');
    router.push('/');
  };

  if (!isAuthenticated || !user) {
    return null;
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">My Profile</h1>
        <p className="text-gray-600">Manage your account information</p>
      </div>

      {/* Profile Card */}
      <div className="bg-white p-6 rounded-lg shadow mb-6">
        <div className="flex items-center gap-6 mb-6">
          <div className="w-24 h-24 rounded-full bg-blue-100 flex items-center justify-center">
            <User size={48} className="text-blue-600" />
          </div>
          <div>
            <h2 className="text-2xl font-semibold text-gray-900">
              {user.first_name || 'User'} {user.last_name || ''}
            </h2>
            <p className="text-gray-600 capitalize">{user.role.replace(/_/g, ' ')}</p>
          </div>
        </div>

        <div className="space-y-4">
          {user.email && (
            <div className="flex items-center gap-3 text-gray-700">
              <Mail size={20} />
              <span>{user.email}</span>
            </div>
          )}

          {user.phone && (
            <div className="flex items-center gap-3 text-gray-700">
              <Phone size={20} />
              <span>{user.phone}</span>
            </div>
          )}

          <div className="flex items-center gap-3 text-gray-700">
            <Settings size={20} />
            <span>ID: {user.id}</span>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white p-6 rounded-lg shadow mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <button
            onClick={() => router.push('/profile/bookings')}
            className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors text-left"
          >
            <div className="flex items-center gap-3">
              <Calendar className="text-blue-600" size={24} />
              <div>
                <p className="font-medium text-gray-900">My Bookings</p>
                <p className="text-sm text-gray-600">View and manage appointments</p>
              </div>
            </div>
          </button>

          {(user.role === 'salon_owner' || user.role === 'salon_manager') && (
            <button
              onClick={() => router.push('/dashboard')}
              className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors text-left"
            >
              <div className="flex items-center gap-3">
                <Settings className="text-blue-600" size={24} />
                <div>
                  <p className="font-medium text-gray-900">Salon Dashboard</p>
                  <p className="text-sm text-gray-600">Manage your salon</p>
                </div>
              </div>
            </button>
          )}
        </div>
      </div>

      {/* Account Settings */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Account Settings</h3>

        <button
          onClick={handleLogout}
          className="flex items-center gap-2 text-red-600 hover:text-red-700"
        >
          <LogOut size={20} />
          <span>Logout</span>
        </button>
      </div>
    </div>
  );
}
