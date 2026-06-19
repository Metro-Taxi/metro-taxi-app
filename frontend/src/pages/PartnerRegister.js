import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Car, Store, Users, Building, MapPin, Mail, Phone, ArrowLeft, ArrowRight, Check, Sparkles, Banknote, QrCode } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/**
 * Page publique d'inscription partenaire — Patch V10 (19/06/2026)
 * Multi-step : Type → Infos → Confirmation
 */
const PartnerRegister = () => {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [referralCode, setReferralCode] = useState(null);

  const [formData, setFormData] = useState({
    partner_type: '',
    business_name: '',
    contact_first_name: '',
    contact_last_name: '',
    email: '',
    phone: '',
    street_address: '',
    postal_code: '',
    city: '',
    siret: '',
    activity_zone: '',
    motivation: '',
    preferred_contact: 'email',
  });

  const update = (k, v) => setFormData(prev => ({ ...prev, [k]: v }));

  const partnerTypes = [
    {
      key: 'commerce_fixe',
      label: 'Commerce fixe',
      icon: Store,
      desc: 'Boutique, restaurant, salon... QR code en vitrine + 15% par abonnement.',
      examples: 'Golden GSM, Kelly&apos;s, Taxiphones...',
    },
    {
      key: 'ambulant',
      label: 'Ambassadeur ambulant',
      icon: Users,
      desc: 'Démarchage rue/marché/sortie de métro. Tu reçois 15% par client signé.',
      examples: 'Sur le terrain, modèle Lyca Mobile',
    },
    {
      key: 'entreprise',
      label: 'Entreprise / Institution',
      icon: Building,
      desc: 'Hôtel, école, mairie, association... QR pour ta clientèle interne.',
      examples: 'Hôtels, écoles, mairies...',
    },
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload = { ...formData };
      // Nettoyer les champs vides
      Object.keys(payload).forEach(k => { if (!payload[k]) delete payload[k]; });
      const res = await axios.post(`${API}/partners/apply`, payload);
      setReferralCode(res.data.referral_code);
      setStep(3);
    } catch (error) {
      const msg = error.response?.data?.detail || 'Une erreur est survenue. Réessaie.';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const canProceedStep2 = () => {
    if (!formData.business_name || !formData.contact_first_name || !formData.contact_last_name) return false;
    if (!formData.email || !formData.phone) return false;
    if (formData.partner_type === 'commerce_fixe' && (!formData.city || !formData.street_address)) return false;
    if (formData.partner_type === 'ambulant' && !formData.activity_zone) return false;
    return true;
  };

  return (
    <div className="min-h-screen bg-[#09090B] text-white">
      {/* Header */}
      <header className="border-b border-zinc-800 px-4 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <Car className="w-7 h-7 text-[#FFD60A]" />
            <span className="text-xl font-black">MÉTRO-TAXI</span>
          </Link>
          <Link to="/" className="text-zinc-400 hover:text-white text-sm flex items-center gap-1">
            <ArrowLeft className="w-4 h-4" /> Retour
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section className="border-b border-zinc-800 px-4 py-12 bg-gradient-to-br from-[#0f0f12] to-[#09090B]">
        <div className="max-w-3xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 bg-[#FFD60A]/10 border border-[#FFD60A]/30 rounded-full px-4 py-2 mb-6"
          >
            <Sparkles className="w-4 h-4 text-[#FFD60A]" />
            <span className="text-[#FFD60A] text-sm font-bold">PROGRAMME PARTENAIRES 2026</span>
          </motion.div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black mb-4 leading-tight">
            Deviens partenaire,<br/>
            <span className="text-[#FFD60A]">gagne 15% à chaque abonnement</span>
          </h1>
          <p className="text-zinc-400 text-lg mb-8 max-w-xl mx-auto">
            Pour chaque <strong className="text-white">paiement d&apos;abonnement</strong> signé via ton code parrainage (initial ou renouvellement), tu touches <strong className="text-white">15%</strong>.
          </p>
          <div className="grid grid-cols-3 gap-4 max-w-2xl mx-auto">
            <div className="bg-[#18181B] border border-zinc-800 rounded-lg p-4">
              <Banknote className="w-6 h-6 text-[#FFD60A] mx-auto mb-2" />
              <p className="text-2xl font-black">15%</p>
              <p className="text-xs text-zinc-500">par abonnement</p>
            </div>
            <div className="bg-[#18181B] border border-zinc-800 rounded-lg p-4">
              <QrCode className="w-6 h-6 text-[#FFD60A] mx-auto mb-2" />
              <p className="text-2xl font-black">QR</p>
              <p className="text-xs text-zinc-500">à afficher</p>
            </div>
            <div className="bg-[#18181B] border border-zinc-800 rounded-lg p-4">
              <Sparkles className="w-6 h-6 text-[#FFD60A] mx-auto mb-2" />
              <p className="text-2xl font-black">0€</p>
              <p className="text-xs text-zinc-500">d&apos;inscription</p>
            </div>
          </div>
        </div>
      </section>

      {/* Form */}
      <section className="px-4 py-12">
        <div className="max-w-2xl mx-auto">
          {/* Progress */}
          <div className="flex items-center justify-center gap-2 mb-10">
            {[1, 2, 3].map(s => (
              <React.Fragment key={s}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                  step >= s ? 'bg-[#FFD60A] text-black' : 'bg-zinc-800 text-zinc-500'
                }`} data-testid={`step-indicator-${s}`}>
                  {step > s ? <Check className="w-4 h-4" /> : s}
                </div>
                {s < 3 && <div className={`w-12 h-0.5 ${step > s ? 'bg-[#FFD60A]' : 'bg-zinc-800'}`} />}
              </React.Fragment>
            ))}
          </div>

          <AnimatePresence mode="wait">
            {step === 1 && (
              <motion.div
                key="step1"
                initial={{ opacity: 0, x: 30 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -30 }}
                data-testid="partner-step-1"
              >
                <h2 className="text-2xl font-bold mb-2">Quel type de partenaire es-tu ?</h2>
                <p className="text-zinc-400 mb-8 text-sm">Choisis le profil qui te correspond. Tu peux toujours changer plus tard.</p>
                <div className="space-y-3">
                  {partnerTypes.map(t => {
                    const Icon = t.icon;
                    return (
                      <button
                        key={t.key}
                        onClick={() => { update('partner_type', t.key); setStep(2); }}
                        className={`w-full text-left p-5 rounded-lg border-2 transition-all hover:border-[#FFD60A] hover:bg-[#FFD60A]/5 ${
                          formData.partner_type === t.key
                            ? 'border-[#FFD60A] bg-[#FFD60A]/5'
                            : 'border-zinc-800 bg-[#18181B]'
                        }`}
                        data-testid={`partner-type-${t.key}`}
                      >
                        <div className="flex items-start gap-4">
                          <div className="bg-[#FFD60A]/10 rounded-full p-3 flex-shrink-0">
                            <Icon className="w-6 h-6 text-[#FFD60A]" />
                          </div>
                          <div className="flex-1">
                            <h3 className="font-bold text-lg mb-1">{t.label}</h3>
                            <p className="text-zinc-400 text-sm mb-2">{t.desc}</p>
                            <p className="text-zinc-500 text-xs italic">{t.examples}</p>
                          </div>
                          <ArrowRight className="w-5 h-5 text-zinc-600 self-center" />
                        </div>
                      </button>
                    );
                  })}
                </div>
              </motion.div>
            )}

            {step === 2 && (
              <motion.form
                key="step2"
                initial={{ opacity: 0, x: 30 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -30 }}
                onSubmit={handleSubmit}
                className="space-y-5"
                data-testid="partner-step-2"
              >
                <h2 className="text-2xl font-bold mb-2">Tes informations</h2>
                <p className="text-zinc-400 mb-6 text-sm">Tout reste confidentiel. On te contacte sous 24-48h.</p>

                <div className="space-y-2">
                  <Label className="text-zinc-300">Nom du commerce / activité *</Label>
                  <Input
                    value={formData.business_name}
                    onChange={(e) => update('business_name', e.target.value)}
                    placeholder={formData.partner_type === 'ambulant' ? 'Ton nom complet' : 'Ex: Golden GSM'}
                    className="bg-zinc-900 border-zinc-700 text-white h-11"
                    required
                    data-testid="business-name-input"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-2">
                    <Label className="text-zinc-300">Prénom *</Label>
                    <Input
                      value={formData.contact_first_name}
                      onChange={(e) => update('contact_first_name', e.target.value)}
                      className="bg-zinc-900 border-zinc-700 text-white h-11"
                      required
                      data-testid="first-name-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-zinc-300">Nom *</Label>
                    <Input
                      value={formData.contact_last_name}
                      onChange={(e) => update('contact_last_name', e.target.value)}
                      className="bg-zinc-900 border-zinc-700 text-white h-11"
                      required
                      data-testid="last-name-input"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="space-y-2">
                    <Label className="text-zinc-300 flex items-center gap-2"><Mail className="w-3 h-3" />Email *</Label>
                    <Input
                      type="email"
                      value={formData.email}
                      onChange={(e) => update('email', e.target.value)}
                      placeholder="contact@exemple.com"
                      className="bg-zinc-900 border-zinc-700 text-white h-11"
                      required
                      data-testid="email-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-zinc-300 flex items-center gap-2"><Phone className="w-3 h-3" />Téléphone *</Label>
                    <Input
                      type="tel"
                      value={formData.phone}
                      onChange={(e) => update('phone', e.target.value)}
                      placeholder="06 12 34 56 78"
                      className="bg-zinc-900 border-zinc-700 text-white h-11"
                      required
                      data-testid="phone-input"
                    />
                  </div>
                </div>

                {formData.partner_type === 'commerce_fixe' && (
                  <>
                    <div className="space-y-2">
                      <Label className="text-zinc-300 flex items-center gap-2"><MapPin className="w-3 h-3" />Adresse du commerce *</Label>
                      <Input
                        value={formData.street_address}
                        onChange={(e) => update('street_address', e.target.value)}
                        placeholder="12 rue Ornano"
                        className="bg-zinc-900 border-zinc-700 text-white h-11"
                        required
                        data-testid="address-input"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="space-y-2">
                        <Label className="text-zinc-300">Code postal *</Label>
                        <Input
                          value={formData.postal_code}
                          onChange={(e) => update('postal_code', e.target.value)}
                          placeholder="75018"
                          className="bg-zinc-900 border-zinc-700 text-white h-11"
                          required
                          data-testid="postal-input"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label className="text-zinc-300">Ville *</Label>
                        <Input
                          value={formData.city}
                          onChange={(e) => update('city', e.target.value)}
                          placeholder="Paris"
                          className="bg-zinc-900 border-zinc-700 text-white h-11"
                          required
                          data-testid="city-input"
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label className="text-zinc-300">SIRET (optionnel)</Label>
                      <Input
                        value={formData.siret}
                        onChange={(e) => update('siret', e.target.value)}
                        placeholder="123 456 789 00012"
                        className="bg-zinc-900 border-zinc-700 text-white h-11"
                        data-testid="siret-input"
                      />
                    </div>
                  </>
                )}

                {formData.partner_type === 'ambulant' && (
                  <div className="space-y-2">
                    <Label className="text-zinc-300 flex items-center gap-2"><MapPin className="w-3 h-3" />Zone d&apos;activité *</Label>
                    <Input
                      value={formData.activity_zone}
                      onChange={(e) => update('activity_zone', e.target.value)}
                      placeholder="Sortie métro Marx Dormoy, marché du dimanche..."
                      className="bg-zinc-900 border-zinc-700 text-white h-11"
                      required
                      data-testid="zone-input"
                    />
                  </div>
                )}

                <div className="space-y-2">
                  <Label className="text-zinc-300">Comment comptes-tu promouvoir Métro-Taxi ? <span className="text-zinc-600">(optionnel mais apprécié)</span></Label>
                  <Textarea
                    value={formData.motivation}
                    onChange={(e) => update('motivation', e.target.value)}
                    rows={3}
                    placeholder="Ex: J'ai 200 clients par jour qui demandent souvent comment rentrer..."
                    className="bg-zinc-900 border-zinc-700 text-white"
                    data-testid="motivation-input"
                  />
                </div>

                <div className="space-y-2">
                  <Label className="text-zinc-300">Préférence de contact</Label>
                  <div className="grid grid-cols-3 gap-2">
                    {['email', 'phone', 'whatsapp'].map(opt => (
                      <button
                        key={opt}
                        type="button"
                        onClick={() => update('preferred_contact', opt)}
                        className={`py-2 px-3 rounded border text-sm capitalize ${
                          formData.preferred_contact === opt
                            ? 'border-[#FFD60A] bg-[#FFD60A]/10 text-[#FFD60A]'
                            : 'border-zinc-700 text-zinc-400 hover:border-zinc-600'
                        }`}
                        data-testid={`contact-pref-${opt}`}
                      >
                        {opt === 'phone' ? 'Téléphone' : opt === 'email' ? 'Email' : 'WhatsApp'}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="flex gap-3 pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setStep(1)}
                    className="border-zinc-700 text-zinc-300"
                    data-testid="back-btn"
                  >
                    <ArrowLeft className="w-4 h-4 mr-1" /> Retour
                  </Button>
                  <Button
                    type="submit"
                    disabled={loading || !canProceedStep2()}
                    className="flex-1 bg-[#FFD60A] text-black font-bold h-11 hover:bg-[#E6C209]"
                    data-testid="submit-partner-btn"
                  >
                    {loading ? (
                      <div className="w-5 h-5 border-2 border-black border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <>Envoyer ma candidature <ArrowRight className="w-4 h-4 ml-1" /></>
                    )}
                  </Button>
                </div>
              </motion.form>
            )}

            {step === 3 && referralCode && (
              <motion.div
                key="step3"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="text-center"
                data-testid="partner-step-3"
              >
                <div className="w-20 h-20 bg-[#FFD60A] rounded-full flex items-center justify-center mx-auto mb-6">
                  <Check className="w-12 h-12 text-black" strokeWidth={3} />
                </div>
                <h2 className="text-3xl font-bold mb-3">Candidature reçue !</h2>
                <p className="text-zinc-400 mb-8 max-w-md mx-auto">
                  On t&apos;a envoyé un email de confirmation. Notre équipe te contacte sous 24-48h pour activer ton compte et te transmettre tes identifiants.
                </p>
                <div className="bg-[#18181B] border-2 border-[#FFD60A] rounded-xl p-6 max-w-sm mx-auto mb-6">
                  <p className="text-zinc-500 text-xs uppercase tracking-wider mb-2">Ton futur code parrainage</p>
                  <p className="text-[#FFD60A] text-5xl font-black font-mono tracking-widest" data-testid="referral-code-display">
                    {referralCode}
                  </p>
                  <p className="text-zinc-500 text-xs mt-2">(actif après validation)</p>
                </div>
                <Link to="/">
                  <Button className="bg-[#FFD60A] text-black font-bold hover:bg-[#E6C209]" data-testid="back-to-home-btn">
                    Retour à l&apos;accueil
                  </Button>
                </Link>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-zinc-800 px-4 py-8 text-center text-zinc-600 text-xs">
        <p>© 2026 Métro-Taxi · SIRET 918 687 864 RCS Bobigny</p>
        <p className="mt-1">Une question ? <a href="mailto:contact@metro-taxi.com" className="text-[#FFD60A] hover:underline">contact@metro-taxi.com</a></p>
      </footer>
    </div>
  );
};

export default PartnerRegister;
