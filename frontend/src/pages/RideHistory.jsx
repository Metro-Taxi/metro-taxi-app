import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  MapPin, Calendar, Clock, Car, Star, ChevronLeft, ChevronRight,
  Filter, X, User, Navigation
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';
import axios from 'axios';
import { useTranslation } from 'react-i18next';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const RideHistory = ({ onClose }) => {
  const { token } = useAuth();
  const { t, i18n } = useTranslation();
  const [rides, setRides] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filter, setFilter] = useState({ status: '' });
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    fetchRides();
  }, [page, filter]);

  const fetchRides = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: page.toString(),
        limit: '10'
      });
      
      if (filter.status) {
        params.append('status', filter.status);
      }

      const response = await axios.get(`${API}/rides/history?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setRides(response.data.rides);
      setTotalPages(response.data.pages);
    } catch (error) {
      toast.error(t('rideHistory.fetchError', 'Error loading ride history'));
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString(i18n.language, {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'bg-green-500/20 text-green-400';
      case 'cancelled': return 'bg-red-500/20 text-red-400';
      case 'in_progress': return 'bg-blue-500/20 text-blue-400';
      default: return 'bg-yellow-500/20 text-yellow-400';
    }
  };

  const getStatusLabel = (status) => {
    const labels = {
      completed: t('rideHistory.statusCompleted', 'Completed'),
      cancelled: t('rideHistory.statusCancelled', 'Cancelled'),
      in_progress: t('rideHistory.statusInProgress', 'In Progress'),
      pending: t('rideHistory.statusPending', 'Pending'),
      accepted: t('rideHistory.statusAccepted', 'Accepted')
    };
    return labels[status] || status;
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="bg-[#18181B] border border-zinc-800 rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden"
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-[#FFD60A] to-[#FFE55C] p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-black rounded-xl flex items-center justify-center">
                <Navigation className="w-6 h-6 text-[#FFD60A]" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-black">
                  {t('rideHistory.title', 'Ride History')}
                </h2>
                <p className="text-black/70 text-sm">
                  {t('rideHistory.subtitle', 'View all your past rides')}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setShowFilters(!showFilters)}
                className="bg-black/10 hover:bg-black/20 text-black"
              >
                <Filter className="w-5 h-5" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={onClose}
                className="bg-black/10 hover:bg-black/20 text-black"
              >
                <X className="w-5 h-5" />
              </Button>
            </div>
          </div>

          {/* Filters */}
          {showFilters && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              className="mt-4 flex gap-2 flex-wrap"
            >
              {['', 'completed', 'cancelled', 'in_progress'].map((status) => (
                <button
                  key={status}
                  onClick={() => { setFilter({ status }); setPage(1); }}
                  className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                    filter.status === status
                      ? 'bg-black text-[#FFD60A]'
                      : 'bg-black/20 text-black hover:bg-black/30'
                  }`}
                >
                  {status === '' ? t('rideHistory.filterAll', 'All') : getStatusLabel(status)}
                </button>
              ))}
            </motion.div>
          )}
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-2 border-[#FFD60A] border-t-transparent rounded-full animate-spin" />
            </div>
          ) : rides.length === 0 ? (
            <div className="text-center py-12">
              <Navigation className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
              <p className="text-zinc-400">{t('rideHistory.noRides', 'No rides found')}</p>
            </div>
          ) : (
            <div className="space-y-4">
              {rides.map((ride, index) => (
                <motion.div
                  key={ride.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 hover:border-zinc-700 transition-colors"
                >
                  <div className="flex items-start justify-between gap-4">
                    {/* Left: Route info */}
                    <div className="flex-1">
                      <div className="flex items-start gap-3">
                        <div className="flex flex-col items-center">
                          <div className="w-3 h-3 rounded-full bg-green-500" />
                          <div className="w-0.5 h-8 bg-zinc-700" />
                          <div className="w-3 h-3 rounded-full bg-red-500" />
                        </div>
                        <div className="flex-1">
                          <p className="text-white text-sm font-medium">
                            {ride.pickup_address || `${ride.pickup_location?.lat?.toFixed(4)}, ${ride.pickup_location?.lng?.toFixed(4)}`}
                          </p>
                          <p className="text-zinc-400 text-xs mt-4">
                            {ride.destination_address || `${ride.destination?.lat?.toFixed(4)}, ${ride.destination?.lng?.toFixed(4)}`}
                          </p>
                        </div>
                      </div>

                      {/* Driver info */}
                      {ride.driver_name && (
                        <div className="flex items-center gap-2 mt-3 pl-6">
                          <div className="w-8 h-8 bg-[#FFD60A] rounded-full flex items-center justify-center">
                            <Car className="w-4 h-4 text-black" />
                          </div>
                          <div>
                            <p className="text-white text-sm">{ride.driver_name}</p>
                            {ride.vehicle_plate && (
                              <p className="text-zinc-500 text-xs font-mono">{ride.vehicle_plate}</p>
                            )}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Right: Status and date */}
                    <div className="text-right">
                      <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(ride.status)}`}>
                        {getStatusLabel(ride.status)}
                      </span>
                      <p className="text-zinc-500 text-xs mt-2">
                        <Calendar className="w-3 h-3 inline mr-1" />
                        {formatDate(ride.created_at)}
                      </p>
                      {ride.distance_km && (
                        <p className="text-zinc-500 text-xs mt-1">
                          <MapPin className="w-3 h-3 inline mr-1" />
                          {ride.distance_km.toFixed(1)} km
                        </p>
                      )}
                      
                      {/* Rating */}
                      {ride.rating && (
                        <div className="flex items-center justify-end gap-1 mt-2">
                          {[...Array(5)].map((_, i) => (
                            <Star
                              key={i}
                              className={`w-3 h-3 ${
                                i < ride.rating.rating ? 'text-[#FFD60A] fill-[#FFD60A]' : 'text-zinc-600'
                              }`}
                            />
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="border-t border-zinc-800 p-4 flex items-center justify-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="text-zinc-400"
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <span className="text-zinc-400 text-sm">
              {t('rideHistory.page', 'Page')} {page} / {totalPages}
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="text-zinc-400"
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        )}
      </motion.div>
    </motion.div>
  );
};

export default RideHistory;
