import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Car, Check, ArrowRight, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const SubscriptionSuccess = () => {
  const [searchParams] = useSearchParams();
  const { token, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [status, setStatus] = useState('checking'); // checking, success, error
  const [paymentDetails, setPaymentDetails] = useState(null);

  useEffect(() => {
    const sessionId = searchParams.get('session_id');
    if (sessionId) {
      pollPaymentStatus(sessionId);
    } else {
      setStatus('error');
    }
  }, [searchParams]);

  const pollPaymentStatus = async (sessionId, attempts = 0) => {
    const maxAttempts = 10;
    const pollInterval = 2000;

    if (attempts >= maxAttempts) {
      setStatus('error');
      return;
    }

    try {
      const response = await axios.get(`${API}/payments/status/${sessionId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const data = response.data;
      setPaymentDetails(data);

      if (data.payment_status === 'paid') {
        setStatus('success');
        await refreshUser(); // Refresh user data to get updated subscription
        return;
      } else if (data.status === 'expired') {
        setStatus('error');
        return;
      }

      // Continue polling
      setTimeout(() => pollPaymentStatus(sessionId, attempts + 1), pollInterval);
    } catch (error) {
      console.error('Payment status error:', error);
      if (attempts < maxAttempts - 1) {
        setTimeout(() => pollPaymentStatus(sessionId, attempts + 1), pollInterval);
      } else {
        setStatus('error');
      }
    }
  };

  return (
    <div className="min-h-screen bg-[#09090B] flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        {/* Logo */}
        <Link to="/" className="flex items-center justify-center gap-2 mb-12">
          <Car className="w-10 h-10 text-[#FFD60A]" />
          <span className="text-3xl font-black text-white">MÉTRO-TAXI</span>
        </Link>

        {status === 'checking' && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
          >
            <div className="w-24 h-24 bg-zinc-800 rounded-full flex items-center justify-center mx-auto mb-6">
              <Loader2 className="w-12 h-12 text-[#FFD60A] animate-spin" />
            </div>
            <h1 className="text-2xl font-bold text-white mb-4">
              Vérification du paiement...
            </h1>
            <p className="text-zinc-400">
              Veuillez patienter pendant que nous confirmons votre paiement.
            </p>
          </motion.div>
        )}

        {status === 'success' && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
          >
            <div className="w-24 h-24 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-6">
              <Check className="w-12 h-12 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-white mb-4">
              Paiement réussi !
            </h1>
            <p className="text-zinc-400 mb-8">
              Votre abonnement est maintenant actif. Vous pouvez commencer à voyager immédiatement.
            </p>
            
            {paymentDetails && (
              <div className="bg-zinc-900 border border-zinc-800 rounded p-6 mb-8 text-left">
                <h3 className="text-white font-medium mb-4">Détails du paiement</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-zinc-400">Montant</span>
                    <span className="text-white font-mono">
                      {(paymentDetails.amount_total / 100).toFixed(2)} {paymentDetails.currency?.toUpperCase()}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-400">Statut</span>
                    <span className="text-green-400">Payé</span>
                  </div>
                </div>
              </div>
            )}
            
            <Button
              onClick={() => navigate('/dashboard')}
              className="w-full bg-[#FFD60A] text-black font-bold h-14 hover:bg-[#E6C209]"
              data-testid="go-to-dashboard-btn"
            >
              COMMENCER À VOYAGER
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </motion.div>
        )}

        {status === 'error' && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
          >
            <div className="w-24 h-24 bg-red-500 rounded-full flex items-center justify-center mx-auto mb-6">
              <span className="text-4xl text-white">✕</span>
            </div>
            <h1 className="text-2xl font-bold text-white mb-4">
              Erreur de paiement
            </h1>
            <p className="text-zinc-400 mb-8">
              Le paiement n'a pas pu être confirmé. Veuillez réessayer ou contacter le support.
            </p>
            <div className="flex flex-col gap-3">
              <Button
                onClick={() => navigate('/subscription')}
                className="w-full bg-[#FFD60A] text-black font-bold h-12 hover:bg-[#E6C209]"
              >
                Réessayer
              </Button>
              <Button
                onClick={() => navigate('/dashboard')}
                variant="outline"
                className="w-full border-zinc-700 text-white hover:bg-zinc-800"
              >
                Retour au tableau de bord
              </Button>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default SubscriptionSuccess;
