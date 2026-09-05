import React, { useEffect, useState } from 'react';
import { Smartphone, Share, Plus, Menu, Monitor } from 'lucide-react';

/**
 * AppStoresSection — Section "Bientôt sur les stores" en bas de Landing.
 *
 * - Boutons Google Play / App Store affichés en état "Bientôt disponible"
 *   (désactivés, pas de lien réel tant que Métro-Taxi n'est pas publiée).
 * - Détection User-Agent → affichage conditionnel de l'instruction adaptée
 *   (iOS "Ajouter à l'écran d'accueil", Android idem via menu Chrome, Desktop
 *    invitation à passer sur mobile).
 * - Aucun QR code additionnel : le QR permanent metro-taxi.com des supports
 *   marketing reste la seule porte d'entrée.
 *
 * Composant 100% additif — aucun effet de bord sur le reste de l'app.
 */
const AppStoresSection = () => {
  const [device, setDevice] = useState('desktop'); // 'ios' | 'android' | 'desktop'
  const [isStandalone, setIsStandalone] = useState(false);

  useEffect(() => {
    const ua = navigator.userAgent || '';
    const isIOS = /iphone|ipad|ipod/i.test(ua);
    const isAndroid = /android/i.test(ua);
    if (isIOS) setDevice('ios');
    else if (isAndroid) setDevice('android');
    else setDevice('desktop');

    const standalone =
      (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches) ||
      window.navigator.standalone === true;
    setIsStandalone(standalone);
  }, []);

  return (
    <section
      className="py-16 px-6 bg-gradient-to-b from-black to-[#0A0A0A] border-t border-zinc-800"
      data-testid="app-stores-section"
    >
      <div className="max-w-5xl mx-auto">
        {/* Titre */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-[#FFD60A]/10 border border-[#FFD60A]/30 rounded-full mb-4">
            <Smartphone className="w-4 h-4 text-[#FFD60A]" />
            <span className="text-xs font-semibold text-[#FFD60A] uppercase tracking-wider">
              Applications mobiles
            </span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-3">
            Bientôt disponible sur mobile
          </h2>
          <p className="text-zinc-400 text-base max-w-2xl mx-auto">
            En attendant la publication officielle, installe Métro-Taxi
            directement sur ton écran d'accueil depuis ton navigateur.
          </p>
        </div>

        {/* Boutons stores (désactivés, "Bientôt disponible") */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12">
          {/* App Store button (disabled) */}
          <button
            type="button"
            disabled
            aria-label="App Store — Bientôt disponible"
            className="relative flex items-center gap-3 px-6 py-3 bg-zinc-900 border border-zinc-700 rounded-xl opacity-60 cursor-not-allowed min-w-[220px]"
            data-testid="app-store-btn-disabled"
          >
            <svg viewBox="0 0 24 24" className="w-8 h-8 fill-white" aria-hidden="true">
              <path d="M17.05 20.28c-.98.95-2.05.8-3.08.35-1.09-.46-2.09-.48-3.24 0-1.44.62-2.2.44-3.06-.35C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.53 4.08zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z" />
            </svg>
            <div className="text-left">
              <div className="text-[10px] text-zinc-400 uppercase tracking-wide">Bientôt sur</div>
              <div className="text-lg font-semibold text-white leading-tight">App Store</div>
            </div>
            <span className="absolute -top-2 -right-2 px-2 py-0.5 bg-[#FFD60A] text-black text-[10px] font-bold rounded-full">
              Bientôt
            </span>
          </button>

          {/* Google Play button (disabled) */}
          <button
            type="button"
            disabled
            aria-label="Google Play — Bientôt disponible"
            className="relative flex items-center gap-3 px-6 py-3 bg-zinc-900 border border-zinc-700 rounded-xl opacity-60 cursor-not-allowed min-w-[220px]"
            data-testid="google-play-btn-disabled"
          >
            <svg viewBox="0 0 24 24" className="w-8 h-8" aria-hidden="true">
              <path fill="#34A853" d="M3.5 20.5V3.5l13.5 8.5-13.5 8.5z" opacity=".9" />
              <path fill="#FBBC04" d="M17 12L3.5 20.5l10-6.3L17 12z" />
              <path fill="#EA4335" d="M17 12l-3.5-2.2-10-6.3L17 12z" />
              <path fill="#4285F4" d="M17 12l4-2.5c1-.6 1-1.9 0-2.5L17 4.5v15L21 17c1-.6 1-1.9 0-2.5L17 12z" />
            </svg>
            <div className="text-left">
              <div className="text-[10px] text-zinc-400 uppercase tracking-wide">Bientôt sur</div>
              <div className="text-lg font-semibold text-white leading-tight">Google Play</div>
            </div>
            <span className="absolute -top-2 -right-2 px-2 py-0.5 bg-[#FFD60A] text-black text-[10px] font-bold rounded-full">
              Bientôt
            </span>
          </button>
        </div>

        {/* Encart adapté au device détecté */}
        {!isStandalone && device === 'ios' && (
          <div
            className="max-w-2xl mx-auto p-6 bg-zinc-900/60 border border-[#FFD60A]/30 rounded-2xl"
            data-testid="install-hint-ios"
          >
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-12 h-12 bg-[#FFD60A]/10 rounded-xl flex items-center justify-center">
                <Smartphone className="w-6 h-6 text-[#FFD60A]" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-white mb-2">
                  📱 Utilisateur iPhone ?
                </h3>
                <p className="text-zinc-300 text-sm mb-3">
                  Pour installer Métro-Taxi sur ton écran d'accueil :
                </p>
                <ol className="text-zinc-200 text-sm space-y-2">
                  <li className="flex items-center gap-2">
                    <Share className="w-4 h-4 text-[#FFD60A] flex-shrink-0" />
                    <span>Appuie sur <strong>Partager</strong> en bas de Safari</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <Plus className="w-4 h-4 text-[#FFD60A] flex-shrink-0" />
                    <span>Choisis <strong>Ajouter à l'écran d'accueil</strong></span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="w-4 h-4 flex items-center justify-center text-[#FFD60A] font-bold flex-shrink-0">✓</span>
                    <span>Confirme avec <strong>Ajouter</strong></span>
                  </li>
                </ol>
              </div>
            </div>
          </div>
        )}

        {!isStandalone && device === 'android' && (
          <div
            className="max-w-2xl mx-auto p-6 bg-zinc-900/60 border border-[#FFD60A]/30 rounded-2xl"
            data-testid="install-hint-android"
          >
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-12 h-12 bg-[#FFD60A]/10 rounded-xl flex items-center justify-center">
                <Smartphone className="w-6 h-6 text-[#FFD60A]" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-white mb-2">
                  🤖 Utilisateur Android ?
                </h3>
                <p className="text-zinc-300 text-sm mb-3">
                  Ajoute Métro-Taxi à ton écran d'accueil depuis ton navigateur :
                </p>
                <ol className="text-zinc-200 text-sm space-y-2">
                  <li className="flex items-center gap-2">
                    <Menu className="w-4 h-4 text-[#FFD60A] flex-shrink-0" />
                    <span>Ouvre le <strong>menu</strong> de Chrome (⋮ en haut à droite)</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <Plus className="w-4 h-4 text-[#FFD60A] flex-shrink-0" />
                    <span>Sélectionne <strong>Installer l'application</strong> ou <strong>Ajouter à l'écran d'accueil</strong></span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="w-4 h-4 flex items-center justify-center text-[#FFD60A] font-bold flex-shrink-0">✓</span>
                    <span>Confirme l'installation</span>
                  </li>
                </ol>
              </div>
            </div>
          </div>
        )}

        {device === 'desktop' && (
          <div
            className="max-w-2xl mx-auto p-6 bg-zinc-900/60 border border-zinc-700 rounded-2xl"
            data-testid="install-hint-desktop"
          >
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-12 h-12 bg-zinc-800 rounded-xl flex items-center justify-center">
                <Monitor className="w-6 h-6 text-zinc-400" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-white mb-2">
                  💻 Sur ordinateur ?
                </h3>
                <p className="text-zinc-300 text-sm">
                  Métro-Taxi est pensé pour ton smartphone. Ouvre{' '}
                  <span className="text-[#FFD60A] font-semibold">metro-taxi.com</span>{' '}
                  depuis ton téléphone pour l'installer sur ton écran d'accueil.
                </p>
              </div>
            </div>
          </div>
        )}

        {isStandalone && (
          <div
            className="max-w-2xl mx-auto p-6 bg-[#FFD60A]/5 border border-[#FFD60A]/40 rounded-2xl text-center"
            data-testid="install-hint-already-installed"
          >
            <p className="text-white text-sm">
              ✅ Métro-Taxi est déjà installé sur ton écran d'accueil. Bienvenue !
            </p>
          </div>
        )}
      </div>
    </section>
  );
};

export default AppStoresSection;
