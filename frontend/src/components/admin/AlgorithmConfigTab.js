import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Loader2, Save, RotateCcw, Brain, MapPin, Moon, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ZONE_META = {
  paris_intra:     { label: 'Paris intra-muros',     icon: MapPin, color: 'text-[#FFD60A]', desc: '75001 → 75020 — Maillage dense, transbordements fréquents' },
  banlieue:        { label: 'Petite couronne',       icon: MapPin, color: 'text-blue-400',  desc: '92, 93, 94 — Densité moyenne' },
  grande_couronne: { label: 'Grande couronne',       icon: MapPin, color: 'text-purple-400', desc: '77, 78, 91, 95 — Densité faible' },
  hors_zone:       { label: 'Hors zone',             icon: MapPin, color: 'text-zinc-400', desc: 'En dehors de l\'Île-de-France — Comportement prudent' },
  night:           { label: 'Profil Nuit (22h-05h)', icon: Moon,   color: 'text-indigo-300', desc: 'Prime sur la zone — Peu de chauffeurs disponibles' },
};

const FIELD_META = {
  segment_min_km:          { label: 'Segment min (km)',      step: 0.5, min: 1, max: 30 },
  segment_max_km:          { label: 'Segment max (km)',      step: 0.5, min: 1, max: 50 },
  max_pickup_distance_km:  { label: 'Pickup max (km)',       step: 0.5, min: 0.5, max: 15 },
  max_transfers:           { label: 'Transbordements max',   step: 1,   min: 0, max: 5 },
  direction_threshold:     { label: 'Seuil direction (0-100)', step: 5, min: 0, max: 100 },
};

const ZONE_ORDER = ['paris_intra', 'banlieue', 'grande_couronne', 'night', 'hors_zone'];

