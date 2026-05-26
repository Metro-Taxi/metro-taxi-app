import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Car, Gift, MapPin, Ticket, ArrowRight, Sparkles, CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

/**
 * Landing dédiée campagne Saint-Denis (lancement 13 juin 2026).
 * Stratégie : "1ère course OFFERTE ≤ 10 km" pour les 30 premiers inscrits.
 * Le chauffeur est payé normalement (1,50€/km) par la plateforme.
 */
const SaintDenis = () => {
  const [code, setCode] = useState('');

  const ctaHref = code.trim()
    ? `/register/user?promo=${encodeURIComponent(code.trim().toUpperCase())}&src=saint-denis`
    : '/register/user?src=saint-denis';

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
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
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
            Pour fêter notre arrivée dans le 93, les <span className="text-white font-semibold">30 premiers usagers</span> roulent gratuitement sur leur première course
            <span className="text-white font-semibold"> jusqu'à 10 km</span>. Aucun abonnement requis pour tester.
          </p>

          <div className="mt-10 grid grid-cols-1 md:grid-cols-3 gap-4 max-w-3xl">
            <div className="bg-[#18181B] border border-zinc-800 p-5 rounded-sm">
              <Gift className="w-6 h-6 text-[#FFD60A] mb-3" />
              <p className="text-white font-bold">0 € à payer</p>
              <p className="text-sm text-zinc-500 mt-1">La plateforme prend en charge ta 1<sup>ère</sup> course.</p>
            </div>
            <div className="bg-[#18181B] border border-zinc-800 p-5 rounded-sm">
              <MapPin className="w-6 h-6 text-[#FFD60A] mb-3" />
              <p className="text-white font-bold">Jusqu'à 10 km</p>
              <p className="text-sm text-zinc-500 mt-1">Largement de quoi traverser Saint-Denis et la périphérie.</p>
            </div>
            <div className="bg-[#18181B] border border-zinc-800 p-5 rounded-sm">
              <Sparkles className="w-6 h-6 text-[#FFD60A] mb-3" />
              <p className="text-white font-bold">30 places seulement</p>
              <p className="text-sm text-zinc-500 mt-1">Premier arrivé, premier servi. Codes uniques.</p>
            </div>
          </div>

          {/* Code form */}
          <div className="mt-12 bg-[#18181B] border border-zinc-800 p-6 md:p-8 rounded-sm max-w-2xl">
            <label htmlFor="promo-input" className="text-sm text-zinc-300 mb-2 block flex items-center gap-2">
              <Ticket className="w-4 h-4 text-[#FFD60A]" />
              Tu as un code promo Saint-Denis ?
            </label>
            <div className="flex flex-col sm:flex-row gap-3">
              <input
                id="promo-input"
                data-testid="saint-denis-promo-input"
                value={code}
                onChange={(e) => setCode(e.target.value.toUpperCase())}
                placeholder="STDENIS-2026-XXXX"
                className="flex-1 bg-zinc-900 border border-zinc-700 px-4 py-3 rounded text-white placeholder:text-zinc-600 focus:outline-none focus:border-[#FFD60A] font-mono uppercase tracking-wider"
                maxLength={40}
              />
              <Link to={ctaHref} className="inline-block">
                <Button
                  data-testid="saint-denis-cta-btn"
                  className="w-full sm:w-auto bg-[#FFD60A] text-black font-bold h-12 px-6 hover:bg-[#E6C209]"
                >
                  Je m'inscris <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </Link>
            </div>
            <p className="text-xs text-zinc-500 mt-3">
              Tu peux aussi t'inscrire sans code et activer un abonnement classique (6,99 € / 24h, 19,99 € / 7j, 53,99 € / mois).
            </p>
          </div>

          {/* How it works */}
          <div className="mt-16">
            <h2 className="text-lg md:text-lg font-bold mb-6">Comment ça marche ?</h2>
            <ol className="space-y-4 max-w-2xl">
              {[
                { t: "Inscris-toi avec ton code", d: "Saisis ton code STDENIS-2026-XXXX dans le formulaire d'inscription." },
                { t: "Demande ta course", d: "Indique ton point de départ et ta destination. La distance doit être ≤ 10 km." },
                { t: "Roule gratuitement", d: "Ton chauffeur est payé par la plateforme. Tu ne paies rien." },
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
