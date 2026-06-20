import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup, useMap, Circle } from 'react-leaflet';
import L from 'leaflet';
import { motion, AnimatePresence } from 'framer-motion';
import { Car, User, LogOut, Menu, X, Power, MapPin, Check, XCircle, Users, Navigation, Wallet, ArrowLeft, Globe, HelpCircle, Loader2, BellRing, KeyRound } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import DriverEarnings from './DriverEarnings';
import HelpCenter from '@/components/HelpCenter';
import ChangePasswordModal from '@/components/ChangePasswordModal';
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
// Only re-centers on initial load — subsequent GPS updates do NOT force a re-center,
// so the driver can freely zoom in/out and pan to see the passenger marker.
// When a new ride is accepted (rideAcceptedKey changes), auto-fit both driver and
// passenger markers into the viewport ONCE so the driver sees both at a glance.
const MapUpdater = ({ center, fitBounds, rideAcceptedKey }) => {
  const map = useMap();
  const hasInitialized = useRef(false);
  const lastAcceptedKey = useRef(null);
  
  useEffect(() => {
    if (center && !hasInitialized.current) {
      map.setView(center, 15);
      hasInitialized.current = true;
    }
  }, [center, map]);
  
  // Auto-fit on ride acceptance — runs once per new ride
  useEffect(() => {
    if (rideAcceptedKey && rideAcceptedKey !== lastAcceptedKey.current && fitBounds && fitBounds.length === 2) {
      try {
        map.fitBounds(fitBounds, { padding: [60, 60], maxZoom: 15 });
      } catch (_) { /* leaflet may not be ready yet */ }
      lastAcceptedKey.current = rideAcceptedKey;
    }
  }, [rideAcceptedKey, fitBounds, map]);
  
  return null;
};

