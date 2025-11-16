'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { getMySalon, updateSalon, uploadLogo, uploadCover, createBranch, updateBranch, deleteBranch } from '@/lib/api/salons';
import { ArrowLeft, Save, Upload, Plus, Edit, Trash, MapPin, ExternalLink, Sparkles, Camera, Building2 } from 'lucide-react';
import toast from 'react-hot-toast';

interface Branch {
  id: string;
  branch_name: string;
  city: string;
  address: string;
  phone?: string;
  email?: string;
  working_hours?: any;
  is_active: boolean;
}

interface Salon {
  id: string;
  business_name: string;
  display_name: string;
  slug: string;
  description_ru?: string;
  description_kk?: string;
  description_en?: string;
  email?: string;
  phone?: string;
  website_url?: string;
  logo_url?: string;
  cover_image_url?: string;
  is_active: boolean;
  branches: Branch[];
}

export default function EditSalonPage() {
  const params = useParams();
  const router = useRouter();
  const [salon, setSalon] = useState<Salon | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [formData, setFormData] = useState({
    business_name: '',
    display_name: '',
    description_ru: '',
    description_kk: '',
    description_en: '',
    email: '',
    phone: '',
    website_url: '',
  });

  const [showBranchModal, setShowBranchModal] = useState(false);
  const [editingBranch, setEditingBranch] = useState<Branch | null>(null);
  const [branchForm, setBranchForm] = useState({
    branch_name: '',
    city: '',
    address: '',
    phone: '',
    email: '',
  });

  useEffect(() => {
    loadSalon();
  }, [params.id]);

  const loadSalon = async () => {
    try {
      setLoading(true);
      const data = await getMySalon(params.id as string);
      setSalon(data);
      setFormData({
        business_name: data.business_name || '',
        display_name: data.display_name || '',
        description_ru: data.description_ru || '',
        description_kk: data.description_kk || '',
        description_en: data.description_en || '',
        email: data.email || '',
        phone: data.phone || '',
        website_url: data.website_url || '',
      });
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to load salon');
      router.push('/dashboard');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      setSaving(true);
      await updateSalon(params.id as string, formData);
      toast.success('Salon updated successfully!');
      loadSalon();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to update salon');
    } finally {
      setSaving(false);
    }
  };

  const handleLogoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
      toast.error('File size must be less than 5MB');
      return;
    }

    const loadingToast = toast.loading('Uploading logo...');

    try {
      await uploadLogo(params.id as string, file);
      toast.success('Logo uploaded successfully!', { id: loadingToast });
      loadSalon();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to upload logo', { id: loadingToast });
    }
  };

  const handleCoverUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
      toast.error('File size must be less than 5MB');
      return;
    }

    const loadingToast = toast.loading('Uploading cover photo...');

    try {
      await uploadCover(params.id as string, file);
      toast.success('Cover photo uploaded successfully!', { id: loadingToast });
      loadSalon();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to upload cover photo', { id: loadingToast });
    }
  };

  const handleOpenBranchModal = (branch?: Branch) => {
    if (branch) {
      setEditingBranch(branch);
      setBranchForm({
        branch_name: branch.branch_name,
        city: branch.city,
        address: branch.address,
        phone: branch.phone || '',
        email: branch.email || '',
      });
    } else {
      setEditingBranch(null);
      setBranchForm({
        branch_name: '',
        city: '',
        address: '',
        phone: '',
        email: '',
      });
    }
    setShowBranchModal(true);
  };

  const handleBranchSubmit = async () => {
    if (!branchForm.branch_name || !branchForm.city || !branchForm.address) {
      toast.error('Please fill in all required fields');
      return;
    }

    const loadingToast = toast.loading(editingBranch ? 'Updating branch...' : 'Creating branch...');

    try {
      if (editingBranch) {
        await updateBranch(params.id as string, editingBranch.id, branchForm);
        toast.success('Branch updated successfully!', { id: loadingToast });
      } else {
        await createBranch(params.id as string, branchForm);
        toast.success('Branch created successfully!', { id: loadingToast });
      }
      setShowBranchModal(false);
      loadSalon();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save branch', { id: loadingToast });
    }
  };

  const handleDeleteBranch = async (branchId: string) => {
    if (!confirm('Are you sure you want to delete this branch?')) return;

    const loadingToast = toast.loading('Deleting branch...');

    try {
      await deleteBranch(params.id as string, branchId);
      toast.success('Branch deleted successfully!', { id: loadingToast });
      loadSalon();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to delete branch', { id: loadingToast });
    }
  };

  if (loading || !salon) {
    return (
      <div className="flex justify-center items-center min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 font-medium">Loading salon...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <button
            onClick={() => router.push('/dashboard')}
            className="flex items-center gap-2 text-gray-600 hover:text-blue-600 mb-4 transition-colors duration-200 group"
          >
            <ArrowLeft size={20} className="group-hover:-translate-x-1 transition-transform duration-200" />
            <span className="font-medium">Back to Dashboard</span>
          </button>

          <div className="flex items-center gap-3 mb-2">
            <Sparkles className="text-blue-600" size={32} />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              {salon.display_name}
            </h1>
          </div>
          <p className="text-gray-600 text-lg">Manage your salon settings and information</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Basic Information */}
            <form onSubmit={handleSubmit} className="bg-white p-8 rounded-2xl shadow-lg border border-gray-100 hover:shadow-xl transition-shadow duration-300">
              <div className="flex items-center gap-2 mb-6">
                <Building2 className="text-blue-600" size={24} />
                <h2 className="text-2xl font-bold text-gray-900">Basic Information</h2>
              </div>

              <div className="space-y-5">
                <div className="group">
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Business Name
                  </label>
                  <input
                    type="text"
                    name="business_name"
                    value={formData.business_name}
                    onChange={handleChange}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all duration-200 outline-none"
                    placeholder="Enter business name"
                  />
                </div>

                <div className="group">
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Display Name
                  </label>
                  <input
                    type="text"
                    name="display_name"
                    value={formData.display_name}
                    onChange={handleChange}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all duration-200 outline-none"
                    placeholder="Enter display name"
                  />
                </div>

                <div className="group">
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Description (Russian)
                  </label>
                  <textarea
                    name="description_ru"
                    value={formData.description_ru}
                    onChange={handleChange}
                    rows={4}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all duration-200 outline-none resize-none"
                    placeholder="Describe your salon..."
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div className="group">
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Email
                    </label>
                    <input
                      type="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all duration-200 outline-none"
                      placeholder="salon@example.com"
                    />
                  </div>

                  <div className="group">
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Phone
                    </label>
                    <input
                      type="tel"
                      name="phone"
                      value={formData.phone}
                      onChange={handleChange}
                      className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all duration-200 outline-none"
                      placeholder="+7 (XXX) XXX-XX-XX"
                    />
                  </div>
                </div>

                <div className="group">
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Website URL
                  </label>
                  <input
                    type="url"
                    name="website_url"
                    value={formData.website_url}
                    onChange={handleChange}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all duration-200 outline-none"
                    placeholder="https://yourwebsite.com"
                  />
                </div>

                <button
                  type="submit"
                  disabled={saving}
                  className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-4 rounded-xl hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center justify-center gap-3 font-semibold shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98]"
                >
                  <Save size={20} />
                  <span>{saving ? 'Saving...' : 'Save Changes'}</span>
                </button>
              </div>
            </form>

            {/* Branches */}
            <div className="bg-white p-8 rounded-2xl shadow-lg border border-gray-100 hover:shadow-xl transition-shadow duration-300">
              <div className="flex justify-between items-center mb-6">
                <div className="flex items-center gap-2">
                  <MapPin className="text-blue-600" size={24} />
                  <h2 className="text-2xl font-bold text-gray-900">Branches</h2>
                </div>
                <button
                  onClick={() => handleOpenBranchModal()}
                  className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-5 py-3 rounded-xl hover:from-blue-700 hover:to-purple-700 inline-flex items-center gap-2 font-semibold shadow-md hover:shadow-lg transition-all duration-200 transform hover:scale-105"
                >
                  <Plus size={18} />
                  <span>Add Branch</span>
                </button>
              </div>

              {!salon.branches || salon.branches.length === 0 ? (
                <div className="text-center py-12 bg-gray-50 rounded-xl border-2 border-dashed border-gray-300">
                  <MapPin className="mx-auto text-gray-400 mb-3" size={48} />
                  <p className="text-gray-500 text-lg">No branches yet</p>
                  <p className="text-gray-400 text-sm mt-1">Add your first branch to get started</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {salon.branches.map((branch) => (
                    <div key={branch.id} className="border-2 border-gray-200 rounded-xl p-5 hover:border-blue-300 hover:shadow-md transition-all duration-200 bg-gradient-to-r from-white to-blue-50">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h3 className="font-bold text-gray-900 text-lg mb-2">{branch.branch_name}</h3>
                          <div className="space-y-2 text-sm text-gray-600">
                            <div className="flex items-center gap-2">
                              <MapPin size={16} className="text-blue-600" />
                              <span>{branch.city}, {branch.address}</span>
                            </div>
                            {branch.phone && (
                              <p className="flex items-center gap-2">
                                <span className="font-medium">Phone:</span> {branch.phone}
                              </p>
                            )}
                            {branch.email && (
                              <p className="flex items-center gap-2">
                                <span className="font-medium">Email:</span> {branch.email}
                              </p>
                            )}
                          </div>
                          <span className={`inline-block mt-3 px-3 py-1 text-xs font-semibold rounded-full ${branch.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                            {branch.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleOpenBranchModal(branch)}
                            className="p-3 text-blue-600 hover:bg-blue-100 rounded-xl transition-colors duration-200"
                            title="Edit branch"
                          >
                            <Edit size={18} />
                          </button>
                          <button
                            onClick={() => handleDeleteBranch(branch.id)}
                            className="p-3 text-red-600 hover:bg-red-100 rounded-xl transition-colors duration-200"
                            title="Delete branch"
                          >
                            <Trash size={18} />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            {/* Logo */}
            <div className="bg-white p-6 rounded-2xl shadow-lg border border-gray-100 hover:shadow-xl transition-shadow duration-300">
              <div className="flex items-center gap-2 mb-4">
                <Camera className="text-blue-600" size={20} />
                <h3 className="text-lg font-bold text-gray-900">Logo</h3>
              </div>
              {salon.logo_url && (
                <div className="mb-4 p-4 bg-gray-50 rounded-xl border-2 border-gray-200">
                  <img src={salon.logo_url} alt="Logo" className="w-full h-32 object-contain rounded-lg" />
                </div>
              )}
              <label className="cursor-pointer inline-flex items-center gap-2 bg-gradient-to-r from-gray-100 to-gray-200 hover:from-gray-200 hover:to-gray-300 text-gray-700 px-4 py-3 rounded-xl transition-all duration-200 w-full justify-center font-semibold shadow-sm hover:shadow-md">
                <Upload size={18} />
                <span>Upload Logo</span>
                <input
                  type="file"
                  accept="image/jpeg,image/png"
                  onChange={handleLogoUpload}
                  className="hidden"
                />
              </label>
              <p className="text-xs text-gray-500 mt-2 text-center">Max 5MB, JPG or PNG</p>
            </div>

            {/* Cover Photo */}
            <div className="bg-white p-6 rounded-2xl shadow-lg border border-gray-100 hover:shadow-xl transition-shadow duration-300">
              <div className="flex items-center gap-2 mb-4">
                <Camera className="text-blue-600" size={20} />
                <h3 className="text-lg font-bold text-gray-900">Cover Photo</h3>
              </div>
              {salon.cover_image_url && (
                <div className="mb-4 p-4 bg-gray-50 rounded-xl border-2 border-gray-200">
                  <img src={salon.cover_image_url} alt="Cover" className="w-full h-32 object-cover rounded-lg" />
                </div>
              )}
              <label className="cursor-pointer inline-flex items-center gap-2 bg-gradient-to-r from-gray-100 to-gray-200 hover:from-gray-200 hover:to-gray-300 text-gray-700 px-4 py-3 rounded-xl transition-all duration-200 w-full justify-center font-semibold shadow-sm hover:shadow-md">
                <Upload size={18} />
                <span>Upload Cover</span>
                <input
                  type="file"
                  accept="image/jpeg,image/png"
                  onChange={handleCoverUpload}
                  className="hidden"
                />
              </label>
              <p className="text-xs text-gray-500 mt-2 text-center">Max 5MB, JPG or PNG</p>
            </div>

            {/* Quick Links */}
            <div className="bg-gradient-to-br from-blue-600 to-purple-600 p-6 rounded-2xl shadow-lg text-white">
              <h3 className="text-lg font-bold mb-4">Quick Links</h3>
              <div className="space-y-2">
                <button
                  onClick={() => router.push(`/dashboard/salons/${params.id}/masters`)}
                  className="w-full text-left px-4 py-3 bg-white/20 hover:bg-white/30 rounded-xl transition-all duration-200 backdrop-blur-sm font-medium"
                >
                  Manage Masters
                </button>
                <button
                  onClick={() => router.push(`/dashboard/salons/${params.id}/services`)}
                  className="w-full text-left px-4 py-3 bg-white/20 hover:bg-white/30 rounded-xl transition-all duration-200 backdrop-blur-sm font-medium"
                >
                  Manage Services
                </button>
                <button
                  onClick={() => router.push(`/salon/${salon.slug}`)}
                  className="w-full text-left px-4 py-3 bg-white/20 hover:bg-white/30 rounded-xl transition-all duration-200 backdrop-blur-sm font-medium inline-flex items-center gap-2"
                >
                  <span>View Public Page</span>
                  <ExternalLink size={16} />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Branch Modal */}
      {showBranchModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fadeIn">
          <div className="bg-white rounded-2xl max-w-md w-full p-8 shadow-2xl transform animate-slideUp">
            <h3 className="text-2xl font-bold text-gray-900 mb-6">
              {editingBranch ? 'Edit Branch' : 'Add Branch'}
            </h3>

            <div className="space-y-5 mb-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Branch Name *
                </label>
                <input
                  type="text"
                  value={branchForm.branch_name}
                  onChange={(e) => setBranchForm({ ...branchForm, branch_name: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all duration-200 outline-none"
                  placeholder="Main Branch"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  City *
                </label>
                <input
                  type="text"
                  value={branchForm.city}
                  onChange={(e) => setBranchForm({ ...branchForm, city: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all duration-200 outline-none"
                  placeholder="Almaty"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Address *
                </label>
                <input
                  type="text"
                  value={branchForm.address}
                  onChange={(e) => setBranchForm({ ...branchForm, address: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all duration-200 outline-none"
                  placeholder="123 Main Street"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Phone
                </label>
                <input
                  type="tel"
                  value={branchForm.phone}
                  onChange={(e) => setBranchForm({ ...branchForm, phone: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all duration-200 outline-none"
                  placeholder="+7 (XXX) XXX-XX-XX"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Email
                </label>
                <input
                  type="email"
                  value={branchForm.email}
                  onChange={(e) => setBranchForm({ ...branchForm, email: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all duration-200 outline-none"
                  placeholder="branch@salon.com"
                />
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setShowBranchModal(false)}
                className="flex-1 px-4 py-3 border-2 border-gray-300 rounded-xl hover:bg-gray-50 transition-colors duration-200 font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={handleBranchSubmit}
                className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 px-4 rounded-xl hover:from-blue-700 hover:to-purple-700 font-semibold shadow-lg hover:shadow-xl transition-all duration-200"
              >
                {editingBranch ? 'Update' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .animate-fadeIn {
          animation: fadeIn 0.2s ease-out;
        }

        .animate-slideUp {
          animation: slideUp 0.3s ease-out;
        }
      `}</style>
    </div>
  );
}
