'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { GoogleLogin } from '@react-oauth/google';
import { googleLogin, requestVerificationCode, verifyCode } from '@/lib/api/auth';
import { useAuthStore } from '@/lib/store/useAuthStore';
import { getErrorMessage } from '@/lib/utils/errorHandler';
import toast from 'react-hot-toast';

export default function LoginPage() {
  const router = useRouter();
  const { setAuth } = useAuthStore();
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const [codeSent, setCodeSent] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleGoogleSuccess = async (credentialResponse: any) => {
    try {
      setLoading(true);
      const response = await googleLogin(credentialResponse.credential);

      setAuth(response.user, response.access_token, response.refresh_token);

      toast.success('Login successful!');
      router.push('/dashboard');
    } catch (error: any) {
      toast.error(getErrorMessage(error) || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleRequestCode = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      await requestVerificationCode(phone);
      setCodeSent(true);
      toast.success('Code sent to your phone!');
    } catch (error: any) {
      toast.error(getErrorMessage(error) || 'Failed to send code');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyCode = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      const response = await verifyCode(phone, code);

      setAuth(response.user, response.access_token, response.refresh_token);

      toast.success('Login successful!');
      router.push('/');
    } catch (error: any) {
      toast.error(getErrorMessage(error) || 'Invalid code');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to Jazyl
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Book appointments at the best salons
          </p>
        </div>

        <div className="mt-8 space-y-6">
          {/* Google OAuth for Salon Owners */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Salon Owners & Staff
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              Sign in with your Google account
            </p>

            <div className="flex justify-center">
              <GoogleLogin
                onSuccess={handleGoogleSuccess}
                onError={() => toast.error('Google login failed')}
              />
            </div>
          </div>

          {/* Phone Auth for Clients */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Clients
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              Sign in with your phone number
            </p>

            {!codeSent ? (
              <form onSubmit={handleRequestCode} className="space-y-4">
                <div>
                  <label htmlFor="phone" className="block text-sm font-medium text-gray-700">
                    Phone Number
                  </label>
                  <input
                    id="phone"
                    name="phone"
                    type="tel"
                    required
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="+77012345678"
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                >
                  {loading ? 'Sending...' : 'Send Verification Code'}
                </button>
              </form>
            ) : (
              <form onSubmit={handleVerifyCode} className="space-y-4">
                <div>
                  <label htmlFor="code" className="block text-sm font-medium text-gray-700">
                    Verification Code
                  </label>
                  <input
                    id="code"
                    name="code"
                    type="text"
                    required
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    placeholder="123456"
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                >
                  {loading ? 'Verifying...' : 'Verify & Login'}
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setCodeSent(false);
                    setCode('');
                  }}
                  className="w-full text-sm text-blue-600 hover:text-blue-500"
                >
                  Use different number
                </button>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
