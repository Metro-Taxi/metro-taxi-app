import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Car, ArrowLeft, Check, CreditCard, Shield, Clock, Users, Globe, MapPin, Loader2, Building2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import LanguageSelector from '@/components/LanguageSelector';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Country flag mapping
const countryFlags = {
  FR: '🇫🇷',
  GB: '🇬🇧',
  ES: '🇪🇸',
  DE: '🇩🇪',
};

const Subscription = () => {
  const { user, token, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { t } = useTranslation();
  const [plans, setPlans] = useState({});
  const [loading, setLoading] = useState(null);
  const [regions, setRegions] = useState([]);
  const [selectedRegion, setSelectedRegion] = useState(null);
  const [regionsLoading, setRegionsLoading] = useState(true);
  const [userSubscriptions, setUserSubscriptions] = useState([]);
  const [isRedirecting, setIsRedirecting] = useState(false);
  
  // SEPA payment states
  const [sepaDialogOpen, setSepaDialogOpen] = useState(false);
  const [selectedPlanForSepa, setSelectedPlanForSepa] = useState(null);
  const [sepaForm, setSepaForm] = useState({
    iban: '',
    account_holder_name: '',
    email: user?.email || ''
  });
  const [sepaLoading, setSepaLoading] = useState(false);

  useEffect(() => {
    // Reset redirecting state on mount
    setIsRedirecting(false);
    fetchPlans();
    fetchRegions();
    fetchUserSubscriptions();
  }, []);
  
  useEffect(() => {
    if (user?.email) {
      setSepaForm(prev => ({ ...prev, email: user.email }));
    }
  }, [user]);

  // Check URL for region parameter
  useEffect(() => {
    const regionParam = searchParams.get('region');
    if (regionParam && regions.length > 0) {
      const region = regions.find(r => r.id === regionParam);
      if (region) {
        setSelectedRegion(region);
      }
    }
  }, [searchParams, regions]);

  const fetchPlans = async () => {
    try {
      const response = await axios.get(`${API}/subscriptions/plans`);
      setPlans(response.data.plans);
    } catch (error) {
      console.error('Error fetching plans:', error);
    }
  };

  const fetchRegions = async () => {
    try {
      const response = await axios.get(`${API}/regions/active`);
      setRegions(response.data);
      // Auto-select first region if only one
      if (response.data.length === 1) {
        setSelectedRegion(response.data[0]);
      }
    } catch (error) {
      console.error('Error fetching regions:', error);
    } finally {
      setRegionsLoading(false);
    }
  };

  const fetchUserSubscriptions = async () => {
    try {
      const response = await axios.get(`${API}/subscription/regions`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUserSubscriptions(response.data.subscriptions || []);
    } catch (error) {
      console.error('Error fetching user subscriptions:', error);
    }
  };

  const getSubscriptionForRegion = (regionId) => {
    return userSubscriptions.find(s => s.region_id === regionId && s.is_active);
  };

  const handleSubscribe = async (planId) => {
    if (!selectedRegion) {
      toast.error(t('regions.regionRequired', 'Please select a region first'));
      return;
    }

    setLoading(planId);
    try {
      const originUrl = window.location.origin;
      const response = await axios.post(`${API}/payments/checkout/region`, {
        plan_id: planId,
        region_id: selectedRegion.id,
        origin_url: originUrl
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.url) {
        // Set redirecting flag to prevent React updates during redirect
        setIsRedirecting(true);
        
        // Redirect to Stripe
        window.location.href = response.data.url;
      } else {
        toast.error(t('subscription.error', 'Error creating payment session'));
        setLoading(null);
      }
    } catch (error) {
      console.error('Checkout error:', error);
      const message = error.response?.data?.detail || t('subscription.error', 'Erreur lors de la création du paiement');
      toast.error(message);
      setLoading(null);
    }
  };

  // SEPA Payment functions
  const openSepaDialog = (planId) => {
    if (!selectedRegion) {
      toast.error(t('regions.regionRequired', 'Please select a region first'));
      return;
    }
    setSelectedPlanForSepa(planId);
    setSepaDialogOpen(true);
  };

  const handleSepaPayment = async () => {
    if (!sepaForm.iban || !sepaForm.account_holder_name || !sepaForm.email) {
      toast.error(t('sepa.fillAllFields', 'Please fill all fields'));
      return;
    }

    // Basic IBAN validation (format check)
    const ibanClean = sepaForm.iban.replace(/\s/g, '').toUpperCase();
    if (ibanClean.length < 15 || ibanClean.length > 34) {
      toast.error(t('sepa.invalidIban', 'Invalid IBAN format'));
      return;
    }

    setSepaLoading(true);
    try {
      const originUrl = window.location.origin;
      const response = await axios.post(`${API}/payments/checkout/sepa`, {
        plan_id: selectedPlanForSepa,
        region_id: selectedRegion.id,
        iban: ibanClean,
        account_holder_name: sepaForm.account_holder_name,
        email: sepaForm.email,
        origin_url: originUrl
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.status === 'processing') {
        toast.success(t('sepa.processing', 'SEPA payment initiated! You will receive a confirmation email within 5-14 business days.'));
        setSepaDialogOpen(false);
        // Refresh subscriptions after a short delay
        setTimeout(() => {
          fetchUserSubscriptions();
        }, 2000);
      } else if (response.data.status === 'succeeded') {
        toast.success(t('sepa.success', 'SEPA payment successful!'));
        setSepaDialogOpen(false);
        fetchUserSubscriptions();
      } else if (response.data.status === 'requires_action') {
        toast.info(t('sepa.requiresAction', 'Additional action required'));
      } else {
        toast.info(response.data.message || 'Payment status: ' + response.data.status);
      }
    } catch (error) {
      console.error('SEPA error:', error);
      const message = error.response?.data?.detail || t('sepa.error', 'SEPA payment error');
      toast.error(message);
    } finally {
      setSepaLoading(false);
    }
  };

  // Show loading screen during redirect
  if (isRedirecting) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-[#FFD60A] border-t-transparent rounded-full animate-spin mx-auto mb-6"></div>
          <p className="text-white text-xl font-semibold mb-2">{t('subscription.redirecting', 'Redirection vers le paiement...')}</p>
          <p className="text-zinc-400 text-sm">{t('subscription.pleaseWait', 'Veuillez patienter...')}</p>
        </div>
      </div>
    );
  }

  const planData = [
    { 
      id: '24h', 
      name: t('subscription.plans.day.name', '24 HEURES'), 
      price: t('subscription.plans.day.price', '6,99 €'), 
      period: t('subscription.plans.day.period', 'jour'),
      features: [
        t('subscription.plans.day.feature1', 'Trajets illimités pendant 24h'), 
        t('subscription.plans.day.feature2', 'Accès à tous les véhicules'), 
        t('subscription.plans.day.feature3', 'Transbordements optimisés')
      ]
    },
    { 
      id: '1week', 
      name: t('subscription.plans.week.name', '1 SEMAINE'), 
      price: t('subscription.plans.week.price', '16,99 €'), 
      period: t('subscription.plans.week.period', 'semaine'),
      popular: true,
      features: [
        t('subscription.plans.week.feature1', 'Trajets illimités pendant 7 jours'), 
        t('subscription.plans.week.feature2', 'Accès prioritaire'), 
        t('subscription.plans.week.feature3', 'Transbordements optimisés'), 
        t('subscription.plans.week.feature4', 'Support prioritaire')
      ]
    },
    { 
      id: '1month', 
      name: t('subscription.plans.month.name', '1 MOIS'), 
      price: t('subscription.plans.month.price', '53,99 €'), 
      period: t('subscription.plans.month.period', 'mois'),
      features: [
        t('subscription.plans.month.feature1', 'Trajets illimités pendant 30 jours'), 
        t('subscription.plans.month.feature2', 'Accès prioritaire'), 
        t('subscription.plans.month.feature3', 'Transbordements optimisés'), 
        t('subscription.plans.month.feature4', 'Support prioritaire'), 
        t('subscription.plans.month.feature5', 'Économie maximale')
      ]
    }
  ];

  return (
    <div className="min-h-screen bg-[#09090B] py-12 px-4">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-12">
          <Link to="/dashboard" className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors">
            <ArrowLeft className="w-5 h-5" />
            {t('cgu.back', 'Retour')}
          </Link>
          <div className="flex items-center gap-4">
            <LanguageSelector />
            <div className="flex items-center gap-2">
              <Car className="w-8 h-8 text-[#FFD60A]" />
              <span className="text-2xl font-black text-white">MÉTRO-TAXI</span>
            </div>
          </div>
        </div>

        {/* Current subscription status */}
        {userSubscriptions.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8 p-6 bg-green-500/10 border border-green-500/30 rounded"
          >
            <h3 className="text-green-400 font-bold mb-3 flex items-center gap-2">
              <Check className="w-5 h-5" />
              {t('regions.activeInRegions', 'Active subscriptions')}
            </h3>
            <div className="flex flex-wrap gap-3">
              {userSubscriptions.filter(s => s.is_active).map(sub => (
                <div key={sub.region_id} className="flex items-center gap-2 bg-green-500/20 px-3 py-2 rounded">
                  <span>{countryFlags[sub.region?.country] || '🌍'}</span>
                  <span className="text-white font-medium">{sub.region?.name}</span>
                  <span className="text-green-400 text-sm">
                    ({sub.hours_remaining}h)
                  </span>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Region Selection */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex items-center gap-2 mb-4">
            <Globe className="w-6 h-6 text-[#FFD60A]" />
            <h2 className="text-xl font-bold text-white">
              {t('regions.selectRegion', 'Select your region')}
            </h2>
          </div>
          
          {regionsLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-8 h-8 animate-spin text-[#FFD60A]" />
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {regions.map((region) => {
                const existingSub = getSubscriptionForRegion(region.id);
                return (
                  <button
                    key={region.id}
                    onClick={() => setSelectedRegion(region)}
                    className={`
                      relative p-4 rounded-xl border-2 transition-all text-left
                      ${selectedRegion?.id === region.id
                        ? 'border-[#FFD60A] bg-[#FFD60A]/10'
                        : 'border-zinc-700 hover:border-zinc-500 bg-zinc-800/50'
                      }
                    `}
                    data-testid={`subscription-region-${region.id}`}
                  >
                    {existingSub && (
                      <div className="absolute top-2 right-2 bg-green-500 text-white text-xs px-2 py-0.5 rounded">
                        {t('subscription.active', 'Actif')}
                      </div>
                    )}
                    
                    <div className="flex items-center gap-3">
                      <span className="text-3xl">{countryFlags[region.country] || '🌍'}</span>
                      <div>
                        <h4 className="font-semibold text-white">{region.name}</h4>
                        <p className="text-sm text-zinc-400">
                          {region.currency}
                        </p>
                        {existingSub && (
                          <p className="text-xs text-green-400 mt-1">
                            {existingSub.hours_remaining}h {t('subscription.remaining', 'restantes')}
                          </p>
                        )}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
          
          {selectedRegion && (
            <p className="text-sm text-zinc-400 mt-3 flex items-center gap-2">
              <MapPin className="w-4 h-4 text-[#FFD60A]" />
              {t('regions.subscriptionForRegion', 'Subscription for')}: <span className="text-white font-medium">{selectedRegion.name}</span>
            </p>
          )}
        </motion.div>

        {/* Title */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <h1 className="text-4xl md:text-5xl font-black text-white mb-4">
            {t('subscription.chooseTitle', 'CHOISISSEZ VOTRE')} <span className="text-[#FFD60A]">{t('subscription.planWord', 'FORFAIT')}</span>
          </h1>
          <p className="text-zinc-400 text-lg max-w-xl mx-auto">
            {t('subscription.subtitle', 'Un abonnement simple. Des trajets illimités. Payez une fois, voyagez sans compter.')}
          </p>
        </motion.div>

        {/* Plans */}
        <div className="grid md:grid-cols-3 gap-6">
          {planData.map((plan, index) => (
            <motion.div
              key={plan.id}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className={`subscription-card ${plan.popular ? 'popular' : ''}`}
            >
              <h3 className="text-lg font-bold text-zinc-400 mb-4">{plan.name}</h3>
              
              <div className="mb-6">
                <span className="text-5xl font-black text-[#FFD60A]">{plan.price}</span>
              </div>
              
              <p className="text-zinc-500 mb-6">/ {plan.period}</p>
              
              <ul className="space-y-3 mb-8">
                {plan.features.map((feature, i) => (
                  <li key={i} className="flex items-center gap-2 text-zinc-300">
                    <Check className="w-4 h-4 text-[#FFD60A] flex-shrink-0" />
                    <span className="text-sm">{feature}</span>
                  </li>
                ))}
              </ul>
              
              <Button
                onClick={() => handleSubscribe(plan.id)}
                disabled={loading === plan.id}
                className={`w-full h-12 font-bold ${
                  plan.popular 
                    ? 'bg-[#FFD60A] text-black hover:bg-[#E6C209]' 
                    : 'bg-zinc-800 text-white hover:bg-zinc-700'
                }`}
                data-testid={`subscribe-${plan.id}-btn`}
              >
                {loading === plan.id ? (
                  <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    <CreditCard className="w-4 h-4 mr-2" />
                    {t('subscription.subscribeBtn', "S'ABONNER")}
                  </>
                )}
              </Button>
              
              {/* SEPA Button - Only for EUR regions */}
              {selectedRegion?.currency === 'EUR' && (
                <Button
                  variant="outline"
                  onClick={() => openSepaDialog(plan.id)}
                  className="w-full h-10 mt-2 text-sm border-zinc-700 hover:bg-zinc-800"
                  data-testid={`sepa-${plan.id}-btn`}
                >
                  <Building2 className="w-4 h-4 mr-2" />
                  {t('sepa.payWithSepa', 'Payer par prélèvement SEPA')}
                  <span className="ml-2 text-xs text-green-400">(-4%)</span>
                </Button>
              )}
            </motion.div>
          ))}
        </div>

        {/* Payment methods */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-12 text-center"
        >
          <p className="text-zinc-500 mb-4">{t('subscription.securePayments', 'Paiements sécurisés acceptés')}</p>
          <div className="flex justify-center flex-wrap gap-4">
            <div className="bg-zinc-800 px-4 py-2 rounded flex items-center gap-2">
              <span className="text-white text-sm font-medium">Visa</span>
            </div>
            <div className="bg-zinc-800 px-4 py-2 rounded flex items-center gap-2">
              <span className="text-white text-sm font-medium">Mastercard</span>
            </div>
            <div className="bg-zinc-800 px-4 py-2 rounded flex items-center gap-2">
              <span className="text-white text-sm font-medium">American Express</span>
            </div>
            <div className="bg-green-800/50 border border-green-600/50 px-4 py-2 rounded flex items-center gap-2">
              <Building2 className="w-4 h-4 text-green-400" />
              <span className="text-green-400 text-sm font-medium">SEPA</span>
              <span className="text-green-300 text-xs">(-4%)</span>
            </div>
          </div>
        </motion.div>

        {/* Trust badges */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="mt-12 grid md:grid-cols-3 gap-6"
        >
          <div className="flex items-center gap-4 p-4 bg-zinc-900/50 rounded border border-zinc-800">
            <Shield className="w-8 h-8 text-[#FFD60A]" />
            <div>
              <p className="text-white font-medium">Paiement sécurisé</p>
              <p className="text-zinc-500 text-sm">Via Stripe</p>
            </div>
          </div>
          <div className="flex items-center gap-4 p-4 bg-zinc-900/50 rounded border border-zinc-800">
            <Clock className="w-8 h-8 text-[#FFD60A]" />
            <div>
              <p className="text-white font-medium">Activation immédiate</p>
              <p className="text-zinc-500 text-sm">Voyagez tout de suite</p>
            </div>
          </div>
          <div className="flex items-center gap-4 p-4 bg-zinc-900/50 rounded border border-zinc-800">
            <Users className="w-8 h-8 text-[#FFD60A]" />
            <div>
              <p className="text-white font-medium">Trajets illimités</p>
              <p className="text-zinc-500 text-sm">Sans surcoût</p>
            </div>
          </div>
        </motion.div>
      </div>

      {/* SEPA Payment Dialog */}
      <Dialog open={sepaDialogOpen} onOpenChange={setSepaDialogOpen}>
        <DialogContent className="bg-[#18181B] border-zinc-800 max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Building2 className="w-5 h-5 text-green-400" />
              {t('sepa.title', 'Prélèvement SEPA')}
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            {/* SEPA Benefits */}
            <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-3">
              <p className="text-green-400 text-sm font-medium mb-1">
                {t('sepa.saveMoney', 'Économisez ~4% sur les frais !')}
              </p>
              <p className="text-zinc-400 text-xs">
                {t('sepa.sepaInfo', 'Le prélèvement SEPA est traité sous 5-14 jours ouvrés.')}
              </p>
            </div>

            {/* Plan info */}
            {selectedPlanForSepa && plans[selectedPlanForSepa] && (
              <div className="bg-zinc-800/50 rounded-lg p-3 text-center">
                <p className="text-zinc-400 text-sm">{t('sepa.selectedPlan', 'Plan sélectionné')}</p>
                <p className="text-white font-bold text-lg">{plans[selectedPlanForSepa].name}</p>
                <p className="text-[#FFD60A] font-bold text-2xl">{plans[selectedPlanForSepa].price}€</p>
              </div>
            )}
            
            {/* IBAN Input */}
            <div className="space-y-2">
              <Label className="text-zinc-300">IBAN *</Label>
              <Input
                value={sepaForm.iban}
                onChange={(e) => setSepaForm(prev => ({ ...prev, iban: e.target.value.toUpperCase() }))}
                placeholder="FR76 1234 5678 9012 3456 7890 123"
                className="bg-zinc-900 border-zinc-700 text-white font-mono"
                data-testid="sepa-iban-input"
              />
              <p className="text-xs text-zinc-500">{t('sepa.ibanHelp', 'Votre IBAN bancaire (ex: FR76...)')}</p>
            </div>
            
            {/* Account Holder Name */}
            <div className="space-y-2">
              <Label className="text-zinc-300">{t('sepa.accountHolder', 'Titulaire du compte')} *</Label>
              <Input
                value={sepaForm.account_holder_name}
                onChange={(e) => setSepaForm(prev => ({ ...prev, account_holder_name: e.target.value }))}
                placeholder="Jean Dupont"
                className="bg-zinc-900 border-zinc-700 text-white"
                data-testid="sepa-name-input"
              />
            </div>
            
            {/* Email */}
            <div className="space-y-2">
              <Label className="text-zinc-300">Email *</Label>
              <Input
                type="email"
                value={sepaForm.email}
                onChange={(e) => setSepaForm(prev => ({ ...prev, email: e.target.value }))}
                placeholder="email@exemple.com"
                className="bg-zinc-900 border-zinc-700 text-white"
                data-testid="sepa-email-input"
              />
            </div>
            
            {/* Mandate info */}
            <p className="text-xs text-zinc-500">
              {t('sepa.mandateInfo', 'En confirmant, vous autorisez Metro-Taxi à débiter votre compte via SEPA Direct Debit. Un mandat sera créé automatiquement.')}
            </p>
            
            {/* Actions */}
            <div className="flex gap-3 pt-2">
              <Button
                variant="outline"
                onClick={() => setSepaDialogOpen(false)}
                className="flex-1"
              >
                {t('common.cancel', 'Annuler')}
              </Button>
              <Button
                onClick={handleSepaPayment}
                disabled={sepaLoading}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white"
                data-testid="confirm-sepa-btn"
              >
                {sepaLoading ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Check className="w-4 h-4 mr-2" />
                )}
                {t('sepa.confirm', 'Confirmer le prélèvement')}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Subscription;
