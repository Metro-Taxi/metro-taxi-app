import React, { useState, useEffect } from 'react';
import { Bell, BellOff, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import { notificationService } from './NotificationCenter';

/**
 * Bouton pour activer les Web Push Notifications.
 * Compatible iOS 16.4+ (nécessite que l'app soit installée à l'écran d'accueil PWA).
 * Sur Android/Desktop, marche directement.
 */
const EnableNotificationsButton = ({ token, variant = 'default' }) => {
  const [permission, setPermission] = useState(
    typeof Notification !== 'undefined' ? Notification.permission : 'default'
  );
  const [subscribing, setSubscribing] = useState(false);
  const [isIOSStandalone, setIsIOSStandalone] = useState(false);
  const [isIOSNotInstalled, setIsIOSNotInstalled] = useState(false);

  useEffect(() => {
    // Détection iOS
    const ua = navigator.userAgent.toLowerCase();
    const isIOS = /iphone|ipad|ipod/.test(ua) || (ua.includes('mac') && 'ontouchend' in document);
    // PWA installée = mode standalone
    const standalone = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;
    setIsIOSStandalone(isIOS && standalone);
    setIsIOSNotInstalled(isIOS && !standalone);
  }, []);

  const handleEnable = async () => {
    if (!('Notification' in window) || !('serviceWorker' in navigator) || !('PushManager' in window)) {
      toast.error("Ton navigateur ne supporte pas les notifications push.");
      return;
    }
    setSubscribing(true);
    try {
      const granted = await notificationService.requestPermission();
      setPermission(Notification.permission);
      if (!granted) {
        toast.error("Permission refusée. Tu peux la réactiver dans les réglages de ton navigateur.");
        return;
      }
      const ok = await notificationService.subscribeToPush(token);
      if (ok) {
        toast.success("✅ Notifications activées ! Tu recevras une alerte même app fermée.");
      } else {
        toast.error("Échec de l'abonnement push. Réessaie.");
      }
    } catch (e) {
      console.error('Push subscribe error:', e);
      toast.error("Erreur lors de l'activation des notifications.");
    } finally {
      setSubscribing(false);
    }
  };

  // Si iOS sans PWA installée → message explicatif
  if (isIOSNotInstalled) {
    return (
      <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-3 text-xs text-blue-200" data-testid="ios-install-pwa-notice">
        <p className="font-bold mb-1">📲 Notifications iOS : installe d&apos;abord l&apos;app</p>
        <p>Sur iPhone, tape sur <b>Partager</b> (carré + flèche) puis <b>« Sur l&apos;écran d&apos;accueil »</b>. Relance ensuite l&apos;app depuis l&apos;icône pour activer les notifs.</p>
      </div>
    );
  }

  // Déjà accordé : badge vert
  if (permission === 'granted') {
    return (
      <div className="flex items-center gap-2 text-xs text-green-400" data-testid="notifications-enabled-badge">
        <Check className="w-4 h-4" />
        Notifications activées
      </div>
    );
  }

  // Refusé : message
  if (permission === 'denied') {
    return (
      <div className="flex items-center gap-2 text-xs text-zinc-500" data-testid="notifications-denied-badge">
        <BellOff className="w-4 h-4" />
        Notifications bloquées (réglages du navigateur)
      </div>
    );
  }

  // Bouton d'activation
  return (
    <Button
      onClick={handleEnable}
      disabled={subscribing}
      className={variant === 'compact'
        ? "bg-[#FFD60A] hover:bg-yellow-400 text-black text-xs font-bold py-2 px-3 flex items-center gap-2"
        : "bg-[#FFD60A] hover:bg-yellow-400 text-black font-bold py-3 px-4 flex items-center gap-2 w-full"}
      data-testid="enable-notifications-btn"
    >
      <Bell className="w-4 h-4" />
      {subscribing ? "Activation..." : "Activer les notifications"}
    </Button>
  );
};

export default EnableNotificationsButton;
