import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate, Link } from 'react-router-dom';
import { 
  FileText, Check, Car, Users, MapPin, ArrowLeftRight, 
  Shield, UserCheck, AlertTriangle, ChevronLeft
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useTranslation } from 'react-i18next';
import LanguageSelector from '@/components/LanguageSelector';

const TermsAndConditions = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [accepted, setAccepted] = useState(false);

  const handleAccept = () => {
    // Store acceptance in localStorage
    localStorage.setItem('cgu-accepted', 'true');
    localStorage.setItem('cgu-accepted-date', new Date().toISOString());
    
    // Navigate back or to home
    navigate(-1);
  };

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-black/90 backdrop-blur-sm border-b border-zinc-800">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-10 h-10 bg-[#FFD60A] rounded-lg flex items-center justify-center">
              <Car className="w-6 h-6 text-black" />
            </div>
            <span className="text-xl font-bold text-white">Métro-Taxi</span>
          </Link>
          <LanguageSelector />
        </div>
      </header>

      {/* Content */}
      <main className="pt-24 pb-32 px-4">
        <div className="max-w-4xl mx-auto">
          {/* Back button */}
          <button 
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 text-zinc-400 hover:text-white mb-6 transition-colors"
          >
            <ChevronLeft className="w-5 h-5" />
            {t('cgu.back', 'Retour')}
          </button>

          {/* Title */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-12"
          >
            <div className="w-20 h-20 bg-[#FFD60A] rounded-2xl flex items-center justify-center mx-auto mb-6">
              <FileText className="w-10 h-10 text-black" />
            </div>
            <h1 className="text-3xl md:text-4xl font-bold mb-4">
              {t('cgu.title', 'Conditions Générales d\'Utilisation (CGU)')}
            </h1>
            <p className="text-zinc-400">
              {t('cgu.lastUpdate', 'Dernière mise à jour')}: {new Date().toLocaleDateString()}
            </p>
          </motion.div>

          {/* Introduction */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 md:p-8 mb-6"
          >
            <p className="text-lg text-zinc-300 leading-relaxed">
              {t('cgu.intro', 'Métro-Taxi est une plateforme de mise en relation entre des usagers abonnés et des chauffeurs VTC.')}
            </p>
          </motion.section>

          {/* Service Description */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 md:p-8 mb-6"
          >
            <h2 className="text-xl font-bold text-[#FFD60A] mb-6 flex items-center gap-3">
              <Car className="w-6 h-6" />
              {t('cgu.serviceTitle', 'Le service permet')}
            </h2>
            <ul className="space-y-4">
              {[
                { icon: MapPin, text: t('cgu.service1', 'D\'afficher en temps réel les véhicules disponibles') },
                { icon: ArrowLeftRight, text: t('cgu.service2', 'De visualiser leur direction') },
                { icon: Users, text: t('cgu.service3', 'De connaître le nombre de places disponibles') },
                { icon: Car, text: t('cgu.service4', 'D\'accéder à un système de covoiturage dynamique') },
                { icon: ArrowLeftRight, text: t('cgu.service5', 'D\'effectuer des transbordements entre véhicules') }
              ].map((item, index) => (
                <li key={index} className="flex items-start gap-4">
                  <div className="w-10 h-10 bg-[#FFD60A]/10 rounded-lg flex items-center justify-center flex-shrink-0">
                    <item.icon className="w-5 h-5 text-[#FFD60A]" />
                  </div>
                  <span className="text-zinc-300 pt-2">{item.text}</span>
                </li>
              ))}
            </ul>
          </motion.section>

          {/* User Rules */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 md:p-8 mb-6"
          >
            <h2 className="text-xl font-bold text-[#FFD60A] mb-6 flex items-center gap-3">
              <Users className="w-6 h-6" />
              {t('cgu.userRulesTitle', 'Règles pour les usagers')}
            </h2>
            <ul className="space-y-4">
              {[
                t('cgu.userRule1', 'Disposer d\'un abonnement actif'),
                t('cgu.userRule2', 'Être prêt au point de prise en charge'),
                t('cgu.userRule3', 'Respecter les chauffeurs et les autres passagers')
              ].map((rule, index) => (
                <li key={index} className="flex items-center gap-4">
                  <div className="w-8 h-8 bg-green-500/20 rounded-full flex items-center justify-center flex-shrink-0">
                    <Check className="w-4 h-4 text-green-400" />
                  </div>
                  <span className="text-zinc-300">{rule}</span>
                </li>
              ))}
            </ul>
          </motion.section>

          {/* Driver Rules */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 md:p-8 mb-6"
          >
            <h2 className="text-xl font-bold text-[#FFD60A] mb-6 flex items-center gap-3">
              <UserCheck className="w-6 h-6" />
              {t('cgu.driverRulesTitle', 'Règles pour les chauffeurs')}
            </h2>
            <ul className="space-y-4">
              {[
                t('cgu.driverRule1', 'Être en conformité avec la réglementation VTC'),
                t('cgu.driverRule2', 'Assurer la sécurité et le respect des passagers'),
                t('cgu.driverRule3', 'Utiliser l\'application comme outil de mise en relation')
              ].map((rule, index) => (
                <li key={index} className="flex items-center gap-4">
                  <div className="w-8 h-8 bg-blue-500/20 rounded-full flex items-center justify-center flex-shrink-0">
                    <Check className="w-4 h-4 text-blue-400" />
                  </div>
                  <span className="text-zinc-300">{rule}</span>
                </li>
              ))}
            </ul>
          </motion.section>

          {/* Responsibility */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 md:p-8 mb-8"
          >
            <h2 className="text-xl font-bold text-[#FFD60A] mb-6 flex items-center gap-3">
              <Shield className="w-6 h-6" />
              {t('cgu.responsibilityTitle', 'Responsabilité')}
            </h2>
            <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4 mb-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
                <p className="text-zinc-300">
                  {t('cgu.responsibility1', 'Métro-Taxi agit uniquement comme une plateforme de mise en relation.')}
                </p>
              </div>
            </div>
            <p className="text-zinc-300">
              {t('cgu.responsibility2', 'Les trajets sont réalisés sous la responsabilité des chauffeurs.')}
            </p>
          </motion.section>

          {/* Accept Button */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="bg-gradient-to-r from-[#FFD60A]/20 to-[#FFE55C]/20 border border-[#FFD60A]/30 rounded-2xl p-6 md:p-8"
          >
            <div className="flex flex-col md:flex-row items-center gap-6">
              <label className="flex items-center gap-3 cursor-pointer flex-1">
                <input
                  type="checkbox"
                  checked={accepted}
                  onChange={(e) => setAccepted(e.target.checked)}
                  className="w-6 h-6 rounded border-2 border-[#FFD60A] bg-transparent checked:bg-[#FFD60A] cursor-pointer"
                />
                <span className="text-white">
                  {t('cgu.readAndAccept', 'J\'ai lu et j\'accepte les Conditions Générales d\'Utilisation')}
                </span>
              </label>
              <Button
                onClick={handleAccept}
                disabled={!accepted}
                className={`px-8 py-3 rounded-xl font-semibold transition-all ${
                  accepted 
                    ? 'bg-[#FFD60A] hover:bg-[#FFE55C] text-black' 
                    : 'bg-zinc-700 text-zinc-400 cursor-not-allowed'
                }`}
                data-testid="accept-cgu-btn"
              >
                <Check className="w-5 h-5 mr-2" />
                {t('cgu.acceptButton', 'J\'accepte les CGU')}
              </Button>
            </div>
          </motion.div>
        </div>
      </main>

      {/* Footer */}
      <footer className="fixed bottom-0 left-0 right-0 bg-black/90 backdrop-blur-sm border-t border-zinc-800 py-4">
        <div className="max-w-4xl mx-auto px-4 text-center text-zinc-500 text-sm">
          © {new Date().getFullYear()} Métro-Taxi. {t('cgu.allRightsReserved', 'Tous droits réservés.')}
        </div>
      </footer>
    </div>
  );
};

export default TermsAndConditions;
