import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Ticket, ArrowLeft, Copy, Download, RefreshCw, CheckCircle2, Loader2, QrCode, Archive } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

/**
 * Admin page: gestion des codes promo (campagnes Saint-Denis et autres).
 * - Génère N codes uniques
 * - Affiche les codes (utilisés / disponibles)
 * - Stats par campagne
 */
const PromoCodesPage = () => {
  const [campaign, setCampaign] = useState('saint-denis-2026-06-13');
  const [prefix, setPrefix] = useState('STDENIS');
  const [count, setCount] = useState(30);
  const [maxDistance, setMaxDistance] = useState(10);
  const [expiresAt, setExpiresAt] = useState('2026-06-30T23:59:59Z');
  const [region, setRegion] = useState('saint-denis');

  const [generating, setGenerating] = useState(false);
  const [loading, setLoading] = useState(false);
  const [codes, setCodes] = useState([]);
  const [stats, setStats] = useState(null);
  const [filter, setFilter] = useState('');

  const authHeader = () => ({
    headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
  });

  const fetchCodes = async () => {
    setLoading(true);
    try {
      const params = filter ? { campaign: filter } : {};
      const { data } = await axios.get(`${API}/api/admin/promo-codes`, { ...authHeader(), params });
      setCodes(data.codes || []);
      const { data: s } = await axios.get(`${API}/api/admin/promo-codes/stats`, authHeader());
      setStats(s);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erreur lors du chargement');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCodes();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleGenerate = async () => {
    if (!campaign || !prefix || !count || !expiresAt) {
      toast.error('Tous les champs sont requis');
      return;
    }
    setGenerating(true);
    try {
      const { data } = await axios.post(
        `${API}/api/admin/promo-codes/generate`,
        {
          campaign,
          prefix,
          count: parseInt(count, 10),
          max_distance_km: parseFloat(maxDistance),
          expires_at: expiresAt,
          region,
        },
        authHeader()
      );
      toast.success(`${data.generated_count} code(s) généré(s) sur ${data.requested_count}`);
      fetchCodes();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erreur de génération');
    } finally {
      setGenerating(false);
    }
  };

  const copyAllCodes = () => {
    const text = codes.map((c) => c.code).join('\n');
    navigator.clipboard.writeText(text);
    toast.success(`${codes.length} code(s) copié(s)`);
  };

  const downloadCSV = () => {
    const headers = ['code', 'campaign', 'used', 'used_by', 'used_at', 'expires_at', 'max_distance_km'];
    const rows = codes.map((c) =>
      headers.map((h) => (c[h] === null || c[h] === undefined ? '' : `"${String(c[h]).replace(/"/g, '""')}"`)).join(',')
    );
    const csv = [headers.join(','), ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `promo_codes_${campaign || 'all'}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const downloadSingleQR = async (code) => {
    try {
      const res = await axios.get(`${API}/api/admin/promo-codes/qr?code=${encodeURIComponent(code)}`, {
        ...authHeader(),
        responseType: 'blob',
      });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = `qr_${code}.png`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      toast.error("Erreur lors de la génération du QR");
    }
  };

  const downloadAllQR = async () => {
    try {
      toast.info('Génération du ZIP en cours…');
      const params = filter ? `?campaign=${encodeURIComponent(filter)}` : '';
      const res = await axios.post(
        `${API}/api/admin/promo-codes/qr-batch${params}`,
        {},
        { ...authHeader(), responseType: 'blob' }
      );
      const url = URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = `qrcodes_${filter || 'all'}.zip`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success('ZIP téléchargé');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erreur lors de la génération du ZIP');
    }
  };

  return (
    <div className="min-h-screen bg-[#09090B] text-white p-6" data-testid="promo-codes-page">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <Link to="/admin" className="text-zinc-400 hover:text-white inline-flex items-center gap-2 text-sm mb-3">
              <ArrowLeft className="w-4 h-4" /> Retour admin
            </Link>
            <h1 className="text-3xl font-black flex items-center gap-2">
              <Ticket className="w-8 h-8 text-[#FFD60A]" /> Codes Promo
            </h1>
            <p className="text-zinc-400 mt-1 text-sm">Gestion des campagnes (Saint-Denis et autres zones pilotes)</p>
          </div>
          <Button
            onClick={fetchCodes}
            variant="outline"
            disabled={loading}
            data-testid="promo-refresh-btn"
            className="border-zinc-700"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
          </Button>
        </div>

        {/* Stats */}
        {stats?.by_campaign?.length > 0 && (
          <div className="bg-[#18181B] border border-zinc-800 p-6 rounded-sm mb-8">
            <h2 className="font-bold mb-4">Stats par campagne</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {stats.by_campaign.map((row) => (
                <div key={row.campaign} className="bg-zinc-900 p-4 rounded border border-zinc-800">
                  <p className="font-semibold text-[#FFD60A]">{row.campaign}</p>
                  <p className="text-sm text-zinc-400 mt-2">
                    {row.used} / {row.total} utilisés · {row.consumed} consommés
                  </p>
                  <p className="text-xs text-zinc-500 mt-1">Coût plateforme: {row.platform_cost_eur.toFixed(2)} €</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Generate form */}
        <div className="bg-[#18181B] border border-zinc-800 p-6 rounded-sm mb-8">
          <h2 className="font-bold mb-4">Générer une nouvelle campagne</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <Label className="text-zinc-300">Campagne</Label>
              <Input
                data-testid="promo-campaign-input"
                value={campaign}
                onChange={(e) => setCampaign(e.target.value)}
                className="bg-zinc-900 border-zinc-700 h-11 mt-1"
              />
            </div>
            <div>
              <Label className="text-zinc-300">Prefix code</Label>
              <Input
                data-testid="promo-prefix-input"
                value={prefix}
                onChange={(e) => setPrefix(e.target.value.toUpperCase())}
                className="bg-zinc-900 border-zinc-700 h-11 mt-1 font-mono"
              />
            </div>
            <div>
              <Label className="text-zinc-300">Quantité</Label>
              <Input
                data-testid="promo-count-input"
                type="number"
                min={1}
                max={500}
                value={count}
                onChange={(e) => setCount(e.target.value)}
                className="bg-zinc-900 border-zinc-700 h-11 mt-1"
              />
            </div>
            <div>
              <Label className="text-zinc-300">Distance max (km)</Label>
              <Input
                data-testid="promo-distance-input"
                type="number"
                step="0.5"
                min={0.5}
                max={50}
                value={maxDistance}
                onChange={(e) => setMaxDistance(e.target.value)}
                className="bg-zinc-900 border-zinc-700 h-11 mt-1"
              />
            </div>
            <div>
              <Label className="text-zinc-300">Région</Label>
              <Input
                data-testid="promo-region-input"
                value={region}
                onChange={(e) => setRegion(e.target.value)}
                className="bg-zinc-900 border-zinc-700 h-11 mt-1"
              />
            </div>
            <div>
              <Label className="text-zinc-300">Expire le (ISO)</Label>
              <Input
                data-testid="promo-expires-input"
                value={expiresAt}
                onChange={(e) => setExpiresAt(e.target.value)}
                placeholder="2026-06-30T23:59:59Z"
                className="bg-zinc-900 border-zinc-700 h-11 mt-1 font-mono text-xs"
              />
            </div>
          </div>
          <Button
            onClick={handleGenerate}
            disabled={generating}
            data-testid="promo-generate-btn"
            className="mt-5 bg-[#FFD60A] text-black font-bold hover:bg-[#E6C209]"
          >
            {generating ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Ticket className="w-4 h-4 mr-2" />}
            Générer les codes
          </Button>
        </div>

        {/* Codes list */}
        <div className="bg-[#18181B] border border-zinc-800 p-6 rounded-sm">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-4">
            <div className="flex items-center gap-3">
              <h2 className="font-bold">Codes générés ({codes.length})</h2>
              <Input
                data-testid="promo-filter-input"
                placeholder="Filtrer par campagne..."
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && fetchCodes()}
                className="bg-zinc-900 border-zinc-700 h-9 w-64 text-sm"
              />
              <Button onClick={fetchCodes} size="sm" variant="outline" className="border-zinc-700">
                Filtrer
              </Button>
            </div>
            <div className="flex gap-2">
              <Button
                onClick={copyAllCodes}
                size="sm"
                variant="outline"
                disabled={!codes.length}
                data-testid="promo-copy-all-btn"
                className="border-zinc-700"
              >
                <Copy className="w-3.5 h-3.5 mr-1.5" /> Copier
              </Button>
              <Button
                onClick={downloadCSV}
                size="sm"
                variant="outline"
                disabled={!codes.length}
                data-testid="promo-export-csv-btn"
                className="border-zinc-700"
              >
                <Download className="w-3.5 h-3.5 mr-1.5" /> CSV
              </Button>
              <Button
                onClick={downloadAllQR}
                size="sm"
                variant="outline"
                disabled={!codes.length}
                data-testid="promo-export-qr-zip-btn"
                className="border-zinc-700"
              >
                <Archive className="w-3.5 h-3.5 mr-1.5" /> ZIP QR
              </Button>
            </div>
          </div>

          {codes.length === 0 ? (
            <p className="text-zinc-500 text-center py-8">Aucun code généré pour l'instant.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-zinc-500 border-b border-zinc-800">
                  <tr>
                    <th className="text-left py-2 px-2">Code</th>
                    <th className="text-left py-2 px-2">Campagne</th>
                    <th className="text-left py-2 px-2">État</th>
                    <th className="text-left py-2 px-2">Utilisé par</th>
                    <th className="text-left py-2 px-2">Expire</th>
                    <th className="text-left py-2 px-2">QR</th>
                  </tr>
                </thead>
                <tbody>
                  {codes.map((c) => (
                    <tr key={c.id} className="border-b border-zinc-900 hover:bg-zinc-900/40">
                      <td className="py-2 px-2 font-mono text-[#FFD60A]">{c.code}</td>
                      <td className="py-2 px-2 text-zinc-400">{c.campaign}</td>
                      <td className="py-2 px-2">
                        {c.consumed_at ? (
                          <span className="inline-flex items-center gap-1 text-green-400">
                            <CheckCircle2 className="w-3.5 h-3.5" /> Consommé
                          </span>
                        ) : c.used ? (
                          <span className="text-amber-400">Réservé</span>
                        ) : (
                          <span className="text-zinc-500">Disponible</span>
                        )}
                      </td>
                      <td className="py-2 px-2 text-zinc-500 text-xs">{c.used_by || '—'}</td>
                      <td className="py-2 px-2 text-zinc-500 text-xs">{c.expires_at?.slice(0, 10) || '—'}</td>
                      <td className="py-2 px-2">
                        <button
                          onClick={() => downloadSingleQR(c.code)}
                          className="text-zinc-400 hover:text-[#FFD60A] inline-flex items-center gap-1 text-xs"
                          title={`Télécharger le QR pour ${c.code}`}
                          data-testid={`promo-qr-btn-${c.code}`}
                        >
                          <QrCode className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PromoCodesPage;
