import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Car, ArrowLeft, User, Phone, Mail, CreditCard, Calendar, Shield, QrCode } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const Profile = () => {
  const { user, token } = useAuth();
  const [virtualCard, setVirtualCard] = useState(null);

  useEffect(() => {
    if (user?.id) {
      fetchVirtualCard();
    }
  }, [user]);

  const fetchVirtualCard = async () => {
    try {
      const response = await axios.get(`${API}/users/${user.id}/card`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setVirtualCard(response.data.card);
    } catch (error) {
      console.error('Error fetching virtual card:', error);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getPlanName = (planId) => {
    const plans = {
      '24h': '24 Heures',
      '1week': '1 Semaine',
      '1month': '1 Mois'
    };
    return plans[planId] || planId;
  };

  return (
    <div className="min-h-screen bg-[#09090B] py-12 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <Link to="/dashboard" className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors">
            <ArrowLeft className="w-5 h-5" />
            Retour
          </Link>
          <div className="flex items-center gap-2">
            <Car className="w-8 h-8 text-[#FFD60A]" />
            <span className="text-2xl font-black text-white">MÉTRO-TAXI</span>
          </div>
        </div>

        {/* Title */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-3xl font-black text-white mb-2">Mon Profil</h1>
          <p className="text-zinc-400">Gérez vos informations et consultez votre carte virtuelle</p>
        </motion.div>

        {/* Virtual Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-8"
        >
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <CreditCard className="w-5 h-5 text-[#FFD60A]" />
            Carte Virtuelle Métro-Taxi
          </h2>
          
          <div className="virtual-card">
            <div className="relative z-10">
              {/* Card Header */}
              <div className="flex justify-between items-start mb-8">
                <div className="flex items-center gap-2">
                  <Car className="w-8 h-8 text-[#FFD60A]" />
                  <span className="text-xl font-black text-white">MÉTRO-TAXI</span>
                </div>
                <div className={`px-3 py-1 rounded text-sm font-bold ${
                  virtualCard?.subscription_active 
                    ? 'bg-green-500/20 text-green-400 border border-green-500/50' 
                    : 'bg-zinc-700/50 text-zinc-400 border border-zinc-600'
                }`}>
                  {virtualCard?.subscription_active ? 'ACTIF' : 'INACTIF'}
                </div>
              </div>
              
              {/* Card Body */}
              <div className="mb-6">
                <p className="text-zinc-400 text-sm mb-1">TITULAIRE</p>
                <p className="text-2xl font-bold text-white">{virtualCard?.name || `${user?.first_name} ${user?.last_name}`}</p>
              </div>
              
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <p className="text-zinc-400 text-sm mb-1">IDENTIFIANT</p>
                  <p className="text-white font-mono text-sm">{user?.id?.slice(0, 8).toUpperCase()}</p>
                </div>
                <div>
                  <p className="text-zinc-400 text-sm mb-1">TÉLÉPHONE</p>
                  <p className="text-white">{virtualCard?.phone || user?.phone}</p>
                </div>
              </div>
              
              {virtualCard?.subscription_active && (
                <div className="bg-black/30 p-4 rounded">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="text-zinc-400 text-sm">ABONNEMENT</p>
                      <p className="text-[#FFD60A] font-bold">{getPlanName(virtualCard?.subscription_plan)}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-zinc-400 text-sm">EXPIRE LE</p>
                      <p className="text-white">{formatDate(virtualCard?.subscription_expires)}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </motion.div>

        {/* User Information */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-[#18181B] border border-zinc-800 rounded p-6"
        >
          <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
            <User className="w-5 h-5 text-[#FFD60A]" />
            Informations personnelles
          </h2>
          
          <div className="space-y-4">
            <div className="flex items-center gap-4 p-4 bg-zinc-900 rounded">
              <User className="w-5 h-5 text-zinc-400" />
              <div>
                <p className="text-zinc-400 text-sm">Nom complet</p>
                <p className="text-white font-medium">{user?.first_name} {user?.last_name}</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4 p-4 bg-zinc-900 rounded">
              <Mail className="w-5 h-5 text-zinc-400" />
              <div>
                <p className="text-zinc-400 text-sm">Email</p>
                <p className="text-white font-medium">{user?.email}</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4 p-4 bg-zinc-900 rounded">
              <Phone className="w-5 h-5 text-zinc-400" />
              <div>
                <p className="text-zinc-400 text-sm">Téléphone</p>
                <p className="text-white font-medium">{user?.phone}</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4 p-4 bg-zinc-900 rounded">
              <Calendar className="w-5 h-5 text-zinc-400" />
              <div>
                <p className="text-zinc-400 text-sm">Membre depuis</p>
                <p className="text-white font-medium">{formatDate(user?.created_at)}</p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Subscription CTA */}
        {!user?.subscription_active && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="mt-8 p-6 bg-[#FFD60A]/10 border border-[#FFD60A]/30 rounded"
          >
            <div className="flex items-center gap-4">
              <Shield className="w-10 h-10 text-[#FFD60A]" />
              <div className="flex-1">
                <h3 className="text-white font-bold mb-1">Activez votre abonnement</h3>
                <p className="text-zinc-400 text-sm">Profitez de trajets illimités avec nos forfaits adaptés à vos besoins.</p>
              </div>
              <Link to="/subscription">
                <Button className="bg-[#FFD60A] text-black font-bold hover:bg-[#E6C209]" data-testid="activate-subscription-btn">
                  S'ABONNER
                </Button>
              </Link>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default Profile;
