import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Wallet, TrendingUp, Calendar, CreditCard, Building2, 
  CheckCircle, Clock, AlertCircle, ExternalLink, RefreshCw,
  ChevronDown, ChevronUp, Car
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';
import axios from 'axios';
import { useTranslation } from 'react-i18next';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Currency configuration per language
const CURRENCY_CONFIG = {
  'fr': { currency: 'EUR', locale: 'fr-FR', symbol: '€', rate: 1 },
  'en': { currency: 'USD', locale: 'en-US', symbol: '$', rate: 1.08 },
  'en-GB': { currency: 'GBP', locale: 'en-GB', symbol: '£', rate: 0.86 },
  'de': { currency: 'EUR', locale: 'de-DE', symbol: '€', rate: 1 },
  'nl': { currency: 'EUR', locale: 'nl-NL', symbol: '€', rate: 1 },
  'es': { currency: 'EUR', locale: 'es-ES', symbol: '€', rate: 1 },
  'pt': { currency: 'EUR', locale: 'pt-PT', symbol: '€', rate: 1 },
  'it': { currency: 'EUR', locale: 'it-IT', symbol: '€', rate: 1 },
  'sv': { currency: 'SEK', locale: 'sv-SE', symbol: 'kr', rate: 11.5 },
  'no': { currency: 'NOK', locale: 'nb-NO', symbol: 'kr', rate: 11.8 },
  'da': { currency: 'DKK', locale: 'da-DK', symbol: 'kr', rate: 7.45 },
  'zh': { currency: 'CNY', locale: 'zh-CN', symbol: '¥', rate: 7.8 },
  'hi': { currency: 'INR', locale: 'hi-IN', symbol: '₹', rate: 90 },
  'pa': { currency: 'INR', locale: 'pa-IN', symbol: '₹', rate: 90 },
  'ar': { currency: 'SAR', locale: 'ar-SA', symbol: 'ر.س', rate: 4.05 },
  'ru': { currency: 'RUB', locale: 'ru-RU', symbol: '₽', rate: 99 }
};

