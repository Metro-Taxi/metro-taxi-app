import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup, useMap, useMapEvents, Circle, Polyline } from 'react-leaflet';
import L from 'leaflet';
import { motion, AnimatePresence } from 'framer-motion';
import { Car, User, MapPin, LogOut, CreditCard, Menu, X, Navigation, Users, ArrowRight, RefreshCw, Mail, Clock, Route, Compass } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
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
const userIcon = L.divIcon({
  className: 'custom-icon',
  html: '<div class="user-marker"></div>',
  iconSize: [16, 16],
  iconAnchor: [8, 8],
});

// Create driver icon with direction arrow
const createDriverIcon = (bearing, seats) => {
  const rotation = bearing ? `transform: rotate(${bearing}deg);` : '';
  const seatColor = seats > 2 ? '#22C55E' : seats > 0 ? '#FFD60A' : '#EF4444';
  return L.divIcon({
    className: 'custom-icon',
    html: `<div style="position:relative;">
      <div style="background:#FFD60A;border:2px solid #000;border-radius:4px;width:32px;height:32px;display:flex;align-items:center;justify-content:center;">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="2"><path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9L18 10l-2-4H8L6 10l-2.5 1.1C2.7 11.3 2 12.1 2 13v3c0 .6.4 1 1 1h2"/><circle cx="7" cy="17" r="2"/><path d="M9 17h6"/><circle cx="17" cy="17" r="2"/></svg>
      </div>
      ${bearing ? `<div style="position:absolute;top:-12px;left:50%;transform:translateX(-50%) ${rotation};"><svg width="14" height="14" viewBox="0 0 24 24" fill="#FFD60A"><path d="M12 2l7 20-7-5-7 5z"/></svg></div>` : ''}
      <div style="position:absolute;bottom:-6px;right:-6px;background:${seatColor};border-radius:50%;width:16px;height:16px;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:bold;color:black;">${seats}</div>
    </div>`,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
  });
};

const transferIcon = L.divIcon({
  className: 'custom-icon',
  html: '<div style="background:#3B82F6;border:2px solid white;border-radius:50%;width:20px;height:20px;display:flex;align-items:center;justify-content:center;"><svg width="12" height="12" viewBox="0 0 24 24" fill="white"><path d="M7 16V4m0 0L3 8m4-4l4 4M17 8v12m0 0l4-4m-4 4l-4-4"/></svg></div>',
  iconSize: [20, 20],
  iconAnchor: [10, 10],
});

