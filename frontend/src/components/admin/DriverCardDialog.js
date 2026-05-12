import React, { useState, useEffect } from 'react';
import {
  Loader2, X, Car, Phone, Mail, MapPin, IdCard, Calendar,
  Banknote, CheckCircle, XCircle, TrendingUp, Star, Award,
} from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const DriverCardDialog = ({ driverId, open, onClose, token, onChanged }) => {
  const [loading, setLoading] = useState(true);
  const [card, setCard] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchCard = async () => {
    if (!driverId) return;
    try {
      setLoading(true);
      const { data } = await axios.get(`${API}/admin/drivers/${driverId}/card`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setCard(data.card);
    } catch (e) {
      toast.error('Impossible de charger la fiche chauffeur');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (open && driverId) fetchCard();
  }, [open, driverId]); // eslint-disable-line

  const handleValidate = async () => {
    try {
      setActionLoading(true);
      await axios.post(`${API}/admin/drivers/${driverId}/validate`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success('Chauffeur validé ✅');
      await fetchCard();
      if (onChanged) onChanged();
    } catch {
      toast.error('Erreur lors de la validation');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeactivate = async () => {
    if (!window.confirm('Désactiver ce chauffeur ? Il ne pourra plus recevoir de trajets.')) return;
    try {
      setActionLoading(true);
      await axios.post(`${API}/admin/drivers/${driverId}/deactivate`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success('Chauffeur désactivé');
      await fetchCard();
      if (onChanged) onChanged();
    } catch {
      toast.error('Erreur lors de la désactivation');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="bg-[#0A0A0B] border-zinc-800 text-white max-w-3xl max-h-[90vh] overflow-y-auto" data-testid="driver-card-dialog">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold text-[#FFD60A] flex items-center gap-2">
            <Car className="w-6 h-6" /> Fiche chauffeur
          </DialogTitle>
        </DialogHeader>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-[#FFD60A]" />
          </div>
        ) : !card ? (
          <p className="text-zinc-400 py-8 text-center">Aucune donnée</p>
        ) : (
          <div className="space-y-5">
            {/* Identity card */}
            <div className="bg-gradient-to-br from-[#FFD60A]/20 to-zinc-900 border border-[#FFD60A]/30 rounded p-5">
              <div className="flex items-start justify-between flex-wrap gap-3">
                <div>
                  <p className="text-zinc-400 text-xs uppercase tracking-wider">{card.driver_number}</p>
                  <h3 className="text-2xl font-bold mt-1">{card.name}</h3>
                  {card.pioneer_number && (
                    <div className="mt-2 inline-flex items-center gap-1 bg-[#FFD60A] text-black px-2 py-1 rounded text-xs font-bold">
                      <Award className="w-3 h-3" /> Pionnier #{card.pioneer_number}
                    </div>
                  )}
                </div>
                <div className="flex flex-col gap-2 items-end">
                  <span className={`px-3 py-1 rounded text-xs font-bold ${card.is_validated ? 'bg-green-500/20 text-green-400' : 'bg-amber-500/20 text-amber-400'}`}>
                    {card.is_validated ? 'Validé' : 'En attente'}
                  </span>
                  <span className={`px-3 py-1 rounded text-xs font-bold ${card.is_active ? 'bg-blue-500/20 text-blue-400' : 'bg-zinc-700 text-zinc-400'}`}>
                    {card.is_active ? 'Actif' : 'Inactif'}
                  </span>
                </div>
              </div>
            </div>

            {/* Quick action buttons */}
            <div className="flex gap-2 flex-wrap">
              {!card.is_validated && (
                <Button
                  onClick={handleValidate}
                  disabled={actionLoading}
                  className="bg-green-500 hover:bg-green-600 text-black"
                  data-testid="driver-validate-btn"
                >
                  {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <CheckCircle className="w-4 h-4 mr-2" />}
                  Valider le chauffeur
                </Button>
              )}
              {card.is_validated && (
                <Button
                  onClick={handleDeactivate}
                  disabled={actionLoading}
                  variant="destructive"
                  className="bg-red-500 hover:bg-red-600"
                  data-testid="driver-deactivate-btn"
                >
                  {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <XCircle className="w-4 h-4 mr-2" />}
                  Désactiver
                </Button>
              )}
            </div>

            {/* Contact info */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <InfoRow icon={Mail} label="Email" value={card.email} extra={card.email_verified ? '✓ vérifié' : 'non vérifié'} />
              <InfoRow icon={Phone} label="Téléphone" value={card.phone} />
              <InfoRow icon={Car} label="Plaque" value={card.vehicle_plate} extra={card.vehicle_type} />
              <InfoRow icon={IdCard} label="Licence VTC" value={card.vtc_license} />
              <InfoRow icon={MapPin} label="Région" value={card.region_id || '—'} />
              <InfoRow icon={Calendar} label="Inscrit le" value={card.created_at ? new Date(card.created_at).toLocaleDateString('fr-FR') : '—'} />
              {card.source_inscription && (
                <InfoRow icon={MapPin} label="Source d'inscription" value={card.source_inscription} />
              )}
              <InfoRow icon={Car} label="Places véhicule" value={card.seats} />
            </div>

            {/* Bank info */}
            {(card.iban || card.bic) && (
              <div className="bg-zinc-900/50 border border-zinc-800 rounded p-4">
                <h4 className="text-sm font-bold text-zinc-300 mb-2 flex items-center gap-2">
                  <Banknote className="w-4 h-4" /> Informations bancaires
                </h4>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-zinc-500 text-xs">IBAN</p>
                    <p className="font-mono text-zinc-300">{card.iban || '—'}</p>
                  </div>
                  <div>
                    <p className="text-zinc-500 text-xs">BIC</p>
                    <p className="font-mono text-zinc-300">{card.bic || '—'}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Earnings */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <StatCard
                icon={TrendingUp}
                label={`Revenus ${card.current_month_earnings?.month || ''}`}
                value={`${(card.current_month_earnings?.total_revenue || 0).toFixed(2)} €`}
                sub={`${(card.current_month_earnings?.total_km || 0).toFixed(1)} km · ${card.current_month_earnings?.rides_count || 0} trajets`}
              />
              <StatCard
                icon={Banknote}
                label="En attente de virement"
                value={`${card.pending_payout_amount.toFixed(2)} €`}
                sub="Versement le 10 du mois"
                highlight
              />
              <StatCard
                icon={Star}
                label="Total trajets complétés"
                value={card.total_completed_rides}
                sub="Depuis l'inscription"
              />
            </div>

            {/* Recent rides */}
            <div className="bg-zinc-900/50 border border-zinc-800 rounded p-4">
              <h4 className="text-sm font-bold text-zinc-300 mb-3">Derniers trajets ({card.recent_rides?.length || 0})</h4>
              {!card.recent_rides || card.recent_rides.length === 0 ? (
                <p className="text-zinc-500 text-sm text-center py-4">Aucun trajet pour l'instant</p>
              ) : (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {card.recent_rides.map((r) => (
                    <div key={r.id} className="bg-zinc-900 border border-zinc-800 rounded p-3 text-xs">
                      <div className="flex justify-between items-center mb-1">
                        <span className="font-mono text-zinc-500">{r.id?.substring(0, 8)}</span>
                        <span className={`px-2 py-0.5 rounded text-[10px] ${
                          r.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                          r.status === 'in_progress' ? 'bg-blue-500/20 text-blue-400' :
                          r.status === 'pending' ? 'bg-amber-500/20 text-amber-400' :
                          'bg-zinc-700 text-zinc-400'
                        }`}>{r.status}</span>
                      </div>
                      <div className="text-zinc-400">
                        {r.user_name && <span>👤 {r.user_name} · </span>}
                        {r.km_with_user && <span>{r.km_with_user.toFixed(2)} km · </span>}
                        {r.driver_revenue && <span className="text-[#FFD60A]">{r.driver_revenue.toFixed(2)} €</span>}
                      </div>
                      {r.created_at && (
                        <p className="text-zinc-600 text-[10px] mt-1">{new Date(r.created_at).toLocaleString('fr-FR')}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

const InfoRow = ({ icon: Icon, label, value, extra }) => (
  <div className="flex items-start gap-2 bg-zinc-900/30 rounded p-2">
    <Icon className="w-4 h-4 text-zinc-500 mt-0.5 flex-shrink-0" />
    <div className="min-w-0 flex-1">
      <p className="text-zinc-500 text-[10px] uppercase tracking-wider">{label}</p>
      <p className="text-zinc-200 text-sm truncate">{value || '—'}</p>
      {extra && <p className="text-zinc-500 text-[10px]">{extra}</p>}
    </div>
  </div>
);

const StatCard = ({ icon: Icon, label, value, sub, highlight }) => (
  <div className={`${highlight ? 'bg-[#FFD60A]/10 border-[#FFD60A]/30' : 'bg-zinc-900/50 border-zinc-800'} border rounded p-4`}>
    <div className="flex items-center gap-2 mb-2">
      <Icon className={`w-4 h-4 ${highlight ? 'text-[#FFD60A]' : 'text-zinc-400'}`} />
      <p className="text-zinc-400 text-xs">{label}</p>
    </div>
    <p className={`text-2xl font-bold ${highlight ? 'text-[#FFD60A]' : 'text-white'}`}>{value}</p>
    {sub && <p className="text-zinc-500 text-[10px] mt-1">{sub}</p>}
  </div>
);

export default DriverCardDialog;
