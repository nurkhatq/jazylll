'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { getMySalon, createService, updateService, deleteService } from '@/lib/api/salons';
import { ArrowLeft, Plus, Edit, Trash, Clock } from 'lucide-react';
import toast from 'react-hot-toast';

interface Service {
  id: string;
  name_ru: string;
  name_kk: string;
  name_en: string;
  description_ru?: string;
  description_kk?: string;
  description_en?: string;
  price: number;
  duration_minutes: number;
  is_active: boolean;
}

export default function ServicesPage() {
  const params = useParams();
  const router = useRouter();
  const [services, setServices] = useState<Service[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingService, setEditingService] = useState<Service | null>(null);

  const [serviceForm, setServiceForm] = useState({
    name_ru: '',
    name_kk: '',
    name_en: '',
    description_ru: '',
    description_kk: '',
    description_en: '',
    price: '',
    duration_minutes: '',
  });

  useEffect(() => {
    loadServices();
  }, [params.id]);

  const loadServices = async () => {
    try {
      setLoading(true);
      const salon = await getMySalon(params.id as string);
      setServices(salon.services || []);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to load services');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenModal = (service?: Service) => {
    if (service) {
      setEditingService(service);
      setServiceForm({
        name_ru: service.name_ru,
        name_kk: service.name_kk || '',
        name_en: service.name_en || '',
        description_ru: service.description_ru || '',
        description_kk: service.description_kk || '',
        description_en: service.description_en || '',
        price: service.price.toString(),
        duration_minutes: service.duration_minutes.toString(),
      });
    } else {
      setEditingService(null);
      setServiceForm({
        name_ru: '',
        name_kk: '',
        name_en: '',
        description_ru: '',
        description_kk: '',
        description_en: '',
        price: '',
        duration_minutes: '',
      });
    }
    setShowModal(true);
  };

  const handleSubmit = async () => {
    if (!serviceForm.name_ru || !serviceForm.price || !serviceForm.duration_minutes) {
      toast.error('Please fill in all required fields');
      return;
    }

    const data = {
      name_ru: serviceForm.name_ru,
      name_kk: serviceForm.name_kk || undefined,
      name_en: serviceForm.name_en || undefined,
      description_ru: serviceForm.description_ru || undefined,
      description_kk: serviceForm.description_kk || undefined,
      description_en: serviceForm.description_en || undefined,
      price: parseFloat(serviceForm.price),
      duration_minutes: parseInt(serviceForm.duration_minutes),
    };

    try {
      if (editingService) {
        await updateService(params.id as string, editingService.id, data);
        toast.success('Service updated successfully!');
      } else {
        await createService(params.id as string, data);
        toast.success('Service created successfully!');
      }
      setShowModal(false);
      loadServices();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save service');
    }
  };

  const handleDelete = async (serviceId: string) => {
    if (!confirm('Are you sure you want to delete this service?')) return;

    try {
      await deleteService(params.id as string, serviceId);
      toast.success('Service deleted successfully!');
      loadServices();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to delete service');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-gray-600">Loading services...</div>
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
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Services Management</h1>
            <p className="text-gray-600">Manage services offered by your salon</p>
          </div>
          <button
            onClick={() => handleOpenModal()}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 inline-flex items-center gap-2"
          >
            <Plus size={20} />
            <span>Add Service</span>
          </button>
        </div>
      </div>

      {/* Services List */}
      {services.length === 0 ? (
        <div className="bg-white p-12 rounded-lg shadow text-center">
          <p className="text-gray-600 mb-4">No services yet</p>
          <button
            onClick={() => handleOpenModal()}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 inline-flex items-center gap-2"
          >
            <Plus size={20} />
            <span>Add First Service</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {services.map((service) => (
            <div key={service.id} className="bg-white p-6 rounded-lg shadow">
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900">{service.name_ru}</h3>
                  {service.description_ru && (
                    <p className="text-sm text-gray-600 mt-1">{service.description_ru}</p>
                  )}
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium ${
                    service.is_active
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }`}
                >
                  {service.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>

              <div className="space-y-2 mb-4">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Price:</span>
                  <span className="font-semibold text-gray-900">
                    {service.price.toLocaleString()} ₸
                  </span>
                </div>

                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Duration:</span>
                  <span className="flex items-center gap-1 font-medium text-gray-900">
                    <Clock size={14} />
                    {service.duration_minutes} min
                  </span>
                </div>
              </div>

              {/* Translations */}
              {(service.name_kk || service.name_en) && (
                <div className="border-t border-gray-200 pt-4 mb-4">
                  <p className="text-xs font-medium text-gray-500 mb-2">Translations:</p>
                  {service.name_kk && (
                    <p className="text-sm text-gray-700">
                      <span className="font-medium">KK:</span> {service.name_kk}
                    </p>
                  )}
                  {service.name_en && (
                    <p className="text-sm text-gray-700">
                      <span className="font-medium">EN:</span> {service.name_en}
                    </p>
                  )}
                </div>
              )}

              <div className="flex gap-2 pt-4 border-t border-gray-200">
                <button
                  onClick={() => handleOpenModal(service)}
                  className="flex-1 px-4 py-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  <Edit size={16} />
                  <span>Edit</span>
                </button>

                <button
                  onClick={() => handleDelete(service.id)}
                  className="flex-1 px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  <Trash size={16} />
                  <span>Delete</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Service Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-semibold text-gray-900 mb-6">
              {editingService ? 'Edit Service' : 'Add Service'}
            </h3>

            <div className="space-y-6">
              {/* Basic Info */}
              <div>
                <h4 className="font-medium text-gray-900 mb-3">Basic Information</h4>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Service Name (Russian) *
                    </label>
                    <input
                      type="text"
                      value={serviceForm.name_ru}
                      onChange={(e) =>
                        setServiceForm({ ...serviceForm, name_ru: e.target.value })
                      }
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Haircut"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Price (₸) *
                      </label>
                      <input
                        type="number"
                        value={serviceForm.price}
                        onChange={(e) =>
                          setServiceForm({ ...serviceForm, price: e.target.value })
                        }
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="5000"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Duration (minutes) *
                      </label>
                      <input
                        type="number"
                        value={serviceForm.duration_minutes}
                        onChange={(e) =>
                          setServiceForm({ ...serviceForm, duration_minutes: e.target.value })
                        }
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="60"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Description (Russian)
                    </label>
                    <textarea
                      value={serviceForm.description_ru}
                      onChange={(e) =>
                        setServiceForm({ ...serviceForm, description_ru: e.target.value })
                      }
                      rows={3}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Describe the service..."
                    />
                  </div>
                </div>
              </div>

              {/* Translations */}
              <div className="border-t border-gray-200 pt-6">
                <h4 className="font-medium text-gray-900 mb-3">Translations (Optional)</h4>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Service Name (Kazakh)
                    </label>
                    <input
                      type="text"
                      value={serviceForm.name_kk}
                      onChange={(e) =>
                        setServiceForm({ ...serviceForm, name_kk: e.target.value })
                      }
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Service Name (English)
                    </label>
                    <input
                      type="text"
                      value={serviceForm.name_en}
                      onChange={(e) =>
                        setServiceForm({ ...serviceForm, name_en: e.target.value })
                      }
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700"
              >
                {editingService ? 'Update' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
