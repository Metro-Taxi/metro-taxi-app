import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { Check, X, AlertTriangle, Store, Users, Building, Phone, Mail, MapPin, Banknote, Eye } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/**
 * Tab admin "Commerces" — Patch V10 (19/06/2026)
 * Liste, valide, refuse les partenaires commerciaux + ambulants + entreprises.
 */
const CommercialPartnersTab = ({ token }) => {
  const [partners, setPartners] = useState([]);
  const [counts, setCounts] = useState({ pending: 0, active: 0, suspended: 0, rejected: 0 });
  const [filter, setFilter] = useState('pending');
  const [loading, setLoading] = useState(true);
  const [selectedPartner, setSelectedPartner] = useState(null);
  const [notes, setNotes] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  const loadPartners = async (statusFilter = filter) => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/admin/partners?status_filter=${statusFilter}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPartners(res.data.partners || []);
      setCounts(res.data.counts || {});
    } catch (e) {
      toast.error('Erreur chargement partenaires');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPartners(filter);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter, token]);

  const handleAction = async (action) => {
    if (!selectedPartner) return;
    setActionLoading(true);
    try {
      await axios.post(
        `${API}/admin/partners/${selectedPartner.id}/validate`,
        { action, notes },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      const labels = { approve: 'validé', reject: 'rejeté', suspend: 'suspendu' };
      toast.success(`Partenaire ${labels[action]}.`);
      setSelectedPartner(null);
      setNotes('');
      await loadPartners();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Erreur');
    } finally {
      setActionLoading(false);
    }
  };

  const typeIcons = {
    commerce_fixe: { Icon: Store, label: 'Commerce' },
    ambulant: { Icon: Users, label: 'Ambulant' },
    entreprise: { Icon: Building, label: 'Entreprise' },
  };

  return (
    <div className="space-y-4">
      {/* Filter bar */}
      <div className="flex flex-wrap gap-2">
        {['pending', 'active', 'suspended', 'rejected', 'all'].map(s => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              filter === s
                ? 'bg-[#FFD60A] text-black'
                : 'bg-[#18181B] text-zinc-400 hover:text-white border border-zinc-800'
            }`}
            data-testid={`filter-${s}`}
          >
            {s === 'pending' && '⏳ En attente'}
            {s === 'active' && '✓ Actifs'}
            {s === 'suspended' && '⏸ Suspendus'}
            {s === 'rejected' && '✗ Rejetés'}
            {s === 'all' && 'Tous'}
            {s !== 'all' && counts[s] != null && (
              <span className="ml-2 bg-black/20 px-2 py-0.5 rounded-full text-xs">{counts[s]}</span>
            )}
          </button>
        ))}
      </div>

      {/* List */}
      <div className="bg-[#18181B] border border-zinc-800 rounded-lg overflow-hidden">
        {loading ? (
          <div className="p-8 text-center">
            <div className="w-8 h-8 border-2 border-[#FFD60A] border-t-transparent rounded-full animate-spin mx-auto" />
          </div>
        ) : partners.length === 0 ? (
          <div className="p-12 text-center text-zinc-500">
            <Store className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>Aucun partenaire {filter === 'all' ? '' : filter}.</p>
            <p className="text-xs mt-2">Les partenaires s&apos;inscrivent via <code className="text-[#FFD60A]">/partenaires/inscription</code></p>
          </div>
        ) : (
          <div className="divide-y divide-zinc-800">
            {partners.map((p) => {
              const TypeIcon = typeIcons[p.partner_type]?.Icon || Store;
              const typeLabel = typeIcons[p.partner_type]?.label || 'Partenaire';
              return (
                <motion.div
                  key={p.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="p-4 hover:bg-zinc-900/50 transition flex items-center gap-4"
                  data-testid={`partner-row-${p.referral_code}`}
                >
                  <div className="bg-[#FFD60A]/10 rounded-full w-12 h-12 flex items-center justify-center flex-shrink-0">
                    <TypeIcon className="w-5 h-5 text-[#FFD60A]" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <h3 className="font-bold text-white truncate">{p.business_name}</h3>
                      <span className="text-xs bg-zinc-800 text-zinc-400 px-2 py-0.5 rounded-full">{typeLabel}</span>
                      <span className="text-xs bg-[#FFD60A]/10 text-[#FFD60A] px-2 py-0.5 rounded-full font-mono">{p.referral_code}</span>
                    </div>
                    <p className="text-sm text-zinc-400 truncate">
                      {p.contact_first_name} {p.contact_last_name} · <a href={`mailto:${p.email}`} className="text-[#FFD60A]">{p.email}</a> · <a href={`tel:${p.phone}`} className="text-[#FFD60A]">{p.phone}</a>
                    </p>
                    {p.city && <p className="text-xs text-zinc-500 truncate mt-0.5">📍 {p.street_address ? `${p.street_address}, ` : ''}{p.postal_code} {p.city}</p>}
                    {p.activity_zone && <p className="text-xs text-zinc-500 truncate mt-0.5">🚶 {p.activity_zone}</p>}
                  </div>
                  <div className="flex gap-2 flex-shrink-0">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => { setSelectedPartner(p); setNotes(p.admin_notes || ''); }}
                      className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
                      data-testid={`view-partner-${p.referral_code}`}
                    >
                      <Eye className="w-4 h-4" />
                    </Button>
                  </div>
                </motion.div>
              );
            })}
          </div>
        )}
      </div>

      {/* Detail modal */}
      {selectedPartner && (
        <div
          className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={() => setSelectedPartner(null)}
        >
          <div
            className="bg-[#18181B] border border-zinc-800 rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6 border-b border-zinc-800 flex items-start justify-between">
              <div>
                <h3 className="text-xl font-bold text-white">{selectedPartner.business_name}</h3>
                <p className="text-sm text-zinc-400 mt-1">
                  <span className="bg-[#FFD60A]/10 text-[#FFD60A] px-2 py-0.5 rounded-full font-mono text-xs">{selectedPartner.referral_code}</span>
                  {' · '}
                  <span className="capitalize">{selectedPartner.partner_type.replace('_', ' ')}</span>
                  {' · '}
                  <span className={`uppercase font-bold ${
                    selectedPartner.status === 'active' ? 'text-green-400' :
                    selectedPartner.status === 'pending' ? 'text-yellow-400' :
                    selectedPartner.status === 'rejected' ? 'text-red-400' : 'text-zinc-500'
                  }`}>{selectedPartner.status}</span>
                </p>
              </div>
              <button onClick={() => setSelectedPartner(null)} className="text-zinc-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-4 text-sm">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-zinc-500 text-xs uppercase">Contact</p>
                  <p className="text-white">{selectedPartner.contact_first_name} {selectedPartner.contact_last_name}</p>
                </div>
                <div>
                  <p className="text-zinc-500 text-xs uppercase">Contact préféré</p>
                  <p className="text-white capitalize">{selectedPartner.preferred_contact || 'email'}</p>
                </div>
                <div>
                  <p className="text-zinc-500 text-xs uppercase flex items-center gap-1"><Mail className="w-3 h-3" />Email</p>
                  <a href={`mailto:${selectedPartner.email}`} className="text-[#FFD60A] break-all">{selectedPartner.email}</a>
                </div>
                <div>
                  <p className="text-zinc-500 text-xs uppercase flex items-center gap-1"><Phone className="w-3 h-3" />Téléphone</p>
                  <a href={`tel:${selectedPartner.phone}`} className="text-[#FFD60A]">{selectedPartner.phone}</a>
                </div>
                {selectedPartner.street_address && (
                  <div className="col-span-2">
                    <p className="text-zinc-500 text-xs uppercase flex items-center gap-1"><MapPin className="w-3 h-3" />Adresse</p>
                    <p className="text-white">{selectedPartner.street_address}, {selectedPartner.postal_code} {selectedPartner.city}</p>
                  </div>
                )}
                {selectedPartner.activity_zone && (
                  <div className="col-span-2">
                    <p className="text-zinc-500 text-xs uppercase">Zone d&apos;activité</p>
                    <p className="text-white">{selectedPartner.activity_zone}</p>
                  </div>
                )}
                {selectedPartner.siret && (
                  <div>
                    <p className="text-zinc-500 text-xs uppercase">SIRET</p>
                    <p className="text-white font-mono text-xs">{selectedPartner.siret}</p>
                  </div>
                )}
                <div>
                  <p className="text-zinc-500 text-xs uppercase flex items-center gap-1"><Banknote className="w-3 h-3" />Commission</p>
                  <p className="text-[#FFD60A] font-bold">{((selectedPartner.commission_rate || 0.15) * 100).toFixed(0)}%</p>
                </div>
              </div>

              {selectedPartner.motivation && (
                <div>
                  <p className="text-zinc-500 text-xs uppercase mb-1">Motivation</p>
                  <p className="text-white bg-zinc-900 rounded p-3">{selectedPartner.motivation}</p>
                </div>
              )}

              <div>
                <p className="text-zinc-500 text-xs uppercase mb-1">Notes admin (privées)</p>
                <Textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={3}
                  placeholder="Notes internes sur ce partenaire..."
                  className="bg-zinc-900 border-zinc-700 text-white"
                  data-testid="admin-notes-input"
                />
              </div>
            </div>

            <div className="p-6 border-t border-zinc-800 flex flex-wrap gap-2 justify-end">
              {selectedPartner.status === 'pending' && (
                <>
                  <Button
                    onClick={() => handleAction('reject')}
                    disabled={actionLoading}
                    variant="outline"
                    className="border-red-500/30 text-red-400 hover:bg-red-500/10"
                    data-testid="reject-partner-btn"
                  >
                    <X className="w-4 h-4 mr-1" />Rejeter
                  </Button>
                  <Button
                    onClick={() => handleAction('approve')}
                    disabled={actionLoading}
                    className="bg-green-600 text-white hover:bg-green-700 font-bold"
                    data-testid="approve-partner-btn"
                  >
                    <Check className="w-4 h-4 mr-1" />
                    {actionLoading ? 'Activation...' : 'Approuver et activer'}
                  </Button>
                </>
              )}
              {selectedPartner.status === 'active' && (
                <Button
                  onClick={() => handleAction('suspend')}
                  disabled={actionLoading}
                  variant="outline"
                  className="border-yellow-500/30 text-yellow-400 hover:bg-yellow-500/10"
                  data-testid="suspend-partner-btn"
                >
                  <AlertTriangle className="w-4 h-4 mr-1" />Suspendre
                </Button>
              )}
              {(selectedPartner.status === 'suspended' || selectedPartner.status === 'rejected') && (
                <Button
                  onClick={() => handleAction('approve')}
                  disabled={actionLoading}
                  className="bg-green-600 text-white hover:bg-green-700 font-bold"
                  data-testid="reactivate-partner-btn"
                >
                  <Check className="w-4 h-4 mr-1" />Réactiver
                </Button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CommercialPartnersTab;
