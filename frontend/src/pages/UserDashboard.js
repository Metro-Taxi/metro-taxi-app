import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup, useMap, useMapEvents, Circle, Polyline } from 'react-leaflet';
import L from 'leaflet';
import { motion, AnimatePresence } from 'framer-motion';
import { Car, User, MapPin, LogOut, CreditCard, Menu, X, Navigation, Users, ArrowRight, RefreshCw, Mail, Clock, Route, Compass, History, Star, Home, AlertTriangle, Bell, MessageCircle, Search, Loader2, HelpCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import 'leaflet/dist/leaflet.css';
import NotificationCenter from '@/components/NotificationCenter';
import RideHistory from '@/pages/RideHistory';
import { PendingRatings } from '@/components/RatingSystem';
import ChatWindow from '@/components/ChatWindow';
import HelpCenter from '@/components/HelpCenter';

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
  const [showHistory, setShowHistory] = useState(false);
  const [showImportantPopup, setShowImportantPopup] = useState(false);
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);
  const [showChat, setShowChat] = useState(false);
  const [chatDriverName, setChatDriverName] = useState('');
  const [showHelp, setShowHelp] = useState(false);
  const [searchingVehicles, setSearchingVehicles] = useState(false);
  const [matchedDrivers, setMatchedDrivers] = useState([]);
  
  // Address search states
  const [addressSearch, setAddressSearch] = useState('');
  const [addressSuggestions, setAddressSuggestions] = useState([]);
  const [searchingAddress, setSearchingAddress] = useState(false);

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

  // Check subscription status and show popup if needed
  useEffect(() => {
    const checkSubscriptionAndShowPopup = async () => {
      try {
        const response = await axios.get(`${API}/subscription/status`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setSubscriptionStatus(response.data);
        
        // Check if we should show the important popup
        const lastPopupShown = localStorage.getItem('metro-taxi-important-popup-shown');
        const lastPopupDate = lastPopupShown ? new Date(lastPopupShown) : null;
        const now = new Date();
        
        // Show popup if:
        // 1. Never shown before, OR
        // 2. Last shown more than 24 hours ago AND subscription is expiring soon
        const shouldShowOnFirstVisit = !lastPopupShown;
        const isExpiringSoon = response.data.is_expiring_soon;
        const lastShownMoreThan24hAgo = lastPopupDate && (now - lastPopupDate) > 24 * 60 * 60 * 1000;
        
        if (shouldShowOnFirstVisit || (isExpiringSoon && lastShownMoreThan24hAgo)) {
          // Small delay to let the page render first
          setTimeout(() => setShowImportantPopup(true), 1000);
        }
      } catch (error) {
        console.error('Subscription status check error:', error);
      }
    };
    
    if (token && user?.subscription_active) {
      checkSubscriptionAndShowPopup();
    }
  }, [token, user]);

  const handleCloseImportantPopup = () => {
    setShowImportantPopup(false);
    localStorage.setItem('metro-taxi-important-popup-shown', new Date().toISOString());
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
    
    setSearchingVehicles(true);
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
      setOptimalRoute(null);
    } finally {
      setSearchingVehicles(false);
    }
  }, [token, userLocation, destination]);

  // Fetch matching drivers for the selected destination
  const fetchMatchingDrivers = useCallback(async () => {
    if (!userLocation || !destination) return;
    
    setSearchingVehicles(true);
    try {
      const response = await axios.post(`${API}/matching/find-drivers`, {
        user_lat: userLocation[0],
        user_lng: userLocation[1],
        dest_lat: destination[0],
        dest_lng: destination[1]
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMatchedDrivers(response.data.drivers || []);
      
      // Also fetch optimal route
      await fetchOptimalRoute();
    } catch (error) {
      console.error('Fetch matching drivers error:', error);
      setMatchedDrivers([]);
    } finally {
      setSearchingVehicles(false);
    }
  }, [token, userLocation, destination, fetchOptimalRoute]);

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
      fetchMatchingDrivers();
    } else {
      setMatchedDrivers([]);
      setOptimalRoute(null);
    }
  }, [destination, fetchTransfers, fetchMatchingDrivers]);

  // Handle map click to set destination
  const handleMapClick = (e) => {
    if (showDestinationPicker) {
      setDestination([e.latlng.lat, e.latlng.lng]);
      setShowDestinationPicker(false);
      toast.success(t('common.destinationSet'));
    }
  };

  // Search address using Nominatim (OpenStreetMap)
  const searchAddress = async (query) => {
    if (!query || query.length < 3) {
      setAddressSuggestions([]);
      return;
    }
    
    setSearchingAddress(true);
    try {
      const response = await axios.get(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5&countrycodes=fr,gb,de,es,it,be,ch,nl`,
        { headers: { 'Accept-Language': 'fr' } }
      );
      setAddressSuggestions(response.data || []);
    } catch (error) {
      console.error('Address search error:', error);
      setAddressSuggestions([]);
    } finally {
      setSearchingAddress(false);
    }
  };

  // Debounced address search
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (addressSearch) {
        searchAddress(addressSearch);
      }
    }, 500);
    return () => clearTimeout(timeoutId);
  }, [addressSearch]);

  // Select address from suggestions
  const selectAddress = (suggestion) => {
    const lat = parseFloat(suggestion.lat);
    const lng = parseFloat(suggestion.lon);
    setDestination([lat, lng]);
    setAddressSearch(suggestion.display_name.split(',')[0]);
    setAddressSuggestions([]);
    setShowDestinationPicker(false);
    toast.success(t('common.destinationSet'));
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

  // Check if subscription is expired (admins are exempt)
  const isAdmin = user?.role === 'admin';
  const isSubscriptionExpired = !isAdmin && !user?.subscription_active;

  return (
    <div className="h-screen w-full bg-[#09090B] relative overflow-hidden">
      {/* Subscription Expired Overlay */}
      {isSubscriptionExpired && (
        <div className="absolute inset-0 z-[2000] bg-black/90 backdrop-blur-sm flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8 max-w-md w-full text-center"
          >
            {/* Warning Icon */}
            <div className="w-20 h-20 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
              <AlertTriangle className="w-10 h-10 text-red-500" />
            </div>
            
            {/* Title */}
            <h2 className="text-2xl font-bold text-white mb-4">
              {t('subscription.expiredTitle', 'Abonnement expiré')}
            </h2>
            
            {/* Message */}
            <p className="text-zinc-400 mb-8 leading-relaxed">
              {t('subscription.expiredMessage', 'Votre abonnement a expiré. Veuillez le renouveler pour continuer à utiliser Métro-Taxi.')}
            </p>
            
            {/* Blocked Features */}
            <div className="bg-zinc-800/50 rounded-xl p-4 mb-8">
              <p className="text-sm text-zinc-500 mb-3">{t('subscription.blockedFeatures', 'Fonctionnalités bloquées :')}</p>
              <ul className="space-y-2 text-left">
                <li className="flex items-center gap-2 text-zinc-400 text-sm">
                  <X className="w-4 h-4 text-red-500" />
                  {t('subscription.blocked.rides', 'Réservation de trajets')}
                </li>
                <li className="flex items-center gap-2 text-zinc-400 text-sm">
                  <X className="w-4 h-4 text-red-500" />
                  {t('subscription.blocked.vehicles', 'Connexion aux véhicules')}
                </li>
                <li className="flex items-center gap-2 text-zinc-400 text-sm">
                  <X className="w-4 h-4 text-red-500" />
                  {t('subscription.blocked.map', 'Visualisation des chauffeurs')}
                </li>
              </ul>
            </div>
            
            {/* Renew Button */}
            <Link to="/subscription" className="block">
              <Button 
                className="w-full bg-[#FFD60A] hover:bg-[#FFE55C] text-black font-bold py-4 text-lg"
                data-testid="renew-subscription-overlay-btn"
              >
                <RefreshCw className="w-5 h-5 mr-2" />
                {t('subscription.renewButton', 'Renouveler mon abonnement')}
              </Button>
            </Link>
            
            {/* Logout option */}
            <button
              onClick={handleLogout}
              className="mt-4 text-zinc-500 hover:text-white text-sm transition-colors"
            >
              {t('nav.logout', 'Se déconnecter')}
            </button>
          </motion.div>
        </div>
      )}

      {/* Important Information Popup */}
      <AnimatePresence>
        {showImportantPopup && !isSubscriptionExpired && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-[1500] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4"
            data-testid="important-popup-overlay"
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              className="bg-zinc-900 border border-[#FFD60A]/30 rounded-2xl p-6 md:p-8 max-w-md w-full"
            >
              {/* Header with icon */}
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 bg-[#FFD60A]/20 rounded-xl flex items-center justify-center flex-shrink-0">
                  <Bell className="w-6 h-6 text-[#FFD60A]" />
                </div>
                <h2 className="text-xl font-bold text-[#FFD60A]">
                  {t('popup.importantTitle', 'Important')}
                </h2>
              </div>
              
              {/* Message content */}
              <div className="space-y-4 mb-8">
                <p className="text-white font-medium">
                  {t('popup.subscriptionRequired', 'Votre abonnement doit être actif pour utiliser Métro-Taxi.')}
                </p>
                
                <p className="text-zinc-400">
                  {t('popup.notificationReminder', 'Vous recevrez des notifications de rappel avant expiration.')}
                </p>
                
                <p className="text-zinc-400">
                  {t('popup.renewRecommendation', 'Nous vous recommandons de renouveler votre abonnement dès réception de ces alertes afin d\'éviter toute interruption du service pendant vos déplacements.')}
                </p>
              </div>
              
              {/* Expiration warning if expiring soon */}
              {subscriptionStatus?.is_expiring_soon && (
                <div className="bg-orange-500/10 border border-orange-500/30 rounded-xl p-4 mb-6">
                  <div className="flex items-center gap-2 text-orange-400">
                    <AlertTriangle className="w-5 h-5" />
                    <span className="font-medium">
                      {t('popup.expiringSoon', 'Votre abonnement expire dans')} {subscriptionStatus.hours_remaining}h
                    </span>
                  </div>
                </div>
              )}
              
              {/* Understand button */}
              <Button 
                onClick={handleCloseImportantPopup}
                className="w-full bg-[#FFD60A] hover:bg-[#FFE55C] text-black font-bold py-3"
                data-testid="understood-btn"
              >
                {t('popup.understoodButton', 'J\'ai compris')}
              </Button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header */}
      <header className="absolute top-0 left-0 right-0 z-[1000] glass-panel">
        <div className="flex justify-between items-center px-4 py-3">
          <Link to="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity" data-testid="home-link">
            <Car className="w-6 h-6 text-[#FFD60A]" />
            <span className="text-lg font-bold text-white">MÉTRO-TAXI</span>
          </Link>
          
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
            <NotificationCenter />
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
                <Link to="/" onClick={() => setMenuOpen(false)}>
                  <Button variant="ghost" className="w-full justify-start text-white hover:bg-zinc-800" data-testid="home-menu-link">
                    <Home className="w-5 h-5 mr-3" />
                    {t('nav.home', 'Accueil')}
                  </Button>
                </Link>
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
                  className="w-full justify-start text-white hover:bg-zinc-800"
                  onClick={() => { setMenuOpen(false); setShowHistory(true); }}
                  data-testid="history-link"
                >
                  <History className="w-5 h-5 mr-3" />
                  {t('rideHistory.title', 'Ride History')}
                </Button>
                <Button 
                  variant="ghost" 
                  className="w-full justify-start text-zinc-300 hover:bg-zinc-800"
                  onClick={() => { setShowHelp(true); setMenuOpen(false); }}
                  data-testid="help-menu-btn"
                >
                  <HelpCircle className="w-5 h-5 mr-3 text-[#FFD60A]" />
                  {t('help.button', 'AIDE')}
                </Button>
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
              
              {/* Chat Button */}
              {activeRide.driver_id && (
                <div className="mt-4 pt-4 border-t border-zinc-800">
                  <Button
                    onClick={() => {
                      setChatDriverName(activeRide.driver_name || 'Chauffeur');
                      setShowChat(true);
                    }}
                    className="w-full bg-zinc-800 hover:bg-zinc-700 text-white flex items-center justify-center gap-2"
                    data-testid="open-chat-btn"
                  >
                    <MessageCircle className="w-4 h-4" />
                    {t('chat.openChat', 'Contacter le chauffeur')}
                  </Button>
                </div>
              )}
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
                <h3 className="font-bold text-white text-lg">{t('common.requestRide')}</h3>
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
              <button 
                onClick={async () => {
                  try {
                    await axios.post(`${API}/auth/resend-verification`, {}, {
                      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
                    });
                    toast.success(t('verifyEmail.emailSent', 'Email de vérification envoyé !'));
                  } catch (error) {
                    toast.error(t('verifyEmail.error', 'Erreur lors de l\'envoi'));
                  }
                }}
                className="text-yellow-400 text-xs underline hover:text-yellow-300 transition-colors"
              >
                {t('dashboard.user.verifyEmail')}
              </button>
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

      {/* Destination picker with address search */}
      {showDestinationPicker && (
        <div className="absolute top-20 left-1/2 transform -translate-x-1/2 z-[1000] w-80 max-w-[90vw]">
          <div className="bg-[#18181B] border border-zinc-700 rounded-lg shadow-xl p-3">
            <div className="relative mb-2">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-zinc-400" />
              <input
                type="text"
                value={addressSearch}
                onChange={(e) => setAddressSearch(e.target.value)}
                placeholder={t('dashboard.user.searchAddress', 'Rechercher une adresse...')}
                className="w-full pl-10 pr-10 py-2 bg-zinc-900 border border-zinc-700 rounded text-white text-sm focus:outline-none focus:border-[#FFD60A]"
                data-testid="address-search-input"
              />
              {searchingAddress && (
                <Loader2 className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[#FFD60A] animate-spin" />
              )}
            </div>
            
            {/* Address suggestions */}
            {addressSuggestions.length > 0 && (
              <div className="max-h-48 overflow-y-auto border-t border-zinc-700">
                {addressSuggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => selectAddress(suggestion)}
                    className="w-full text-left p-2 hover:bg-zinc-800 text-sm text-white border-b border-zinc-800 last:border-b-0"
                    data-testid={`address-suggestion-${index}`}
                  >
                    <div className="flex items-start gap-2">
                      <MapPin className="w-4 h-4 text-[#FFD60A] mt-0.5 flex-shrink-0" />
                      <span className="line-clamp-2">{suggestion.display_name}</span>
                    </div>
                  </button>
                ))}
              </div>
            )}
            
            <div className="text-center text-xs text-zinc-500 mt-2 pt-2 border-t border-zinc-700">
              {t('dashboard.user.orClickMap', 'ou cliquez sur la carte')}
            </div>
          </div>
        </div>
      )}

      {/* Optimal Route Panel - Shows after destination is selected */}
      <AnimatePresence>
        {destination && !selectedDriver && !activeRide && (
          <motion.div
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            className="ride-panel"
          >
            <div className="max-w-lg mx-auto">
              {/* Header with destination */}
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-bold text-white text-lg flex items-center gap-2">
                  <MapPin className="w-5 h-5 text-red-500" />
                  {t('dashboard.user.destinationSelected', 'Destination sélectionnée')}
                </h3>
                <button 
                  onClick={() => {
                    setDestination(null);
                    setOptimalRoute(null);
                    setMatchedDrivers([]);
                  }}
                  className="text-zinc-400 hover:text-white"
                  data-testid="clear-destination-btn"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Search button - Always visible when destination is set */}
              <Button
                onClick={fetchMatchingDrivers}
                disabled={searchingVehicles}
                className="w-full bg-[#FFD60A] text-black font-bold h-12 hover:bg-[#E6C209] mb-4"
                data-testid="search-vehicles-btn"
              >
                {searchingVehicles ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    {t('dashboard.user.searchingVehicles', 'Recherche en cours...')}
                  </>
                ) : (
                  <>
                    <Search className="w-5 h-5 mr-2" />
                    {t('dashboard.user.findVehicles', 'Rechercher les véhicules')}
                  </>
                )}
              </Button>

              {/* Route summary - Only show if optimalRoute exists */}
              {optimalRoute && (
                <div className="mb-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Route className="w-4 h-4 text-[#FFD60A]" />
                    <span className="text-sm text-zinc-400">{t('common.optimalRoute', 'Trajet optimal')}</span>
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    <div className="bg-zinc-800/50 p-2 rounded text-center">
                      <p className="text-lg font-bold text-[#FFD60A]">{optimalRoute.total_distance_km || '?'}</p>
                      <p className="text-xs text-zinc-400">km</p>
                    </div>
                    <div className="bg-zinc-800/50 p-2 rounded text-center">
                      <p className="text-lg font-bold text-blue-400">{optimalRoute.total_transfers || 0}</p>
                      <p className="text-xs text-zinc-400">{t('common.transfers', 'transferts')}</p>
                    </div>
                    <div className="bg-zinc-800/50 p-2 rounded text-center">
                      <p className="text-lg font-bold text-green-400">{optimalRoute.estimated_total_time_minutes || '?'}</p>
                      <p className="text-xs text-zinc-400">min</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Available vehicles list */}
              {matchedDrivers.length > 0 && (
                <div className="mb-4">
                  <p className="text-sm text-zinc-400 mb-2 flex items-center gap-2">
                    <Car className="w-4 h-4 text-[#FFD60A]" />
                    {t('dashboard.user.availableVehicles', 'Véhicules disponibles')} ({matchedDrivers.length})
                  </p>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {matchedDrivers.slice(0, 5).map((driver) => (
                      <div 
                        key={driver.id}
                        className="bg-zinc-800/50 p-3 rounded border border-zinc-700 hover:border-[#FFD60A] cursor-pointer transition-all"
                        onClick={() => handleDriverSelect(driver)}
                        data-testid={`driver-option-${driver.id}`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-[#FFD60A] flex items-center justify-center text-black font-bold">
                              {driver.first_name?.charAt(0) || 'C'}
                            </div>
                            <div>
                              <p className="text-white font-medium">{driver.first_name}</p>
                              <p className="text-xs text-zinc-400">{driver.vehicle_plate} • {driver.vehicle_type}</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="text-green-400 font-bold">{driver.available_seats} {t('dashboard.user.seats', 'places')}</p>
                            {driver.matching && (
                              <p className="text-xs text-zinc-500">
                                {driver.matching.pickup_distance} km • {driver.matching.eta_minutes} min
                              </p>
                            )}
                          </div>
                        </div>
                        {driver.matching && (
                          <div className="mt-2 flex items-center gap-2">
                            <Progress value={driver.matching.score} className="h-1 flex-1" />
                            <span className="text-xs text-[#FFD60A]">{Math.round(driver.matching.score)}%</span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* No vehicles message */}
              {!searchingVehicles && matchedDrivers.length === 0 && optimalRoute && (
                <div className="bg-yellow-500/10 border border-yellow-500/30 rounded p-3 mb-4">
                  <div className="flex items-center gap-2 text-yellow-400">
                    <AlertTriangle className="w-5 h-5" />
                    <p className="text-sm">{t('dashboard.user.noVehiclesFound', 'Aucun véhicule disponible pour le moment')}</p>
                  </div>
                  <p className="text-xs text-zinc-400 mt-1">
                    {t('dashboard.user.tryAgainLater', 'Réessayez dans quelques instants ou modifiez votre destination')}
                  </p>
                </div>
              )}

              {/* Segments detail (collapsible) */}
              {optimalRoute?.segments && optimalRoute.segments.length > 0 && (
                <details className="mb-4">
                  <summary className="text-sm text-zinc-400 cursor-pointer hover:text-white">
                    {t('common.routeSegments', 'Détails du trajet')} ({optimalRoute.segments.length} segments)
                  </summary>
                  <div className="space-y-2 mt-2">
                    {optimalRoute.segments.map((segment, index) => (
                      <div key={index} className="bg-zinc-800/30 p-2 rounded border border-zinc-700 text-sm">
                        <div className="flex items-center justify-between">
                          <span className="text-white">{t('dashboard.user.segment', 'Segment')} {segment.index}</span>
                          <span className="text-xs text-zinc-400">{segment.distance_km} km</span>
                        </div>
                        {segment.driver && (
                          <div className="flex items-center gap-2 mt-1 text-xs text-zinc-400">
                            <Car className="w-3 h-3 text-[#FFD60A]" />
                            <span>{segment.driver.first_name} - {segment.driver.vehicle_plate}</span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </details>
              )}

              {/* Select first driver button - Only if optimal route has a driver */}
              {optimalRoute?.segments?.[0]?.driver && (
                <Button
                  onClick={() => handleDriverSelect(optimalRoute.segments[0].driver)}
                  className="w-full bg-green-600 text-white font-bold h-12 hover:bg-green-700"
                  data-testid="select-optimal-route-btn"
                >
                  {t('common.requestOptimalRide', 'Demander le trajet optimal')}
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Ride History Modal */}
      <AnimatePresence>
        {showHistory && (
          <RideHistory onClose={() => setShowHistory(false)} />
        )}
      </AnimatePresence>

      {/* Pending Ratings */}
      {!activeRide && (
        <div className="absolute bottom-4 left-4 right-4 z-[500]">
          <PendingRatings />
        </div>
      )}

      {/* Chat Window */}
      <AnimatePresence>
        {showChat && activeRide && (
          <ChatWindow
            rideId={activeRide.id}
            driverName={chatDriverName}
            userName={user?.first_name}
            isDriver={false}
            onClose={() => setShowChat(false)}
          />
        )}
      </AnimatePresence>

      {/* Help Center */}
      <HelpCenter 
        isOpen={showHelp} 
        onClose={() => setShowHelp(false)} 
        userType="user" 
      />
    </div>
  );
};

export default UserDashboard;
