import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate, Link } from 'react-router-dom';
import { 
  ShoppingBag, Check, Car, CreditCard, Clock, XCircle,
  AlertTriangle, ChevronLeft, Euro, Calendar, RefreshCcw
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useTranslation } from 'react-i18next';
import LanguageSelector from '@/components/LanguageSelector';

const SalesTerms = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [accepted, setAccepted] = useState(false);

  const handleAccept = () => {
    // Store acceptance in localStorage
    localStorage.setItem('cgv-accepted', 'true');
    localStorage.setItem('cgv-accepted-date', new Date().toISOString());
    
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
            data-testid="back-btn"
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
              <ShoppingBag className="w-10 h-10 text-black" />
            </div>
            <h1 className="text-3xl md:text-4xl font-bold mb-4">
              {t('cgv.title', 'Conditions Générales de Vente (CGV)')}
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
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-[#FFD60A]/10 rounded-xl flex items-center justify-center flex-shrink-0">
                <CreditCard className="w-6 h-6 text-[#FFD60A]" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white mb-3">
                  {t('cgv.subscriptionModel', 'Modèle par abonnement')}
                </h2>
                <p className="text-lg text-zinc-300 leading-relaxed">
                  {t('cgv.intro', 'Métro-Taxi fonctionne exclusivement par abonnement.')}
                </p>
                <p className="text-zinc-400 mt-2">
                  {t('cgv.noPerRide', 'Aucun paiement n\'est effectué par trajet.')}
                </p>
              </div>
            </div>
          </motion.section>

          {/* Pricing */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 md:p-8 mb-6"
          >
            <h2 className="text-xl font-bold text-[#FFD60A] mb-6 flex items-center gap-3">
              <Euro className="w-6 h-6" />
              {t('cgv.pricingTitle', 'Tarifs')}
            </h2>
            <div className="grid md:grid-cols-3 gap-4">
              {[
                { 
                  duration: t('cgv.pricing.day', '24 heures'), 
                  price: '6,99 €',
                  icon: Clock
                },
                { 
                  duration: t('cgv.pricing.week', '1 semaine'), 
                  price: '16,99 €',
                  icon: Calendar,
                  popular: true
                },
                { 
                  duration: t('cgv.pricing.month', '1 mois'), 
                  price: '53,99 €',
                  icon: Calendar
                }
              ].map((plan, index) => (
                <div 
                  key={index} 
                  className={`relative p-5 rounded-xl border transition-all ${
                    plan.popular 
                      ? 'bg-[#FFD60A]/10 border-[#FFD60A]/50' 
                      : 'bg-zinc-800/50 border-zinc-700'
                  }`}
                >
                  {plan.popular && (
                    <span className="absolute -top-2 right-3 bg-[#FFD60A] text-black text-xs font-bold px-2 py-1 rounded">
                      {t('pricing.popularBadge', 'POPULAIRE')}
                    </span>
                  )}
                  <div className="flex items-center gap-3 mb-3">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                      plan.popular ? 'bg-[#FFD60A]/20' : 'bg-zinc-700'
                    }`}>
                      <plan.icon className={`w-5 h-5 ${plan.popular ? 'text-[#FFD60A]' : 'text-zinc-400'}`} />
                    </div>
                    <span className="text-zinc-300 font-medium">{plan.duration}</span>
                  </div>
                  <p className={`text-3xl font-black ${plan.popular ? 'text-[#FFD60A]' : 'text-white'}`}>
                    {plan.price}
                  </p>
                </div>
              ))}
            </div>
          </motion.section>

          {/* Conditions */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 md:p-8 mb-6"
          >
            <h2 className="text-xl font-bold text-[#FFD60A] mb-6 flex items-center gap-3">
              <Check className="w-6 h-6" />
              {t('cgv.conditionsTitle', 'Conditions')}
            </h2>
            <ul className="space-y-4">
              {[
                {
                  icon: Check,
                  text: t('cgv.condition1', 'L\'abonnement doit être actif pour accéder au service'),
                  color: 'green'
                },
                {
                  icon: RefreshCcw,
                  text: t('cgv.condition2', 'Les abonnements sont non remboursables sauf cas exceptionnel'),
                  color: 'yellow'
                },
                {
                  icon: Calendar,
                  text: t('cgv.condition3', 'Le renouvellement est à l\'initiative de l\'utilisateur'),
                  color: 'blue'
                }
              ].map((condition, index) => (
                <li key={index} className="flex items-start gap-4">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    condition.color === 'green' ? 'bg-green-500/20' :
                    condition.color === 'yellow' ? 'bg-yellow-500/20' :
                    'bg-blue-500/20'
                  }`}>
                    <condition.icon className={`w-5 h-5 ${
                      condition.color === 'green' ? 'text-green-400' :
                      condition.color === 'yellow' ? 'text-yellow-400' :
                      'text-blue-400'
                    }`} />
                  </div>
                  <span className="text-zinc-300 pt-2">{condition.text}</span>
                </li>
              ))}
            </ul>
          </motion.section>

          {/* Service Suspension */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 md:p-8 mb-8"
          >
            <h2 className="text-xl font-bold text-[#FFD60A] mb-6 flex items-center gap-3">
              <XCircle className="w-6 h-6" />
              {t('cgv.suspensionTitle', 'Suspension du service')}
            </h2>
            
            <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 mb-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                <p className="text-zinc-300 font-medium">
                  {t('cgv.suspensionWarning', 'En cas d\'expiration de l\'abonnement :')}
                </p>
              </div>
            </div>

            <ul className="space-y-3 ml-4">
              {[
                t('cgv.suspension1', 'L\'accès à l\'application est automatiquement désactivé'),
                t('cgv.suspension2', 'Aucun trajet ne peut être effectué')
              ].map((item, index) => (
                <li key={index} className="flex items-center gap-3 text-zinc-400">
                  <div className="w-2 h-2 bg-red-500 rounded-full flex-shrink-0" />
                  {item}
                </li>
              ))}
            </ul>
          </motion.section>

          {/* Accept Button */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="bg-gradient-to-r from-[#FFD60A]/20 to-[#FFE55C]/20 border border-[#FFD60A]/30 rounded-2xl p-6 md:p-8"
          >
            <div className="flex flex-col md:flex-row items-center gap-6">
              <label className="flex items-center gap-3 cursor-pointer flex-1">
                <input
                  type="checkbox"
                  checked={accepted}
                  onChange={(e) => setAccepted(e.target.checked)}
                  className="w-6 h-6 rounded border-2 border-[#FFD60A] bg-transparent checked:bg-[#FFD60A] cursor-pointer"
                  data-testid="accept-cgv-checkbox"
                />
                <span className="text-white">
                  {t('cgv.readAndAccept', 'J\'ai lu et j\'accepte les Conditions Générales de Vente')}
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
                data-testid="accept-cgv-btn"
              >
                <Check className="w-5 h-5 mr-2" />
                {t('cgv.acceptButton', 'J\'accepte les CGV')}
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

export default SalesTerms;
