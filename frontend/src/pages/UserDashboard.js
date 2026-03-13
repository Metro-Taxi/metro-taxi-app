import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup, useMap, Circle, Polyline } from 'react-leaflet';
import L from 'leaflet';
import { motion, AnimatePresence } from 'framer-motion';
import { Car, User, MapPin, LogOut, CreditCard, Menu, X, Navigation, Users, ArrowRight, RefreshCw, Mail, CheckCircle, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';
import axios from 'axios';
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
const userIcon = L.divIcon({
  className: 'custom-icon',
  html: '<div class="user-marker"></div>',
  iconSize: [16, 16],
  iconAnchor: [8, 8],
});

const driverIcon = L.divIcon({
  className: 'custom-icon',
  html: '<div style="background:#FFD60A;border:2px solid #000;border-radius:4px;width:28px;height:28px;display:flex;align-items:center;justify-content:center;"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="2"><path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9L18 10l-2-4H8L6 10l-2.5 1.1C2.7 11.3 2 12.1 2 13v3c0 .6.4 1 1 1h2"/><circle cx="7" cy="17" r="2"/><path d="M9 17h6"/><circle cx="17" cy="17" r="2"/></svg></div>',
  iconSize: [28, 28],
  iconAnchor: [14, 14],
});

const transferIcon = L.divIcon({
  className: 'custom-icon',
  html: '<div style="background:#3B82F6;border:2px solid white;border-radius:50%;width:16px;height:16px;"></div>',
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

const UserDashboard = () => {
  const { user, token, logout, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const [userLocation, setUserLocation] = useState(null);
  const [drivers, setDrivers] = useState([]);
  const [selectedDriver, setSelectedDriver] = useState(null);
  const [destination, setDestination] = useState(null);
  const [activeRide, setActiveRide] = useState(null);
  const [loading, setLoading] = useState(false);
  const [transfers, setTransfers] = useState([]);
  const [showTransfers, setShowTransfers] = useState(false);
  const [rideProgress, setRideProgress] = useState(null);
  const [emailVerified, setEmailVerified] = useState(true);

  // Paris center as default
  const defaultCenter = [48.8566, 2.3522];

  // Get user location
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          setUserLocation([latitude, longitude]);
          updateUserLocation(latitude, longitude);
        },
        (error) => {
          console.error('Geolocation error:', error);
          setUserLocation(defaultCenter);
        },
        { enableHighAccuracy: true }
      );
    } else {
      setUserLocation(defaultCenter);
    }
  }, []);

  const updateUserLocation = async (lat, lng) => {
    try {
      await axios.post(`${API}/users/location`, 
        { latitude: lat, longitude: lng },
        { headers: { Authorization: `Bearer ${token}` } }
      );
    } catch (error) {
      console.error('Location update error:', error);
    }
  };

  // Fetch available drivers
  const fetchDrivers = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/drivers/available`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDrivers(response.data.drivers || []);
    } catch (error) {
      console.error('Fetch drivers error:', error);
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
    fetchDrivers();
    fetchActiveRide();
    const interval = setInterval(() => {
      fetchDrivers();
      fetchActiveRide();
    }, 5000);
    return () => clearInterval(interval);
  }, [fetchDrivers, fetchActiveRide]);

  const handleDriverSelect = (driver) => {
    if (!user?.subscription_active) {
      toast.error('Abonnement requis pour demander un trajet');
      navigate('/subscription');
      return;
    }
    setSelectedDriver(driver);
  };

  const handleRequestRide = async () => {
    if (!selectedDriver || !userLocation) return;
    
    setLoading(true);
    try {
      const response = await axios.post(`${API}/rides/request`, {
        driver_id: selectedDriver.id,
        pickup_lat: userLocation[0],
        pickup_lng: userLocation[1],
        destination_lat: destination ? destination[0] : selectedDriver.destination?.lat || userLocation[0] + 0.01,
        destination_lng: destination ? destination[1] : selectedDriver.destination?.lng || userLocation[1] + 0.01
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setActiveRide(response.data.ride);
      setSelectedDriver(null);
      toast.success('Demande envoyée au chauffeur !');
    } catch (error) {
      const message = error.response?.data?.detail || 'Erreur lors de la demande';
      toast.error(message);
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
            <span className="text-lg font-bold text-white">MÉTRO-TAXI</span>
          </div>
          
          <div className="flex items-center gap-2">
            {user?.subscription_active ? (
              <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded border border-green-500/50">
                Abonné
              </span>
            ) : (
              <Link to="/subscription">
                <span className="text-xs bg-[#FFD60A]/20 text-[#FFD60A] px-2 py-1 rounded border border-[#FFD60A]/50 cursor-pointer">
                  S'abonner
                </span>
              </Link>
            )}
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="text-white p-2 hover:bg-zinc-800 rounded"
              data-testid="menu-toggle-btn"
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
                  <p className="font-bold text-white">{user?.first_name} {user?.last_name}</p>
                  <p className="text-sm text-zinc-400">{user?.email}</p>
                </div>
              </div>
              
              <nav className="space-y-2">
                <Link to="/profile" onClick={() => setMenuOpen(false)}>
                  <Button variant="ghost" className="w-full justify-start text-white hover:bg-zinc-800" data-testid="profile-link">
                    <User className="w-5 h-5 mr-3" />
                    Mon Profil
                  </Button>
                </Link>
                <Link to="/subscription" onClick={() => setMenuOpen(false)}>
                  <Button variant="ghost" className="w-full justify-start text-white hover:bg-zinc-800" data-testid="subscription-link">
                    <CreditCard className="w-5 h-5 mr-3" />
                    Abonnement
                  </Button>
                </Link>
                <Button 
                  variant="ghost" 
                  className="w-full justify-start text-red-400 hover:bg-red-500/10 hover:text-red-400"
                  onClick={handleLogout}
                  data-testid="logout-btn"
                >
                  <LogOut className="w-5 h-5 mr-3" />
                  Déconnexion
                </Button>
              </nav>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Map */}
      <MapContainer
        center={userLocation || defaultCenter}
        zoom={14}
        className="h-full w-full z-0"
        zoomControl={false}
      >
        <TileLayer
          attribution='&copy; OpenStreetMap'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MapUpdater center={userLocation} />
        
        {/* User location */}
        {userLocation && (
          <>
            <Marker position={userLocation} icon={userIcon}>
              <Popup className="custom-popup">
                <div className="text-center p-2">
                  <p className="font-bold">Votre position</p>
                </div>
              </Popup>
            </Marker>
            <Circle 
              center={userLocation} 
              radius={100} 
              pathOptions={{ color: '#3B82F6', fillColor: '#3B82F6', fillOpacity: 0.1 }}
            />
          </>
        )}
        
        {/* Drivers */}
        {drivers.map((driver) => (
          <Marker 
            key={driver.id} 
            position={[driver.location.lat, driver.location.lng]}
            icon={driverIcon}
            eventHandlers={{
              click: () => handleDriverSelect(driver)
            }}
          >
            <Popup>
              <div className="p-2 min-w-[180px]">
                <p className="font-bold text-lg">{driver.first_name}</p>
                <p className="text-sm text-zinc-600 font-mono">{driver.vehicle_plate}</p>
                <p className="text-sm">{driver.vehicle_type}</p>
                <div className="flex items-center gap-1 mt-2 text-[#FFD60A]">
                  <Users className="w-4 h-4" />
                  <span>{driver.available_seats} places libres</span>
                </div>
                {driver.destination && (
                  <div className="flex items-center gap-1 mt-1 text-zinc-500">
                    <Navigation className="w-4 h-4" />
                    <span className="text-xs">Direction définie</span>
                  </div>
                )}
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      {/* Bottom Panel - Active Ride */}
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
                <h3 className="font-bold text-white text-lg">Trajet en cours</h3>
                <span className={`text-xs px-2 py-1 rounded ${
                  activeRide.status === 'accepted' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'
                }`}>
                  {activeRide.status === 'accepted' ? 'Accepté' : 'En attente'}
                </span>
              </div>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-[#FFD60A] rounded flex items-center justify-center">
                  <Car className="w-6 h-6 text-black" />
                </div>
                <div className="flex-1">
                  <p className="text-white font-medium">
                    {activeRide.status === 'accepted' ? 'Le chauffeur arrive !' : 'En attente de confirmation...'}
                  </p>
                  <p className="text-zinc-400 text-sm">ID: {activeRide.id.slice(0, 8)}</p>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Bottom Panel - Driver Selection */}
      <AnimatePresence>
        {selectedDriver && !activeRide && (
          <motion.div
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            className="ride-panel"
          >
            <div className="max-w-lg mx-auto">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-bold text-white text-lg">Demander un trajet</h3>
                <button 
                  onClick={() => setSelectedDriver(null)}
                  className="text-zinc-400 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              <div className="flex items-center gap-4 mb-4">
                <div className="w-14 h-14 bg-[#FFD60A] rounded flex items-center justify-center">
                  <Car className="w-7 h-7 text-black" />
                </div>
                <div className="flex-1">
                  <p className="text-white font-bold text-lg">{selectedDriver.first_name}</p>
                  <p className="text-zinc-400 font-mono">{selectedDriver.vehicle_plate}</p>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-sm text-zinc-500">{selectedDriver.vehicle_type}</span>
                    <span className="text-sm text-[#FFD60A]">{selectedDriver.available_seats} places</span>
                  </div>
                </div>
              </div>
              
              <Button
                onClick={handleRequestRide}
                disabled={loading}
                className="w-full bg-[#FFD60A] text-black font-bold h-14 hover:bg-[#E6C209] btn-press"
                data-testid="request-ride-btn"
              >
                {loading ? (
                  <div className="w-5 h-5 border-2 border-black border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    DEMANDER CE TRAJET
                    <ArrowRight className="w-5 h-5 ml-2" />
                  </>
                )}
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Drivers count indicator */}
      <div className="absolute bottom-24 left-4 z-[1000] glass-panel px-4 py-2 rounded">
        <div className="flex items-center gap-2 text-white">
          <Car className="w-4 h-4 text-[#FFD60A]" />
          <span className="text-sm">{drivers.length} véhicules disponibles</span>
        </div>
      </div>
    </div>
  );
};

export default UserDashboard;