const AlgorithmConfigTab = ({ token }) => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [defaults, setDefaults] = useState({});
  const [effective, setEffective] = useState({});
  const [lastUpdated, setLastUpdated] = useState(null);
  const [draft, setDraft] = useState({});

  const fetchConfig = async () => {
    try {
      setLoading(true);
      const { data } = await axios.get(`${API}/admin/algorithm-config`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setDefaults(data.defaults || {});
      setEffective(data.effective || {});
      setDraft(JSON.parse(JSON.stringify(data.effective || {})));
      setLastUpdated(data.last_updated);
    } catch (e) {
      toast.error('Impossible de charger la config algorithme');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchConfig(); }, []); // eslint-disable-line

  const handleChange = (zone, field, value) => {
    const numericValue = field === 'max_transfers' || field === 'direction_threshold'
      ? parseInt(value, 10)
      : parseFloat(value);
    setDraft((prev) => ({
      ...prev,
      [zone]: { ...prev[zone], [field]: isNaN(numericValue) ? '' : numericValue },
    }));
  };

  const computeDiff = () => {
    const overrides = {};
    Object.keys(defaults).forEach((zone) => {
      const zoneDiff = {};
      Object.keys(defaults[zone] || {}).forEach((field) => {
        const draftVal = draft[zone]?.[field];
        const defaultVal = defaults[zone][field];
        if (draftVal !== undefined && draftVal !== '' && draftVal !== defaultVal) {
          zoneDiff[field] = draftVal;
        }
      });
      if (Object.keys(zoneDiff).length > 0) overrides[zone] = zoneDiff;
    });
    return overrides;
  };

  const handleSave = async () => {
    const overrides = computeDiff();
    if (Object.keys(overrides).length === 0) {
      toast.info('Aucune modification à enregistrer');
      return;
    }
    try {
      setSaving(true);
      await axios.put(`${API}/admin/algorithm-config`, { zones: overrides }, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success('Configuration sauvegardée ✅ — appliquée immédiatement');
      await fetchConfig();
    } catch (e) {
      const detail = e.response?.data?.detail || e.message;
      toast.error(`Erreur : ${detail}`);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    if (!window.confirm('Réinitialiser la configuration aux valeurs par défaut ?')) return;
    try {
      setResetting(true);
      await axios.post(`${API}/admin/algorithm-config/reset`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success('Configuration réinitialisée aux valeurs par défaut');
      await fetchConfig();
    } catch (e) {
      toast.error('Erreur lors de la réinitialisation');
    } finally {
      setResetting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-[#FFD60A]" />
      </div>
    );
  }

  const hasChanges = Object.keys(computeDiff()).length > 0;

  return (
    <div className="space-y-6" data-testid="algorithm-config-tab">
      {/* Header */}
      <div className="bg-[#18181B] border border-zinc-800 rounded p-6">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Brain className="w-6 h-6 text-[#FFD60A]" />
              <h2 className="text-2xl font-bold text-white">Algorithme de transbordement adaptatif</h2>
            </div>
            <p className="text-zinc-400 text-sm max-w-2xl">
              Ajuste les seuils par zone géographique. Les changements s'appliquent <strong className="text-[#FFD60A]">immédiatement</strong> à toutes les nouvelles demandes de trajet.
              Le profil <strong>Nuit</strong> écrase la zone entre <strong>22h-05h (Paris)</strong>.
            </p>
            {lastUpdated && (
              <p className="text-xs text-zinc-500 mt-2">
                Dernière modification : {new Date(lastUpdated).toLocaleString('fr-FR')}
              </p>
            )}
          </div>
          <div className="flex gap-2">
            <Button
              onClick={handleReset}
              disabled={resetting || saving}
              variant="outline"
              className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
              data-testid="algorithm-reset-btn"
            >
              {resetting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <RotateCcw className="w-4 h-4 mr-2" />}
              Réinitialiser
            </Button>
            <Button
              onClick={handleSave}
              disabled={saving || resetting || !hasChanges}
              className="bg-[#FFD60A] text-black hover:bg-[#FFD60A]/90 disabled:opacity-50"
              data-testid="algorithm-save-btn"
            >
              {saving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
              Sauvegarder
            </Button>
          </div>
        </div>
        {hasChanges && (
          <div className="mt-4 flex items-center gap-2 text-amber-400 text-sm bg-amber-400/10 px-3 py-2 rounded">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>Modifications non sauvegardées</span>
          </div>
        )}
      </div>

      {/* Zone cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {ZONE_ORDER.map((zone) => {
          const meta = ZONE_META[zone];
          if (!meta || !draft[zone]) return null;
          const Icon = meta.icon;
          return (
            <motion.div
              key={zone}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-[#18181B] border border-zinc-800 rounded p-5"
              data-testid={`zone-card-${zone}`}
            >
              <div className="flex items-center gap-3 mb-1">
                <Icon className={`w-5 h-5 ${meta.color}`} />
                <h3 className={`text-lg font-bold ${meta.color}`}>{meta.label}</h3>
              </div>
              <p className="text-zinc-500 text-xs mb-4">{meta.desc}</p>
              <div className="grid grid-cols-2 gap-3">
                {Object.keys(FIELD_META).map((field) => {
                  const fmeta = FIELD_META[field];
                  const value = draft[zone]?.[field] ?? '';
                  const defaultVal = defaults[zone]?.[field];
                  const isModified = value !== '' && value !== defaultVal;
                  return (
                    <div key={field}>
                      <Label className="text-zinc-400 text-xs flex items-center justify-between">
                        <span>{fmeta.label}</span>
                        {isModified && (
                          <span className="text-amber-400 text-[10px]">●</span>
                        )}
                      </Label>
                      <Input
                        type="number"
                        step={fmeta.step}
                        min={fmeta.min}
                        max={fmeta.max}
                        value={value}
                        onChange={(e) => handleChange(zone, field, e.target.value)}
                        className={`bg-zinc-900 border-zinc-700 text-white mt-1 ${isModified ? 'border-amber-500' : ''}`}
                        data-testid={`zone-${zone}-field-${field}`}
                      />
                      <p className="text-zinc-600 text-[10px] mt-0.5">défaut : {defaultVal}</p>
                    </div>
                  );
                })}
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Info footer */}
      <div className="bg-zinc-900/50 border border-zinc-800 rounded p-4 text-zinc-400 text-xs space-y-1">
        <p>💡 <strong className="text-zinc-300">Comment ça marche</strong> :</p>
        <p>• Le système détecte la zone de départ via le <strong>code postal</strong> (priorité) puis le <strong>GPS</strong> (fallback).</p>
        <p>• Entre 22h et 05h (heure de Paris), le profil <strong className="text-indigo-300">Nuit</strong> remplace la zone.</p>
        <p>• Plus la zone est dense (Paris intra) → plus les segments sont courts et les transbordements fréquents.</p>
        <p>• Plus la zone est étendue (grande couronne, nuit) → segments longs, moins de transbordements.</p>
      </div>
    </div>
  );
};

export default AlgorithmConfigTab;
