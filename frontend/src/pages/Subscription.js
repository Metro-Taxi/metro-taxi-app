import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Car, ArrowLeft, Check, CreditCard, Shield, Clock, Users } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import LanguageSelector from '@/components/LanguageSelector';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const Subscription = () => {
  const { user, token, refreshUser } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [plans, setPlans] = useState({});
  const [loading, setLoading] = useState(null);

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const response = await axios.get(`${API}/subscriptions/plans`);
      setPlans(response.data.plans);
    } catch (error) {
      console.error('Error fetching plans:', error);
    }
  };

  const handleSubscribe = async (planId) => {
    setLoading(planId);
    try {
      const originUrl = window.location.origin;
      const response = await axios.post(`${API}/payments/checkout`, {
        plan_id: planId,
        origin_url: originUrl
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Redirect to Stripe checkout
      window.location.href = response.data.url;
    } catch (error) {
      const message = error.response?.data?.detail || t('subscription.error', 'Erreur lors de la création du paiement');
      toast.error(message);
      setLoading(null);
    }
  };

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
        {user?.subscription_active && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8 p-6 bg-green-500/10 border border-green-500/30 rounded"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center">
                <Check className="w-6 h-6 text-white" />
              </div>
              <div>
                <p className="text-green-400 font-bold">Abonnement actif</p>
                <p className="text-zinc-400 text-sm">
                  Expire le: {new Date(user.subscription_expires).toLocaleDateString('fr-FR')}
                </p>
              </div>
            </div>
          </motion.div>
        )}

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
          <p className="text-zinc-500 mb-4">Paiements sécurisés acceptés</p>
          <div className="flex justify-center gap-4">
            <div className="bg-zinc-800 px-4 py-2 rounded flex items-center gap-2">
              <span className="text-white text-sm font-medium">Visa</span>
            </div>
            <div className="bg-zinc-800 px-4 py-2 rounded flex items-center gap-2">
              <span className="text-white text-sm font-medium">Mastercard</span>
            </div>
            <div className="bg-zinc-800 px-4 py-2 rounded flex items-center gap-2">
              <span className="text-white text-sm font-medium">American Express</span>
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
    </div>
  );
};

export default Subscription;
