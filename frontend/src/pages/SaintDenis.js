import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Car, Gift, MapPin, ArrowRight, Sparkles, CheckCircle2, Users, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import i18n from '@/i18n';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;
const CAMPAIGN_ID = 'saint-denis-2026-06-13';

/**
 * Landing dédiée campagne Saint-Denis (lancement 13 juin 2026).
 *
 * Nouvelle mécanique "auto-attribution" :
 *  - Plus de code à saisir / scanner
 *  - Compteur LIVE des places restantes (effet rareté)
 *  - Le crédit "1ère course offerte ≤ 10 km" est attribué automatiquement
 *    à l'activation de l'abonnement, aux 30 premiers ABONNÉS.
 *  - Le crédit est consommable à partir du samedi 13 juin 2026 (date d'ouverture).
 */
const SaintDenis = () => {
  const [campaign, setCampaign] = useState(null);
  const [loading, setLoading] = useState(true);

  // Force French (DGCCRF clarity argument)
  useEffect(() => {
    if (i18n.language !== 'fr') {
      i18n.changeLanguage('fr');
      try { localStorage.setItem('i18nextLng', 'fr'); } catch (_) {}
    }
  }, []);

  // Fetch live counter
  const fetchStatus = async () => {
    try {
      const { data } = await axios.get(`${API}/api/campaigns/${CAMPAIGN_ID}/status`);
      setCampaign(data);
    } catch (err) {
      setCampaign(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    // Refresh toutes les 30 secondes pour effet "compteur live"
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const ctaHref = `/register/user?campaign=${encodeURIComponent(CAMPAIGN_ID)}`;

  const slotsRemaining = campaign?.slots_remaining ?? 30;
  const slotsTotal = campaign?.slots_total ?? 30;
  const slotsUsed = campaign?.slots_used ?? 0;
  const isFull = !loading && campaign && slotsRemaining === 0;
  const isExpired = !loading && campaign?.expired;

  return (
    <div className="min-h-screen bg-[#09090B] text-white" data-testid="saint-denis-page">
      {/* Top nav */}
      <nav className="px-6 py-5 flex items-center justify-between border-b border-zinc-900">
        <Link to="/" className="flex items-center gap-2" data-testid="saint-denis-logo">
          <Car className="w-7 h-7 text-[#FFD60A]" />
          <span className="text-xl font-black tracking-tight">MÉTRO-TAXI</span>
        </Link>
        <Link to="/login" className="text-sm text-zinc-400 hover:text-white" data-testid="saint-denis-login-link">
          Se connecter
        </Link>
      </nav>

      {/* Hero */}
      <section className="px-6 py-16 md:py-24 max-w-5xl mx-auto">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#FFD60A]/10 border border-[#FFD60A]/30 text-[#FFD60A] text-xs font-semibold mb-6">
            <MapPin className="w-3.5 h-3.5" />
            ZONE PILOTE — SAINT-DENIS (93)
            <span className="text-zinc-500">·</span>
            LANCEMENT 13 JUIN 2026
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black leading-tight">
            Ta <span className="text-[#FFD60A]">1<sup>ère</sup> course offerte</span>
            <br />à Saint-Denis.
          </h1>
          <p className="mt-6 text-lg text-zinc-400 max-w-2xl">
            Pour fêter notre arrivée dans le 93, les <span className="text-white font-semibold">30 premiers ABONNÉS</span> reçoivent
            leur première course <span className="text-white font-semibold">jusqu'à 10 km offerte</span>. Aucun code à saisir : c'est <span className="text-white font-semibold">automatique</span> à l'activation de ton abonnement.
          </p>

          {/* COMPTEUR LIVE — Effet rareté */}
          <div
            className="mt-10 bg-gradient-to-r from-[#FFD60A]/15 to-transparent border-l-4 border-[#FFD60A] p-6 rounded-sm max-w-2xl"
            data-testid="saint-denis-counter"
          >
            {loading ? (
              <p className="text-zinc-400">Chargement du compteur en direct…</p>
            ) : isExpired ? (
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-6 h-6 text-amber-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-amber-400 font-bold">La campagne Saint-Denis est terminée.</p>
                  <p className="text-sm text-zinc-400 mt-1">Tu peux toujours t'abonner pour profiter de nos tarifs et du covoiturage Métro-Taxi.</p>
                </div>
              </div>
            ) : isFull ? (
              <div className="flex items-start gap-3">
                <Sparkles className="w-6 h-6 text-zinc-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-zinc-200 font-bold">Les 30 premiers abonnés ont été récompensés !</p>
                  <p className="text-sm text-zinc-400 mt-1">Tu peux quand même rejoindre Métro-Taxi avec un abonnement classique. Bienvenue.</p>
                </div>
              </div>
            ) : (
              <div>
                <p className="text-sm text-zinc-400 uppercase tracking-wider font-semibold">PLACES RESTANTES</p>
                <p className="text-5xl md:text-6xl font-black text-[#FFD60A] mt-2" data-testid="saint-denis-slots-remaining">
                  {slotsRemaining}<span className="text-2xl text-zinc-500">/{slotsTotal}</span>
                </p>
                <p className="text-sm text-zinc-400 mt-3">
                  Déjà <span className="text-white font-semibold">{slotsUsed}</span> abonné{slotsUsed > 1 ? 's' : ''} ont sécurisé leur course offerte.
                </p>
                {slotsRemaining <= 10 && (
                  <p className="text-xs text-amber-400 mt-2 font-semibold animate-pulse">⚡ Dépêche-toi, ça part vite !</p>
                )}
              </div>
            )}
          </div>

          <div className="mt-10 grid grid-cols-1 md:grid-cols-3 gap-4 max-w-3xl">
            <div className="bg-[#18181B] border border-zinc-800 p-5 rounded-sm">
              <Gift className="w-6 h-6 text-[#FFD60A] mb-3" />
              <p className="text-white font-bold">0 € sur ta 1ère course</p>
              <p className="text-sm text-zinc-500 mt-1">La plateforme prend en charge ta première course offerte.</p>
            </div>
            <div className="bg-[#18181B] border border-zinc-800 p-5 rounded-sm">
              <MapPin className="w-6 h-6 text-[#FFD60A] mb-3" />
              <p className="text-white font-bold">Jusqu'à 10 km</p>
              <p className="text-sm text-zinc-500 mt-1">Largement de quoi traverser Saint-Denis et la périphérie.</p>
            </div>
            <div className="bg-[#18181B] border border-zinc-800 p-5 rounded-sm">
              <Users className="w-6 h-6 text-[#FFD60A] mb-3" />
              <p className="text-white font-bold">Covoiturage berline</p>
              <p className="text-sm text-zinc-500 mt-1">Place assise, climatisation, porte-à-porte. Vraiment confortable.</p>
            </div>
          </div>

          {/* CTA */}
          <div className="mt-12 max-w-2xl">
            <Link to={ctaHref}>
              <Button
                data-testid="saint-denis-cta-btn"
                disabled={isFull || isExpired}
                className="w-full sm:w-auto bg-[#FFD60A] text-black font-bold h-14 px-8 text-base hover:bg-[#E6C209] disabled:opacity-50"
              >
                {isFull || isExpired ? "Campagne terminée" : "Je deviens Pionnier Saint-Denis"} <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
            <p className="text-xs text-zinc-500 mt-3">
              Abonnement à partir de 6,99 € / 24h. Ta course offerte (jusqu'à 10 km) est consommable à partir du <span className="text-white">samedi 13 juin 2026</span>.
            </p>
          </div>

          {/* How it works */}
          <div className="mt-16">
            <h2 className="text-lg font-bold mb-6">Comment ça marche ?</h2>
            <ol className="space-y-4 max-w-2xl">
              {[
                { t: "Inscris-toi en 1 minute", d: "Pas de code à saisir — clique simplement sur le bouton ci-dessus." },
                { t: "Choisis ton abonnement", d: "À partir de 6,99 € pour 24h. Tu deviens immédiatement Pionnier Saint-Denis si tu fais partie des 30 premiers." },
                { t: "Réserve ta course à partir du 13 juin", d: "Ta première course (jusqu'à 10 km) est offerte. Au-delà de 10 km, il faudra choisir une destination plus proche." },
              ].map((s, i) => (
                <li key={i} className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-[#FFD60A] flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-white font-semibold">{s.t}</p>
                    <p className="text-sm text-zinc-400">{s.d}</p>
                  </div>
                </li>
              ))}
            </ol>
          </div>

          <div className="mt-12 text-sm text-zinc-500">
            Tu es chauffeur VTC ? <Link to="/register/driver" className="text-[#FFD60A] hover:underline">Rejoins le réseau des pionniers</Link>.
          </div>
        </motion.div>
      </section>
    </div>
  );
};

export default SaintDenis;
