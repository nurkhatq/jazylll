'use client';

import Link from 'next/link';
import { useAuthStore } from '@/lib/store/useAuthStore';
import { useRouter } from 'next/navigation';
import { User, LogOut, LayoutDashboard, Menu, X } from 'lucide-react';
import { useState } from 'react';

export default function Navbar() {
  const { user, isAuthenticated, clearAuth } = useAuthStore();
  const router = useRouter();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    clearAuth();
    router.push('/');
  };

  return (
    <nav className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link href="/" className="flex items-center">
              <span className="text-2xl font-bold text-blue-600">Jazyl</span>
            </Link>

            <div className="hidden md:ml-10 md:flex md:space-x-8">
              <Link
                href="/"
                className="text-gray-900 hover:text-blue-600 px-3 py-2 text-sm font-medium"
              >
                Home
              </Link>
              <Link
                href="/catalog"
                className="text-gray-900 hover:text-blue-600 px-3 py-2 text-sm font-medium"
              >
                Browse Salons
              </Link>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {isAuthenticated && user ? (
              <div className="hidden md:flex items-center space-x-4">
                <span className="text-sm text-gray-700">
                  {user.first_name || user.email || user.phone}
                </span>

                {user.role !== 'client' && (
                  <Link
                    href="/dashboard"
                    className="flex items-center space-x-1 text-gray-700 hover:text-blue-600"
                  >
                    <LayoutDashboard size={20} />
                    <span className="text-sm">Dashboard</span>
                  </Link>
                )}

                <Link
                  href="/profile"
                  className="flex items-center space-x-1 text-gray-700 hover:text-blue-600"
                >
                  <User size={20} />
                  <span className="text-sm">Profile</span>
                </Link>

                <button
                  onClick={handleLogout}
                  className="flex items-center space-x-1 text-gray-700 hover:text-red-600"
                >
                  <LogOut size={20} />
                  <span className="text-sm">Logout</span>
                </button>
              </div>
            ) : (
              <div className="hidden md:flex space-x-4">
                <Link
                  href="/auth/login"
                  className="bg-blue-600 text-white hover:bg-blue-700 px-4 py-2 rounded-lg text-sm font-medium"
                >
                  Get Started
                </Link>
              </div>
            )}

            {/* Mobile menu button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 rounded-md text-gray-700 hover:bg-gray-100"
            >
              {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className="md:hidden">
          <div className="px-2 pt-2 pb-3 space-y-1">
            <Link
              href="/"
              className="block px-3 py-2 text-gray-900 hover:bg-gray-100 rounded-md"
            >
              Home
            </Link>
            <Link
              href="/catalog"
              className="block px-3 py-2 text-gray-900 hover:bg-gray-100 rounded-md"
            >
              Browse Salons
            </Link>

            {isAuthenticated && user ? (
              <>
                {user.role !== 'client' && (
                  <Link
                    href="/dashboard"
                    className="block px-3 py-2 text-gray-900 hover:bg-gray-100 rounded-md"
                  >
                    Dashboard
                  </Link>
                )}
                <Link
                  href="/profile"
                  className="block px-3 py-2 text-gray-900 hover:bg-gray-100 rounded-md"
                >
                  Profile
                </Link>
                <button
                  onClick={handleLogout}
                  className="block w-full text-left px-3 py-2 text-red-600 hover:bg-gray-100 rounded-md"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link
                  href="/auth/login"
                  className="block px-3 py-2 bg-blue-600 text-white text-center rounded-md"
                >
                  Get Started
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
