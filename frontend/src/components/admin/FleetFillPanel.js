import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Loader2, TrendingUp, AlertTriangle, CheckCircle2, Users } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const HEALTH_META = {
  excellent:        { label: 'Excellent', color: 'text-emerald-400', bg: 'bg-emerald-400/10', icon: CheckCircle2 },
  ok:               { label: 'Correct',   color: 'text-[#FFD60A]',   bg: 'bg-[#FFD60A]/10',   icon: TrendingUp },
  below_threshold:  { label: 'En perte',  color: 'text-red-400',     bg: 'bg-red-400/10',     icon: AlertTriangle },
  no_data:          { label: 'Aucun trajet', color: 'text-zinc-500', bg: 'bg-zinc-800/50',    icon: Users },
};

const FleetFillPanel = ({ token }) => {
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(7);
  const [data, setData] = useState(null);

  const fetchData = async (d = days) => {
    try {
      setLoading(true);
      const { data: res } = await axios.get(`${API}/admin/algorithm/avg-fill?days=${d}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setData(res);
    } catch (e) {
      toast.error('Impossible de charger les stats de remplissage');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []); // eslint-disable-line

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center py-10">
        <Loader2 className="w-8 h-8 animate-spin text-[#FFD60A]" />
      </div>
    );
  }

  if (!data) return null;

  const summary = data.fleet_summary || {};

  return (
    <div className="space-y-4" data-testid="fleet-fill-panel">
      {/* Header + period selector */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-[#FFD60A]" />
            <h3 className="text-lg font-bold text-white">Performance flotte — remplissage moyen</h3>
          </div>
          <p className="text-zinc-500 text-xs mt-1">Plus le remplissage est haut, plus la marge est protégée.</p>
        </div>
        <div className="flex gap-1">
          {[7, 14, 30].map((d) => (
            <button
              key={d}
              onClick={() => { setDays(d); fetchData(d); }}
              className={`px-3 py-1.5 text-xs rounded transition ${
                days === d
                  ? 'bg-[#FFD60A] text-black font-bold'
                  : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
              }`}
              data-testid={`fleet-fill-period-${d}d`}
            >
              {d}j
            </button>
          ))}
        </div>
      </div>

      {/* Fleet summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-[#18181B] border border-zinc-800 rounded p-3" data-testid="fleet-summary-avg">
          <p className="text-xs text-zinc-500">Remplissage moyen</p>
          <p className="text-2xl font-bold text-[#FFD60A]">{summary.avg_passengers_per_ride ?? 0}</p>
          <p className="text-[10px] text-zinc-600">abonnés / trajet</p>
        </div>
        <div className="bg-[#18181B] border border-zinc-800 rounded p-3" data-testid="fleet-summary-rides">
          <p className="text-xs text-zinc-500">Trajets terminés</p>
          <p className="text-2xl font-bold text-white">{summary.total_rides ?? 0}</p>
          <p className="text-[10px] text-zinc-600">sur {data.period_days}j</p>
        </div>
        <div className="bg-[#18181B] border border-zinc-800 rounded p-3" data-testid="fleet-summary-excellent">
          <p className="text-xs text-zinc-500">Chauffeurs excellents</p>
          <p className="text-2xl font-bold text-emerald-400">{summary.excellent_count ?? 0}</p>
          <p className="text-[10px] text-zinc-600">≥ cible de remplissage</p>
        </div>
        <div className="bg-[#18181B] border border-zinc-800 rounded p-3" data-testid="fleet-summary-below">
          <p className="text-xs text-zinc-500">Sous le seuil</p>
          <p className="text-2xl font-bold text-red-400">{summary.below_threshold_count ?? 0}</p>
          <p className="text-[10px] text-zinc-600">trajets déficitaires</p>
        </div>
      </div>

      {/* Driver table */}
      <div className="bg-[#18181B] border border-zinc-800 rounded overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-zinc-900/60 text-zinc-400 text-xs uppercase">
              <tr>
                <th className="text-left px-3 py-2">Chauffeur</th>
                <th className="text-left px-3 py-2">Véhicule</th>
                <th className="text-right px-3 py-2">Trajets</th>
                <th className="text-right px-3 py-2">Abonnés moy.</th>
                <th className="text-right px-3 py-2">Seuil min / cible</th>
                <th className="text-right px-3 py-2">Ratio</th>
                <th className="text-center px-3 py-2">Santé</th>
              </tr>
            </thead>
            <tbody>
              {(data.drivers || []).map((d) => {
                const meta = HEALTH_META[d.health] || HEALTH_META.no_data;
                const Icon = meta.icon;
                return (
                  <motion.tr
                    key={d.driver_id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="border-t border-zinc-800/60 hover:bg-zinc-900/30"
                    data-testid={`fleet-fill-row-${d.driver_id}`}
                  >
                    <td className="px-3 py-2 text-white">
                      {d.driver_name || '—'}
                      {d.pioneer_number && (
                        <span className="ml-2 text-[10px] px-1.5 py-0.5 bg-[#FFD60A]/20 text-[#FFD60A] rounded">
                          P{d.pioneer_number}
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-zinc-400 capitalize">
                      {d.vehicle_type}
                      {d.vehicle_plate && <span className="text-zinc-600 ml-1 text-xs">· {d.vehicle_plate}</span>}
                    </td>
                    <td className="px-3 py-2 text-right text-zinc-300">{d.rides_count}</td>
                    <td className="px-3 py-2 text-right font-bold text-white">{d.avg_passengers_per_ride}</td>
                    <td className="px-3 py-2 text-right text-zinc-500">{d.min_fill_required} / {d.target_fill}</td>
                    <td className="px-3 py-2 text-right">
                      <span className={meta.color + ' font-bold'}>{Math.round((d.fill_ratio || 0) * 100)}%</span>
                    </td>
                    <td className="px-3 py-2 text-center">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs ${meta.bg} ${meta.color}`}>
                        <Icon className="w-3 h-3" />
                        {meta.label}
                      </span>
                    </td>
                  </motion.tr>
                );
              })}
              {(!data.drivers || data.drivers.length === 0) && (
                <tr>
                  <td colSpan={7} className="text-center py-6 text-zinc-500 text-xs">
                    Aucun chauffeur actif trouvé.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default FleetFillPanel;
