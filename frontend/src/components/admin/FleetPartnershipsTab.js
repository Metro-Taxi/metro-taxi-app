import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Loader2, Building2, Mail, Phone, MapPin, Calendar, MessageSquare,
  CheckCircle2, Clock, XCircle, ArrowRight, RefreshCw, Users,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const STATUS_META = {
  new:       { label: 'Nouveau',  color: 'text-amber-300',   bg: 'bg-amber-300/10',   icon: Clock },
  contacted: { label: 'Contacté', color: 'text-blue-300',    bg: 'bg-blue-300/10',    icon: ArrowRight },
  accepted:  { label: 'Accepté',  color: 'text-emerald-400', bg: 'bg-emerald-400/10', icon: CheckCircle2 },
  rejected:  { label: 'Refusé',   color: 'text-zinc-400',    bg: 'bg-zinc-500/10',    icon: XCircle },
};

const FleetPartnershipsTab = ({ token }) => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [selected, setSelected] = useState(null);
  const [statusDialogOpen, setStatusDialogOpen] = useState(false);
  const [newStatus, setNewStatus] = useState('');
  const [notes, setNotes] = useState('');
  const [updating, setUpdating] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      const { data: res } = await axios.get(`${API}/admin/fleet-partnerships`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setData(res);
    } catch (e) {
      toast.error('Impossible de charger les demandes de partenariat');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []); // eslint-disable-line

  const openStatusDialog = (application, status) => {
    setSelected(application);
    setNewStatus(status);
    setNotes(application.notes || '');
    setStatusDialogOpen(true);
  };

  const handleUpdateStatus = async () => {
    if (!selected || !newStatus) return;
    try {
      setUpdating(true);
      await axios.post(
        `${API}/admin/fleet-partnerships/${selected.id}/status`,
        { status: newStatus, notes: notes || null },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success(`Statut mis à jour → ${STATUS_META[newStatus]?.label}`);
      setStatusDialogOpen(false);
      await fetchData();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Erreur de mise à jour');
    } finally {
      setUpdating(false);
    }
  };

  if (loading && !data) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-[#FFD60A]" />
      </div>
    );
  }

  if (!data) return null;

  const applications = data.applications || [];
  const byStatus = data.by_status || {};

  return (
    <div className="space-y-5" data-testid="fleet-partnerships-tab">
      {/* Header + stats */}
      <div className="bg-[#18181B] border border-zinc-800 rounded p-5">
        <div className="flex items-start justify-between flex-wrap gap-3 mb-4">
          <div>
            <div className="flex items-center gap-2">
              <Building2 className="w-6 h-6 text-[#FFD60A]" />
              <h2 className="text-2xl font-bold text-white">Partenariats Patron VTC</h2>
            </div>
            <p className="text-zinc-400 text-sm mt-1">
              Demandes B2B reçues via <a href="/patron-vtc" target="_blank" rel="noopener noreferrer" className="text-[#FFD60A] hover:underline">/patron-vtc</a>
            </p>
          </div>
          <Button
            onClick={fetchData}
            variant="outline"
            size="sm"
            className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
            data-testid="fleet-partnerships-refresh"
          >
            <RefreshCw className="w-4 h-4 mr-2" /> Rafraîchir
          </Button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <StatCard label="Total demandes" value={data.total || 0} accent />
          <StatCard label="Véhicules totaux" value={data.total_fleet_size || 0} icon={Users} />
          <StatCard label="Nouveaux" value={byStatus.new || 0} color="text-amber-300" />
          <StatCard label="Contactés" value={byStatus.contacted || 0} color="text-blue-300" />
          <StatCard label="Acceptés" value={byStatus.accepted || 0} color="text-emerald-400" />
        </div>
      </div>

      {/* Table */}
      <div className="bg-[#18181B] border border-zinc-800 rounded overflow-hidden">
        {applications.length === 0 ? (
          <div className="text-center py-12 px-6">
            <Building2 className="w-12 h-12 text-zinc-600 mx-auto mb-3" />
            <p className="text-zinc-400 font-medium">Aucune demande pour l'instant</p>
            <p className="text-zinc-600 text-xs mt-1">Distribue la page /patron-vtc aux patrons VTC que tu rencontres.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-zinc-900/60 text-zinc-400 text-xs uppercase">
                <tr>
                  <th className="text-left px-4 py-3">Patron / Société</th>
                  <th className="text-left px-4 py-3">Contact</th>
                  <th className="text-right px-4 py-3">Flotte</th>
                  <th className="text-left px-4 py-3">Ville</th>
                  <th className="text-left px-4 py-3">Reçue</th>
                  <th className="text-center px-4 py-3">Statut</th>
                  <th className="text-right px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {applications.map((app) => {
                  const meta = STATUS_META[app.status] || STATUS_META.new;
                  const Icon = meta.icon;
                  return (
                    <motion.tr
                      key={app.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="border-t border-zinc-800/60 hover:bg-zinc-900/30 align-top"
                      data-testid={`fleet-partnership-row-${app.id}`}
                    >
                      <td className="px-4 py-3">
                        <div className="text-white font-medium">{app.full_name}</div>
                        {app.company_name && (
                          <div className="text-zinc-500 text-xs">{app.company_name}</div>
                        )}
                      </td>
                      <td className="px-4 py-3 text-xs">
                        <div className="text-zinc-300 flex items-center gap-1">
                          <Mail className="w-3 h-3 text-zinc-500" /> {app.email}
                        </div>
                        <div className="text-zinc-300 flex items-center gap-1 mt-1">
                          <Phone className="w-3 h-3 text-zinc-500" /> {app.phone}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <span className="text-[#FFD60A] font-bold text-lg">{app.fleet_size}</span>
                        <span className="text-zinc-500 text-xs ml-1">véh.</span>
                      </td>
                      <td className="px-4 py-3 text-zinc-300">
                        <span className="inline-flex items-center gap-1">
                          <MapPin className="w-3 h-3 text-zinc-500" /> {app.city}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-zinc-400 text-xs">
                        {app.created_at ? new Date(app.created_at).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' }) : '—'}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs ${meta.bg} ${meta.color}`}>
                          <Icon className="w-3 h-3" /> {meta.label}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-1 justify-end flex-wrap">
                          <button
                            onClick={() => { setSelected(app); setStatusDialogOpen(false); }}
                            className="text-xs text-zinc-400 hover:text-white px-2 py-1 rounded hover:bg-zinc-800"
                            data-testid={`fleet-partnership-view-${app.id}`}
                          >
                            Voir
                          </button>
                          {app.status === 'new' && (
                            <button
                              onClick={() => openStatusDialog(app, 'contacted')}
                              className="text-xs text-blue-300 hover:text-blue-200 px-2 py-1 rounded hover:bg-blue-500/10"
                              data-testid={`fleet-partnership-contact-${app.id}`}
                            >
                              Contacté
                            </button>
                          )}
                          {(app.status === 'new' || app.status === 'contacted') && (
                            <>
                              <button
                                onClick={() => openStatusDialog(app, 'accepted')}
                                className="text-xs text-emerald-400 hover:text-emerald-300 px-2 py-1 rounded hover:bg-emerald-500/10"
                                data-testid={`fleet-partnership-accept-${app.id}`}
                              >
                                Accepter
                              </button>
                              <button
                                onClick={() => openStatusDialog(app, 'rejected')}
                                className="text-xs text-zinc-500 hover:text-zinc-300 px-2 py-1 rounded hover:bg-zinc-700/40"
                                data-testid={`fleet-partnership-reject-${app.id}`}
                              >
                                Refuser
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </motion.tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Detail card (selected, but pas pour update statut) */}
      {selected && !statusDialogOpen && (
        <Dialog open={!!selected} onOpenChange={(v) => !v && setSelected(null)}>
          <DialogContent className="bg-[#0A0A0B] border-zinc-800 text-white max-w-2xl" data-testid="fleet-partnership-detail-dialog">
            <DialogHeader>
              <DialogTitle className="text-xl font-bold text-[#FFD60A] flex items-center gap-2">
                <Building2 className="w-5 h-5" /> {selected.full_name}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-3 text-sm">
              {selected.company_name && (
                <Row icon={Building2} label="Société" value={selected.company_name} />
              )}
              <Row icon={Mail} label="Email" value={selected.email} />
              <Row icon={Phone} label="Téléphone" value={selected.phone} />
              <Row icon={Users} label="Taille flotte" value={`${selected.fleet_size} véhicules`} highlight />
              <Row icon={MapPin} label="Ville" value={selected.city} />
              <Row icon={Calendar} label="Reçue le" value={selected.created_at ? new Date(selected.created_at).toLocaleString('fr-FR') : '—'} />
              {selected.message && (
                <div className="bg-zinc-900/40 border border-zinc-800 rounded p-3">
                  <div className="text-zinc-500 text-xs mb-1 flex items-center gap-1">
                    <MessageSquare className="w-3 h-3" /> Message
                  </div>
                  <p className="text-zinc-200 whitespace-pre-wrap">{selected.message}</p>
                </div>
              )}
              {selected.notes && (
                <div className="bg-amber-500/5 border border-amber-500/20 rounded p-3">
                  <div className="text-amber-300 text-xs mb-1">Notes internes</div>
                  <p className="text-zinc-200 whitespace-pre-wrap">{selected.notes}</p>
                </div>
              )}
            </div>
          </DialogContent>
        </Dialog>
      )}

      {/* Status update dialog */}
      <Dialog open={statusDialogOpen} onOpenChange={(v) => !updating && setStatusDialogOpen(v)}>
        <DialogContent className="bg-[#0A0A0B] border-zinc-800 text-white max-w-md" data-testid="fleet-partnership-status-dialog">
          <DialogHeader>
            <DialogTitle className="text-lg font-bold text-[#FFD60A]">
              Passer à : {STATUS_META[newStatus]?.label}
            </DialogTitle>
          </DialogHeader>
          {selected && (
            <div className="space-y-3">
              <p className="text-sm text-zinc-400">
                Pour <strong className="text-white">{selected.full_name}</strong> ({selected.fleet_size} véhicules)
              </p>
              <div>
                <label className="text-zinc-300 text-sm">Notes internes (optionnel)</label>
                <Textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="RDV pris le 20/05 14h. Veut tester sur 5 véhicules d'abord…"
                  className="bg-zinc-950 border-zinc-700 text-white mt-1 min-h-[100px]"
                  data-testid="fleet-partnership-notes-input"
                  maxLength={2000}
                />
              </div>
              <div className="flex gap-2 justify-end pt-2">
                <Button
                  variant="outline"
                  onClick={() => setStatusDialogOpen(false)}
                  disabled={updating}
                  className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
                >
                  Annuler
                </Button>
                <Button
                  onClick={handleUpdateStatus}
                  disabled={updating}
                  className="bg-[#FFD60A] text-black hover:bg-[#FFD60A]/90"
                  data-testid="fleet-partnership-confirm-status-btn"
                >
                  {updating ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                  Confirmer
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

const StatCard = ({ label, value, color, accent, icon: Icon }) => (
  <div className={`bg-zinc-900/40 border ${accent ? 'border-[#FFD60A]/30' : 'border-zinc-800'} rounded p-3`}>
    <p className="text-xs text-zinc-500 flex items-center gap-1">
      {Icon && <Icon className="w-3 h-3" />} {label}
    </p>
    <p className={`text-2xl font-bold mt-1 ${color || (accent ? 'text-[#FFD60A]' : 'text-white')}`}>{value}</p>
  </div>
);

const Row = ({ icon: Icon, label, value, highlight }) => (
  <div className="flex items-start gap-2 py-1.5 border-b border-zinc-900">
    <Icon className="w-4 h-4 text-zinc-500 mt-0.5 flex-shrink-0" />
    <span className="text-zinc-500 text-xs uppercase tracking-wider w-28">{label}</span>
    <span className={`text-sm ${highlight ? 'text-[#FFD60A] font-bold' : 'text-zinc-200'}`}>{value}</span>
  </div>
);

export default FleetPartnershipsTab;
