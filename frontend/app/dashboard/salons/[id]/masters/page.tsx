'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { getSalonMasters, inviteMaster, updateMaster, deactivateMaster } from '@/lib/api/salons';
import { ArrowLeft, Plus, Edit, UserX, Star, Mail, Phone } from 'lucide-react';
import toast from 'react-hot-toast';

interface Master {
  id: string;
  first_name: string;
  last_name: string;
  email?: string;
  phone?: string;
  specialization?: string;
  photo_url?: string;
  rating?: number;
  is_active: boolean;
  status: string;
}

export default function MastersPage() {
  const params = useParams();
  const router = useRouter();
  const [masters, setMasters] = useState<Master[]>([]);
  const [loading, setLoading] = useState(true);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedMaster, setSelectedMaster] = useState<Master | null>(null);

  const [inviteForm, setInviteForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    specialization: '',
  });

  const [editForm, setEditForm] = useState({
    specialization: '',
  });

  useEffect(() => {
    loadMasters();
  }, [params.id]);

  const loadMasters = async () => {
    try {
      setLoading(true);
      const data = await getSalonMasters(params.id as string);
      setMasters(data);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to load masters');
    } finally {
      setLoading(false);
    }
  };

  const handleInvite = async () => {
    if (!inviteForm.first_name || !inviteForm.last_name || (!inviteForm.email && !inviteForm.phone)) {
      toast.error('Please fill in all required fields');
      return;
    }

    try {
      await inviteMaster(params.id as string, {
        first_name: inviteForm.first_name,
        last_name: inviteForm.last_name,
        email: inviteForm.email || undefined,
        phone: inviteForm.phone || undefined,
        specialization: inviteForm.specialization || undefined,
      });
      toast.success('Master invited successfully!');
      setShowInviteModal(false);
      setInviteForm({
        first_name: '',
        last_name: '',
        email: '',
        phone: '',
        specialization: '',
      });
      loadMasters();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to invite master');
    }
  };

  const handleOpenEdit = (master: Master) => {
    setSelectedMaster(master);
    setEditForm({
      specialization: master.specialization || '',
    });
    setShowEditModal(true);
  };

  const handleUpdate = async () => {
    if (!selectedMaster) return;

    try {
      await updateMaster(params.id as string, selectedMaster.id, editForm);
      toast.success('Master updated successfully!');
      setShowEditModal(false);
      loadMasters();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to update master');
    }
  };

  const handleDeactivate = async (masterId: string) => {
    if (!confirm('Are you sure you want to deactivate this master?')) return;

    try {
      await deactivateMaster(params.id as string, masterId);
      toast.success('Master deactivated successfully!');
      loadMasters();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to deactivate master');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'pending_invitation':
        return 'bg-yellow-100 text-yellow-800';
      case 'inactive':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-gray-600">Loading masters...</div>
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

        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Masters Management</h1>
            <p className="text-gray-600">Invite and manage masters for your salon</p>
          </div>
          <button
            onClick={() => setShowInviteModal(true)}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 inline-flex items-center gap-2"
          >
            <Plus size={20} />
            <span>Invite Master</span>
          </button>
        </div>
      </div>

      {/* Masters List */}
      {masters.length === 0 ? (
        <div className="bg-white p-12 rounded-lg shadow text-center">
          <p className="text-gray-600 mb-4">No masters yet</p>
          <button
            onClick={() => setShowInviteModal(true)}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 inline-flex items-center gap-2"
          >
            <Plus size={20} />
            <span>Invite First Master</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {masters.map((master) => (
            <div key={master.id} className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-start gap-4">
                {master.photo_url ? (
                  <img
                    src={master.photo_url}
                    alt={`${master.first_name} ${master.last_name}`}
                    className="w-20 h-20 rounded-full object-cover"
                  />
                ) : (
                  <div className="w-20 h-20 rounded-full bg-gray-200 flex items-center justify-center">
                    <span className="text-gray-600 text-xl font-medium">
                      {master.first_name[0]}
                      {master.last_name[0]}
                    </span>
                  </div>
                )}

                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900">
                    {master.first_name} {master.last_name}
                  </h3>

                  {master.specialization && (
                    <p className="text-sm text-gray-600 mt-1">{master.specialization}</p>
                  )}

                  {master.rating && (
                    <div className="flex items-center gap-1 mt-2">
                      <Star className="text-yellow-400 fill-yellow-400" size={16} />
                      <span className="text-sm font-medium">{master.rating.toFixed(1)}</span>
                    </div>
                  )}

                  <div className="mt-3 space-y-1 text-sm text-gray-600">
                    {master.email && (
                      <div className="flex items-center gap-2">
                        <Mail size={14} />
                        <span>{master.email}</span>
                      </div>
                    )}
                    {master.phone && (
                      <div className="flex items-center gap-2">
                        <Phone size={14} />
                        <span>{master.phone}</span>
                      </div>
                    )}
                  </div>

                  <div className="mt-3 flex items-center gap-2">
                    <span
                      className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(
                        master.status
                      )}`}
                    >
                      {master.status.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                    </span>
                  </div>

                  <div className="mt-4 flex gap-2">
                    <button
                      onClick={() => handleOpenEdit(master)}
                      className="px-4 py-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors flex items-center gap-2"
                    >
                      <Edit size={16} />
                      <span>Edit</span>
                    </button>

                    {master.is_active && (
                      <button
                        onClick={() => handleDeactivate(master.id)}
                        className="px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors flex items-center gap-2"
                      >
                        <UserX size={16} />
                        <span>Deactivate</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Invite Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">Invite Master</h3>

            <div className="space-y-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  First Name *
                </label>
                <input
                  type="text"
                  value={inviteForm.first_name}
                  onChange={(e) => setInviteForm({ ...inviteForm, first_name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="John"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Last Name *
                </label>
                <input
                  type="text"
                  value={inviteForm.last_name}
                  onChange={(e) => setInviteForm({ ...inviteForm, last_name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Doe"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email
                </label>
                <input
                  type="email"
                  value={inviteForm.email}
                  onChange={(e) => setInviteForm({ ...inviteForm, email: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="master@example.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Phone
                </label>
                <input
                  type="tel"
                  value={inviteForm.phone}
                  onChange={(e) => setInviteForm({ ...inviteForm, phone: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="+7 (XXX) XXX-XX-XX"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Specialization
                </label>
                <input
                  type="text"
                  value={inviteForm.specialization}
                  onChange={(e) =>
                    setInviteForm({ ...inviteForm, specialization: e.target.value })
                  }
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Hair Stylist"
                />
              </div>

              <p className="text-sm text-gray-600">
                * Email or Phone is required. An invitation will be sent to the master.
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setShowInviteModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleInvite}
                className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700"
              >
                Send Invitation
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && selectedMaster && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">Edit Master</h3>

            <div className="mb-4">
              <p className="text-gray-700">
                {selectedMaster.first_name} {selectedMaster.last_name}
              </p>
            </div>

            <div className="space-y-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Specialization
                </label>
                <input
                  type="text"
                  value={editForm.specialization}
                  onChange={(e) => setEditForm({ ...editForm, specialization: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Hair Stylist"
                />
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setShowEditModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleUpdate}
                className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700"
              >
                Update
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
