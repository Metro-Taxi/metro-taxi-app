import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Card } from '@/components/ui/card';
import { Loader2, RefreshCw, Copy } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const QRStatsTab = ({ token }) => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);

  const auth = { headers: { Authorization: `Bearer ${token}` } };

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await axios.get(`${API}/admin/qr/stats`, auth);
      setStats(data);
    } catch (err) {
      toast.error("Erreur lors du chargement des stats QR");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, []);

  const baseUrl = (typeof window !== 'undefined' && window.location.origin) || 'https://metro-taxi.com';

  const copyUrl = (campaign) => {
    const url = `${baseUrl}/?ref=${encodeURIComponent(campaign)}`;
    if (navigator.clipboard) {
      navigator.clipboard.writeText(url).then(() => toast.success("URL copiée"));
    }
  };

  const fmt = (iso) => {
    if (!iso) return '—';
    try { return new Date(iso).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' }); }
    catch (_e) { return iso; }
  };

  return (
    <div className="space-y-4" data-testid="qr-stats-content">
      <Card className="bg-[#18181B] border-zinc-800 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-bold text-white">📊 Stats des QR codes & flyers</h2>
            <p className="text-sm text-zinc-400 mt-1">
              Mesure les conversions de tes campagnes (Orly, CDG, Gare de Lyon, banderole, etc.).
              Génère un QR vers <code className="text-[#FFD60A]">metro-taxi.com/?ref=NOM_CAMPAGNE</code> pour chaque flyer.
            </p>
          </div>
          <Button
            onClick={load}
            disabled={loading}
            className="bg-[#FFD60A] hover:bg-yellow-400 text-black font-bold flex items-center gap-2"
            data-testid="qr-stats-refresh"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
            Rafraîchir
          </Button>
        </div>

        {!stats && loading && <p className="text-zinc-500 text-sm">Chargement...</p>}

        {stats && (
          <>
            {/* Totaux */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
              <div className="bg-zinc-900 border border-zinc-800 rounded p-3">
                <p className="text-xs text-zinc-400">Total scans QR</p>
                <p className="text-2xl font-bold text-[#FFD60A]" data-testid="stat-total-scans">{stats.totals.total_scans}</p>
              </div>
              <div className="bg-zinc-900 border border-zinc-800 rounded p-3">
                <p className="text-xs text-zinc-400">Inscriptions issues</p>
                <p className="text-2xl font-bold text-green-400" data-testid="stat-total-signups">{stats.totals.total_signups}</p>
              </div>
              <div className="bg-zinc-900 border border-zinc-800 rounded p-3">
                <p className="text-xs text-zinc-400">Conversion globale</p>
                <p className="text-2xl font-bold text-blue-400">
                  {stats.totals.global_conversion_pct === null ? '—' : `${stats.totals.global_conversion_pct}%`}
                </p>
              </div>
              <div className="bg-zinc-900 border border-zinc-800 rounded p-3">
                <p className="text-xs text-zinc-400">Scans 7 derniers jours</p>
                <p className="text-2xl font-bold text-orange-400">{stats.totals.scans_last_7_days}</p>
              </div>
            </div>

            {/* Tableau par campagne */}
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-zinc-800 text-zinc-400">
                    <th className="text-left py-2 px-3">Campagne</th>
                    <th className="text-right py-2 px-3">Scans</th>
                    <th className="text-right py-2 px-3">Usagers</th>
                    <th className="text-right py-2 px-3">Chauffeurs</th>
                    <th className="text-right py-2 px-3">Conversion</th>
                    <th className="text-left py-2 px-3 hidden md:table-cell">Dernier scan</th>
                    <th className="text-left py-2 px-3">URL</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.rows.length === 0 && (
                    <tr><td colSpan={7} className="text-center text-zinc-500 py-6">Aucune campagne enregistrée pour l&apos;instant. Génère un QR vers <code>metro-taxi.com/?ref=cdg-flyer</code> et le premier scan apparaîtra ici.</td></tr>
                  )}
                  {stats.rows.map((r) => (
                    <tr key={r.campaign} className="border-b border-zinc-900 hover:bg-zinc-900/50">
                      <td className="py-2 px-3 font-mono text-white">{r.campaign}</td>
                      <td className="py-2 px-3 text-right text-[#FFD60A]">{r.scans}</td>
                      <td className="py-2 px-3 text-right text-green-400">{r.users_signed_up}</td>
                      <td className="py-2 px-3 text-right text-blue-400">{r.drivers_signed_up}</td>
                      <td className="py-2 px-3 text-right">
                        {r.conversion_pct === null ? <span className="text-zinc-500">N/A</span> : (
                          <span className={r.conversion_pct >= 5 ? 'text-green-400' : r.conversion_pct >= 1 ? 'text-orange-400' : 'text-red-400'}>
                            {r.conversion_pct}%
                          </span>
                        )}
                      </td>
                      <td className="py-2 px-3 text-zinc-400 hidden md:table-cell">{fmt(r.last_scan)}</td>
                      <td className="py-2 px-3">
                        <Button
                          onClick={() => copyUrl(r.campaign)}
                          variant="ghost"
                          size="sm"
                          className="text-[#FFD60A] hover:text-yellow-300 h-7 px-2"
                          title={`${baseUrl}/?ref=${r.campaign}`}
                        >
                          <Copy className="w-3 h-3 mr-1" />
                          Copier
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mode d'emploi */}
            <div className="mt-6 p-4 bg-zinc-900 border border-zinc-800 rounded">
              <h3 className="font-bold text-[#FFD60A] mb-2">💡 Comment créer un nouveau QR tracké ?</h3>
              <ol className="text-xs text-zinc-300 space-y-1 list-decimal list-inside">
                <li>Choisis un nom court pour ta campagne (ex: <code>flyer-cdg-juillet</code>)</li>
                <li>Génère un QR avec <a className="text-blue-400 underline" target="_blank" rel="noreferrer" href="https://www.qr-code-generator.com/">qr-code-generator.com</a> qui pointe vers <code>{baseUrl}/?ref=NOM_CAMPAGNE</code></li>
                <li>Imprime sur ton flyer</li>
                <li>Le 1er scan créera la ligne dans ce tableau, et chaque inscription sera comptée automatiquement</li>
              </ol>
            </div>
          </>
        )}
      </Card>
    </div>
  );
};

export default QRStatsTab;
