'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { getMySalon, updateSalon, uploadLogo, uploadCover, createBranch, updateBranch, deleteBranch } from '@/lib/api/salons';
import { ArrowLeft, Save, Upload, Plus, Edit, Trash, MapPin } from 'lucide-react';
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

    try {
      await uploadLogo(params.id as string, file);
      toast.success('Logo uploaded successfully!');
      loadSalon();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to upload logo');
    }
  };

  const handleCoverUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
      toast.error('File size must be less than 5MB');
      return;
    }

    try {
      await uploadCover(params.id as string, file);
      toast.success('Cover photo uploaded successfully!');
      loadSalon();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to upload cover photo');
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

    try {
      if (editingBranch) {
        await updateBranch(params.id as string, editingBranch.id, branchForm);
        toast.success('Branch updated successfully!');
      } else {
        await createBranch(params.id as string, branchForm);
        toast.success('Branch created successfully!');
      }
      setShowBranchModal(false);
      loadSalon();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save branch');
    }
  };

  const handleDeleteBranch = async (branchId: string) => {
    if (!confirm('Are you sure you want to delete this branch?')) return;

    try {
      await deleteBranch(params.id as string, branchId);
      toast.success('Branch deleted successfully!');
      loadSalon();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to delete branch');
    }
  };

  if (loading || !salon) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-gray-600">Loading salon...</div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <button
          onClick={() => router.push('/dashboard')}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft size={20} />
          <span>Back to Dashboard</span>
        </button>

        <h1 className="text-3xl font-bold text-gray-900 mb-2">{salon.display_name}</h1>
        <p className="text-gray-600">Manage your salon settings and information</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Basic Information */}
          <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Business Name
                </label>
                <input
                  type="text"
                  name="business_name"
                  value={formData.business_name}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Display Name
                </label>
                <input
                  type="text"
                  name="display_name"
                  value={formData.display_name}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description (Russian)
                </label>
                <textarea
                  name="description_ru"
                  value={formData.description_ru}
                  onChange={handleChange}
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Phone
                </label>
                <input
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Website URL
                </label>
                <input
                  type="url"
                  name="website_url"
                  value={formData.website_url}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <button
                type="submit"
                disabled={saving}
                className="w-full bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed inline-flex items-center justify-center gap-2"
              >
                <Save size={20} />
                <span>{saving ? 'Saving...' : 'Save Changes'}</span>
              </button>
            </div>
          </form>

          {/* Branches */}
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Branches</h2>
              <button
                onClick={() => handleOpenBranchModal()}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 inline-flex items-center gap-2"
              >
                <Plus size={18} />
                <span>Add Branch</span>
              </button>
            </div>

            {salon.branches.length === 0 ? (
              <p className="text-gray-500 text-center py-4">No branches yet</p>
            ) : (
              <div className="space-y-3">
                {salon.branches.map((branch) => (
                  <div key={branch.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900">{branch.branch_name}</h3>
                        <div className="mt-1 space-y-1 text-sm text-gray-600">
                          <div className="flex items-center gap-2">
                            <MapPin size={14} />
                            <span>{branch.city}, {branch.address}</span>
                          </div>
                          {branch.phone && <p>Phone: {branch.phone}</p>}
                          {branch.email && <p>Email: {branch.email}</p>}
                        </div>
                        <span className={`inline-block mt-2 px-2 py-1 text-xs rounded ${branch.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                          {branch.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleOpenBranchModal(branch)}
                          className="p-2 text-blue-600 hover:bg-blue-50 rounded"
                        >
                          <Edit size={18} />
                        </button>
                        <button
                          onClick={() => handleDeleteBranch(branch.id)}
                          className="p-2 text-red-600 hover:bg-red-50 rounded"
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
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Logo</h3>
            {salon.logo_url && (
              <img src={salon.logo_url} alt="Logo" className="w-full h-32 object-contain mb-4 rounded" />
            )}
            <label className="cursor-pointer inline-flex items-center gap-2 bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg transition-colors">
              <Upload size={18} />
              <span>Upload Logo</span>
              <input
                type="file"
                accept="image/jpeg,image/png"
                onChange={handleLogoUpload}
                className="hidden"
              />
            </label>
            <p className="text-xs text-gray-500 mt-2">Max 5MB, JPG or PNG</p>
          </div>

          {/* Cover Photo */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Cover Photo</h3>
            {salon.cover_image_url && (
              <img src={salon.cover_image_url} alt="Cover" className="w-full h-32 object-cover mb-4 rounded" />
            )}
            <label className="cursor-pointer inline-flex items-center gap-2 bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg transition-colors">
              <Upload size={18} />
              <span>Upload Cover</span>
              <input
                type="file"
                accept="image/jpeg,image/png"
                onChange={handleCoverUpload}
                className="hidden"
              />
            </label>
            <p className="text-xs text-gray-500 mt-2">Max 5MB, JPG or PNG</p>
          </div>

          {/* Quick Links */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Links</h3>
            <div className="space-y-2">
              <button
                onClick={() => router.push(`/dashboard/salons/${params.id}/masters`)}
                className="w-full text-left px-4 py-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
              >
                Manage Masters
              </button>
              <button
                onClick={() => router.push(`/dashboard/salons/${params.id}/services`)}
                className="w-full text-left px-4 py-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
              >
                Manage Services
              </button>
              <button
                onClick={() => router.push(`/salon/${salon.slug}`)}
                className="w-full text-left px-4 py-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
              >
                View Public Page
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Branch Modal */}
      {showBranchModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">
              {editingBranch ? 'Edit Branch' : 'Add Branch'}
            </h3>

            <div className="space-y-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Branch Name *
                </label>
                <input
                  type="text"
                  value={branchForm.branch_name}
                  onChange={(e) => setBranchForm({ ...branchForm, branch_name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Main Branch"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  City *
                </label>
                <input
                  type="text"
                  value={branchForm.city}
                  onChange={(e) => setBranchForm({ ...branchForm, city: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Almaty"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Address *
                </label>
                <input
                  type="text"
                  value={branchForm.address}
                  onChange={(e) => setBranchForm({ ...branchForm, address: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="123 Main Street"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Phone
                </label>
                <input
                  type="tel"
                  value={branchForm.phone}
                  onChange={(e) => setBranchForm({ ...branchForm, phone: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="+7 (XXX) XXX-XX-XX"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email
                </label>
                <input
                  type="email"
                  value={branchForm.email}
                  onChange={(e) => setBranchForm({ ...branchForm, email: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="branch@salon.com"
                />
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setShowBranchModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleBranchSubmit}
                className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700"
              >
                {editingBranch ? 'Update' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
