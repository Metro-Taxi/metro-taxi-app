import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, X, Check, CheckCheck, Trash2, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Helper function to convert base64 URL-safe string to Uint8Array
function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/-/g, '+')
    .replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

// Service for managing push notifications
export const notificationService = {
  async requestPermission() {
    if (!('Notification' in window)) {
      console.log('This browser does not support notifications');
      return false;
    }

    const permission = await Notification.requestPermission();
    return permission === 'granted';
  },

  async subscribeToPush(token) {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
      console.log('Push notifications not supported');
      return false;
    }

    try {
      // Get VAPID public key from backend
      const vapidResponse = await axios.get(`${API}/notifications/vapid-public-key`);
      const vapidPublicKey = vapidResponse.data.publicKey;
      
      if (!vapidPublicKey) {
        console.log('VAPID public key not available');
        return false;
      }

      const registration = await navigator.serviceWorker.ready;
      
      // Subscribe with real VAPID key
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(vapidPublicKey)
      });

      // Send subscription to backend
      await axios.post(
        `${API}/notifications/subscribe`,
        subscription.toJSON(),
        { headers: { Authorization: `Bearer ${token}` } }
      );

      console.log('Push notification subscription successful');
      return true;
    } catch (error) {
      console.error('Failed to subscribe to push:', error);
      return false;
    }
  },

  showLocalNotification(title, options = {}) {
    if (Notification.permission === 'granted') {
      new Notification(title, {
        icon: '/icons/icon-192x192.png',
        badge: '/icons/icon-72x72.png',
        ...options
      });
    }
  }
};

const NotificationCenter = () => {
  const { token } = useAuth();
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    if (token) {
      fetchNotifications();
      // Poll for new notifications every 30 seconds
      const interval = setInterval(fetchNotifications, 30000);
      return () => clearInterval(interval);
    }
  }, [token]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchNotifications = async () => {
    try {
      const response = await axios.get(`${API}/notifications?limit=20`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setNotifications(response.data.notifications);
      setUnreadCount(response.data.unread_count);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  };

  const markAsRead = async (notificationId) => {
    try {
      await axios.put(
        `${API}/notifications/${notificationId}/read`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      fetchNotifications();
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      await axios.put(
        `${API}/notifications/read-all`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      fetchNotifications();
      toast.success(t('notifications.allRead', 'All notifications marked as read'));
    } catch (error) {
      console.error('Error marking all as read:', error);
    }
  };

  const formatTime = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;
    
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return t('notifications.justNow', 'Just now');
    if (minutes < 60) return `${minutes}m`;
    if (hours < 24) return `${hours}h`;
    if (days < 7) return `${days}d`;
    
    return date.toLocaleDateString(i18n.language);
  };

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'ride_accepted': return '🚗';
      case 'driver_arrived': return '📍';
      case 'rating': return '⭐';
      case 'subscription': return '💳';
      case 'subscription_expiry': return '⚠️';
      case 'payout': return '💰';
      default: return '🔔';
    }
  };

  const handleNotificationAction = (notif) => {
    // Mark as read first
    if (!notif.read) {
      markAsRead(notif.id);
    }
    
    // Handle subscription expiry action
    if (notif.data?.type === 'subscription_expiry' && notif.data?.action === 'renew') {
      setIsOpen(false);
      navigate('/subscription');
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-lg hover:bg-zinc-800 transition-colors"
        data-testid="notification-bell"
      >
        <Bell className="w-5 h-5 text-zinc-400" />
        {unreadCount > 0 && (
          <motion.span
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="absolute -top-1 -right-1 w-5 h-5 bg-[#FFD60A] text-black text-xs font-bold rounded-full flex items-center justify-center"
          >
            {unreadCount > 9 ? '9+' : unreadCount}
          </motion.span>
        )}
      </button>

      {/* Dropdown */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            className="absolute right-0 top-full mt-2 w-80 bg-zinc-900 border border-zinc-800 rounded-xl shadow-2xl overflow-hidden z-50"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800">
              <h3 className="text-white font-medium">
                {t('notifications.title', 'Notifications')}
              </h3>
              {unreadCount > 0 && (
                <button
                  onClick={markAllAsRead}
                  className="text-xs text-[#FFD60A] hover:text-[#FFE55C] flex items-center gap-1"
                >
                  <CheckCheck className="w-3 h-3" />
                  {t('notifications.markAllRead', 'Mark all read')}
                </button>
              )}
            </div>

            {/* Notifications list */}
            <div className="max-h-96 overflow-y-auto">
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="w-6 h-6 border-2 border-[#FFD60A] border-t-transparent rounded-full animate-spin" />
                </div>
              ) : notifications.length === 0 ? (
                <div className="text-center py-8">
                  <Bell className="w-12 h-12 text-zinc-700 mx-auto mb-2" />
                  <p className="text-zinc-500 text-sm">
                    {t('notifications.empty', 'No notifications yet')}
                  </p>
                </div>
              ) : (
                <div>
                  {notifications.map((notif) => (
                    <motion.div
                      key={notif.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className={`px-4 py-3 border-b border-zinc-800/50 hover:bg-zinc-800/50 transition-colors ${
                        !notif.read ? 'bg-[#FFD60A]/5' : ''
                      } ${notif.data?.type === 'subscription_expiry' ? 'bg-orange-500/10 border-l-2 border-l-orange-500' : ''}`}
                    >
                      <div className="flex items-start gap-3">
                        <span className="text-xl">
                          {getNotificationIcon(notif.data?.type)}
                        </span>
                        <div className="flex-1 min-w-0">
                          <p className={`text-sm ${notif.read ? 'text-zinc-400' : 'text-white font-medium'}`}>
                            {notif.title}
                          </p>
                          <p className="text-zinc-500 text-xs mt-0.5 line-clamp-2">
                            {notif.body}
                          </p>
                          
                          {/* Subscription Expiry Action Button */}
                          {notif.data?.type === 'subscription_expiry' && notif.data?.action === 'renew' && (
                            <button
                              onClick={() => handleNotificationAction(notif)}
                              className="mt-2 flex items-center gap-1.5 bg-[#FFD60A] text-black text-xs font-bold px-3 py-1.5 rounded-lg hover:bg-[#FFE55C] transition-colors"
                              data-testid="renew-subscription-btn"
                            >
                              <RefreshCw className="w-3 h-3" />
                              {t('notifications.renewNow', 'Renouveler maintenant')}
                            </button>
                          )}
                          
                          <p className="text-zinc-600 text-xs mt-1">
                            {formatTime(notif.created_at)}
                          </p>
                        </div>
                        {!notif.read && (
                          <div className="w-2 h-2 bg-[#FFD60A] rounded-full flex-shrink-0 mt-1.5" />
                        )}
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default NotificationCenter;
