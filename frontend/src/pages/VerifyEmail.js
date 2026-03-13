import React, { useState, useEffect } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Car, CheckCircle, XCircle, Loader2, Mail } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const VerifyEmail = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { token, refreshUser } = useAuth();
  const [status, setStatus] = useState('verifying'); // verifying, success, error
  const [message, setMessage] = useState('');

  useEffect(() => {
    const verificationToken = searchParams.get('token');
    if (verificationToken) {
      verifyEmail(verificationToken);
    } else {
      setStatus('error');
      setMessage('Token de vérification manquant');
    }
  }, [searchParams]);

  const verifyEmail = async (verificationToken) => {
    try {
      const response = await axios.post(`${API}/auth/verify-email`, {
        token: verificationToken
      });
      
      setStatus('success');
      setMessage(response.data.message);
      
      // Refresh user data if logged in
      if (token) {
        await refreshUser();
      }
    } catch (error) {
      setStatus('error');
      setMessage(error.response?.data?.detail || 'Erreur lors de la vérification');
    }
  };

  return (
    <div className="min-h-screen bg-[#09090B] flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="max-w-md w-full text-center"
      >
        {/* Logo */}
        <Link to="/" className="flex items-center justify-center gap-2 mb-12">
          <Car className="w-10 h-10 text-[#FFD60A]" />
          <span className="text-3xl font-black text-white">MÉTRO-TAXI</span>
        </Link>

        {status === 'verifying' && (
          <div>
            <div className="w-20 h-20 bg-zinc-800 rounded-full flex items-center justify-center mx-auto mb-6">
              <Loader2 className="w-10 h-10 text-[#FFD60A] animate-spin" />
            </div>
            <h1 className="text-2xl font-bold text-white mb-4">
              Vérification en cours...
            </h1>
            <p className="text-zinc-400">
              Veuillez patienter pendant que nous vérifions votre adresse email.
            </p>
          </div>
        )}

        {status === 'success' && (
          <div>
            <div className="w-20 h-20 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="w-10 h-10 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-white mb-4">
              Email vérifié !
            </h1>
            <p className="text-zinc-400 mb-8">
              {message || 'Votre adresse email a été vérifiée avec succès.'}
            </p>
            <Button
              onClick={() => navigate('/dashboard')}
              className="bg-[#FFD60A] text-black font-bold px-8 py-3 hover:bg-[#E6C209]"
              data-testid="continue-btn"
            >
              CONTINUER
            </Button>
          </div>
        )}

        {status === 'error' && (
          <div>
            <div className="w-20 h-20 bg-red-500 rounded-full flex items-center justify-center mx-auto mb-6">
              <XCircle className="w-10 h-10 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-white mb-4">
              Erreur de vérification
            </h1>
            <p className="text-zinc-400 mb-8">
              {message || 'Le lien de vérification est invalide ou expiré.'}
            </p>
            <div className="flex flex-col gap-3">
              <Button
                onClick={() => navigate('/login')}
                className="bg-[#FFD60A] text-black font-bold px-8 py-3 hover:bg-[#E6C209]"
              >
                SE CONNECTER
              </Button>
              <Link to="/">
                <Button variant="outline" className="w-full border-zinc-700 text-white hover:bg-zinc-800">
                  Retour à l'accueil
                </Button>
              </Link>
            </div>
          </div>
        )}
      </motion.div>
    </div>
  );
};

export default VerifyEmail;
