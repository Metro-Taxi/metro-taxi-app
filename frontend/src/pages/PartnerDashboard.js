import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { QRCodeSVG } from 'qrcode.react';
import { Car, LogOut, Users, Banknote, TrendingUp, Download, Copy, Share2, Store, Building, Sparkles, KeyRound } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';
import ChangePasswordModal from '@/components/ChangePasswordModal';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/**
 * Dashboard partenaire — Patch V10 (19/06/2026)
 * Affiche : stats temps réel, QR code téléchargeable, signups récents, commission.
 */
const PartnerDashboard = () => {
  const navigate = useNavigate();
  const { partner, token, logout } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showPwd, setShowPwd] = useState(false);
  const qrRef = useRef(null);

  useEffect(() => {
    if (!partner) {
      navigate('/login');
      return;
    }
    loadDashboard();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [partner]);

  const loadDashboard = async () => {
    try {
      const res = await axios.get(`${API}/partners/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setData(res.data);
    } catch (e) {
      toast.error('Erreur de chargement');
    } finally {
      setLoading(false);
    }
  };

  if (loading || !data) {
    return (
      <div className="min-h-screen bg-[#09090B] flex items-center justify-center">
        <div className="w-10 h-10 border-2 border-[#FFD60A] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const referralUrl = `https://metro-taxi.com/inscription?ref=${data.referral_code}`;
  const partnerTypeLabel = {
    commerce_fixe: { label: 'Commerce fixe', Icon: Store },
    ambulant: { label: 'Ambassadeur ambulant', Icon: Users },
    entreprise: { label: 'Entreprise', Icon: Building },
  }[data.partner_type] || { label: 'Partenaire', Icon: Store };
  const TypeIcon = partnerTypeLabel.Icon;

  const handleDownloadQR = () => {
    const svg = qrRef.current?.querySelector('svg');
    if (!svg) return;
    const serializer = new XMLSerializer();
    const svgStr = serializer.serializeToString(svg);
    const canvas = document.createElement('canvas');
    const size = 1024;
    canvas.width = size;
    canvas.height = size;
    const img = new Image();
    img.onload = () => {
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = '#FFFFFF';
      ctx.fillRect(0, 0, size, size);
      ctx.drawImage(img, 0, 0, size, size);
      canvas.toBlob((blob) => {
        const link = document.createElement('a');
        link.download = `MetroTaxi-QR-${data.referral_code}.png`;
        link.href = URL.createObjectURL(blob);
        link.click();
        toast.success('QR code téléchargé !');
      });
    };
    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgStr)));
  };

  const handleCopyLink = () => {
    navigator.clipboard.writeText(referralUrl);
    toast.success('Lien copié dans le presse-papier !');
  };

  const handleShare = async () => {
    const text = `Inscris-toi sur Métro-Taxi avec mon code parrainage ${data.referral_code} et profite du VTC abordable en région parisienne :`;
    if (navigator.share) {
      try {
        await navigator.share({ title: 'Métro-Taxi - Code parrainage', text, url: referralUrl });
      } catch (_) { /* user cancelled share */ }
    } else {
      navigator.clipboard.writeText(`${text} ${referralUrl}`);
      toast.success('Texte de partage copié !');
    }
  };

  const subscribers = data.recent_referrals?.filter(u => u.subscription_active).length || 0;
  const commissionMonth = subscribers * 6.99 * 0.15; // estimation simple

  return (
    <div className="min-h-screen bg-[#09090B] text-white">
      {/* Header */}
      <header className="border-b border-zinc-800 px-4 py-4 sticky top-0 bg-[#09090B]/95 backdrop-blur z-10">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Car className="w-7 h-7 text-[#FFD60A]" />
            <div>
              <p className="text-xs text-zinc-500">Espace partenaire</p>
              <h1 className="font-bold text-lg leading-none">{data.business_name}</h1>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowPwd(true)}
              className="text-zinc-400 hover:text-white"
              data-testid="partner-change-password"
            >
              <KeyRound className="w-4 h-4 sm:mr-2" />
              <span className="hidden sm:inline">Mot de passe</span>
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => { logout(); navigate('/'); }}
              className="text-zinc-400 hover:text-white"
              data-testid="partner-logout-btn"
            >
              <LogOut className="w-4 h-4 sm:mr-2" />
              <span className="hidden sm:inline">Déconnexion</span>
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8 space-y-8">
        {/* Welcome */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-br from-[#FFD60A]/10 to-transparent border border-[#FFD60A]/30 rounded-xl p-6"
        >
          <div className="flex items-center gap-3 mb-2">
            <TypeIcon className="w-5 h-5 text-[#FFD60A]" />
            <span className="text-[#FFD60A] text-sm font-bold">{partnerTypeLabel.label}</span>
            <span className="text-zinc-500 text-xs">· Commission {(data.commission_rate * 100).toFixed(0)}%</span>
          </div>
          <h2 className="text-2xl font-bold mb-1">Salut {data.contact_first_name} 👋</h2>
          <p className="text-zinc-400 text-sm">Affiche ton QR code dans ton commerce. Tu touches 15% à chaque abonnement payé via ton code (initial + renouvellements).</p>
        </motion.div>

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-[#18181B] border border-zinc-800 rounded-xl p-5" data-testid="stat-signups">
            <div className="flex items-center justify-between mb-2">
              <span className="text-zinc-500 text-xs uppercase tracking-wider">Inscrits via ton code</span>
              <Users className="w-4 h-4 text-zinc-600" />
            </div>
            <p className="text-3xl font-black">{data.recent_referrals?.length || 0}</p>
          </div>
          <div className="bg-[#18181B] border border-zinc-800 rounded-xl p-5" data-testid="stat-subscribers">
            <div className="flex items-center justify-between mb-2">
              <span className="text-zinc-500 text-xs uppercase tracking-wider">Abonnés actifs</span>
              <Sparkles className="w-4 h-4 text-zinc-600" />
            </div>
            <p className="text-3xl font-black text-[#FFD60A]">{subscribers}</p>
          </div>
          <div className="bg-[#18181B] border border-zinc-800 rounded-xl p-5" data-testid="stat-commission">
            <div className="flex items-center justify-between mb-2">
              <span className="text-zinc-500 text-xs uppercase tracking-wider">Commission estimée</span>
              <Banknote className="w-4 h-4 text-zinc-600" />
            </div>
            <p className="text-3xl font-black text-green-400">~ {commissionMonth.toFixed(2)} €</p>
            <p className="text-xs text-zinc-600 mt-1">ce mois-ci</p>
          </div>
        </div>

        {/* QR + Code */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-[#18181B] border border-zinc-800 rounded-xl p-6"
          >
            <h3 className="font-bold text-lg mb-4">Ton QR code à afficher</h3>
            <div ref={qrRef} className="bg-white rounded-lg p-6 mb-4 flex items-center justify-center">
              <QRCodeSVG
                value={referralUrl}
                size={220}
                level="H"
                imageSettings={{ src: '/favicon.ico', height: 30, width: 30, excavate: true }}
                data-testid="partner-qr-code"
              />
            </div>
            <Button
              onClick={handleDownloadQR}
              className="w-full bg-[#FFD60A] text-black font-bold hover:bg-[#E6C209]"
              data-testid="download-qr-btn"
            >
              <Download className="w-4 h-4 mr-2" /> Télécharger le QR (PNG haute résolution)
            </Button>
            <p className="text-xs text-zinc-500 mt-3 text-center">
              💡 Imprime-le en A5 (15 × 21 cm) et colle-le sur ta vitrine.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-[#18181B] border border-zinc-800 rounded-xl p-6"
          >
            <h3 className="font-bold text-lg mb-4">Ton code parrainage</h3>
            <div className="bg-[#0a0a0a] border-2 border-[#FFD60A] rounded-lg p-6 text-center mb-4">
              <p className="text-zinc-500 text-xs uppercase tracking-wider mb-2">Code unique</p>
              <p className="text-[#FFD60A] text-5xl font-black font-mono tracking-widest" data-testid="partner-code">
                {data.referral_code}
              </p>
            </div>
            <div className="space-y-2">
              <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-3 flex items-center gap-2">
                <code className="flex-1 text-xs text-zinc-400 truncate" data-testid="partner-link">{referralUrl}</code>
                <Button size="sm" variant="ghost" onClick={handleCopyLink} className="text-zinc-400 hover:text-white" data-testid="copy-link-btn">
                  <Copy className="w-4 h-4" />
                </Button>
              </div>
              <Button
                onClick={handleShare}
                variant="outline"
                className="w-full border-zinc-700 text-zinc-300 hover:bg-zinc-800"
                data-testid="share-link-btn"
              >
                <Share2 className="w-4 h-4 mr-2" /> Partager mon lien
              </Button>
            </div>
            <div className="mt-6 bg-yellow-500/5 border border-yellow-500/20 rounded p-3">
              <p className="text-xs text-yellow-200/80 leading-relaxed">
                💬 <strong>Astuce</strong> : dis simplement à tes clients <em>&quot;Tape <strong className="text-[#FFD60A]">{data.referral_code}</strong> lors de l&apos;inscription&quot;</em>, ou laisse-les scanner le QR.
              </p>
            </div>
          </motion.div>
        </div>

        {/* Recent referrals */}
        {data.recent_referrals && data.recent_referrals.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-[#18181B] border border-zinc-800 rounded-xl p-6"
          >
            <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-[#FFD60A]" />
              Inscriptions récentes <span className="text-zinc-500 text-sm font-normal">({data.recent_referrals.length})</span>
            </h3>
            <div className="space-y-2">
              {data.recent_referrals.slice(0, 10).map((u, i) => (
                <div key={u.id || i} className="flex items-center justify-between p-3 bg-zinc-900 rounded">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-[#FFD60A]/20 rounded-full flex items-center justify-center">
                      <span className="text-[#FFD60A] text-sm font-bold">{u.first_name || '?'}</span>
                    </div>
                    <div>
                      <p className="text-sm text-white">Client #{(u.id || '').slice(-6).toUpperCase()}</p>
                      <p className="text-xs text-zinc-500">{u.created_at ? new Date(u.created_at).toLocaleDateString('fr-FR') : ''}</p>
                    </div>
                  </div>
                  {u.subscription_active ? (
                    <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded-full font-medium">Abonné</span>
                  ) : (
                    <span className="text-xs bg-zinc-700 text-zinc-400 px-2 py-1 rounded-full">Inscrit</span>
                  )}
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </main>

      <ChangePasswordModal open={showPwd} onClose={() => setShowPwd(false)} />

      <footer className="border-t border-zinc-800 px-4 py-6 text-center text-zinc-600 text-xs">
        © 2026 Métro-Taxi · SIRET 918 687 864 RCS Bobigny
      </footer>
    </div>
  );
};

export default PartnerDashboard;
