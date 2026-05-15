import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Building2, Users, Wallet, ShieldCheck, ArrowRight, Loader2, CheckCircle2, Mail, Phone, MapPin } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import { Link } from 'react-router-dom';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const PatronVTC = () => {
  const [form, setForm] = useState({
    full_name: '',
    company_name: '',
    email: '',
    phone: '',
    fleet_size: '',
    city: '',
    message: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleChange = (field) => (e) => {
    setForm((p) => ({ ...p, [field]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.full_name || !form.email || !form.phone || !form.fleet_size || !form.city) {
      toast.error('Merci de remplir les champs obligatoires');
      return;
    }
    const fleetSize = parseInt(form.fleet_size, 10);
    if (isNaN(fleetSize) || fleetSize < 1) {
      toast.error('Indique le nombre de véhicules de ta flotte');
      return;
    }
    try {
      setSubmitting(true);
      await axios.post(`${API}/fleet-partnerships/apply`, {
        ...form,
        fleet_size: fleetSize,
      });
      setSubmitted(true);
      toast.success('Demande envoyée — Judée te recontacte sous 48h', { duration: 6000 });
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erreur — réessaie');
    } finally {
      setSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div className="min-h-screen bg-[#09090B] text-white flex items-center justify-center p-6" data-testid="patron-vtc-success">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-lg w-full bg-[#18181B] border border-[#FFD60A]/30 rounded-2xl p-8 text-center"
        >
          <CheckCircle2 className="w-16 h-16 text-emerald-400 mx-auto mb-4" />
          <h1 className="text-3xl font-bold mb-2">Demande envoyée ✅</h1>
          <p className="text-zinc-400 mb-6">
            Merci pour ton intérêt. Judée Souleymane Nazim, fondateur de Métro-Taxi, te recontacte sous <strong className="text-[#FFD60A]">48h</strong>.
          </p>
          <p className="text-sm text-zinc-500 mb-6">Tu vas recevoir un email de confirmation à <strong className="text-white">{form.email}</strong>.</p>
          <Link to="/">
            <Button className="bg-[#FFD60A] text-black hover:bg-[#FFD60A]/90" data-testid="patron-vtc-back-home">
              Retour à l'accueil
            </Button>
          </Link>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#09090B] text-white" data-testid="patron-vtc-page">
      {/* Hero */}
      <section className="relative overflow-hidden border-b border-zinc-800">
        <div className="absolute inset-0 bg-gradient-to-br from-[#FFD60A]/5 via-transparent to-transparent" />
        <div className="max-w-5xl mx-auto px-6 py-16 relative">
          <Link to="/" className="text-zinc-500 hover:text-white text-sm inline-flex items-center gap-1 mb-8" data-testid="patron-vtc-back-link">
            ← Retour
          </Link>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-3xl"
          >
            <div className="inline-flex items-center gap-2 bg-[#FFD60A]/10 border border-[#FFD60A]/30 text-[#FFD60A] px-3 py-1 rounded-full text-xs uppercase tracking-wider mb-5">
              <Building2 className="w-3.5 h-3.5" />
              Programme B2B — Patron VTC
            </div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight mb-5">
              Ta flotte mérite mieux que <span className="text-[#FFD60A]">25 % de commission</span>.
            </h1>
            <p className="text-lg text-zinc-300 leading-relaxed mb-2">
              Métro-Taxi, c'est <strong className="text-white">0 % de commission</strong>, <strong className="text-white">1,50 € / km</strong> garantis à tes chauffeurs avec des abonnés à bord, et un algorithme qui maximise leur remplissage.
            </p>
            <p className="text-sm text-zinc-500">
              Discutons partenariat : ta flotte connectée, tes chauffeurs payés le 10 du mois, ta marge protégée.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Bénéfices */}
      <section className="max-w-5xl mx-auto px-6 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { icon: Wallet,       title: '0 % commission',       desc: 'Tes chauffeurs gardent 100 % de leurs km. On vit du forfait abonné, pas de leur travail.', color: 'text-emerald-400' },
            { icon: Users,        title: 'Algorithme mutualisé', title2: 'Algorithme mutualisé', desc: 'Plusieurs abonnés par trajet = revenus optimisés pour tes chauffeurs.', color: 'text-blue-400' },
            { icon: ShieldCheck,  title: 'Modèle anti-requalif', desc: 'CGP rigoureuses validées par Parallel Avocats. Tes chauffeurs restent indépendants.', color: 'text-[#FFD60A]' },
          ].map((b, i) => {
            const Icon = b.icon;
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.08 }}
                className="bg-[#18181B] border border-zinc-800 rounded-xl p-5"
                data-testid={`patron-vtc-benefit-${i}`}
              >
                <Icon className={`w-7 h-7 ${b.color} mb-3`} />
                <h3 className="text-lg font-bold mb-1">{b.title}</h3>
                <p className="text-zinc-400 text-sm leading-relaxed">{b.desc}</p>
              </motion.div>
            );
          })}
        </div>
      </section>

      {/* Form */}
      <section className="max-w-3xl mx-auto px-6 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-[#18181B] border border-zinc-800 rounded-2xl p-6 sm:p-8"
        >
          <h2 className="text-2xl font-bold mb-2">Demande de partenariat flotte</h2>
          <p className="text-zinc-500 text-sm mb-6">Judée Souleymane Nazim te recontacte personnellement sous 48h.</p>

          <form onSubmit={handleSubmit} className="space-y-4" data-testid="patron-vtc-form">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label className="text-zinc-300">Nom complet <span className="text-red-400">*</span></Label>
                <Input
                  required
                  value={form.full_name}
                  onChange={handleChange('full_name')}
                  placeholder="Salim El Hadi"
                  className="bg-zinc-950 border-zinc-700 text-white mt-1"
                  data-testid="patron-vtc-input-name"
                />
              </div>
              <div>
                <Label className="text-zinc-300">Société (optionnel)</Label>
                <Input
                  value={form.company_name}
                  onChange={handleChange('company_name')}
                  placeholder="Ex: Cab Premium SARL"
                  className="bg-zinc-950 border-zinc-700 text-white mt-1"
                  data-testid="patron-vtc-input-company"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label className="text-zinc-300">
                  <Mail className="w-3.5 h-3.5 inline mr-1" /> Email <span className="text-red-400">*</span>
                </Label>
                <Input
                  required
                  type="email"
                  value={form.email}
                  onChange={handleChange('email')}
                  placeholder="salim@cabpremium.com"
                  className="bg-zinc-950 border-zinc-700 text-white mt-1"
                  data-testid="patron-vtc-input-email"
                />
              </div>
              <div>
                <Label className="text-zinc-300">
                  <Phone className="w-3.5 h-3.5 inline mr-1" /> Téléphone <span className="text-red-400">*</span>
                </Label>
                <Input
                  required
                  type="tel"
                  value={form.phone}
                  onChange={handleChange('phone')}
                  placeholder="06 12 34 56 78"
                  className="bg-zinc-950 border-zinc-700 text-white mt-1"
                  data-testid="patron-vtc-input-phone"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label className="text-zinc-300">
                  <Building2 className="w-3.5 h-3.5 inline mr-1" /> Nombre de véhicules <span className="text-red-400">*</span>
                </Label>
                <Input
                  required
                  type="number"
                  min="1"
                  value={form.fleet_size}
                  onChange={handleChange('fleet_size')}
                  placeholder="Ex: 20"
                  className="bg-zinc-950 border-zinc-700 text-white mt-1"
                  data-testid="patron-vtc-input-fleet-size"
                />
              </div>
              <div>
                <Label className="text-zinc-300">
                  <MapPin className="w-3.5 h-3.5 inline mr-1" /> Ville principale <span className="text-red-400">*</span>
                </Label>
                <Input
                  required
                  value={form.city}
                  onChange={handleChange('city')}
                  placeholder="Paris, Saint-Denis…"
                  className="bg-zinc-950 border-zinc-700 text-white mt-1"
                  data-testid="patron-vtc-input-city"
                />
              </div>
            </div>

            <div>
              <Label className="text-zinc-300">Message (optionnel)</Label>
              <Textarea
                value={form.message}
                onChange={handleChange('message')}
                placeholder="Parle-nous de ta flotte : types de véhicules, zones desservies, attentes…"
                className="bg-zinc-950 border-zinc-700 text-white mt-1 min-h-[100px]"
                data-testid="patron-vtc-input-message"
              />
            </div>

            <Button
              type="submit"
              disabled={submitting}
              className="w-full bg-[#FFD60A] text-black hover:bg-[#FFD60A]/90 disabled:opacity-50 h-12 text-base font-bold"
              data-testid="patron-vtc-submit-btn"
            >
              {submitting ? (
                <><Loader2 className="w-5 h-5 mr-2 animate-spin" /> Envoi…</>
              ) : (
                <>Envoyer ma demande <ArrowRight className="w-5 h-5 ml-2" /></>
              )}
            </Button>
            <p className="text-xs text-zinc-500 text-center">
              En cliquant, tu acceptes d'être recontacté par Métro-Taxi à propos d'un partenariat B2B. Tes données ne sont jamais revendues.
            </p>
          </form>
        </motion.div>
      </section>
    </div>
  );
};

export default PatronVTC;