const destinationIcon = L.divIcon({
  className: 'custom-icon',
  html: '<div style="background:#EF4444;border:2px solid white;border-radius:50%;width:16px;height:16px;"></div>',
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

// Map click handler component
const MapClickHandler = ({ onMapClick, isActive }) => {
  const map = useMapEvents({
    click: (e) => {
      if (isActive && onMapClick) {
        onMapClick(e);
      }
    },
  });
  return null;
};

const UserDashboard = () => {
  const { user, token, logout, refreshUser } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslation();
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
  const [optimalRoute, setOptimalRoute] = useState(null);
  const [networkStatus, setNetworkStatus] = useState(null);
  const [showDestinationPicker, setShowDestinationPicker] = useState(false);

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
      if (response.data.ride) {
        setRideProgress(response.data.ride.progress_percent || 0);
      }
    } catch (error) {
      console.error('Fetch active ride error:', error);
    }
  }, [token]);

  // Check email verification status
  const checkEmailVerification = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/auth/verification-status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setEmailVerified(response.data.email_verified);
    } catch (error) {
      console.error('Email verification check error:', error);
    }
  }, [token]);

  // Fetch transfer suggestions
  const fetchTransfers = useCallback(async () => {
    if (!userLocation || !destination) return;
    
    try {
      const response = await axios.post(`${API}/matching/transfers`, {
        user_lat: userLocation[0],
        user_lng: userLocation[1],
        dest_lat: destination[0],
        dest_lng: destination[1]
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTransfers(response.data.transfers || []);
    } catch (error) {
      console.error('Fetch transfers error:', error);
    }
  }, [token, userLocation, destination]);

  // Fetch optimal route with segments
  const fetchOptimalRoute = useCallback(async () => {
    if (!userLocation || !destination) return;
    
    try {
      const response = await axios.post(`${API}/matching/optimal-route`, {
        user_lat: userLocation[0],
        user_lng: userLocation[1],
        dest_lat: destination[0],
        dest_lng: destination[1]
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setOptimalRoute(response.data.route);
    } catch (error) {
      console.error('Fetch optimal route error:', error);
    }
  }, [token, userLocation, destination]);

  // Fetch network status
  const fetchNetworkStatus = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/matching/network-status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setNetworkStatus(response.data);
    } catch (error) {
      console.error('Fetch network status error:', error);
    }
  }, [token]);

  useEffect(() => {
    fetchDrivers();
    fetchActiveRide();
    checkEmailVerification();
    fetchNetworkStatus();
    const interval = setInterval(() => {
      fetchDrivers();
      fetchActiveRide();
      fetchNetworkStatus();
    }, 5000);
    return () => clearInterval(interval);
  }, [fetchDrivers, fetchActiveRide, checkEmailVerification, fetchNetworkStatus]);

  // Fetch transfers and optimal route when destination changes
  useEffect(() => {
    if (destination) {
      fetchTransfers();
      fetchOptimalRoute();
    }
  }, [destination, fetchTransfers, fetchOptimalRoute]);

  // Handle map click to set destination
  const handleMapClick = (e) => {
    if (showDestinationPicker) {
      setDestination([e.latlng.lat, e.latlng.lng]);
      setShowDestinationPicker(false);
      toast.success(t('common.destinationSet'));
    }
  };

  const handleDriverSelect = (driver) => {
    if (!user?.subscription_active) {
      toast.error(t('common.subscriptionRequired'));
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
      toast.success(t('common.requestSent'));
    } catch (error) {
      const message = error.response?.data?.detail || t('common.requestError');
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
                {t('common.subscribed')}
              </span>
            ) : (
              <Link to="/subscription">
                <span className="text-xs bg-[#FFD60A]/20 text-[#FFD60A] px-2 py-1 rounded border border-[#FFD60A]/50 cursor-pointer">
                  {t('common.subscribe')}
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
                    {t('common.myProfile')}
                  </Button>
                </Link>
                <Link to="/subscription" onClick={() => setMenuOpen(false)}>
                  <Button variant="ghost" className="w-full justify-start text-white hover:bg-zinc-800" data-testid="subscription-link">
                    <CreditCard className="w-5 h-5 mr-3" />
                    {t('profile.subscription.title')}
                  </Button>
                </Link>
                <Button 
                  variant="ghost" 
                  className="w-full justify-start text-red-400 hover:bg-red-500/10 hover:text-red-400"
                  onClick={handleLogout}
                  data-testid="logout-btn"
                >
                  <LogOut className="w-5 h-5 mr-3" />
                  {t('nav.logout')}
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
        <MapClickHandler onMapClick={handleMapClick} isActive={showDestinationPicker} />
        
        {/* User location */}
        {userLocation && (
          <>
            <Marker position={userLocation} icon={userIcon}>
              <Popup className="custom-popup">
                <div className="text-center p-2">
                  <p className="font-bold">{t('dashboard.user.yourPosition')}</p>
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

        {/* Destination marker */}
        {destination && (
          <Marker position={destination} icon={destinationIcon}>
            <Popup>
              <div className="p-2 text-center">
                <p className="font-bold">{t('dashboard.user.destination')}</p>
                <Button 
                  size="sm" 
                  variant="ghost" 
                  className="mt-2 text-red-500"
                  onClick={() => setDestination(null)}
                >
                  {t('dashboard.user.remove')}
                </Button>
              </div>
            </Popup>
          </Marker>
        )}

        {/* Route line from user to destination */}
        {userLocation && destination && (
          <Polyline 
            positions={[userLocation, destination]} 
            pathOptions={{ color: '#FFD60A', weight: 3, dashArray: '10, 10' }}
          />
        )}

        {/* Optimal route segments */}
        {optimalRoute && optimalRoute.segments && optimalRoute.segments.map((segment, index) => (
          <React.Fragment key={`segment-${index}`}>
            <Polyline 
              positions={[
                [segment.start.lat, segment.start.lng],
                [segment.end.lat, segment.end.lng]
              ]} 
              pathOptions={{ 
                color: index === 0 ? '#22C55E' : '#3B82F6', 
                weight: 4 
              }}
            />
          </React.Fragment>
        ))}

        {/* Transfer points */}
        {optimalRoute && optimalRoute.transfer_points && optimalRoute.transfer_points.map((point, index) => (
          <Marker 
            key={`transfer-${index}`}
            position={[point.location.lat, point.location.lng]} 
            icon={transferIcon}
          >
            <Popup>
              <div className="p-2 text-center">
                <p className="font-bold text-blue-600">{t('common.transferPoint')} {index + 1}</p>
                <p className="text-sm text-gray-600">{t('common.changeVehicle')}</p>
              </div>
            </Popup>
          </Marker>
        ))}
        
        {/* Drivers with direction */}
        {drivers.map((driver) => {
          const bearing = driver.destination ? 
            Math.atan2(
              driver.destination.lng - driver.location.lng,
              driver.destination.lat - driver.location.lat
            ) * (180 / Math.PI) : null;
          
          return (
            <Marker 
              key={driver.id} 
              position={[driver.location.lat, driver.location.lng]}
              icon={createDriverIcon(bearing, driver.available_seats || 0)}
              eventHandlers={{
                click: () => handleDriverSelect(driver)
              }}
            >
              <Popup>
                <div className="p-2 min-w-[200px]">
                  <p className="font-bold text-lg">{driver.first_name}</p>
                  <p className="text-sm text-zinc-600 font-mono">{driver.vehicle_plate}</p>
                  <p className="text-sm">{driver.vehicle_type}</p>
                  <div className="flex items-center gap-1 mt-2 text-[#FFD60A]">
                    <Users className="w-4 h-4" />
                    <span>{driver.available_seats} {t('common.places')}</span>
                  </div>
                  {driver.destination && (
                    <div className="flex items-center gap-1 mt-1 text-blue-500">
                      <Compass className="w-4 h-4" />
                      <span className="text-xs">Direction: {Math.round(bearing || 0)}°</span>
                    </div>
                  )}
                  {driver.matching && (
                    <div className="mt-2 pt-2 border-t border-gray-200">
                      <div className="flex items-center gap-1 text-green-600">
                        <Clock className="w-4 h-4" />
                        <span className="text-sm">ETA: {driver.matching.eta_minutes} min</span>
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        Score: {driver.matching.score} | Direction: {Math.round(driver.matching.direction_score)}%
                      </div>
                    </div>
                  )}
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>

      {/* Bottom Panel - Active Ride with Progress */}
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
                <h3 className="font-bold text-white text-lg">{t('dashboard.user.activeRide')}</h3>
                <span className={`text-xs px-2 py-1 rounded ${
                  activeRide.status === 'in_progress' ? 'bg-blue-500/20 text-blue-400' :
                  activeRide.status === 'pickup' ? 'bg-purple-500/20 text-purple-400' :
                  activeRide.status === 'near_destination' ? 'bg-green-500/20 text-green-400' :
                  activeRide.status === 'accepted' ? 'bg-yellow-500/20 text-yellow-400' : 
                  'bg-zinc-500/20 text-zinc-400'
                }`}>
                  {activeRide.status === 'in_progress' ? t('dashboard.user.inProgress') :
                   activeRide.status === 'pickup' ? t('dashboard.user.pickup') :
                   activeRide.status === 'near_destination' ? t('dashboard.user.dropoff') :
                   activeRide.status === 'accepted' ? t('common.confirm') : t('common.loading')}
                </span>
              </div>
              
              {/* Progress Bar */}
              <div className="mb-4">
                <div className="flex justify-between text-xs text-zinc-400 mb-2">
                  <span>{t('dashboard.user.pickup')}</span>
                  <span>{t('dashboard.user.destination')}</span>
                </div>
                <Progress value={activeRide.progress_percent || (activeRide.status === 'accepted' ? 10 : 0)} className="h-2" />
                <p className="text-center text-xs text-zinc-500 mt-1">
                  {activeRide.progress_percent || 0}% {t('dashboard.user.progress')}
                </p>
              </div>
              
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-[#FFD60A] rounded flex items-center justify-center">
                  <Car className="w-6 h-6 text-black" />
                </div>
                <div className="flex-1">
                  <p className="text-white font-medium">
                    {activeRide.status === 'pickup' ? t('dashboard.user.pickup') :
                     activeRide.status === 'in_progress' ? t('dashboard.user.inProgress') :
                     activeRide.status === 'near_destination' ? t('dashboard.user.dropoff') :
                     activeRide.status === 'accepted' ? t('dashboard.user.searchingDriver') : 
                     t('common.loading')}
                  </p>
                  <p className="text-zinc-400 text-sm">ID: {activeRide.id.slice(0, 8)}</p>
                </div>
              </div>
              
              {/* Timeline */}
              <div className="mt-4 pt-4 border-t border-zinc-800">
                <div className="flex justify-between">
                  <div className="flex flex-col items-center">
                    <div className={`w-3 h-3 rounded-full ${activeRide.status !== 'pending' ? 'bg-green-500' : 'bg-zinc-600'}`}></div>
                    <span className="text-xs text-zinc-500 mt-1">{t('common.accepted')}</span>
                  </div>
                  <div className="flex-1 h-0.5 bg-zinc-700 self-center mx-2"></div>
                  <div className="flex flex-col items-center">
                    <div className={`w-3 h-3 rounded-full ${['pickup', 'in_progress', 'near_destination', 'completed'].includes(activeRide.status) ? 'bg-green-500' : 'bg-zinc-600'}`}></div>
                    <span className="text-xs text-zinc-500 mt-1">{t('common.pickedUp')}</span>
                  </div>
                  <div className="flex-1 h-0.5 bg-zinc-700 self-center mx-2"></div>
                  <div className="flex flex-col items-center">
                    <div className={`w-3 h-3 rounded-full ${['in_progress', 'near_destination', 'completed'].includes(activeRide.status) ? 'bg-green-500' : 'bg-zinc-600'}`}></div>
                    <span className="text-xs text-zinc-500 mt-1">{t('common.enRoute')}</span>
                  </div>
                  <div className="flex-1 h-0.5 bg-zinc-700 self-center mx-2"></div>
                  <div className="flex flex-col items-center">
                    <div className={`w-3 h-3 rounded-full ${activeRide.status === 'completed' ? 'bg-green-500' : 'bg-zinc-600'}`}></div>
                    <span className="text-xs text-zinc-500 mt-1">{t('common.arrived')}</span>
                  </div>
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
                    <span className="text-sm text-[#FFD60A]">{selectedDriver.available_seats} {t('dashboard.user.seats')}</span>
                  </div>
                </div>
              </div>
              
              {/* Transfer Suggestions Button */}
              {transfers.length > 0 && (
                <Button
                  onClick={() => setShowTransfers(!showTransfers)}
                  variant="outline"
                  className="w-full mb-3 border-blue-500/50 text-blue-400 hover:bg-blue-500/10"
                  data-testid="show-transfers-btn"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  {showTransfers ? t('dashboard.user.hideTransfers') : t('dashboard.user.showTransfers')} ({transfers.length})
                </Button>
              )}
              
              {/* Transfer Options */}
              <AnimatePresence>
                {showTransfers && transfers.length > 0 && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="mb-4 overflow-hidden"
                  >
                    <p className="text-zinc-400 text-sm mb-2">{t('dashboard.user.transferSuggestions')}:</p>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {transfers.map((transfer, index) => (
                        <div key={index} className="bg-zinc-800/50 p-3 rounded border border-zinc-700">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded">
                              {t('dashboard.user.efficiency')}: {transfer.efficiency_percent || transfer.estimated_efficiency}%
                            </span>
                            {transfer.total_time_minutes && (
                              <span className="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded">
                                {transfer.total_time_minutes} {t('dashboard.user.min')}
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-2 text-sm">
                            <div className="flex-1">
                              <p className="text-white">{transfer.first_driver.name}</p>
                              <p className="text-zinc-500 text-xs">{transfer.first_driver.vehicle}</p>
                              {transfer.first_segment_km && (
                                <p className="text-xs text-[#FFD60A]">{transfer.first_segment_km} km</p>
                              )}
                            </div>
                            <div className="flex flex-col items-center">
                              <ArrowRight className="w-4 h-4 text-[#FFD60A]" />
                              <span className="text-xs text-zinc-500">{t('dashboard.user.transfer')}</span>
                            </div>
                            <div className="flex-1 text-right">
                              <p className="text-white">{transfer.second_driver.name}</p>
                              <p className="text-zinc-500 text-xs">{transfer.second_driver.vehicle}</p>
                              {transfer.second_segment_km && (
                                <p className="text-xs text-[#FFD60A]">{transfer.second_segment_km} km</p>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
              
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
                    {t('dashboard.user.requestRide').toUpperCase()}
                    <ArrowRight className="w-5 h-5 ml-2" />
                  </>
                )}
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Email Verification Banner */}
      {!emailVerified && (
        <div className="absolute top-16 left-4 right-4 z-[1000] bg-yellow-500/20 border border-yellow-500/50 rounded p-3">
          <div className="flex items-center gap-3">
            <Mail className="w-5 h-5 text-yellow-500" />
            <div className="flex-1">
              <p className="text-yellow-400 text-sm font-medium">{t('dashboard.user.emailNotVerified')}</p>
              <p className="text-yellow-400/70 text-xs">{t('dashboard.user.verifyEmail')}</p>
            </div>
          </div>
        </div>
      )}

      {/* Drivers count indicator */}
      <div className="absolute bottom-24 left-4 z-[1000] glass-panel px-4 py-2 rounded">
        <div className="flex items-center gap-2 text-white">
          <Car className="w-4 h-4 text-[#FFD60A]" />
          <span className="text-sm">{drivers.length} {t('dashboard.user.availableVehicles')}</span>
        </div>
        {networkStatus && (
          <div className="text-xs text-zinc-400 mt-1">
            {networkStatus.total_available_seats} {t('dashboard.user.seats')} • {networkStatus.active_rides} {t('dashboard.user.activeRides')}
          </div>
        )}
      </div>

      {/* Destination picker button */}
      {!destination && !activeRide && (
        <div className="absolute bottom-24 right-4 z-[1000]">
          <Button
            onClick={() => setShowDestinationPicker(!showDestinationPicker)}
            className={`${showDestinationPicker ? 'bg-red-500 hover:bg-red-600' : 'bg-[#FFD60A] hover:bg-[#E6C209]'} text-black font-bold`}
            data-testid="set-destination-btn"
          >
            <MapPin className="w-4 h-4 mr-2" />
            {showDestinationPicker ? t('dashboard.user.cancel') : t('dashboard.user.setDestination')}
          </Button>
        </div>
      )}

      {/* Destination picker hint */}
      {showDestinationPicker && (
        <div className="absolute top-20 left-1/2 transform -translate-x-1/2 z-[1000] bg-blue-500 text-white px-4 py-2 rounded-full text-sm">
          {t('dashboard.user.clickMap')}
        </div>
      )}

      {/* Optimal Route Panel */}
      <AnimatePresence>
        {destination && optimalRoute && !selectedDriver && !activeRide && (
          <motion.div
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            className="ride-panel"
          >
            <div className="max-w-lg mx-auto">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-bold text-white text-lg flex items-center gap-2">
                  <Route className="w-5 h-5 text-[#FFD60A]" />
                  Itinéraire optimal
                </h3>
                <button 
                  onClick={() => {
                    setDestination(null);
                    setOptimalRoute(null);
                  }}
                  className="text-zinc-400 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Route summary */}
              <div className="grid grid-cols-3 gap-3 mb-4">
                <div className="bg-zinc-800/50 p-3 rounded text-center">
                  <p className="text-2xl font-bold text-[#FFD60A]">{optimalRoute.total_distance_km}</p>
                  <p className="text-xs text-zinc-400">km total</p>
                </div>
                <div className="bg-zinc-800/50 p-3 rounded text-center">
                  <p className="text-2xl font-bold text-blue-400">{optimalRoute.total_transfers}</p>
                  <p className="text-xs text-zinc-400">transbordements</p>
                </div>
                <div className="bg-zinc-800/50 p-3 rounded text-center">
                  <p className="text-2xl font-bold text-green-400">{optimalRoute.estimated_total_time_minutes}</p>
                  <p className="text-xs text-zinc-400">minutes</p>
                </div>
              </div>

              {/* Route efficiency */}
              <div className="mb-4">
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-zinc-400">Efficacité du trajet</span>
                  <span className="text-[#FFD60A]">{optimalRoute.route_efficiency}%</span>
                </div>
                <Progress value={optimalRoute.route_efficiency} className="h-2" />
              </div>

              {/* Segments */}
              {optimalRoute.segments && optimalRoute.segments.length > 0 && (
                <div className="space-y-2 mb-4">
                  <p className="text-sm text-zinc-400">Segments du trajet :</p>
                  {optimalRoute.segments.map((segment, index) => (
                    <div key={index} className="bg-zinc-800/30 p-3 rounded border border-zinc-700">
                      <div className="flex items-center justify-between">
                        <span className="text-white font-medium">Segment {segment.index}</span>
                        <span className="text-xs text-zinc-400">{segment.distance_km} km • {segment.eta_minutes} min</span>
                      </div>
                      {segment.driver && (
                        <div className="flex items-center gap-2 mt-2 text-sm">
                          <Car className="w-4 h-4 text-[#FFD60A]" />
                          <span className="text-zinc-300">{segment.driver.first_name}</span>
                          <span className="text-zinc-500">•</span>
                          <span className="text-zinc-400">{segment.driver.vehicle_plate}</span>
                          <span className="text-green-400 ml-auto">{segment.driver.available_seats} places</span>
                        </div>
                      )}
                      {!segment.driver && (
                        <p className="text-xs text-yellow-400 mt-1">Recherche d'un chauffeur...</p>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Select first driver */}
              {optimalRoute.segments && optimalRoute.segments[0]?.driver && (
                <Button
                  onClick={() => handleDriverSelect(optimalRoute.segments[0].driver)}
                  className="w-full bg-[#FFD60A] text-black font-bold h-12 hover:bg-[#E6C209]"
                  data-testid="select-route-btn"
                >
                  Demander ce trajet
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default UserDashboard;
