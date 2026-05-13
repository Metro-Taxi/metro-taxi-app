import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Award, Lock, Star, Mail, CheckCircle, Loader2, Crown, Sparkles, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const FoundingMember = () => {
  const { isAuthenticated, role, token } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [myStatus, setMyStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [joining, setJoining] = useState(false);

  const fetchData = async () => {
    try {
      const [statsRes, meRes] = await Promise.all([
        axios.get(`${API}/founding-members/stats`),
        isAuthenticated && role === 'user'
          ? axios.get(`${API}/founding-members/me`, { headers: { Authorization: `Bearer ${token}` } })
          : Promise.resolve({ data: { is_founding_member: false } }),
      ]);
      setStats(statsRes.data);
      setMyStatus(meRes.data);
    } catch (e) {
      toast.error('Impossible de charger les données');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [isAuthenticated, token]); // eslint-disable-line

  const handleJoin = async () => {
    if (!isAuthenticated) {
      navigate('/register/user?src=founder');
      return;
    }
    if (role !== 'user') {
      toast.error('Réservé aux abonnés Métro-Taxi. Crée d\'abord un compte usager.');
      return;
    }
    try {
      setJoining(true);
      const { data } = await axios.post(`${API}/founding-members/join`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success(data.message || 'Bienvenue Membre Fondateur !', { duration: 6000 });
      await fetchData();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Erreur lors de l\'inscription');
    } finally {
      setJoining(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#09090B] flex items-center justify-center">
        <Loader2 className="w-10 h-10 animate-spin text-[#FFD60A]" />
      </div>
    );
  }

  const isMember = myStatus?.is_founding_member;
  const memberNumber = myStatus?.founding_member_number;

  return (
    <div className="min-h-screen bg-[#09090B] text-white" data-testid="founding-member-page">
      {/* Hero */}
      <div className="relative overflow-hidden border-b border-zinc-800">
        <div className="absolute inset-0 bg-gradient-to-br from-[#FFD60A]/10 via-transparent to-amber-500/5 pointer-events-none" />
        <div className="max-w-5xl mx-auto px-6 py-16 lg:py-24 relative">
          <Link to="/" className="inline-block text-zinc-400 hover:text-[#FFD60A] text-sm mb-8 transition">
            ← Retour à l'accueil
          </Link>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 bg-[#FFD60A] text-black px-4 py-2 rounded-full font-bold text-sm mb-6"
          >
            <Crown className="w-4 h-4" />
            CERCLE MEMBRE FONDATEUR
          </motion.div>
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight mb-6"
          >
            Sois l'un des <span className="text-[#FFD60A]">premiers</span> à<br />
            recevoir le tarif <span className="text-[#FFD60A]">verrouillé à vie</span>.
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-lg lg:text-xl text-zinc-300 max-w-3xl leading-relaxed"
          >
            Métro-Taxi ouvre les abonnements quand on atteint <strong className="text-white">150 chauffeurs zone pilote</strong>.
            En attendant, <strong className="text-[#FFD60A]">tu peux verrouiller le tarif Membre Fondateur</strong> dès maintenant — sans payer un centime aujourd'hui.
          </motion.p>
        </div>
      </div>

      {/* Status banner if member */}
      {isMember && (
        <div className="max-w-5xl mx-auto px-6 mt-8">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-gradient-to-r from-[#FFD60A]/20 via-amber-500/10 to-transparent border border-[#FFD60A]/40 rounded-lg p-6 flex items-center gap-4"
            data-testid="member-status-banner"
          >
            <div className="w-16 h-16 bg-[#FFD60A] text-black rounded-full flex items-center justify-center flex-shrink-0">
              <Award className="w-8 h-8" />
            </div>
            <div>
              <p className="text-zinc-400 text-sm">Tu es</p>
              <h3 className="text-2xl font-bold text-[#FFD60A]">Membre Fondateur #{memberNumber}</h3>
              <p className="text-zinc-300 text-sm mt-1">Tarif <strong className="text-white">53,99€/mois</strong> verrouillé à vie ✅</p>
            </div>
          </motion.div>
        </div>
      )}

      {/* Progress + Stats */}
      <div className="max-w-5xl mx-auto px-6 py-12 grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-[#18181B] border border-zinc-800 rounded-lg p-6">
          <h2 className="text-zinc-400 text-sm uppercase tracking-wider mb-3">Progression vers le lancement</h2>
          <p className="text-4xl font-bold text-white mb-1">
            {stats.drivers_count} <span className="text-zinc-500 text-2xl">/ {stats.target_drivers}</span>
          </p>
          <p className="text-zinc-400 text-sm mb-4">chauffeurs VTC pionniers</p>
          <div className="h-3 bg-zinc-800 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${stats.progress_pct}%` }}
              transition={{ duration: 1.2, ease: 'easeOut' }}
              className="h-full bg-gradient-to-r from-[#FFD60A] to-amber-500"
            />
          </div>
          <p className="text-zinc-500 text-xs mt-2">{stats.progress_pct}% du chemin parcouru</p>
        </div>
        <div className="bg-[#18181B] border border-zinc-800 rounded-lg p-6 flex flex-col justify-center">
          <div className="flex items-center gap-2 text-zinc-400 text-sm uppercase tracking-wider mb-2">
            <Sparkles className="w-4 h-4" /> Membres Fondateurs
          </div>
          <p className="text-5xl font-bold text-[#FFD60A]">{stats.founding_members_count}</p>
          <p className="text-zinc-400 text-sm mt-1">déjà à bord</p>
        </div>
      </div>

      {/* Perks */}
      <div className="max-w-5xl mx-auto px-6 py-8">
        <h2 className="text-3xl font-bold mb-8">Tes <span className="text-[#FFD60A]">4 privilèges</span> exclusifs</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { icon: Lock, title: 'Tarif 53,99€/mois verrouillé à VIE', desc: 'Vs ~79€/mois en tarif standard futur. Pour toute la durée de ton abonnement.' },
            { icon: Star, title: 'Accès prioritaire 48h avant tous', desc: 'Tu actives ton abonnement avant l\'ouverture publique officielle.' },
            { icon: Award, title: 'Badge Membre Fondateur dans l\'app', desc: 'Visible sur ton profil chauffeur. Marque de confiance et reconnaissance.' },
            { icon: Mail, title: 'Newsletter privée des coulisses', desc: 'Tous les choix stratégiques, les chiffres, les coulisses du projet.' },
          ].map((perk, i) => {
            const Icon = perk.icon;
            return (
              <motion.div
                key={perk.title}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className="bg-[#18181B] border border-zinc-800 rounded-lg p-5 hover:border-[#FFD60A]/40 transition"
              >
                <div className="w-10 h-10 bg-[#FFD60A]/15 text-[#FFD60A] rounded-lg flex items-center justify-center mb-3">
                  <Icon className="w-5 h-5" />
                </div>
                <h3 className="font-bold text-lg mb-1">{perk.title}</h3>
                <p className="text-zinc-400 text-sm leading-relaxed">{perk.desc}</p>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* CTA */}
      {!isMember && (
        <div className="max-w-5xl mx-auto px-6 py-12">
          <div className="bg-gradient-to-br from-[#FFD60A]/20 via-amber-500/10 to-transparent border border-[#FFD60A]/30 rounded-lg p-8 lg:p-12 text-center">
            <h2 className="text-3xl lg:text-4xl font-bold mb-3">Prêt à rejoindre le cercle ?</h2>
            <p className="text-zinc-300 mb-2">100% gratuit aujourd'hui. Aucun paiement requis.</p>
            <p className="text-zinc-500 text-sm mb-8">On t'envoie un email quand on atteint les 150 chauffeurs — tu pourras alors activer ton abonnement au tarif fondateur.</p>
            <Button
              onClick={handleJoin}
              disabled={joining}
              className="bg-[#FFD60A] hover:bg-[#FFD60A]/90 text-black font-bold text-lg px-8 py-6 h-auto"
              data-testid="join-founding-member-btn"
            >
              {joining ? (
                <><Loader2 className="w-5 h-5 mr-2 animate-spin" />Inscription...</>
              ) : isAuthenticated ? (
                <>Verrouiller mon tarif fondateur <ArrowRight className="w-5 h-5 ml-2" /></>
              ) : (
                <>Créer mon compte fondateur <ArrowRight className="w-5 h-5 ml-2" /></>
              )}
            </Button>
            <p className="text-zinc-500 text-xs mt-4">⚡ Places limitées aux premiers inscrits. Pas de paiement, pas d'engagement avant ouverture.</p>
          </div>
        </div>
      )}

      {/* Why wait */}
      <div className="max-w-5xl mx-auto px-6 py-12 border-t border-zinc-800">
        <div className="flex items-start gap-4 max-w-3xl">
          <CheckCircle className="w-6 h-6 text-[#FFD60A] flex-shrink-0 mt-1" />
          <div>
            <h3 className="text-xl font-bold mb-2">Pourquoi cette attente ?</h3>
            <p className="text-zinc-300 leading-relaxed">
              On a fait le choix difficile mais juste : <strong className="text-white">ne pas vendre d'abonnement avant d'avoir assez de chauffeurs pour te transporter</strong>. Pas de vent vendu, pas de promesse en l'air.
              Quand Métro-Taxi ouvre officiellement, tout fonctionne. Ta confiance d'aujourd'hui mérite cette rigueur.
            </p>
            <p className="text-zinc-500 text-sm mt-3">— Judée Mané, Fondateur</p>
          </div>
        </div>
      </div>

      <div className="h-16" />
    </div>
  );
};

export default FoundingMember;