const DriverEarnings = ({ onClose }) => {
  const { token, driver } = useAuth();
  const { t, i18n } = useTranslation();
  const [earnings, setEarnings] = useState(null);
  const [stripeStatus, setStripeStatus] = useState(null);
  const [payouts, setPayouts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creatingAccount, setCreatingAccount] = useState(false);
  const [activeTab, setActiveTab] = useState('earnings');
  const [historyExpanded, setHistoryExpanded] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [earningsRes, stripeRes, payoutsRes] = await Promise.all([
        axios.get(`${API}/drivers/earnings`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/drivers/stripe-connect/status`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/drivers/payouts`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      setEarnings(earningsRes.data);
      setStripeStatus(stripeRes.data);
      setPayouts(payoutsRes.data.payouts || []);
    } catch (error) {
      console.error('Error fetching earnings:', error);
      toast.error(t('driverEarnings.fetchError', 'Erreur lors du chargement des données'));
    } finally {
      setLoading(false);
    }
  };

  const createStripeAccount = async () => {
    setCreatingAccount(true);
    try {
      const response = await axios.post(`${API}/drivers/stripe-connect/create-account`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.onboarding_url) {
        toast.success(t('driverEarnings.stripeCreated', 'Compte Stripe créé ! Redirection...'));
        window.open(response.data.onboarding_url, '_blank');
      }
      
      // Refresh status
      await fetchData();
    } catch (error) {
      const message = error.response?.data?.detail || t('driverEarnings.stripeError', 'Erreur lors de la création du compte');
      toast.error(message);
    } finally {
      setCreatingAccount(false);
    }
  };

  const formatCurrency = (amount) => {
    const lang = i18n.language || 'fr';
    const config = CURRENCY_CONFIG[lang] || CURRENCY_CONFIG['fr'];
    const convertedAmount = (amount || 0) * config.rate;
    
    try {
      return new Intl.NumberFormat(config.locale, {
        style: 'currency',
        currency: config.currency,
        minimumFractionDigits: config.currency === 'RUB' || config.currency === 'INR' ? 0 : 2,
        maximumFractionDigits: config.currency === 'RUB' || config.currency === 'INR' ? 0 : 2
      }).format(convertedAmount);
    } catch (e) {
      // Fallback for unsupported locales
      return `${convertedAmount.toFixed(2)} ${config.symbol}`;
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    const lang = i18n.language || 'fr';
    const config = CURRENCY_CONFIG[lang] || CURRENCY_CONFIG['fr'];
    return new Date(dateStr).toLocaleDateString(config.locale, {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    });
  };

  const getMonthName = (monthStr) => {
    if (!monthStr) return '-';
    const [year, month] = monthStr.split('-');
    const date = new Date(year, parseInt(month) - 1, 1);
    const lang = i18n.language || 'fr';
    const config = CURRENCY_CONFIG[lang] || CURRENCY_CONFIG['fr'];
    return date.toLocaleDateString(config.locale, { month: 'long', year: 'numeric' });
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <div className="w-8 h-8 border-2 border-[#FFD60A] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto bg-[#09090B]">
      {/* Header */}
      <div className="sticky top-0 bg-[#09090B] z-10 p-4 border-b border-zinc-800">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Wallet className="w-6 h-6 text-[#FFD60A]" />
            {t('driverEarnings.title', 'Mes Revenus')}
          </h2>
          <Button
            variant="ghost"
            size="sm"
            onClick={fetchData}
            className="text-zinc-400 hover:text-white"
          >
            <RefreshCw className="w-4 h-4" />
          </Button>
        </div>
        
        {/* Tabs */}
        <div className="flex gap-2 mt-4">
          <button
            onClick={() => setActiveTab('earnings')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'earnings' 
                ? 'bg-[#FFD60A] text-black' 
                : 'bg-zinc-800 text-zinc-400 hover:text-white'
            }`}
          >
            {t('driverEarnings.tabEarnings', 'Revenus')}
          </button>
          <button
            onClick={() => setActiveTab('stripe')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'stripe' 
                ? 'bg-[#FFD60A] text-black' 
                : 'bg-zinc-800 text-zinc-400 hover:text-white'
            }`}
          >
            {t('driverEarnings.tabStripe', 'Compte Stripe')}
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'history' 
                ? 'bg-[#FFD60A] text-black' 
                : 'bg-zinc-800 text-zinc-400 hover:text-white'
            }`}
          >
            {t('driverEarnings.tabHistory', 'Historique')}
          </button>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* EARNINGS TAB */}
        {activeTab === 'earnings' && earnings && (
          <>
            {/* Current Month Summary */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-gradient-to-br from-[#FFD60A]/20 to-[#FFD60A]/5 border border-[#FFD60A]/30 rounded-xl p-5"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-zinc-400 text-sm">
                  {t('driverEarnings.currentMonth', 'Mois en cours')}
                </span>
                <span className="text-[#FFD60A] font-medium">
                  {getMonthName(earnings.current_month?.month)}
                </span>
              </div>
              <div className="text-4xl font-bold text-white mb-4">
                {formatCurrency(earnings.current_month?.total_revenue)}
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-zinc-500">{t('driverEarnings.kilometers', 'Kilomètres')}</span>
                  <p className="text-white font-medium">{earnings.current_month?.total_km?.toFixed(1) || 0} km</p>
                </div>
                <div>
                  <span className="text-zinc-500">{t('driverEarnings.rides', 'Trajets')}</span>
                  <p className="text-white font-medium">{earnings.current_month?.rides_count || 0}</p>
                </div>
              </div>
            </motion.div>

            {/* Rate Info */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
              <div className="flex items-center gap-2 text-zinc-400 text-sm">
                <TrendingUp className="w-4 h-4 text-green-500" />
                <span>{t('driverEarnings.rateInfo', 'Tarif')}: </span>
                <span className="text-white font-bold">{formatCurrency(earnings.rate_per_km)}/km</span>
              </div>
              <p className="text-zinc-500 text-xs mt-2">
                {t('driverEarnings.rateDescription', 'Uniquement les km parcourus avec usagers Métro-Taxi à bord')}
              </p>
            </div>

            {/* Pending Payout */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-blue-500" />
                  <span className="text-zinc-400">{t('driverEarnings.pendingPayout', 'Prochain virement')}</span>
                </div>
                <span className="text-white font-bold">{formatCurrency(earnings.pending_payout)}</span>
              </div>
              <p className="text-zinc-500 text-xs mt-2">
                {t('driverEarnings.payoutDate', 'Virement automatique le')} {earnings.payout_day} {t('driverEarnings.ofMonth', 'du mois')}
              </p>
            </div>

            {/* Totals */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
              <h3 className="text-white font-medium mb-3">{t('driverEarnings.totals', 'Cumul total')}</h3>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <p className="text-2xl font-bold text-[#FFD60A]">{formatCurrency(earnings.totals?.total_revenue)}</p>
                  <p className="text-zinc-500 text-xs">{t('driverEarnings.totalEarnings', 'Revenus')}</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-white">{earnings.totals?.total_km?.toFixed(0) || 0}</p>
                  <p className="text-zinc-500 text-xs">km</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-white">{earnings.totals?.total_rides || 0}</p>
                  <p className="text-zinc-500 text-xs">{t('driverEarnings.rides', 'Trajets')}</p>
                </div>
              </div>
            </div>

            {/* Monthly History */}
            {earnings.history && earnings.history.length > 0 && (
              <div className="bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden">
                <button
                  onClick={() => setHistoryExpanded(!historyExpanded)}
                  className="w-full p-4 flex items-center justify-between text-white hover:bg-zinc-800 transition-colors"
                >
                  <span className="font-medium">{t('driverEarnings.monthlyHistory', 'Historique mensuel')}</span>
                  {historyExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                </button>
                {historyExpanded && (
                  <div className="border-t border-zinc-800">
                    {earnings.history.map((month, idx) => (
                      <div key={idx} className="p-4 border-b border-zinc-800 last:border-b-0">
                        <div className="flex items-center justify-between">
                          <span className="text-zinc-400">{getMonthName(month.month)}</span>
                          <span className="text-white font-medium">{formatCurrency(month.total_revenue)}</span>
                        </div>
                        <div className="flex gap-4 mt-1 text-xs text-zinc-500">
                          <span>{month.total_km?.toFixed(1)} km</span>
                          <span>{month.rides_count} trajets</span>
                          <span className={month.payout_status === 'paid' ? 'text-green-500' : 'text-yellow-500'}>
                            {month.payout_status === 'paid' ? '✓ Payé' : '⏳ En attente'}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {/* STRIPE TAB */}
        {activeTab === 'stripe' && (
          <>
            {!stripeStatus?.has_stripe_account ? (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 text-center"
              >
                <Building2 className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
                <h3 className="text-white font-bold text-lg mb-2">
                  {t('driverEarnings.noStripeAccount', 'Configurez vos virements')}
                </h3>
                <p className="text-zinc-400 text-sm mb-6">
                  {t('driverEarnings.stripeDescription', 'Créez votre compte Stripe pour recevoir vos revenus automatiquement sur votre compte bancaire.')}
                </p>
                <Button
                  onClick={createStripeAccount}
                  disabled={creatingAccount}
                  className="bg-[#FFD60A] text-black hover:bg-[#E6C209] font-bold"
                >
                  {creatingAccount ? (
                    <div className="w-5 h-5 border-2 border-black border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <>
                      <CreditCard className="w-5 h-5 mr-2" />
                      {t('driverEarnings.createStripe', 'Créer mon compte Stripe')}
                    </>
                  )}
                </Button>
              </motion.div>
            ) : (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-4"
              >
                {/* Stripe Status Card */}
                <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
                  <div className="flex items-center gap-3 mb-4">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      stripeStatus.payouts_enabled ? 'bg-green-500/20' : 'bg-yellow-500/20'
                    }`}>
                      {stripeStatus.payouts_enabled ? (
                        <CheckCircle className="w-5 h-5 text-green-500" />
                      ) : (
                        <Clock className="w-5 h-5 text-yellow-500" />
                      )}
                    </div>
                    <div>
                      <h3 className="text-white font-bold">
                        {stripeStatus.payouts_enabled 
                          ? t('driverEarnings.stripeActive', 'Compte Stripe actif')
                          : t('driverEarnings.stripePending', 'Vérification en attente')
                        }
                      </h3>
                      <p className="text-zinc-500 text-sm font-mono">{stripeStatus.stripe_account_id}</p>
                    </div>
                  </div>

                  {/* Status indicators */}
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div className="bg-zinc-800 rounded-lg p-3">
                      <div className="flex items-center gap-2">
                        {stripeStatus.payouts_enabled ? (
                          <CheckCircle className="w-4 h-4 text-green-500" />
                        ) : (
                          <AlertCircle className="w-4 h-4 text-yellow-500" />
                        )}
                        <span className="text-zinc-400 text-sm">{t('driverEarnings.payoutsStatus', 'Virements')}</span>
                      </div>
                      <p className={`font-medium ${stripeStatus.payouts_enabled ? 'text-green-500' : 'text-yellow-500'}`}>
                        {stripeStatus.payouts_enabled ? t('driverEarnings.enabled', 'Activé') : t('driverEarnings.pending', 'En attente')}
                      </p>
                    </div>
                    <div className="bg-zinc-800 rounded-lg p-3">
                      <div className="flex items-center gap-2">
                        {stripeStatus.charges_enabled ? (
                          <CheckCircle className="w-4 h-4 text-green-500" />
                        ) : (
                          <AlertCircle className="w-4 h-4 text-yellow-500" />
                        )}
                        <span className="text-zinc-400 text-sm">{t('driverEarnings.verificationType', 'Vérification')}</span>
                      </div>
                      <p className={`font-medium ${stripeStatus.charges_enabled ? 'text-green-500' : 'text-yellow-500'}`}>
                        {stripeStatus.charges_enabled ? t('driverEarnings.complete', 'Complète') : t('driverEarnings.incomplete', 'Incomplète')}
                      </p>
                    </div>
                  </div>

                  {/* Requirements */}
                  {stripeStatus.requirements?.currently_due?.length > 0 && (
                    <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4 mb-4">
                      <div className="flex items-center gap-2 mb-2">
                        <AlertCircle className="w-5 h-5 text-yellow-500" />
                        <span className="text-yellow-500 font-medium">
                          {t('driverEarnings.actionRequired', 'Action requise')}
                        </span>
                      </div>
                      <p className="text-zinc-400 text-sm mb-3">
                        {t('driverEarnings.completeVerification', 'Complétez votre vérification Stripe pour recevoir vos virements.')}
                      </p>
                      <Button
                        onClick={createStripeAccount}
                        disabled={creatingAccount}
                        className="w-full bg-yellow-500 text-black hover:bg-yellow-400 font-bold"
                      >
                        <ExternalLink className="w-4 h-4 mr-2" />
                        {t('driverEarnings.completeSetup', 'Compléter la vérification')}
                      </Button>
                    </div>
                  )}

                  {stripeStatus.payouts_enabled && (
                    <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
                      <div className="flex items-center gap-2">
                        <CheckCircle className="w-5 h-5 text-green-500" />
                        <span className="text-green-500">
                          {t('driverEarnings.readyForPayouts', 'Prêt à recevoir des virements')}
                        </span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Bank Info */}
                {driver?.iban && (
                  <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
                    <h4 className="text-white font-medium mb-3 flex items-center gap-2">
                      <Building2 className="w-4 h-4 text-zinc-500" />
                      {t('driverEarnings.bankInfo', 'Informations bancaires')}
                    </h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-zinc-500">IBAN</span>
                        <span className="text-white font-mono">
                          {driver.iban?.slice(0, 4)}****{driver.iban?.slice(-4)}
                        </span>
                      </div>
                      {driver?.bic && (
                        <div className="flex justify-between">
                          <span className="text-zinc-500">BIC</span>
                          <span className="text-white font-mono">{driver.bic}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </motion.div>
            )}
          </>
        )}

        {/* HISTORY TAB */}
        {activeTab === 'history' && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            {payouts.length === 0 ? (
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 text-center">
                <Clock className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
                <h3 className="text-white font-medium mb-2">
                  {t('driverEarnings.noPayouts', 'Aucun virement')}
                </h3>
                <p className="text-zinc-500 text-sm">
                  {t('driverEarnings.noPayoutsDesc', 'Vos virements apparaîtront ici une fois effectués.')}
                </p>
              </div>
            ) : (
              payouts.map((payout, idx) => (
                <div
                  key={idx}
                  className="bg-zinc-900 border border-zinc-800 rounded-lg p-4"
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        payout.status === 'transferred' ? 'bg-green-500/20' : 'bg-blue-500/20'
                      }`}>
                        {payout.status === 'transferred' ? (
                          <CheckCircle className="w-4 h-4 text-green-500" />
                        ) : (
                          <Clock className="w-4 h-4 text-blue-500" />
                        )}
                      </div>
                      <div>
                        <p className="text-white font-medium">{formatCurrency(payout.total_revenue)}</p>
                        <p className="text-zinc-500 text-xs">{formatDate(payout.created_at)}</p>
                      </div>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      payout.status === 'transferred' 
                        ? 'bg-green-500/20 text-green-500' 
                        : 'bg-blue-500/20 text-blue-500'
                    }`}>
                      {payout.status === 'transferred' ? t('driverEarnings.transferred', 'Transféré') : t('driverEarnings.processing', 'En cours')}
                    </span>
                  </div>
                  <div className="flex gap-4 text-xs text-zinc-500">
                    <span>{payout.total_km?.toFixed(1)} km</span>
                    <span>{payout.rides_count} trajets</span>
                    {payout.months && <span>{payout.months.join(', ')}</span>}
                  </div>
                  {payout.stripe_transfer_id && (
                    <p className="text-zinc-600 text-xs mt-2 font-mono">
                      Stripe: {payout.stripe_transfer_id}
                    </p>
                  )}
                </div>
              ))
            )}
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default DriverEarnings;
