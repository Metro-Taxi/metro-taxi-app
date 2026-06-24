import React, { useState } from 'react';
import axios from 'axios';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Loader2, AlertTriangle, CheckCircle2, RefreshCcw, Search, Plus } from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const DriverEarningsDiagnosticDialog = ({ open, onClose, token, prefilledEmail }) => {
  const [email, setEmail] = useState(prefilledEmail || '');
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [recomputing, setRecomputing] = useState(null); // driver_id en cours de recompute
  const [adjustingDriverId, setAdjustingDriverId] = useState(null); // driver_id dont la form est ouverte
  const [adjustForm, setAdjustForm] = useState({ month: '', amount: '', reason: '' });
  const [adjustSubmitting, setAdjustSubmitting] = useState(false);

  const auth = { headers: { Authorization: `Bearer ${token}` } };

  // Quand le dialog s'ouvre avec un email pré-rempli, on lance auto le diagnostic
  React.useEffect(() => {
    if (open && prefilledEmail) {
      setEmail(prefilledEmail);
      // Auto-run après un petit délai pour laisser le state se mettre à jour
      setTimeout(() => { runDiagnoseInline(prefilledEmail); }, 100);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, prefilledEmail]);

  const runDiagnoseInline = async (overrideEmail) => {
    const targetEmail = overrideEmail || email;
    if (!targetEmail || !targetEmail.includes('@')) {
      toast.error("Email invalide");
      return;
    }
    setLoading(true);
    setReport(null);
    try {
      const { data } = await axios.get(`${API}/admin/diagnose/driver-earnings`, {
        ...auth,
        params: { email: targetEmail },
      });
      setReport(data);
      if (data.profiles_count === 0) {
        toast.error("Aucun chauffeur trouvé avec cet email");
      } else if (data.is_duplicate) {
        toast.warning(`⚠️ ${data.profiles_count} profils dupliqués détectés !`);
      } else {
        toast.success("Diagnostic terminé");
      }
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Erreur diagnostic");
    } finally {
      setLoading(false);
    }
  };

  const runDiagnose = () => runDiagnoseInline();

  const runRecompute = async (driverId, dryRun = false) => {
    if (!dryRun && !window.confirm("Confirmer le recalcul des revenus pour ce chauffeur ? Les mois déjà PAYÉS ne seront pas touchés.")) return;
    setRecomputing(driverId);
    try {
      const { data } = await axios.post(`${API}/admin/recompute/driver-earnings`,
        { driver_id: driverId, dry_run: dryRun }, auth);
      toast.success(`${dryRun ? '🔍 Simulation' : '✅ Recalcul'} : ${data.total_completed_rides} courses, ${data.actions.length} mois traités`);
      // Re-run diagnose pour rafraîchir
      await runDiagnose();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Erreur recalcul");
    } finally {
      setRecomputing(null);
    }
  };

  const openAdjustForm = (driverId) => {
    const now = new Date();
    const defaultMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
    setAdjustForm({ month: defaultMonth, amount: '', reason: '' });
    setAdjustingDriverId(driverId);
  };

  const submitManualAdjust = async (driverId) => {
    const amount = parseFloat(String(adjustForm.amount).replace(',', '.'));
    if (!adjustForm.month || !/^\d{4}-(0[1-9]|1[0-2])$/.test(adjustForm.month)) {
      toast.error("Mois invalide (format YYYY-MM)"); return;
    }
    if (!Number.isFinite(amount) || amount === 0) {
      toast.error("Montant invalide (non nul)"); return;
    }
    if (!adjustForm.reason || adjustForm.reason.trim().length < 5) {
      toast.error("Raison obligatoire (5 caractères min)"); return;
    }
    if (!window.confirm(`Appliquer un ajustement de ${amount.toFixed(2)} € sur le mois ${adjustForm.month} ?\nCette action sera tracée dans admin_audit_log.`)) return;
    setAdjustSubmitting(true);
    try {
      const { data } = await axios.post(`${API}/admin/driver-earnings/manual-adjust`, {
        driver_id: driverId,
        month: adjustForm.month,
        amount_eur: amount,
        reason: adjustForm.reason.trim(),
      }, auth);
      toast.success(`✅ Rattrapage OK. Nouveau total ${adjustForm.month} : ${data.new_revenue_eur} €`);
      setAdjustingDriverId(null);
      setAdjustForm({ month: '', amount: '', reason: '' });
      await runDiagnose();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Erreur ajustement");
    } finally {
      setAdjustSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl bg-[#0F0F11] border-zinc-800 text-white max-h-[90vh] overflow-y-auto" data-testid="driver-earnings-diagnostic-dialog">
        <DialogHeader>
          <DialogTitle className="text-xl flex items-center gap-2">
            <Search className="w-5 h-5 text-[#FFD60A]" />
            Diagnostic revenus chauffeur
          </DialogTitle>
        </DialogHeader>

        <div className="flex gap-2 items-stretch mb-4">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="email du chauffeur (ex: maaztagari+vtc@gmail.com)"
            className="flex-1 px-3 py-2 rounded bg-zinc-900 border border-zinc-700 text-white text-sm"
            data-testid="diagnose-email-input"
          />
          <Button
            onClick={runDiagnose}
            disabled={loading}
            className="bg-[#FFD60A] hover:bg-yellow-400 text-black font-bold"
            data-testid="diagnose-run-btn"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Analyser"}
          </Button>
        </div>

        {report && (
          <div className="space-y-4">
            {/* Header summary */}
            <Card className="bg-zinc-900 border-zinc-800 p-4">
              <p className="text-sm text-zinc-400">Email recherché : <span className="text-white font-mono">{report.email_searched}</span></p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3">
                <div>
                  <p className="text-xs text-zinc-500">Profils trouvés</p>
                  <p className={`text-2xl font-bold ${report.is_duplicate ? 'text-red-400' : 'text-white'}`}>
                    {report.profiles_count}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">Courses complétées (total)</p>
                  <p className="text-2xl font-bold text-green-400">{report.summary?.total_completed_rides_across_profiles || 0}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">Revenus calculés (rides)</p>
                  <p className="text-2xl font-bold text-[#FFD60A]">{report.summary?.total_revenue_from_rides_eur || 0} €</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">Revenus stockés</p>
                  <p className={`text-2xl font-bold ${(report.summary?.total_revenue_from_rides_eur || 0) === (report.summary?.total_revenue_stored_eur || 0) ? 'text-green-400' : 'text-red-400'}`}>
                    {report.summary?.total_revenue_stored_eur || 0} €
                  </p>
                </div>
              </div>
              {report.is_duplicate && (
                <div className="mt-3 bg-red-900/30 border border-red-700 rounded p-3 text-sm flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
                  <span><b>Doublon détecté.</b> Ce chauffeur a {report.profiles_count} profils en base. Vérifie ci-dessous quel profil porte les courses. C&apos;est probablement la cause du bug &quot;revenus disparus&quot;.</span>
                </div>
              )}
            </Card>

            {/* Per-profile detail */}
            {report.profiles.map((p, idx) => {
              const hasDiscrepancy = Math.abs(p.discrepancy_eur) >= 0.01;
              return (
                <Card key={p.id} className={`bg-zinc-900 border-zinc-800 p-4 ${hasDiscrepancy ? 'border-l-4 border-l-red-500' : 'border-l-4 border-l-green-500'}`}>
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="font-bold text-white">Profil #{idx + 1} : {p.name}</h3>
                      <p className="text-xs text-zinc-500 font-mono">ID: {p.id}</p>
                      <p className="text-xs text-zinc-400 mt-1">
                        Téléphone {p.phone} · IBAN {p.iban_set ? '✓' : '✗'} · Stripe {p.stripe_account_set ? '✓' : '✗'} · {p.is_validated ? 'Validé' : 'Non validé'} · {p.is_active ? 'Actif' : 'Inactif'}
                      </p>
                      <p className="text-xs text-zinc-500">Inscrit le {p.created_at ? new Date(p.created_at).toLocaleDateString('fr-FR') : '-'}</p>
                    </div>
                    <div className="text-right">
                      {hasDiscrepancy ? (
                        <span className="text-red-400 font-bold flex items-center gap-1"><AlertTriangle className="w-4 h-4" /> Écart {p.discrepancy_eur} €</span>
                      ) : (
                        <span className="text-green-400 flex items-center gap-1"><CheckCircle2 className="w-4 h-4" /> OK</span>
                      )}
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2 text-xs mb-3">
                    <div className="bg-zinc-950 p-2 rounded">
                      <p className="text-zinc-500">Courses (par statut)</p>
                      <p className="font-mono text-white">
                        {Object.entries(p.rides_by_status).map(([s, c]) => `${s}:${c}`).join(' · ') || '0'}
                      </p>
                    </div>
                    <div className="bg-zinc-950 p-2 rounded">
                      <p className="text-zinc-500">Calculé depuis rides completed</p>
                      <p className="font-mono text-[#FFD60A]">{p.sum_revenue_from_completed_rides_eur} €</p>
                    </div>
                    <div className="bg-zinc-950 p-2 rounded">
                      <p className="text-zinc-500">Stocké dans driver_earnings</p>
                      <p className={`font-mono ${hasDiscrepancy ? 'text-red-400' : 'text-green-400'}`}>{p.sum_revenue_stored_in_driver_earnings_eur} €</p>
                    </div>
                  </div>

                  {p.earnings_per_month && p.earnings_per_month.length > 0 && (
                    <details className="text-xs mb-2">
                      <summary className="cursor-pointer text-zinc-400 hover:text-white">Détail par mois ({p.earnings_per_month.length})</summary>
                      <table className="w-full mt-2">
                        <thead className="text-zinc-500">
                          <tr><th className="text-left">Mois</th><th className="text-right">Revenu</th><th className="text-right">Courses</th><th className="text-left pl-2">Statut</th></tr>
                        </thead>
                        <tbody>
                          {p.earnings_per_month.map((e) => (
                            <tr key={e.month} className="border-t border-zinc-800">
                              <td>{e.month}</td>
                              <td className="text-right font-mono">{e.total_revenue} €</td>
                              <td className="text-right">{e.rides_count}</td>
                              <td className={`pl-2 ${e.payout_status === 'paid' ? 'text-green-400' : 'text-orange-400'}`}>{e.payout_status}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </details>
                  )}

                  {hasDiscrepancy && (
                    <div className="flex gap-2 mt-3">
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-xs border-zinc-700 text-zinc-300"
                        onClick={() => runRecompute(p.id, true)}
                        disabled={recomputing === p.id}
                      >
                        {recomputing === p.id ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Search className="w-3 h-3 mr-1" />}
                        Simuler le recalcul (dry-run)
                      </Button>
                      <Button
                        size="sm"
                        onClick={() => runRecompute(p.id, false)}
                        disabled={recomputing === p.id}
                        className="bg-green-600 hover:bg-green-700 text-white text-xs"
                        data-testid={`recompute-btn-${p.id}`}
                      >
                        <RefreshCcw className="w-3 h-3 mr-1" />
                        Recalculer les revenus
                      </Button>
                    </div>
                  )}

                  {/* Rattrapage manuel — utile quand la course IRL n'est pas en base
                      (ex: reset BDD post-import legacy). Crée une ligne driver_earnings
                      directe avec audit log obligatoire. */}
                  <div className="mt-3 pt-3 border-t border-zinc-800">
                    {adjustingDriverId !== p.id ? (
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-xs border-orange-700 text-orange-300 hover:bg-orange-900/30"
                        onClick={() => openAdjustForm(p.id)}
                        data-testid={`open-manual-adjust-${p.id}`}
                      >
                        <Plus className="w-3 h-3 mr-1" />
                        Rattrapage manuel (course hors-BDD)
                      </Button>
                    ) : (
                      <div className="bg-orange-900/10 border border-orange-700/50 rounded p-3 space-y-2">
                        <p className="text-xs text-orange-300 font-bold">Rattrapage manuel — driver_earnings</p>
                        <p className="text-[10px] text-zinc-400">
                          Utilise ce formulaire uniquement si la course a été exécutée IRL mais est absente de la BDD
                          (ex: reset post-import legacy). Une entrée d&apos;audit obligatoire sera créée.
                        </p>
                        <div className="grid grid-cols-2 gap-2">
                          <div>
                            <label className="text-[10px] text-zinc-500 block mb-1">Mois (YYYY-MM)</label>
                            <input
                              type="text"
                              value={adjustForm.month}
                              onChange={(e) => setAdjustForm((f) => ({ ...f, month: e.target.value }))}
                              placeholder="2026-06"
                              className="w-full px-2 py-1 rounded bg-zinc-900 border border-zinc-700 text-white text-xs font-mono"
                              data-testid={`adjust-month-${p.id}`}
                            />
                          </div>
                          <div>
                            <label className="text-[10px] text-zinc-500 block mb-1">Montant € (négatif autorisé)</label>
                            <input
                              type="text"
                              value={adjustForm.amount}
                              onChange={(e) => setAdjustForm((f) => ({ ...f, amount: e.target.value }))}
                              placeholder="7.94"
                              className="w-full px-2 py-1 rounded bg-zinc-900 border border-zinc-700 text-white text-xs font-mono"
                              data-testid={`adjust-amount-${p.id}`}
                            />
                          </div>
                        </div>
                        <div>
                          <label className="text-[10px] text-zinc-500 block mb-1">Raison (obligatoire, min 5 car.)</label>
                          <input
                            type="text"
                            value={adjustForm.reason}
                            onChange={(e) => setAdjustForm((f) => ({ ...f, reason: e.target.value }))}
                            placeholder="Course du 17/06/2026 Delafontaine→Pte Clignancourt — rattrapage post-reset"
                            className="w-full px-2 py-1 rounded bg-zinc-900 border border-zinc-700 text-white text-xs"
                            data-testid={`adjust-reason-${p.id}`}
                          />
                        </div>
                        <div className="flex gap-2 justify-end">
                          <Button
                            size="sm"
                            variant="outline"
                            className="text-xs border-zinc-700 text-zinc-400"
                            onClick={() => { setAdjustingDriverId(null); setAdjustForm({ month: '', amount: '', reason: '' }); }}
                            disabled={adjustSubmitting}
                          >
                            Annuler
                          </Button>
                          <Button
                            size="sm"
                            className="bg-orange-600 hover:bg-orange-700 text-white text-xs"
                            onClick={() => submitManualAdjust(p.id)}
                            disabled={adjustSubmitting}
                            data-testid={`submit-manual-adjust-${p.id}`}
                          >
                            {adjustSubmitting ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Plus className="w-3 h-3 mr-1" />}
                            Appliquer le rattrapage
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                </Card>
              );
            })}

            {/* Orphan rides */}
            {report.orphan_rides && report.orphan_rides.length > 0 && (
              <Card className="bg-orange-900/20 border-orange-700 p-4">
                <h3 className="font-bold text-orange-300 mb-2 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" />
                  Courses orphelines récentes ({report.orphan_rides.length})
                </h3>
                <p className="text-xs text-zinc-400 mb-2">
                  Courses des 30 derniers jours dont le driver_id n&apos;existe dans aucun profil actuel. Peut indiquer un import legacy partiel ou un compte chauffeur supprimé.
                </p>
                <table className="w-full text-xs">
                  <thead className="text-zinc-500"><tr><th className="text-left">Ride</th><th className="text-left">Driver ID</th><th className="text-left">Status</th><th className="text-right">Revenu</th><th className="text-left pl-2">Quand</th></tr></thead>
                  <tbody>
                    {report.orphan_rides.map((r) => (
                      <tr key={r.id} className="border-t border-zinc-800">
                        <td className="font-mono text-xs">{r.id?.slice(0, 8)}</td>
                        <td className="font-mono text-xs text-orange-300">{r.driver_id?.slice(0, 8) || '-'}</td>
                        <td>{r.status}</td>
                        <td className="text-right font-mono">{r.driver_revenue || 0} €</td>
                        <td className="pl-2 text-zinc-400">{r.created_at?.slice(0, 16) || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Card>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default DriverEarningsDiagnosticDialog;