const DriverDashboard = () => {
  const { driver, token, logout, refreshUser } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [menuOpen, setMenuOpen] = useState(false);
  const [showEarnings, setShowEarnings] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [driverLocation, setDriverLocation] = useState(null);
  const [isActive, setIsActive] = useState(driver?.is_active || false);
  const [pendingRides, setPendingRides] = useState([]);
  const [activeRide, setActiveRide] = useState(null);
  const [loading, setLoading] = useState(false);
  const [availableSeats, setAvailableSeats] = useState(driver?.seats || 4);
  const [locatingDriver, setLocatingDriver] = useState(true);
  // 📍 Erreur géoloc explicite (refus permission, timeout, etc.) — empêche d'envoyer
  // une fausse position Paris 4 au backend.
  const [geoError, setGeoError] = useState(null);
  const [otpInput, setOtpInput] = useState('');
  const [earningsSummary, setEarningsSummary] = useState(null);  // {current_month, totals}
  // 🔊 Persistent AudioContext — created on user gesture (toggleActive click) to bypass iOS Safari autoplay policy
  const audioCtxRef = useRef(null);
  // 🔇 Oscillateur silencieux continu — maintient l'audio session iOS active pour
  // permettre aux beeps suivants de jouer sans gesture utilisateur. Patch V9.1.
  const keepAliveRef = useRef(null);
  // 🔒 Wake Lock — keep iPhone screen ON while driver is active so the red flash is visible
  const wakeLockRef = useRef(null);
  // 🚨 Patch V9 — overlay rouge plein écran dismissé manuellement (au lieu d'attendre la décision)
  const [alertDismissed, setAlertDismissed] = useState(false);
  // 🔑 Patch V9 — modale changement de mot de passe
  const [showChangePassword, setShowChangePassword] = useState(false);

  // Paris center as default (fallback only)
  const defaultCenter = [48.8566, 2.3522];

  // Get driver location and update
  useEffect(() => {
    setLocatingDriver(true);
    if (!navigator.geolocation) {
      setGeoError('GPS non supporté sur cet appareil. Active la localisation et utilise un navigateur récent.');
      setLocatingDriver(false);
      return;
    }
    const watchId = navigator.geolocation.watchPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        setDriverLocation([latitude, longitude]);
        setLocatingDriver(false);
        setGeoError(null);
        if (isActive) {
          updateDriverLocation(latitude, longitude);
        }
      },
      (error) => {
        console.error('Geolocation error:', error);
        setLocatingDriver(false);
        // ⚠️ NE PAS retomber sur Paris 4 — sinon le chauffeur apparait à un faux endroit
        // pour tous les passagers. On affiche l'erreur et on bloque le tracking.
        let msg = 'Impossible de récupérer ta position GPS.';
        if (error.code === 1) msg = 'Autorise la localisation dans Réglages → Safari → Position pour Métro-Taxi.';
        else if (error.code === 2) msg = 'Signal GPS faible. Sors à l\'extérieur ou redémarre le GPS.';
        else if (error.code === 3) msg = 'GPS trop lent à répondre. Reste à l\'extérieur et reclique sur "ACTIF".';
        setGeoError(msg);
      },
      { enableHighAccuracy: true, maximumAge: 5000, timeout: 30000 }
    );

    return () => navigator.geolocation.clearWatch(watchId);
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

  // Fetch driver earnings summary (used to display total rides & km in the side menu)
  const fetchEarningsSummary = useCallback(async () => {
    try {
      const r = await axios.get(`${API}/drivers/earnings`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setEarningsSummary(r.data);
    } catch (_) { /* silently fail — not critical */ }
  }, [token]);
  
  useEffect(() => {
    fetchEarningsSummary();
    // Refresh after each completed ride
    if (activeRide && activeRide.status === 'completed') {
      fetchEarningsSummary();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeRide?.status]);

  // Fetch pending rides
  const prevPendingCountRef = useRef(0);
  const fetchPendingRides = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/rides/pending`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const rides = response.data.rides || [];
      // 🔔 Beep when a NEW ride request arrives (count increases)
      if (rides.length > prevPendingCountRef.current) {
        playNewRideBeep();
        // Patch V9 — réactive l'alerte visuelle si nouvelle course après dismissal
        setAlertDismissed(false);
      }
      prevPendingCountRef.current = rides.length;
      setPendingRides(rides);
    } catch (error) {
      console.error('Fetch rides error:', error);
    }
  }, [token]);

  // 🔔 Play a "new ride" notification beep using Web Audio API
  // Uses a persistent AudioContext created on first user gesture (toggleActive)
  const playNewRideBeep = async () => {
    try {
      // Create context if not yet (and on iOS this MUST happen during a user gesture)
      if (!audioCtxRef.current) {
        const AC = window.AudioContext || window.webkitAudioContext;
        if (!AC) return;
        audioCtxRef.current = new AC();
      }
      const ctx = audioCtxRef.current;
      // iOS suspends the context after page load — resume it explicitly
      if (ctx.state === 'suspended') {
        try { await ctx.resume(); } catch (_) { /* iOS may reject if not in gesture */ }
      }
      const playTone = (freq, startTime, duration) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.value = freq;
        gain.gain.setValueAtTime(0.6, startTime);
        gain.gain.exponentialRampToValueAtTime(0.001, startTime + duration);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(startTime);
        osc.stop(startTime + duration);
      };
      const t0 = ctx.currentTime;
      // 3-tone urgent pattern spread over 1.5s with clear gaps (audible on Android — fix 18/06)
      playTone(880, t0,        0.30);  // tone 1: 0s → 0.30s
      playTone(660, t0 + 0.50, 0.30);  // tone 2: 0.50s → 0.80s
      playTone(990, t0 + 1.00, 0.50);  // tone 3: 1.00s → 1.50s (longer for emphasis)
      // Vibrate the phone too (Android only — iOS ignores it)
      if (navigator.vibrate) navigator.vibrate([300, 200, 300, 200, 500]);
    } catch (e) {
      console.warn('Audio beep failed:', e);
    }
  };

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

  // 🚨 Patch V9 — Wake Lock + beep en boucle + flash titre tant qu'il y a une course en attente
  // Solution iOS mode silencieux : flash visuel rouge plein écran (voir overlay JSX) +
  // l'écran est maintenu allumé via l'API Wake Lock (iOS 16.4+).
  useEffect(() => {
    let acquired = false;
    const acquireWakeLock = async () => {
      if ('wakeLock' in navigator && isActive) {
        try {
          wakeLockRef.current = await navigator.wakeLock.request('screen');
          acquired = true;
        } catch (_) { /* iOS may refuse if tab is hidden */ }
      }
    };
    acquireWakeLock();
    const onVisible = () => {
      if (document.visibilityState === 'visible' && isActive && !wakeLockRef.current) {
        acquireWakeLock();
      }
    };
    document.addEventListener('visibilitychange', onVisible);
    return () => {
      document.removeEventListener('visibilitychange', onVisible);
      if (acquired && wakeLockRef.current) {
        try { wakeLockRef.current.release(); } catch (_) { /* released anyway */ }
        wakeLockRef.current = null;
      }
    };
  }, [isActive]);

  // 🔁 Beep + vibration en boucle (toutes les 2s) tant qu'une course est en attente
  // et que le chauffeur n'a pas dismissé l'alerte. Sur Android le bip retentit, sur
  // iOS en silencieux c'est la vibration + le flash visuel qui prennent le relais.
  const showAlert = pendingRides.length > 0 && !alertDismissed && !activeRide;
  useEffect(() => {
    if (!showAlert) return;
    const interval = setInterval(() => {
      playNewRideBeep();
    }, 2000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showAlert]);

  // 🔔 Flash du titre de l'onglet ("🚨 COURSE !") tant que l'alerte est active —
  // utile si le chauffeur a switché d'onglet ou si l'iPhone est en standby (visible
  // sur le centre de notifications).
  useEffect(() => {
    if (!showAlert) return;
    const originalTitle = document.title;
    let toggle = false;
    const interval = setInterval(() => {
      toggle = !toggle;
      document.title = toggle ? '🚨 NOUVELLE COURSE !' : '⚪ Métro-Taxi';
    }, 700);
    return () => {
      clearInterval(interval);
      document.title = originalTitle;
    };
  }, [showAlert]);

  // 💓 Heartbeat: push driver position to server every 30s even if not moving,
  // and immediately when app returns to foreground. Prevents "ghost driver" stale GPS.
  useEffect(() => {
    if (!isActive || !driverLocation) return;
    const heartbeat = setInterval(() => {
      updateDriverLocation(driverLocation[0], driverLocation[1]);
    }, 30000);
    const onVisibilityChange = () => {
      if (document.visibilityState === 'visible' && driverLocation) {
        updateDriverLocation(driverLocation[0], driverLocation[1]);
        // Patch V9.1 — Au retour foreground iOS, l'AudioContext est suspendu.
        // Tente une resume (peut échouer sans gesture, mais ça vaut le coup d'essayer).
        if (audioCtxRef.current && audioCtxRef.current.state === 'suspended') {
          audioCtxRef.current.resume().catch(() => {});
        }
      }
    };
    document.addEventListener('visibilitychange', onVisibilityChange);
    return () => {
      clearInterval(heartbeat);
      document.removeEventListener('visibilitychange', onVisibilityChange);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isActive, driverLocation]);

  const toggleActive = async () => {
    // 🔊 Initialize AudioContext on this user-gesture (iOS Safari requirement for autoplay)
    // Patch V9.1 : démarre un oscillateur silencieux CONTINU pour empêcher iOS de
    // suspendre l'audio session après inactivité (sans ça, le 2e bip ne sonne pas).
    if (!audioCtxRef.current) {
      try {
        const AC = window.AudioContext || window.webkitAudioContext;
        if (AC) {
          audioCtxRef.current = new AC();
          const ctx = audioCtxRef.current;
          if (ctx.state === 'suspended') await ctx.resume();
          // Keep-alive : oscillateur silencieux qui tourne en permanence à gain quasi-zéro
          const keepAliveOsc = ctx.createOscillator();
          const keepAliveGain = ctx.createGain();
          keepAliveOsc.type = 'sine';
          keepAliveOsc.frequency.value = 1; // 1 Hz inaudible
          keepAliveGain.gain.value = 0.00001; // gain quasi-zéro
          keepAliveOsc.connect(keepAliveGain);
          keepAliveGain.connect(ctx.destination);
          keepAliveOsc.start();
          keepAliveRef.current = keepAliveOsc;
        }
      } catch (_) { /* AudioContext may fail to init on very old browsers */ }
    } else {
      // Si AudioContext existe déjà mais suspendu (ex: nouvelle session après backgrounding),
      // ce gesture est l'occasion de le relancer.
      try {
        if (audioCtxRef.current.state === 'suspended') await audioCtxRef.current.resume();
      } catch (_) { /* iOS may reject without gesture */ }
    }
    setLoading(true);
    try {
      const response = await axios.post(`${API}/drivers/toggle-active`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setIsActive(response.data.is_active);
      toast.success(response.data.is_active ? t('common.nowOnline') : t('common.nowOffline'));
      
      if (response.data.is_active && driverLocation) {
        updateDriverLocation(driverLocation[0], driverLocation[1]);
      }
      // Quand le chauffeur se déconnecte, arrête le keep-alive pour économiser la batterie
      if (!response.data.is_active && keepAliveRef.current) {
        try { keepAliveRef.current.stop(); } catch (_) { /* already stopped */ }
        keepAliveRef.current = null;
      }
    } catch (error) {
      toast.error(t('common.statusChangeError'));
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
      toast.success(t('common.rideAccepted'));
      fetchPendingRides();
      fetchActiveRide();
      setAvailableSeats(prev => Math.max(0, prev - 1));
    } catch (error) {
      toast.error(t('common.acceptError'));
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
      toast.info(t('common.requestDeclined'));
      fetchPendingRides();
    } catch (error) {
      toast.error(t('common.declineError'));
    } finally {
      setLoading(false);
    }
  };

  const arriveAtPickup = async (rideId) => {
    setLoading(true);
    try {
      await axios.post(`${API}/rides/${rideId}/progress`, {
        ride_id: rideId,
        status: 'pickup',
        current_lat: driverLocation?.[0],
        current_lng: driverLocation?.[1],
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Le passager a été notifié de ton arrivée");
      fetchActiveRide();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erreur signalement arrivée");
    } finally {
      setLoading(false);
    }
  };

  const startTrip = async (rideId, otp) => {
    if (!otp || otp.length !== 4) {
      toast.error("Demande au passager son code à 4 chiffres affiché dans son app");
      return false;
    }
    setLoading(true);
    try {
      await axios.post(`${API}/rides/${rideId}/progress`, {
        ride_id: rideId,
        status: 'in_progress',
        pickup_otp: otp,
        current_lat: driverLocation?.[0],
        current_lng: driverLocation?.[1],
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Trajet démarré — bonne route !");
      fetchActiveRide();
      return true;
    } catch (error) {
      toast.error(error.response?.data?.detail || "Code incorrect");
      return false;
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
      toast.success(t('common.rideCompleted'));
      setActiveRide(null);
      setAvailableSeats(prev => Math.min(driver?.seats || 4, prev + 1));
      fetchActiveRide();
    } catch (error) {
      toast.error(t('common.completeError'));
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
      {/* 🚨 Patch V9 — OVERLAY VISUEL ROUGE PLEIN ÉCRAN
          Contourne le blocage audio iOS (mode silencieux physique).
          Reste visible tant qu'une course est en attente et que le chauffeur
          n'a pas tapé "Voir la course". Anti-doom : un bouton dismiss permet
          de basculer sur la card classique sans rater l'info. */}
      <AnimatePresence>
        {showAlert && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[3000] flex flex-col items-center justify-center p-6"
            data-testid="ios-ride-alert-overlay"
            style={{
              background: 'linear-gradient(135deg, #dc2626 0%, #991b1b 100%)',
              animation: 'metroFlash 0.6s ease-in-out infinite alternate',
            }}
          >
            <style>{`
              @keyframes metroFlash {
                0%   { background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%); }
                100% { background: linear-gradient(135deg, #fbbf24 0%, #dc2626 100%); }
              }
            `}</style>
            <BellRing className="w-24 h-24 text-white mb-4 animate-bounce" strokeWidth={2.5} />
            <h1 className="text-white text-5xl font-black uppercase tracking-wider mb-2 text-center drop-shadow-lg">
              Nouvelle course !
            </h1>
            <p className="text-white/90 text-xl font-bold mb-8 text-center">
              {pendingRides.length} demande{pendingRides.length > 1 ? 's' : ''} en attente
            </p>
            {pendingRides[0] && (
              <div className="bg-black/40 backdrop-blur-sm border-2 border-white/30 rounded-2xl p-5 mb-6 max-w-md w-full">
                <p className="text-white font-bold text-lg mb-1">{pendingRides[0].user_name}</p>
                {pendingRides[0].estimated_payout != null && (
                  <p className="text-yellow-300 text-2xl font-black">
                    ~ {pendingRides[0].estimated_payout.toFixed(2)} € <span className="text-base font-normal italic">estimé · {pendingRides[0].estimated_km} km</span>
                  </p>
                )}
                <p className="text-white/80 text-sm mt-2 truncate">
                  📍 {pendingRides[0].pickup_address || 'Adresse en cours...'}
                </p>
              </div>
            )}
            <Button
              onClick={() => setAlertDismissed(true)}
              className="bg-white text-red-700 font-black text-xl h-16 px-12 rounded-full shadow-2xl hover:bg-zinc-100 hover:scale-105 transition-transform"
              data-testid="dismiss-ios-alert-btn"
            >
              VOIR LA COURSE →
            </Button>
            <p className="text-white/70 text-xs mt-6 text-center max-w-xs">
              💡 Tape ci-dessus pour ouvrir la fiche et accepter / refuser la course
            </p>
          </motion.div>
        )}
      </AnimatePresence>

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
                
                {/* 📊 Stats trajets (compteurs ajoutés 18/06 — demande Capitaine) */}
                {earningsSummary && (
                  <div className="grid grid-cols-2 gap-2">
                    <div className="bg-zinc-900 p-3 rounded border border-zinc-800">
                      <p className="text-zinc-500 text-[10px] uppercase tracking-wider">Trajets ce mois</p>
                      <p className="text-white font-bold text-xl" data-testid="rides-current-month">
                        {earningsSummary.current_month?.rides_count || 0}
                      </p>
                      <p className="text-[10px] text-zinc-500">
                        {(earningsSummary.current_month?.total_km || 0).toFixed(1)} km
                      </p>
                    </div>
                    <div className="bg-zinc-900 p-3 rounded border border-zinc-800">
                      <p className="text-zinc-500 text-[10px] uppercase tracking-wider">Total trajets</p>
                      <p className="text-[#FFD60A] font-bold text-xl" data-testid="rides-total">
                        {earningsSummary.totals?.total_rides || 0}
                      </p>
                      <p className="text-[10px] text-zinc-500">
                        {(earningsSummary.totals?.total_km || 0).toFixed(0)} km
                      </p>
                    </div>
                  </div>
                )}
                {driver?.region_id && (
                  <div className="bg-zinc-900 p-4 rounded border border-zinc-800">
                    <p className="text-zinc-400 text-sm flex items-center gap-2">
                      <Globe className="w-4 h-4" />
                      {t('dashboard.driver.region', 'Région')}
                    </p>
                    <p className="text-[#FFD60A] font-medium capitalize">{driver.region_id}</p>
                  </div>
                )}
              </div>
              
              {/* Earnings Button */}
              <Button 
                variant="ghost" 
                className="w-full justify-start text-[#FFD60A] hover:bg-[#FFD60A]/10 mb-4"
                onClick={() => {
                  setShowEarnings(true);
                  setMenuOpen(false);
                }}
                data-testid="driver-earnings-btn"
              >
                <Wallet className="w-5 h-5 mr-3" />
                {t('dashboard.driver.myEarnings', 'Mes Revenus')}
              </Button>
              
              <Button 
                variant="ghost" 
                className="w-full justify-start text-zinc-300 hover:bg-zinc-800"
                onClick={() => { setShowHelp(true); setMenuOpen(false); }}
                data-testid="driver-help-btn"
              >
                <HelpCircle className="w-5 h-5 mr-3 text-[#FFD60A]" />
                {t('help.button', 'AIDE')}
              </Button>

              <Button
                variant="ghost"
                className="w-full justify-start text-zinc-300 hover:bg-zinc-800"
                onClick={() => { setShowChangePassword(true); setMenuOpen(false); }}
                data-testid="driver-change-password-btn"
              >
                <KeyRound className="w-5 h-5 mr-3 text-[#FFD60A]" />
                Changer le mot de passe
              </Button>
              
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
      {locatingDriver ? (
        <div className="h-full w-full flex flex-col items-center justify-center bg-zinc-900">
          <Loader2 className="w-12 h-12 text-[#FFD60A] animate-spin mb-4" />
          <p className="text-white text-lg">{t('dashboard.user.locating', 'Localisation en cours...')}</p>
        </div>
      ) : geoError ? (
        <div data-testid="gps-error-screen" className="h-full w-full flex flex-col items-center justify-center bg-zinc-900 p-6 text-center">
          <div className="bg-red-600 text-white p-4 rounded-full mb-6">
            <svg xmlns="http://www.w3.org/2000/svg" className="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5a2.5 2.5 0 110-5 2.5 2.5 0 010 5z" />
              <line x1="3" y1="3" x2="21" y2="21" stroke="white" strokeWidth="3" />
            </svg>
          </div>
          <h2 className="text-white text-xl font-bold mb-3">GPS indisponible</h2>
          <p className="text-zinc-300 text-base mb-6 max-w-md">{geoError}</p>
          <button
            data-testid="gps-retry-button"
            onClick={() => { setGeoError(null); setLocatingDriver(true); setIsActive(false); setTimeout(() => setIsActive(prev => prev), 100); window.location.reload(); }}
            className="bg-[#FFD60A] text-black font-bold px-6 py-3 rounded-lg"
          >
            Réessayer
          </button>
          <p className="text-zinc-500 text-xs mt-6 max-w-md">
            iPhone&nbsp;: Réglages → Confidentialité → Service de localisation → Safari → «&nbsp;Toujours&nbsp;» ou «&nbsp;En utilisant l&apos;app&nbsp;».
          </p>
        </div>
      ) : (
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
        <MapUpdater
          center={driverLocation}
          fitBounds={
            activeRide && activeRide.status === 'accepted' && activeRide.pickup_lat && driverLocation
              ? [driverLocation, [activeRide.pickup_lat, activeRide.pickup_lng]]
              : null
          }
          rideAcceptedKey={activeRide && activeRide.status === 'accepted' ? activeRide.id : null}
        />
        
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

        {/* Active ride pickup marker — keeps passenger visible until boarding */}
        {activeRide && activeRide.pickup_lat && activeRide.pickup_lng && ['accepted', 'pickup', 'in_progress'].includes(activeRide.status) && (
          <Marker
            position={[activeRide.pickup_lat, activeRide.pickup_lng]}
            icon={userRequestIcon}
          >
            <Popup>
              <div className="p-2 min-w-[200px]">
                <p className="font-bold text-zinc-900">{activeRide.user_name}</p>
                <p className="text-xs text-zinc-500 mb-1">
                  {activeRide.status === 'accepted' ? '🚗 Va le chercher ici' :
                   activeRide.status === 'pickup' ? '⏳ Sur place — attends le code OTP' :
                   '✅ Passager à bord'}
                </p>
              </div>
            </Popup>
          </Marker>
        )}
      </MapContainer>
      )}

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
                      {ride.estimated_payout != null && (
                        <div className="text-right">
                          <p className="text-[#FFD60A] font-black text-xl leading-none">~ {ride.estimated_payout.toFixed(2)} €</p>
                          <p className="text-xs text-zinc-400 italic">estimé · {ride.estimated_km} km · {ride.rate_per_km}€/km</p>
                        </div>
                      )}
                    </div>
                    
                    {/* Pickup + Destination addresses — visible BEFORE accept (UX 18/06) */}
                    <div className="space-y-2 mb-3 text-sm">
                      <div className="flex gap-2 items-start">
                        <span className="text-green-400 mt-0.5">●</span>
                        <div className="flex-1">
                          <p className="text-xs text-zinc-500 uppercase tracking-wider">Prise en charge</p>
                          <p className="text-white text-sm leading-tight" data-testid={`pickup-address-${ride.id}`}>
                            {ride.pickup_address || `${ride.pickup_lat?.toFixed(5)}, ${ride.pickup_lng?.toFixed(5)}`}
                          </p>
                        </div>
                      </div>
                      <div className="flex gap-2 items-start">
                        <span className="text-red-400 mt-0.5">●</span>
                        <div className="flex-1">
                          <p className="text-xs text-zinc-500 uppercase tracking-wider">Destination</p>
                          <p className="text-white text-sm leading-tight" data-testid={`destination-address-${ride.id}`}>
                            {ride.destination_address || `${ride.destination_lat?.toFixed(5)}, ${ride.destination_lng?.toFixed(5)}`}
                          </p>
                        </div>
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
                <span className={`text-xs px-2 py-1 rounded border ${
                  activeRide.status === 'in_progress' ? 'bg-blue-500/20 text-blue-400 border-blue-500/50' :
                  activeRide.status === 'pickup' ? 'bg-purple-500/20 text-purple-400 border-purple-500/50' :
                  'bg-yellow-500/20 text-yellow-400 border-yellow-500/50'
                }`}>
                  {activeRide.status === 'in_progress' ? 'EN COURSE' :
                   activeRide.status === 'pickup' ? 'SUR PLACE' :
                   'EN ROUTE VERS PASSAGER'}
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

              {/* Step 1: Driver en route → bouton "J'arrive" */}
              {activeRide.status === 'accepted' && (
                <Button
                  onClick={() => arriveAtPickup(activeRide.id)}
                  disabled={loading}
                  className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold h-12"
                  data-testid="arrive-pickup-btn"
                >
                  <MapPin className="w-5 h-5 mr-2" />
                  JE SUIS ARRIVÉ AU POINT DE PRISE EN CHARGE
                </Button>
              )}

              {/* Step 2: Sur place → demande OTP au passager */}
              {activeRide.status === 'pickup' && (
                <div className="space-y-3">
                  <div className="bg-purple-500/10 border border-purple-500/30 rounded p-3">
                    <p className="text-purple-300 text-sm font-medium mb-1">🔐 Code embarquement</p>
                    <p className="text-zinc-300 text-xs">Demande au passager les 4 chiffres affichés dans son app. Ne démarre PAS la course sans ce code.</p>
                  </div>
                  <input
                    type="tel"
                    inputMode="numeric"
                    maxLength={4}
                    pattern="[0-9]{4}"
                    value={otpInput}
                    onChange={(e) => setOtpInput(e.target.value.replace(/\D/g, '').slice(0, 4))}
                    placeholder="• • • •"
                    className="w-full text-center text-3xl font-mono tracking-[1rem] bg-zinc-900 border-2 border-zinc-700 rounded h-16 text-white focus:border-[#FFD60A] focus:outline-none"
                    data-testid="otp-input"
                  />
                  <Button
                    onClick={async () => {
                      const ok = await startTrip(activeRide.id, otpInput);
                      if (ok) setOtpInput('');
                    }}
                    disabled={loading || otpInput.length !== 4}
                    className="w-full bg-green-600 hover:bg-green-700 text-white font-bold h-12 disabled:opacity-50"
                    data-testid="start-trip-btn"
                  >
                    <Check className="w-5 h-5 mr-2" />
                    VALIDER LE CODE & DÉMARRER LA COURSE
                  </Button>
                </div>
              )}

              {/* Step 3: In progress → bouton "Trajet terminé" */}
              {activeRide.status === 'in_progress' && (
                <Button
                  onClick={() => completeRide(activeRide.id)}
                  disabled={loading}
                  className="w-full bg-green-600 hover:bg-green-700 text-white font-bold h-12"
                  data-testid="complete-ride-btn"
                >
                  <Check className="w-5 h-5 mr-2" />
                  TRAJET TERMINÉ — DÉPOSER LE PASSAGER
                </Button>
              )}
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

      {/* Earnings Panel */}
      <AnimatePresence>
        {showEarnings && (
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25 }}
            className="fixed inset-0 z-[2000] bg-[#09090B]"
          >
            <div className="h-full flex flex-col">
              {/* Header */}
              <div className="flex items-center gap-4 p-4 border-b border-zinc-800 bg-[#18181B]">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowEarnings(false)}
                  className="text-white hover:bg-zinc-800"
                  data-testid="earnings-back-btn"
                >
                  <ArrowLeft className="w-5 h-5" />
                </Button>
                <div className="flex items-center gap-2">
                  <Car className="w-6 h-6 text-[#FFD60A]" />
                  <span className="text-xl font-bold text-white">MÉTRO-TAXI</span>
                </div>
              </div>
              
              {/* Content */}
              <div className="flex-1 overflow-hidden">
                <DriverEarnings onClose={() => setShowEarnings(false)} />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Help Center */}
      <HelpCenter 
        isOpen={showHelp} 
        onClose={() => setShowHelp(false)} 
        userType="driver" 
      />

      {/* Patch V9 — Modale changement de mot de passe */}
      <ChangePasswordModal open={showChangePassword} onClose={() => setShowChangePassword(false)} />
    </div>
  );
};

export default DriverDashboard;
