import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup, useMap, Circle } from 'react-leaflet';
import L from 'leaflet';
import { motion, AnimatePresence } from 'framer-motion';
import { Car, User, LogOut, Menu, X, Power, MapPin, Check, XCircle, Users, Navigation } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import 'leaflet/dist/leaflet.css';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Fix Leaflet default marker icon
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom icons
const driverIcon = L.divIcon({
  className: 'custom-icon',
  html: '<div style="background:#FFD60A;border:2px solid #000;border-radius:50%;width:20px;height:20px;"></div>',
  iconSize: [20, 20],
  iconAnchor: [10, 10],
});

const userRequestIcon = L.divIcon({
  className: 'custom-icon',
  html: '<div style="background:#3B82F6;border:2px solid white;border-radius:50%;width:16px;height:16px;animation:pulse 2s infinite;"></div>',
  iconSize: [16, 16],
  iconAnchor: [8, 8],
});

// Map component that updates center
const MapUpdater = ({ center }) => {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.setView(center, map.getZoom());
    }
  }, [center, map]);
  return null;
};

const DriverDashboard = () => {
  const { driver, token, logout, refreshUser } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [menuOpen, setMenuOpen] = useState(false);
  const [driverLocation, setDriverLocation] = useState(null);
  const [isActive, setIsActive] = useState(driver?.is_active || false);
  const [pendingRides, setPendingRides] = useState([]);
  const [activeRide, setActiveRide] = useState(null);
  const [loading, setLoading] = useState(false);
  const [availableSeats, setAvailableSeats] = useState(driver?.seats || 4);

  // Paris center as default
  const defaultCenter = [48.8566, 2.3522];

  // Get driver location and update
  useEffect(() => {
    if (navigator.geolocation) {
      const watchId = navigator.geolocation.watchPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          setDriverLocation([latitude, longitude]);
          if (isActive) {
            updateDriverLocation(latitude, longitude);
          }
        },
        (error) => {
          console.error('Geolocation error:', error);
          setDriverLocation(defaultCenter);
        },
        { enableHighAccuracy: true, maximumAge: 5000 }
      );

      return () => navigator.geolocation.clearWatch(watchId);
    } else {
      setDriverLocation(defaultCenter);
    }
  }, [isActive]);

  const updateDriverLocation = async (lat, lng) => {
    try {
      await axios.post(`${API}/drivers/location`, {
        latitude: lat,
        longitude: lng,
        available_seats: availableSeats
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
    } catch (error) {
      console.error('Location update error:', error);
    }
  };

  // Fetch pending rides
  const fetchPendingRides = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/rides/pending`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPendingRides(response.data.rides || []);
    } catch (error) {
      console.error('Fetch rides error:', error);
    }
  }, [token]);

  // Fetch active ride
  const fetchActiveRide = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/rides/active`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setActiveRide(response.data.ride);
    } catch (error) {
      console.error('Fetch active ride error:', error);
    }
  }, [token]);

  useEffect(() => {
    if (isActive) {
      fetchPendingRides();
      fetchActiveRide();
      const interval = setInterval(() => {
        fetchPendingRides();
        fetchActiveRide();
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [isActive, fetchPendingRides, fetchActiveRide]);

  const toggleActive = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/drivers/toggle-active`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setIsActive(response.data.is_active);
      toast.success(response.data.is_active ? 'Vous êtes maintenant en ligne !' : 'Vous êtes hors ligne');
      
      if (response.data.is_active && driverLocation) {
        updateDriverLocation(driverLocation[0], driverLocation[1]);
      }
    } catch (error) {
      toast.error('Erreur lors du changement de statut');
    } finally {
      setLoading(false);
    }
  };

  const acceptRide = async (rideId) => {
    setLoading(true);
    try {
      await axios.post(`${API}/rides/${rideId}/accept`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Trajet accepté !');
      fetchPendingRides();
      fetchActiveRide();
      setAvailableSeats(prev => Math.max(0, prev - 1));
    } catch (error) {
      toast.error('Erreur lors de l\'acceptation');
    } finally {
      setLoading(false);
    }
  };

  const rejectRide = async (rideId) => {
    setLoading(true);
    try {
      await axios.post(`${API}/rides/${rideId}/reject`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.info('Demande refusée');
      fetchPendingRides();
    } catch (error) {
      toast.error('Erreur lors du refus');
    } finally {
      setLoading(false);
    }
  };

  const completeRide = async (rideId) => {
    setLoading(true);
    try {
      await axios.post(`${API}/rides/${rideId}/complete`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Trajet terminé !');
      setActiveRide(null);
      setAvailableSeats(prev => Math.min(driver?.seats || 4, prev + 1));
      fetchActiveRide();
    } catch (error) {
      toast.error('Erreur lors de la complétion');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="h-screen w-full bg-[#09090B] relative overflow-hidden">
      {/* Header */}
      <header className="absolute top-0 left-0 right-0 z-[1000] glass-panel">
        <div className="flex justify-between items-center px-4 py-3">
          <div className="flex items-center gap-2">
            <Car className="w-6 h-6 text-[#FFD60A]" />
            <span className="text-lg font-bold text-white">{t('dashboard.driver.title').toUpperCase()}</span>
          </div>
          
          <div className="flex items-center gap-2">
            <span className={`text-xs px-2 py-1 rounded ${
              isActive 
                ? 'bg-green-500/20 text-green-400 border border-green-500/50' 
                : 'bg-zinc-700/50 text-zinc-400 border border-zinc-600'
            }`}>
              {isActive ? t('dashboard.driver.online') : t('dashboard.driver.offline')}
            </span>
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="text-white p-2 hover:bg-zinc-800 rounded"
              data-testid="driver-menu-toggle"
            >
              {menuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </header>

      {/* Side Menu */}
      <AnimatePresence>
        {menuOpen && (
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25 }}
            className="absolute top-0 right-0 h-full w-72 bg-[#18181B] z-[1001] border-l border-zinc-800"
          >
            <div className="p-6 pt-20">
              <div className="flex items-center gap-3 mb-8 pb-6 border-b border-zinc-800">
                <div className="w-12 h-12 bg-[#FFD60A] rounded-full flex items-center justify-center">
                  <User className="w-6 h-6 text-black" />
                </div>
                <div>
                  <p className="font-bold text-white">{driver?.first_name} {driver?.last_name}</p>
                  <p className="text-sm text-zinc-400 font-mono">{driver?.vehicle_plate}</p>
                </div>
              </div>
              
              <div className="space-y-4 mb-6">
                <div className="bg-zinc-900 p-4 rounded border border-zinc-800">
                  <p className="text-zinc-400 text-sm">{t('dashboard.user.vehicle')}</p>
                  <p className="text-white font-medium">{driver?.vehicle_type}</p>
                </div>
                <div className="bg-zinc-900 p-4 rounded border border-zinc-800">
                  <p className="text-zinc-400 text-sm">{t('dashboard.driver.availableSeats')}</p>
                  <p className="text-[#FFD60A] font-bold text-2xl">{availableSeats} / {driver?.seats}</p>
                </div>
              </div>
              
              <Button 
                variant="ghost" 
                className="w-full justify-start text-red-400 hover:bg-red-500/10 hover:text-red-400"
                onClick={handleLogout}
                data-testid="driver-logout-btn"
              >
                <LogOut className="w-5 h-5 mr-3" />
                {t('nav.logout')}
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Map */}
      <MapContainer
        center={driverLocation || defaultCenter}
        zoom={15}
        className="h-full w-full z-0"
        zoomControl={false}
      >
        <TileLayer
          attribution='&copy; OpenStreetMap'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MapUpdater center={driverLocation} />
        
        {/* Driver location */}
        {driverLocation && (
          <>
            <Marker position={driverLocation} icon={driverIcon}>
              <Popup>
                <div className="text-center p-2">
                  <p className="font-bold">{t('dashboard.user.yourPosition')}</p>
                  <p className="text-sm text-zinc-600">{availableSeats} {t('dashboard.user.freeSeats')}</p>
                </div>
              </Popup>
            </Marker>
            <Circle 
              center={driverLocation} 
              radius={50} 
              pathOptions={{ color: '#FFD60A', fillColor: '#FFD60A', fillOpacity: 0.2 }}
            />
          </>
        )}

        {/* Pending ride requests */}
        {pendingRides.map((ride) => (
          <Marker 
            key={ride.id} 
            position={[ride.pickup_lat, ride.pickup_lng]}
            icon={userRequestIcon}
          >
            <Popup>
              <div className="p-2 min-w-[180px]">
                <p className="font-bold">{ride.user_name}</p>
                <p className="text-xs text-zinc-500">{t('dashboard.driver.pendingRequests')}</p>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      {/* Toggle Active Button */}
      <div className="absolute top-20 left-4 z-[1000]">
        <Button
          onClick={toggleActive}
          disabled={loading || !driver?.is_validated}
          className={`h-14 px-6 font-bold ${
            isActive 
              ? 'bg-red-500 hover:bg-red-600 text-white' 
              : 'bg-[#FFD60A] hover:bg-[#E6C209] text-black'
          }`}
          data-testid="toggle-active-btn"
        >
          <Power className="w-5 h-5 mr-2" />
          {isActive ? t('dashboard.driver.goOffline').toUpperCase() : t('dashboard.driver.goOnline').toUpperCase()}
        </Button>
        
        {!driver?.is_validated && (
          <p className="text-yellow-500 text-xs mt-2 bg-yellow-500/10 px-3 py-1 rounded">
            {t('dashboard.admin.drivers.pending')}
          </p>
        )}
      </div>

      {/* Pending Rides Panel */}
      <AnimatePresence>
        {pendingRides.length > 0 && (
          <motion.div
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            className="absolute bottom-0 left-0 right-0 z-[1000] bg-[#18181B] border-t border-zinc-800 max-h-[40vh] overflow-y-auto"
          >
            <div className="p-4">
              <h3 className="font-bold text-white text-lg mb-4">
                {t('dashboard.driver.pendingRequests')} ({pendingRides.length})
              </h3>
              
              <div className="space-y-3">
                {pendingRides.map((ride) => (
                  <div key={ride.id} className="bg-zinc-900 p-4 rounded border border-zinc-800">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <p className="font-bold text-white">{ride.user_name}</p>
                        <p className="text-xs text-zinc-500 font-mono">ID: {ride.id.slice(0, 8)}</p>
                      </div>
                      <div className="flex items-center gap-1 text-zinc-400">
                        <MapPin className="w-4 h-4" />
                        <span className="text-xs">{t('dashboard.driver.nearbyUsers')}</span>
                      </div>
                    </div>
                    
                    <div className="flex gap-2">
                      <Button
                        onClick={() => acceptRide(ride.id)}
                        disabled={loading}
                        className="flex-1 bg-green-600 hover:bg-green-700 text-white"
                        data-testid={`accept-ride-${ride.id}`}
                      >
                        <Check className="w-4 h-4 mr-2" />
                        {t('dashboard.driver.accept')}
                      </Button>
                      <Button
                        onClick={() => rejectRide(ride.id)}
                        disabled={loading}
                        variant="outline"
                        className="flex-1 border-zinc-700 text-zinc-300 hover:bg-zinc-800"
                        data-testid={`reject-ride-${ride.id}`}
                      >
                        <XCircle className="w-4 h-4 mr-2" />
                        {t('dashboard.driver.decline')}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Active Ride Panel */}
      <AnimatePresence>
        {activeRide && (
          <motion.div
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            className="ride-panel"
          >
            <div className="max-w-lg mx-auto">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-bold text-white text-lg">{t('dashboard.driver.currentRide')}</h3>
                <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded border border-green-500/50">
                  {t('dashboard.user.inProgress')}
                </span>
              </div>
              
              <div className="flex items-center gap-4 mb-4">
                <div className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center">
                  <User className="w-6 h-6 text-white" />
                </div>
                <div className="flex-1">
                  <p className="text-white font-bold">{activeRide.user_name}</p>
                  <p className="text-zinc-400 text-sm font-mono">ID: {activeRide.id.slice(0, 8)}</p>
                </div>
              </div>
              
              <Button
                onClick={() => completeRide(activeRide.id)}
                disabled={loading}
                className="w-full bg-green-600 hover:bg-green-700 text-white font-bold h-12"
                data-testid="complete-ride-btn"
              >
                <Check className="w-5 h-5 mr-2" />
                {t('dashboard.driver.completeRide').toUpperCase()}
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Stats indicator */}
      <div className="absolute bottom-24 left-4 z-[1000] glass-panel px-4 py-2 rounded">
        <div className="flex items-center gap-4 text-white">
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-[#FFD60A]" />
            <span className="text-sm">{availableSeats} {t('dashboard.user.seats')}</span>
          </div>
          {isActive && (
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-sm text-green-400">{t('dashboard.driver.online')}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DriverDashboard;
