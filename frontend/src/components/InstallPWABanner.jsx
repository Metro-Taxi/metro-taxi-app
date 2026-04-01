import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { X, Download, Smartphone, Share, Plus } from 'lucide-react';
import { canInstallPWA, installPWA, isPWAInstalled } from '../serviceWorkerRegistration';

const InstallPWABanner = () => {
  const { t } = useTranslation();
  const [showBanner, setShowBanner] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [isInstallable, setIsInstallable] = useState(false);
  const [isIOS, setIsIOS] = useState(false);
  const [isAndroid, setIsAndroid] = useState(false);

  useEffect(() => {
    // Detect device type
    const userAgent = navigator.userAgent || navigator.vendor;
    const isMobileDevice = /iPhone|iPad|iPod|Android/i.test(userAgent);
    const isiOSDevice = /iPhone|iPad|iPod/i.test(userAgent);
    const isAndroidDevice = /Android/i.test(userAgent);
    
    setIsIOS(isiOSDevice);
    setIsAndroid(isAndroidDevice);

    // Only show on mobile devices
    if (!isMobileDevice) {
      return; // Never show on desktop
    }

    // Don't show if already installed as PWA
    if (isPWAInstalled()) {
      return;
    }

    // Check if banner was dismissed
    const checkDismissed = localStorage.getItem('pwa-banner-dismissed');
    if (checkDismissed) {
      const dismissedTime = parseInt(checkDismissed, 10);
      // Show again after 3 days (reduced from 7)
      if (Date.now() - dismissedTime < 3 * 24 * 60 * 60 * 1000) {
        setDismissed(true);
        return;
      } else {
        // Clear old dismissal
        localStorage.removeItem('pwa-banner-dismissed');
      }
    }

    // Check for install prompt availability
    const checkInstallable = () => {
      const canInstall = canInstallPWA();
      setIsInstallable(canInstall);
    };

    // Check immediately
    checkInstallable();
    
    // Listen for beforeinstallprompt
    const handleBeforeInstall = () => {
      setIsInstallable(true);
      setShowBanner(true);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstall);

    // ALWAYS show banner after 3 seconds on mobile (even without beforeinstallprompt)
    // This ensures users see the installation option
    const timer = setTimeout(() => {
      if (!dismissed && !isPWAInstalled()) {
        setShowBanner(true);
      }
    }, 3000);

    return () => {
      clearTimeout(timer);
      window.removeEventListener('beforeinstallprompt', handleBeforeInstall);
    };
  }, [dismissed]);

  const handleInstall = async () => {
    const installed = await installPWA();
    if (installed) {
      setShowBanner(false);
    }
  };

  const handleDismiss = () => {
    localStorage.setItem('pwa-banner-dismissed', Date.now().toString());
    setDismissed(true);
    setShowBanner(false);
  };

  if (!showBanner || dismissed || isPWAInstalled()) {
    return null;
  }

  return (
    <div 
      className="fixed bottom-20 left-4 right-4 md:left-auto md:right-4 md:w-96 bg-gradient-to-r from-yellow-500 to-yellow-400 text-black rounded-2xl shadow-2xl z-50 overflow-hidden animate-slide-up"
      data-testid="pwa-install-banner"
    >
      <div className="p-4">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 w-12 h-12 bg-black rounded-xl flex items-center justify-center">
            <Smartphone className="w-6 h-6 text-yellow-400" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-bold text-lg">
              {t('pwa.installTitle', 'Installer Métro-Taxi')}
            </h3>
            <p className="text-sm opacity-80 mt-1">
              {t('pwa.installDescription', 'Ajoutez l\'application sur votre écran d\'accueil pour un accès rapide')}
            </p>
          </div>
          <button
            onClick={handleDismiss}
            className="flex-shrink-0 p-1 hover:bg-black/10 rounded-full transition-colors"
            aria-label="Fermer"
            data-testid="pwa-dismiss-btn"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <div className="mt-4">
          {isInstallable ? (
            // Native install button (Android Chrome mainly)
            <div className="flex gap-2">
              <button
                onClick={handleInstall}
                className="flex-1 bg-black text-yellow-400 font-semibold py-2.5 px-4 rounded-xl flex items-center justify-center gap-2 hover:bg-gray-900 transition-colors"
                data-testid="pwa-install-btn"
              >
                <Download className="w-4 h-4" />
                {t('pwa.installButton', 'Installer')}
              </button>
              <button
                onClick={handleDismiss}
                className="px-4 py-2.5 border-2 border-black/20 rounded-xl font-medium hover:bg-black/10 transition-colors"
                data-testid="pwa-later-btn"
              >
                {t('pwa.later', 'Plus tard')}
              </button>
            </div>
          ) : isIOS ? (
            // iOS Safari instructions
            <div className="bg-black/10 rounded-xl p-3">
              <p className="font-semibold text-sm mb-2 flex items-center gap-2">
                <Share className="w-4 h-4" />
                {t('pwa.iosTitle', 'Pour installer sur iPhone/iPad :')}
              </p>
              <ol className="text-sm opacity-90 space-y-1 ml-6 list-decimal">
                <li>{t('pwa.iosStep1', 'Appuyez sur le bouton Partager')}<Share className="w-3 h-3 inline ml-1" /></li>
                <li>{t('pwa.iosStep2', 'Faites défiler et appuyez sur "Sur l\'écran d\'accueil"')}</li>
                <li>{t('pwa.iosStep3', 'Appuyez sur "Ajouter"')}</li>
              </ol>
              <button
                onClick={handleDismiss}
                className="mt-3 w-full py-2 border-2 border-black/20 rounded-xl font-medium hover:bg-black/10 transition-colors text-sm"
              >
                {t('pwa.understood', 'J\'ai compris')}
              </button>
            </div>
          ) : isAndroid ? (
            // Android Chrome instructions (when beforeinstallprompt not available)
            <div className="bg-black/10 rounded-xl p-3">
              <p className="font-semibold text-sm mb-2 flex items-center gap-2">
                <Plus className="w-4 h-4" />
                {t('pwa.androidTitle', 'Pour installer sur Android :')}
              </p>
              <ol className="text-sm opacity-90 space-y-1 ml-6 list-decimal">
                <li>{t('pwa.androidStep1', 'Appuyez sur le menu ⋮ en haut à droite')}</li>
                <li>{t('pwa.androidStep2', 'Sélectionnez "Installer l\'application" ou "Ajouter à l\'écran d\'accueil"')}</li>
              </ol>
              <button
                onClick={handleDismiss}
                className="mt-3 w-full py-2 border-2 border-black/20 rounded-xl font-medium hover:bg-black/10 transition-colors text-sm"
              >
                {t('pwa.understood', 'J\'ai compris')}
              </button>
            </div>
          ) : (
            // Fallback generic instructions
            <div className="flex gap-2">
              <div className="flex-1 text-sm bg-black/10 rounded-xl p-3">
                <p className="font-medium">{t('pwa.genericInstructions', 'Utilisez le menu de votre navigateur pour ajouter cette page à votre écran d\'accueil')}</p>
              </div>
              <button
                onClick={handleDismiss}
                className="px-4 py-2.5 border-2 border-black/20 rounded-xl font-medium hover:bg-black/10 transition-colors"
              >
                {t('pwa.later', 'Plus tard')}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default InstallPWABanner;
