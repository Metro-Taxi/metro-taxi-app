import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Car, Users, CreditCard, MapPin, LogOut, Menu, X, 
  Check, XCircle, Eye, UserCheck, UserX, BarChart3,
  TrendingUp, Activity, Mail, Phone, Calendar, IdCard,
  Clock, AlertTriangle, RefreshCw, Trash2, Globe, Plus,
  Power, PowerOff, Edit, Save, Loader2
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import LanguageSelector from '@/components/LanguageSelector';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Country flag mapping
const countryFlags = {
  FR: '🇫🇷',
  GB: '🇬🇧',
  ES: '🇪🇸',
  DE: '🇩🇪',
  IT: '🇮🇹',
  PT: '🇵🇹',
  NL: '🇳🇱',
  BE: '🇧🇪',
  CH: '🇨🇭',
  US: '🇺🇸',
};

const AdminDashboard = () => {
  const { admin, token, logout } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [menuOpen, setMenuOpen] = useState(false);
  const [stats, setStats] = useState(null);
  const [drivers, setDrivers] = useState([]);
  const [users, setUsers] = useState([]);
  const [virtualCards, setVirtualCards] = useState([]);
  const [subscriptionStats, setSubscriptionStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedCard, setSelectedCard] = useState(null);
  const [cardDialogOpen, setCardDialogOpen] = useState(false);
  const [cleanupLoading, setCleanupLoading] = useState(false);
  
  // Region states
  const [regions, setRegions] = useState([]);
  const [regionDialogOpen, setRegionDialogOpen] = useState(false);
  const [editingRegion, setEditingRegion] = useState(null);
  const [regionForm, setRegionForm] = useState({
    id: '',
    name: '',
    country: 'FR',
    currency: 'EUR',
    language: 'fr',
    timezone: 'Europe/Paris',
    bounds: { north: 0, south: 0, east: 0, west: 0 },
    is_active: false
  });
  const [savingRegion, setSavingRegion] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [statsRes, driversRes, usersRes, cardsRes, subsRes, regionsRes] = await Promise.all([
        axios.get(`${API}/admin/stats`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/admin/drivers`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/admin/users`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/admin/cards`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/admin/subscriptions`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/regions`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      
      setStats(statsRes.data);
      setDrivers(driversRes.data.drivers || []);
      setUsers(usersRes.data.users || []);
      setVirtualCards(cardsRes.data.cards || []);
      setSubscriptionStats(subsRes.data);
      setRegions(regionsRes.data || []);
    } catch (error) {
      console.error('Fetch error:', error);
      toast.error(t('dashboard.admin.common.loadingError'));
    } finally {
      setLoading(false);
    }
  };

  const viewUserCard = async (userId) => {
    try {
      const response = await axios.get(`${API}/admin/cards/${userId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSelectedCard(response.data.card);
      setCardDialogOpen(true);
    } catch (error) {
      toast.error(t('common.cardLoadError'));
    }
  };

  const validateDriver = async (driverId) => {
    try {
      await axios.post(`${API}/admin/drivers/${driverId}/validate`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(t('common.driverActivated'));
      fetchData();
    } catch (error) {
      toast.error(t('common.activateError'));
    }
  };

  const deactivateDriver = async (driverId) => {
    try {
      await axios.post(`${API}/admin/drivers/${driverId}/deactivate`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(t('common.driverDeactivated'));
      fetchData();
    } catch (error) {
      toast.error(t('common.deactivateError'));
    }
  };

  const cleanupExpiredSubscriptions = async () => {
    setCleanupLoading(true);
    try {
      const response = await axios.post(`${API}/admin/subscriptions/cleanup`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(response.data.message);
      fetchData();
    } catch (error) {
      toast.error(t('common.cleanupError'));
    } finally {
      setCleanupLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  // Region management functions
  const openCreateRegionDialog = () => {
    setEditingRegion(null);
    setRegionForm({
      id: '',
      name: '',
      country: 'FR',
      currency: 'EUR',
      language: 'fr',
      timezone: 'Europe/Paris',
      bounds: { north: 0, south: 0, east: 0, west: 0 },
      is_active: false
    });
    setRegionDialogOpen(true);
  };

  const openEditRegionDialog = (region) => {
    setEditingRegion(region);
    setRegionForm({
      id: region.id,
      name: region.name,
      country: region.country,
      currency: region.currency,
      language: region.language,
      timezone: region.timezone || 'Europe/Paris',
      bounds: region.bounds || { north: 0, south: 0, east: 0, west: 0 },
      is_active: region.is_active
    });
    setRegionDialogOpen(true);
  };

  const handleRegionFormChange = (field, value) => {
    if (field.startsWith('bounds.')) {
      const boundField = field.split('.')[1];
      setRegionForm(prev => ({
        ...prev,
        bounds: { ...prev.bounds, [boundField]: parseFloat(value) || 0 }
      }));
    } else {
      setRegionForm(prev => ({ ...prev, [field]: value }));
    }
  };

  const saveRegion = async () => {
    if (!regionForm.id || !regionForm.name) {
      toast.error(t('regions.admin.fillRequired', 'Please fill all required fields'));
      return;
    }

    setSavingRegion(true);
    try {
      if (editingRegion) {
        await axios.put(`${API}/admin/regions/${editingRegion.id}`, regionForm, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success(t('regions.admin.updated', 'Region updated successfully'));
      } else {
        await axios.post(`${API}/admin/regions`, regionForm, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success(t('regions.admin.created', 'Region created successfully'));
      }
      setRegionDialogOpen(false);
      fetchData();
    } catch (error) {
      const message = error.response?.data?.detail || t('regions.admin.saveError', 'Error saving region');
      toast.error(message);
    } finally {
      setSavingRegion(false);
    }
  };

  const activateRegion = async (regionId) => {
    try {
      await axios.post(`${API}/admin/regions/${regionId}/activate`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(t('regions.admin.activated', 'Region activated'));
      fetchData();
    } catch (error) {
      toast.error(t('regions.admin.activateError', 'Error activating region'));
    }
  };

  const deactivateRegion = async (regionId) => {
    try {
      await axios.post(`${API}/admin/regions/${regionId}/deactivate`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(t('regions.admin.deactivated', 'Region deactivated'));
      fetchData();
    } catch (error) {
      toast.error(t('regions.admin.deactivateError', 'Error deactivating region'));
    }
  };

  const deleteRegion = async (regionId) => {
    if (!window.confirm(t('regions.admin.confirmDelete', 'Are you sure you want to delete this region?'))) {
      return;
    }
    try {
      await axios.delete(`${API}/admin/regions/${regionId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(t('regions.admin.deleted', 'Region deleted'));
      fetchData();
    } catch (error) {
      const message = error.response?.data?.detail || t('regions.admin.deleteError', 'Error deleting region');
      toast.error(message);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('fr-FR');
  };

  return (
    <div className="min-h-screen bg-[#09090B]">
      {/* Header */}
      <header className="bg-[#18181B] border-b border-zinc-800 px-6 py-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-3">
            <Car className="w-8 h-8 text-[#FFD60A]" />
            <div>
              <span className="text-xl font-bold text-white">MÉTRO-TAXI</span>
              <span className="text-xs text-zinc-400 block">{t('dashboard.admin.title')}</span>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <LanguageSelector />
            <span className="text-zinc-400 text-sm hidden md:block">
              {admin?.email}
            </span>
            <Button 
              variant="ghost" 
              className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
              onClick={handleLogout}
              data-testid="admin-logout-btn"
            >
              <LogOut className="w-5 h-5" />
            </Button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-[#18181B] border border-zinc-800 p-6 rounded"
          >
            <div className="flex items-center justify-between mb-4">
              <Users className="w-8 h-8 text-blue-500" />
              <TrendingUp className="w-4 h-4 text-green-500" />
            </div>
            <p className="text-3xl font-black text-white">{stats?.total_users || 0}</p>
            <p className="text-zinc-400 text-sm">{t('dashboard.admin.stats.users')}</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-[#18181B] border border-zinc-800 p-6 rounded"
          >
            <div className="flex items-center justify-between mb-4">
              <Car className="w-8 h-8 text-[#FFD60A]" />
              <Activity className="w-4 h-4 text-[#FFD60A]" />
            </div>
            <p className="text-3xl font-black text-white">{stats?.total_drivers || 0}</p>
            <p className="text-zinc-400 text-sm">{t('dashboard.admin.stats.drivers')}</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-[#18181B] border border-zinc-800 p-6 rounded"
          >
            <div className="flex items-center justify-between mb-4">
              <CreditCard className="w-8 h-8 text-green-500" />
              <BarChart3 className="w-4 h-4 text-green-500" />
            </div>
            <p className="text-3xl font-black text-white">{stats?.active_subscriptions || 0}</p>
            <p className="text-zinc-400 text-sm">{t('dashboard.admin.stats.subscriptions')}</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-[#18181B] border border-zinc-800 p-6 rounded"
          >
            <div className="flex items-center justify-between mb-4">
              <MapPin className="w-8 h-8 text-purple-500" />
              <Activity className="w-4 h-4 text-purple-500 animate-pulse" />
            </div>
            <p className="text-3xl font-black text-white">{stats?.active_rides || 0}</p>
            <p className="text-zinc-400 text-sm">{t('dashboard.admin.stats.rides')}</p>
          </motion.div>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="drivers" className="w-full">
          <TabsList className="bg-[#18181B] border border-zinc-800 mb-6">
            <TabsTrigger 
              value="drivers" 
              className="data-[state=active]:bg-[#FFD60A] data-[state=active]:text-black"
              data-testid="drivers-tab"
            >
              <Car className="w-4 h-4 mr-2" />
              {t('dashboard.admin.tabs.drivers')}
            </TabsTrigger>
            <TabsTrigger 
              value="users"
              className="data-[state=active]:bg-[#FFD60A] data-[state=active]:text-black"
              data-testid="users-tab"
            >
              <Users className="w-4 h-4 mr-2" />
              {t('dashboard.admin.tabs.users')}
            </TabsTrigger>
            <TabsTrigger 
              value="subscriptions"
              className="data-[state=active]:bg-[#FFD60A] data-[state=active]:text-black"
              data-testid="subscriptions-tab"
            >
              <CreditCard className="w-4 h-4 mr-2" />
              {t('dashboard.admin.tabs.subscriptions')}
            </TabsTrigger>
            <TabsTrigger 
              value="cards"
              className="data-[state=active]:bg-[#FFD60A] data-[state=active]:text-black"
              data-testid="cards-tab"
            >
              <IdCard className="w-4 h-4 mr-2" />
              {t('dashboard.admin.tabs.cards')}
            </TabsTrigger>
            <TabsTrigger 
              value="regions"
              className="data-[state=active]:bg-[#FFD60A] data-[state=active]:text-black"
              data-testid="regions-tab"
            >
              <Globe className="w-4 h-4 mr-2" />
              {t('dashboard.admin.tabs.regions', 'Regions')}
            </TabsTrigger>
          </TabsList>

          {/* Drivers Tab */}
          <TabsContent value="drivers">
            <div className="bg-[#18181B] border border-zinc-800 rounded overflow-hidden">
              <div className="p-4 border-b border-zinc-800">
                <h2 className="text-xl font-bold text-white">{t('dashboard.admin.drivers.title')}</h2>
                <p className="text-zinc-400 text-sm">{t('dashboard.admin.drivers.subtitle')}</p>
              </div>
              
              {loading ? (
                <div className="p-8 text-center">
                  <div className="w-8 h-8 border-4 border-[#FFD60A] border-t-transparent rounded-full animate-spin mx-auto"></div>
                </div>
              ) : drivers.length === 0 ? (
                <div className="p-8 text-center text-zinc-400">
                  {t('dashboard.admin.drivers.noDrivers')}
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="admin-table">
                    <thead>
                      <tr>
                        <th>{t('dashboard.admin.drivers.driver')}</th>
                        <th>{t('dashboard.admin.drivers.contact')}</th>
                        <th>{t('dashboard.admin.drivers.vehicle')}</th>
                        <th>{t('dashboard.admin.drivers.license')}</th>
                        <th>{t('dashboard.admin.drivers.status')}</th>
                        <th>{t('dashboard.admin.drivers.actions')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {drivers.map((driver) => (
                        <tr key={driver.id}>
                          <td>
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 bg-[#FFD60A] rounded-full flex items-center justify-center">
                                <Car className="w-5 h-5 text-black" />
                              </div>
                              <div>
                                <p className="font-medium text-white">{driver.first_name} {driver.last_name}</p>
                                <p className="text-xs text-zinc-500">{t('dashboard.admin.common.registeredOn')} {formatDate(driver.created_at)}</p>
                              </div>
                            </div>
                          </td>
                          <td>
                            <p className="text-white text-sm">{driver.email}</p>
                            <p className="text-zinc-500 text-xs">{driver.phone}</p>
                          </td>
                          <td>
                            <p className="text-white font-mono">{driver.vehicle_plate}</p>
                            <p className="text-zinc-500 text-xs">{driver.vehicle_type} • {driver.seats} {t('dashboard.admin.common.seats')}</p>
                          </td>
                          <td>
                            <p className="text-white font-mono text-sm">{driver.vtc_license}</p>
                          </td>
                          <td>
                            <div className="flex flex-col gap-1">
                              <span className={`text-xs px-2 py-1 rounded inline-flex items-center gap-1 w-fit ${
                                driver.is_validated 
                                  ? 'bg-green-500/20 text-green-400' 
                                  : 'bg-yellow-500/20 text-yellow-400'
                              }`}>
                                {driver.is_validated ? <Check className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                                {driver.is_validated ? t('dashboard.admin.drivers.validated') : t('dashboard.admin.drivers.pending')}
                              </span>
                              {driver.is_active && (
                                <span className="text-xs px-2 py-1 rounded bg-blue-500/20 text-blue-400 w-fit">
                                  {t('dashboard.admin.drivers.online')}
                                </span>
                              )}
                            </div>
                          </td>
                          <td>
                            <div className="flex gap-1">
                              {!driver.is_validated ? (
                                <Button
                                  size="sm"
                                  onClick={() => validateDriver(driver.id)}
                                  className="bg-green-600 hover:bg-green-700 text-white text-xs px-2 py-1 h-auto"
                                  data-testid={`validate-driver-${driver.id}`}
                                >
                                  <UserCheck className="w-3 h-3 mr-1" />
                                  <span className="hidden lg:inline">{t('dashboard.admin.drivers.activate')}</span>
                                </Button>
                              ) : (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => deactivateDriver(driver.id)}
                                  className="border-red-500/50 text-red-400 hover:bg-red-500/10 text-xs px-2 py-1 h-auto"
                                  data-testid={`deactivate-driver-${driver.id}`}
                                >
                                  <UserX className="w-3 h-3 mr-1" />
                                  <span className="hidden lg:inline">{t('dashboard.admin.drivers.deactivate')}</span>
                                </Button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </TabsContent>

          {/* Users Tab */}
          <TabsContent value="users">
            <div className="bg-[#18181B] border border-zinc-800 rounded overflow-hidden">
              <div className="p-4 border-b border-zinc-800">
                <h2 className="text-xl font-bold text-white">{t('dashboard.admin.users.title')}</h2>
                <p className="text-zinc-400 text-sm">{t('dashboard.admin.users.subtitle')}</p>
              </div>
              
              {loading ? (
                <div className="p-8 text-center">
                  <div className="w-8 h-8 border-4 border-[#FFD60A] border-t-transparent rounded-full animate-spin mx-auto"></div>
                </div>
              ) : users.length === 0 ? (
                <div className="p-8 text-center text-zinc-400">
                  {t('dashboard.admin.users.noUsers')}
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="admin-table">
                    <thead>
                      <tr>
                        <th>{t('dashboard.admin.users.user')}</th>
                        <th>{t('dashboard.admin.users.contact')}</th>
                        <th>{t('dashboard.admin.users.subscription')}</th>
                        <th>{t('dashboard.admin.users.expiration')}</th>
                        <th>{t('dashboard.admin.users.registration')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users.map((user) => (
                        <tr key={user.id}>
                          <td>
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
                                <Users className="w-5 h-5 text-white" />
                              </div>
                              <div>
                                <p className="font-medium text-white">{user.first_name} {user.last_name}</p>
                                <p className="text-xs text-zinc-500 font-mono">{user.id.slice(0, 8)}</p>
                              </div>
                            </div>
                          </td>
                          <td>
                            <p className="text-white text-sm">{user.email}</p>
                            <p className="text-zinc-500 text-xs">{user.phone}</p>
                          </td>
                          <td>
                            <span className={`text-xs px-2 py-1 rounded ${
                              user.subscription_active 
                                ? 'bg-green-500/20 text-green-400' 
                                : 'bg-zinc-700/50 text-zinc-400'
                            }`}>
                              {user.subscription_active ? t('dashboard.admin.users.active') : t('dashboard.admin.users.inactive')}
                            </span>
                          </td>
                          <td>
                            <p className="text-white text-sm">
                              {user.subscription_expires ? formatDate(user.subscription_expires) : '-'}
                            </p>
                          </td>
                          <td>
                            <p className="text-zinc-400 text-sm">{formatDate(user.created_at)}</p>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </TabsContent>

          {/* Subscriptions Tab */}
          <TabsContent value="subscriptions">
            <div className="space-y-6">
              {/* Subscription Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-[#18181B] border border-green-500/30 p-6 rounded"
                >
                  <div className="flex items-center justify-between mb-4">
                    <Check className="w-8 h-8 text-green-500" />
                    <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded">{t('dashboard.admin.subscriptions.activeLabel')}</span>
                  </div>
                  <p className="text-3xl font-black text-white">{subscriptionStats?.summary?.total_active || 0}</p>
                  <p className="text-zinc-400 text-sm">{t('dashboard.admin.subscriptions.active')}</p>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                  className="bg-[#18181B] border border-yellow-500/30 p-6 rounded"
                >
                  <div className="flex items-center justify-between mb-4">
                    <Clock className="w-8 h-8 text-yellow-500" />
                    <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded">{t('dashboard.admin.subscriptions.soonLabel')}</span>
                  </div>
                  <p className="text-3xl font-black text-white">{subscriptionStats?.summary?.expiring_soon_24h || 0}</p>
                  <p className="text-zinc-400 text-sm">{t('dashboard.admin.subscriptions.expiringSoon')}</p>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                  className="bg-[#18181B] border border-red-500/30 p-6 rounded"
                >
                  <div className="flex items-center justify-between mb-4">
                    <XCircle className="w-8 h-8 text-red-500" />
                    <span className="text-xs bg-red-500/20 text-red-400 px-2 py-1 rounded">{t('dashboard.admin.subscriptions.expiredLabel')}</span>
                  </div>
                  <p className="text-3xl font-black text-white">{subscriptionStats?.summary?.total_expired || 0}</p>
                  <p className="text-zinc-400 text-sm">{t('dashboard.admin.subscriptions.expired')}</p>
                </motion.div>
              </div>

              {/* Cleanup Button */}
              <div className="flex justify-end">
                <Button
                  onClick={cleanupExpiredSubscriptions}
                  disabled={cleanupLoading}
                  className="bg-red-600 hover:bg-red-700 text-white"
                  data-testid="cleanup-subscriptions-btn"
                >
                  {cleanupLoading ? (
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                  ) : (
                    <Trash2 className="w-4 h-4 mr-2" />
                  )}
                  {t('dashboard.admin.subscriptions.cleanup')}
                </Button>
              </div>

              {/* Active Subscriptions */}
              <div className="bg-[#18181B] border border-zinc-800 rounded overflow-hidden">
                <div className="p-4 border-b border-zinc-800 flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-bold text-white flex items-center gap-2">
                      <Check className="w-5 h-5 text-green-500" />
                      {t('dashboard.admin.subscriptions.active')}
                    </h2>
                    <p className="text-zinc-400 text-sm">{t('dashboard.admin.subscriptions.activeDesc')}</p>
                  </div>
                  <Button variant="ghost" onClick={fetchData} className="text-zinc-400 hover:text-white">
                    <RefreshCw className="w-4 h-4" />
                  </Button>
                </div>
                
                {loading ? (
                  <div className="p-8 text-center">
                    <div className="w-8 h-8 border-4 border-[#FFD60A] border-t-transparent rounded-full animate-spin mx-auto"></div>
                  </div>
                ) : (subscriptionStats?.active_subscriptions || []).length === 0 ? (
                  <div className="p-8 text-center text-zinc-400">
                    {t('dashboard.admin.subscriptions.noActive')}
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="admin-table">
                      <thead>
                        <tr>
                          <th>{t('dashboard.admin.users.user')}</th>
                          <th>Email</th>
                          <th>Plan</th>
                          <th>{t('dashboard.admin.users.expiration')}</th>
                          <th>{t('dashboard.admin.subscriptions.status')}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(subscriptionStats?.active_subscriptions || []).map((sub) => {
                          const isExpiringSoon = subscriptionStats?.expiring_soon?.some(e => e.id === sub.id);
                          return (
                            <tr key={sub.id}>
                              <td>
                                <p className="font-medium text-white">{sub.name}</p>
                              </td>
                              <td>
                                <p className="text-white text-sm">{sub.email}</p>
                              </td>
                              <td>
                                <span className="text-[#FFD60A] font-bold">
                                  {sub.plan === '24h' ? t('subscription.plans.day.name') :
                                   sub.plan === '1week' ? t('subscription.plans.week.name') :
                                   sub.plan === '1month' ? t('subscription.plans.month.name') : sub.plan || '-'}
                                </span>
                              </td>
                              <td>
                                <p className="text-white text-sm">{formatDate(sub.expires)}</p>
                              </td>
                              <td>
                                {isExpiringSoon ? (
                                  <span className="text-xs px-2 py-1 rounded bg-yellow-500/20 text-yellow-400 flex items-center gap-1 w-fit">
                                    <AlertTriangle className="w-3 h-3" />
                                    {t('dashboard.admin.subscriptions.expiresSoon')}
                                  </span>
                                ) : (
                                  <span className="text-xs px-2 py-1 rounded bg-green-500/20 text-green-400">
                                    {t('dashboard.admin.users.active')}
                                  </span>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Expired Subscriptions */}
              {(subscriptionStats?.expired_subscriptions || []).length > 0 && (
                <div className="bg-[#18181B] border border-red-500/30 rounded overflow-hidden">
                  <div className="p-4 border-b border-zinc-800">
                    <h2 className="text-xl font-bold text-white flex items-center gap-2">
                      <XCircle className="w-5 h-5 text-red-500" />
                      {t('dashboard.admin.subscriptions.expired')}
                    </h2>
                    <p className="text-zinc-400 text-sm">{t('dashboard.admin.subscriptions.expiredDesc')}</p>
                  </div>
                  
                  <div className="overflow-x-auto">
                    <table className="admin-table">
                      <thead>
                        <tr>
                          <th>{t('dashboard.admin.users.user')}</th>
                          <th>Email</th>
                          <th>Plan</th>
                          <th>{t('dashboard.admin.users.expiration')}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(subscriptionStats?.expired_subscriptions || []).map((sub) => (
                          <tr key={sub.id}>
                            <td>
                              <p className="font-medium text-white">{sub.name}</p>
                            </td>
                            <td>
                              <p className="text-white text-sm">{sub.email}</p>
                            </td>
                            <td>
                              <span className="text-zinc-400">
                                {sub.plan === '24h' ? t('subscription.plans.day.name') :
                                 sub.plan === '1week' ? t('subscription.plans.week.name') :
                                 sub.plan === '1month' ? t('subscription.plans.month.name') : sub.plan || '-'}
                              </span>
                            </td>
                            <td>
                              <p className="text-red-400 text-sm">{formatDate(sub.expires)}</p>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          </TabsContent>

          {/* Virtual Cards Tab */}
          <TabsContent value="cards">
            <div className="bg-[#18181B] border border-zinc-800 rounded overflow-hidden">
              <div className="p-4 border-b border-zinc-800">
                <h2 className="text-xl font-bold text-white">{t('dashboard.admin.cards.title')}</h2>
                <p className="text-zinc-400 text-sm">{t('dashboard.admin.cards.subtitle')}</p>
              </div>
              
              {loading ? (
                <div className="p-8 text-center">
                  <div className="w-8 h-8 border-4 border-[#FFD60A] border-t-transparent rounded-full animate-spin mx-auto"></div>
                </div>
              ) : virtualCards.length === 0 ? (
                <div className="p-8 text-center text-zinc-400">
                  {t('dashboard.admin.cards.noCards')}
                </div>
              ) : (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
                  {virtualCards.map((card) => (
                    <div 
                      key={card.id}
                      className="bg-gradient-to-br from-zinc-800 to-zinc-900 border-2 border-[#FFD60A]/50 rounded-xl p-5 cursor-pointer hover:border-[#FFD60A] transition-colors"
                      onClick={() => viewUserCard(card.id)}
                      data-testid={`card-${card.id}`}
                    >
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-2">
                          <Car className="w-6 h-6 text-[#FFD60A]" />
                          <span className="font-bold text-white text-sm">MÉTRO-TAXI</span>
                        </div>
                        <span className={`text-xs px-2 py-0.5 rounded ${
                          card.subscription_active 
                            ? 'bg-green-500/20 text-green-400' 
                            : 'bg-zinc-700 text-zinc-400'
                        }`}>
                          {card.subscription_active ? t('dashboard.admin.users.active').toUpperCase() : t('dashboard.admin.users.inactive').toUpperCase()}
                        </span>
                      </div>
                      <p className="text-white font-bold text-lg mb-1">{card.name}</p>
                      <p className="text-[#FFD60A] font-mono text-sm mb-3">{card.card_number}</p>
                      <div className="flex items-center gap-4 text-xs text-zinc-400">
                        <span className="flex items-center gap-1">
                          <Mail className="w-3 h-3" />
                          {card.email_verified ? '✓' : '✗'}
                        </span>
                        <span className="flex items-center gap-1">
                          <Phone className="w-3 h-3" />
                          {card.phone}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </TabsContent>

          {/* Regions Tab */}
          <TabsContent value="regions">
            <div className="bg-[#18181B] border border-zinc-800 rounded overflow-hidden">
              <div className="p-4 border-b border-zinc-800 flex justify-between items-center">
                <div>
                  <h2 className="text-xl font-bold text-white">{t('regions.admin.title', 'Region Management')}</h2>
                  <p className="text-zinc-400 text-sm">{t('regions.admin.subtitle', 'Create, activate or deactivate service regions')}</p>
                </div>
                <Button 
                  onClick={openCreateRegionDialog}
                  className="bg-[#FFD60A] text-black hover:bg-[#FFD60A]/90"
                  data-testid="create-region-btn"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  {t('regions.admin.create', 'Create Region')}
                </Button>
              </div>
              
              {loading ? (
                <div className="p-8 text-center">
                  <div className="w-8 h-8 border-4 border-[#FFD60A] border-t-transparent rounded-full animate-spin mx-auto"></div>
                </div>
              ) : regions.length === 0 ? (
                <div className="p-8 text-center text-zinc-400">
                  {t('regions.admin.noRegions', 'No regions configured')}
                </div>
              ) : (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
                  {regions.map((region) => (
                    <motion.div 
                      key={region.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`relative bg-zinc-900 border-2 rounded-xl p-5 ${
                        region.is_active ? 'border-green-500/50' : 'border-zinc-700'
                      }`}
                      data-testid={`region-card-${region.id}`}
                    >
                      {/* Status Badge */}
                      <div className="absolute top-3 right-3">
                        <span className={`text-xs px-2 py-1 rounded font-bold ${
                          region.is_active 
                            ? 'bg-green-500/20 text-green-400' 
                            : 'bg-zinc-700 text-zinc-400'
                        }`}>
                          {region.is_active ? t('regions.admin.active', 'Active') : t('regions.admin.inactive', 'Inactive')}
                        </span>
                      </div>
                      
                      {/* Region Info */}
                      <div className="flex items-center gap-3 mb-4">
                        <span className="text-4xl">{countryFlags[region.country] || '🌍'}</span>
                        <div>
                          <h3 className="font-bold text-white text-lg">{region.name}</h3>
                          <p className="text-zinc-400 text-sm">{region.id}</p>
                        </div>
                      </div>
                      
                      {/* Stats */}
                      <div className="grid grid-cols-2 gap-3 mb-4">
                        <div className="bg-zinc-800 rounded p-3">
                          <p className="text-2xl font-bold text-white">{region.driver_count || 0}</p>
                          <p className="text-xs text-zinc-400">{t('dashboard.admin.stats.drivers', 'Drivers')}</p>
                        </div>
                        <div className="bg-zinc-800 rounded p-3">
                          <p className="text-2xl font-bold text-white">{region.user_count || 0}</p>
                          <p className="text-xs text-zinc-400">{t('dashboard.admin.stats.users', 'Users')}</p>
                        </div>
                      </div>
                      
                      {/* Details */}
                      <div className="space-y-2 mb-4 text-sm">
                        <div className="flex justify-between">
                          <span className="text-zinc-400">{t('regions.admin.currency', 'Currency')}</span>
                          <span className="text-white font-medium">{region.currency}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-zinc-400">{t('regions.admin.language', 'Language')}</span>
                          <span className="text-white font-medium">{region.language.toUpperCase()}</span>
                        </div>
                        {region.launch_date && (
                          <div className="flex justify-between">
                            <span className="text-zinc-400">{t('regions.admin.launchDate', 'Launch Date')}</span>
                            <span className="text-white font-medium">{formatDate(region.launch_date)}</span>
                          </div>
                        )}
                      </div>
                      
                      {/* Actions */}
                      <div className="flex gap-2 pt-3 border-t border-zinc-800">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => openEditRegionDialog(region)}
                          className="flex-1"
                          data-testid={`edit-region-${region.id}`}
                        >
                          <Edit className="w-4 h-4 mr-1" />
                          {t('common.edit', 'Edit')}
                        </Button>
                        {region.is_active ? (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => deactivateRegion(region.id)}
                            className="flex-1 text-red-400 border-red-400/50 hover:bg-red-400/10"
                            data-testid={`deactivate-region-${region.id}`}
                          >
                            <PowerOff className="w-4 h-4 mr-1" />
                            {t('regions.admin.deactivate', 'Deactivate')}
                          </Button>
                        ) : (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => activateRegion(region.id)}
                            className="flex-1 text-green-400 border-green-400/50 hover:bg-green-400/10"
                            data-testid={`activate-region-${region.id}`}
                          >
                            <Power className="w-4 h-4 mr-1" />
                            {t('regions.admin.activate', 'Activate')}
                          </Button>
                        )}
                      </div>
                      
                      {/* Delete button (only if no drivers/users) */}
                      {(region.driver_count === 0 && region.user_count === 0) && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => deleteRegion(region.id)}
                          className="w-full mt-2 text-red-400 hover:bg-red-400/10"
                          data-testid={`delete-region-${region.id}`}
                        >
                          <Trash2 className="w-4 h-4 mr-1" />
                          {t('common.delete', 'Delete')}
                        </Button>
                      )}
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>

        {/* Card Detail Dialog */}
        <Dialog open={cardDialogOpen} onOpenChange={setCardDialogOpen}>
          <DialogContent className="bg-[#18181B] border-zinc-800 max-w-md">
            <DialogHeader>
              <DialogTitle className="text-white">{t('dashboard.admin.cards.title')}</DialogTitle>
            </DialogHeader>
            {selectedCard && (
              <div>
                {/* Virtual Card Display */}
                <div className="bg-gradient-to-br from-zinc-800 to-zinc-900 border-2 border-[#FFD60A] rounded-xl p-6 mb-6">
                  <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-2">
                      <Car className="w-8 h-8 text-[#FFD60A]" />
                      <span className="font-bold text-white">MÉTRO-TAXI</span>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded font-bold ${
                      selectedCard.subscription_active 
                        ? 'bg-green-500/20 text-green-400 border border-green-500/50' 
                        : 'bg-zinc-700 text-zinc-400'
                    }`}>
                      {selectedCard.subscription_active ? t('dashboard.admin.users.active').toUpperCase() : t('dashboard.admin.users.inactive').toUpperCase()}
                    </span>
                  </div>
                  
                  <p className="text-zinc-400 text-xs mb-1">{t('dashboard.admin.cards.holder')}</p>
                  <p className="text-white font-bold text-xl mb-4">{selectedCard.name}</p>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-zinc-400 text-xs mb-1">{t('dashboard.admin.cards.cardNumber')}</p>
                      <p className="text-[#FFD60A] font-mono text-sm">{selectedCard.card_number}</p>
                    </div>
                    <div>
                      <p className="text-zinc-400 text-xs mb-1">{t('dashboard.admin.cards.phone')}</p>
                      <p className="text-white text-sm">{selectedCard.phone}</p>
                    </div>
                  </div>
                  
                  {selectedCard.subscription_active && (
                    <div className="mt-4 pt-4 border-t border-zinc-700">
                      <div className="flex justify-between">
                        <div>
                          <p className="text-zinc-400 text-xs">{t('dashboard.admin.cards.subscription')}</p>
                          <p className="text-[#FFD60A] font-bold">
                            {selectedCard.subscription_plan === '24h' ? t('subscription.plans.day.name') :
                             selectedCard.subscription_plan === '1week' ? t('subscription.plans.week.name') :
                             selectedCard.subscription_plan === '1month' ? t('subscription.plans.month.name') : '-'}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-zinc-400 text-xs">{t('dashboard.admin.cards.expires')}</p>
                          <p className="text-white">{formatDate(selectedCard.subscription_expires)}</p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
                
                {/* Additional Info */}
                <div className="space-y-3">
                  <div className="flex items-center gap-3 p-3 bg-zinc-900 rounded">
                    <Mail className="w-5 h-5 text-zinc-400" />
                    <div className="flex-1">
                      <p className="text-zinc-400 text-xs">Email</p>
                      <p className="text-white text-sm">{selectedCard.email}</p>
                    </div>
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      selectedCard.email_verified ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                    }`}>
                      {selectedCard.email_verified ? t('dashboard.admin.cards.verified') : t('dashboard.admin.cards.notVerified')}
                    </span>
                  </div>
                  
                  <div className="flex items-center gap-3 p-3 bg-zinc-900 rounded">
                    <Calendar className="w-5 h-5 text-zinc-400" />
                    <div>
                      <p className="text-zinc-400 text-xs">{t('dashboard.admin.cards.memberSince')}</p>
                      <p className="text-white text-sm">{formatDate(selectedCard.created_at)}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-3 p-3 bg-zinc-900 rounded">
                    <MapPin className="w-5 h-5 text-zinc-400" />
                    <div>
                      <p className="text-zinc-400 text-xs">{t('dashboard.admin.cards.totalRides')}</p>
                      <p className="text-white text-sm">{selectedCard.total_rides || 0} {t('dashboard.admin.cards.rides')}</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* Region Create/Edit Dialog */}
        <Dialog open={regionDialogOpen} onOpenChange={setRegionDialogOpen}>
          <DialogContent className="bg-[#18181B] border-zinc-800 max-w-lg max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-white">
                {editingRegion 
                  ? t('regions.admin.editRegion', 'Edit Region') 
                  : t('regions.admin.createRegion', 'Create New Region')
                }
              </DialogTitle>
            </DialogHeader>
            
            <div className="space-y-4 py-4">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-zinc-300">{t('regions.admin.regionId', 'Region ID')} *</Label>
                  <Input
                    value={regionForm.id}
                    onChange={(e) => handleRegionFormChange('id', e.target.value.toLowerCase())}
                    placeholder="paris"
                    className="bg-zinc-900 border-zinc-700 text-white"
                    disabled={!!editingRegion}
                    data-testid="region-id-input"
                  />
                  <p className="text-xs text-zinc-500">{t('regions.admin.idHelp', 'Used in URLs (e.g., paris.metro-taxi.com)')}</p>
                </div>
                <div className="space-y-2">
                  <Label className="text-zinc-300">{t('regions.admin.regionName', 'Display Name')} *</Label>
                  <Input
                    value={regionForm.name}
                    onChange={(e) => handleRegionFormChange('name', e.target.value)}
                    placeholder="Île-de-France"
                    className="bg-zinc-900 border-zinc-700 text-white"
                    data-testid="region-name-input"
                  />
                </div>
              </div>
              
              {/* Country & Currency */}
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label className="text-zinc-300">{t('regions.admin.country', 'Country')}</Label>
                  <select
                    value={regionForm.country}
                    onChange={(e) => handleRegionFormChange('country', e.target.value)}
                    className="w-full h-10 px-3 rounded-md bg-zinc-900 border border-zinc-700 text-white"
                    data-testid="region-country-select"
                  >
                    <option value="FR">🇫🇷 France</option>
                    <option value="GB">🇬🇧 United Kingdom</option>
                    <option value="ES">🇪🇸 Spain</option>
                    <option value="DE">🇩🇪 Germany</option>
                    <option value="IT">🇮🇹 Italy</option>
                    <option value="PT">🇵🇹 Portugal</option>
                    <option value="NL">🇳🇱 Netherlands</option>
                    <option value="BE">🇧🇪 Belgium</option>
                    <option value="CH">🇨🇭 Switzerland</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <Label className="text-zinc-300">{t('regions.admin.currency', 'Currency')}</Label>
                  <select
                    value={regionForm.currency}
                    onChange={(e) => handleRegionFormChange('currency', e.target.value)}
                    className="w-full h-10 px-3 rounded-md bg-zinc-900 border border-zinc-700 text-white"
                    data-testid="region-currency-select"
                  >
                    <option value="EUR">EUR (€)</option>
                    <option value="GBP">GBP (£)</option>
                    <option value="CHF">CHF (Fr)</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <Label className="text-zinc-300">{t('regions.admin.language', 'Language')}</Label>
                  <select
                    value={regionForm.language}
                    onChange={(e) => handleRegionFormChange('language', e.target.value)}
                    className="w-full h-10 px-3 rounded-md bg-zinc-900 border border-zinc-700 text-white"
                    data-testid="region-language-select"
                  >
                    <option value="fr">Français</option>
                    <option value="en">English</option>
                    <option value="es">Español</option>
                    <option value="de">Deutsch</option>
                    <option value="it">Italiano</option>
                    <option value="pt">Português</option>
                    <option value="nl">Nederlands</option>
                  </select>
                </div>
              </div>
              
              {/* Geographic Bounds */}
              <div className="space-y-3">
                <Label className="text-zinc-300">{t('regions.admin.bounds', 'Geographic Bounds')}</Label>
                <p className="text-xs text-zinc-500">{t('regions.admin.boundsHelp', 'Define the area where the service is available')}</p>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label className="text-xs text-zinc-400">North (Lat)</Label>
                    <Input
                      type="number"
                      step="0.0001"
                      value={regionForm.bounds.north}
                      onChange={(e) => handleRegionFormChange('bounds.north', e.target.value)}
                      className="bg-zinc-900 border-zinc-700 text-white"
                      placeholder="49.24"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs text-zinc-400">South (Lat)</Label>
                    <Input
                      type="number"
                      step="0.0001"
                      value={regionForm.bounds.south}
                      onChange={(e) => handleRegionFormChange('bounds.south', e.target.value)}
                      className="bg-zinc-900 border-zinc-700 text-white"
                      placeholder="48.12"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs text-zinc-400">East (Lng)</Label>
                    <Input
                      type="number"
                      step="0.0001"
                      value={regionForm.bounds.east}
                      onChange={(e) => handleRegionFormChange('bounds.east', e.target.value)}
                      className="bg-zinc-900 border-zinc-700 text-white"
                      placeholder="3.56"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs text-zinc-400">West (Lng)</Label>
                    <Input
                      type="number"
                      step="0.0001"
                      value={regionForm.bounds.west}
                      onChange={(e) => handleRegionFormChange('bounds.west', e.target.value)}
                      className="bg-zinc-900 border-zinc-700 text-white"
                      placeholder="1.45"
                    />
                  </div>
                </div>
              </div>
              
              {/* Save Button */}
              <div className="flex gap-3 pt-4">
                <Button
                  variant="outline"
                  onClick={() => setRegionDialogOpen(false)}
                  className="flex-1"
                >
                  {t('common.cancel', 'Cancel')}
                </Button>
                <Button
                  onClick={saveRegion}
                  disabled={savingRegion}
                  className="flex-1 bg-[#FFD60A] text-black hover:bg-[#FFD60A]/90"
                  data-testid="save-region-btn"
                >
                  {savingRegion ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Save className="w-4 h-4 mr-2" />
                  )}
                  {editingRegion ? t('common.save', 'Save') : t('regions.admin.create', 'Create')}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default AdminDashboard;
