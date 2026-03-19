import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { X, Download, Smartphone } from 'lucide-react';
import { canInstallPWA, installPWA, isPWAInstalled } from '../serviceWorkerRegistration';

const InstallPWABanner = () => {
  const { t } = useTranslation();
  const [showBanner, setShowBanner] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [isInstallable, setIsInstallable] = useState(false);

  useEffect(() => {
    // Only show on mobile devices
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
    if (!isMobile) {
      return; // Never show on desktop
    }

    // Don't show if already installed
    if (isPWAInstalled()) {
      return;
    }

    const checkDismissed = localStorage.getItem('pwa-banner-dismissed');
    if (checkDismissed) {
      const dismissedTime = parseInt(checkDismissed, 10);
      // Show again after 7 days
      if (Date.now() - dismissedTime < 7 * 24 * 60 * 60 * 1000) {
        setDismissed(true);
        return;
      }
    }

    // Check for install prompt availability
    const checkInstallable = () => {
      setIsInstallable(canInstallPWA());
    };

    // Check immediately and set up listener
    checkInstallable();
    
    // Listen for beforeinstallprompt
    const handleBeforeInstall = () => {
      setIsInstallable(true);
      setShowBanner(true);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstall);

    // Show banner after 5 seconds on mobile
    if (!dismissed) {
      const timer = setTimeout(() => {
        setShowBanner(true);
      }, 5000);
      return () => {
        clearTimeout(timer);
        window.removeEventListener('beforeinstallprompt', handleBeforeInstall);
      };
    }

    return () => {
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
        
        <div className="flex gap-2 mt-4">
          {isInstallable ? (
            <button
              onClick={handleInstall}
              className="flex-1 bg-black text-yellow-400 font-semibold py-2.5 px-4 rounded-xl flex items-center justify-center gap-2 hover:bg-gray-900 transition-colors"
              data-testid="pwa-install-btn"
            >
              <Download className="w-4 h-4" />
              {t('pwa.installButton', 'Installer')}
            </button>
          ) : (
            <div className="flex-1 text-sm">
              <p className="font-medium">{t('pwa.iosInstructions', 'Sur iOS:')}</p>
              <p className="opacity-80">
                {t('pwa.iosSteps', 'Appuyez sur Partager → "Sur l\'écran d\'accueil"')}
              </p>
            </div>
          )}
          <button
            onClick={handleDismiss}
            className="px-4 py-2.5 border-2 border-black/20 rounded-xl font-medium hover:bg-black/10 transition-colors"
            data-testid="pwa-later-btn"
          >
            {t('pwa.later', 'Plus tard')}
          </button>
        </div>
      </div>
    </div>
  );
};

export default InstallPWABanner;
