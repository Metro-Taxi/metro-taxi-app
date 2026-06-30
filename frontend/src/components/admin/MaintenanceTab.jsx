import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { toast } from 'sonner';
import { Trash2, Eye, CalendarPlus, Loader2, Search } from 'lucide-react';
import DriverEarningsDiagnosticDialog from './DriverEarningsDiagnosticDialog';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const MaintenanceTab = ({ token, currentUserId, currentUserEmail }) => {
  const [loading, setLoading] = useState({ preview: false, purge: false, extend: false });
  const [previewResult, setPreviewResult] = useState(null);
  const [purgeResult, setPurgeResult] = useState(null);
  const [extendResult, setExtendResult] = useState(null);

  const auth = { headers: { Authorization: `Bearer ${token}` } };

  const handlePreview = async () => {
    setLoading((l) => ({ ...l, preview: true }));
    try {
      const { data } = await axios.get(`${API}/admin/test-accounts/preview`, auth);
      setPreviewResult(data);
      toast.success(`${data.total_users} utilisateurs et ${data.total_drivers} chauffeurs de test détectés.`);
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Erreur lors de la prévisualisation.');
    } finally {
      setLoading((l) => ({ ...l, preview: false }));
    }
  };

  const handlePurge = async () => {
    if (!window.confirm("⚠️ Confirmer la suppression DÉFINITIVE de tous les comptes de test ?\n\nCette action est irréversible.\nTon compte et celui de contact@metro-taxi.com sont protégés.")) return;
    setLoading((l) => ({ ...l, purge: true }));
    try {
      const { data } = await axios.post(`${API}/admin/test-accounts/purge`, {}, auth);
      setPurgeResult(data);
      toast.success(`✅ ${data.deleted_users} utilisateurs et ${data.deleted_drivers} chauffeurs supprimés.`);
      setPreviewResult(null);
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Erreur lors de la purge.');
    } finally {
      setLoading((l) => ({ ...l, purge: false }));
    }
  };

  const [extendEmail, setExtendEmail] = useState(currentUserEmail === 'contact@metro-taxi.com' ? 'judeemane@hotmail.com' : (currentUserEmail || ''));
  const [extendDays, setExtendDays] = useState(7);

  const [importUsersJson, setImportUsersJson] = useState('');
  const [importDriversJson, setImportDriversJson] = useState('');
  const [importResult, setImportResult] = useState(null);
  const [importLoading, setImportLoading] = useState(false);
  const [showDiagnostic, setShowDiagnostic] = useState(false);
  const [activatingAll, setActivatingAll] = useState(false);
  const [generatingSepa, setGeneratingSepa] = useState(false);
  const [broadcastMode, setBroadcastMode] = useState(null); // null=loading, true/false=loaded
  const [broadcastDriversCount, setBroadcastDriversCount] = useState(0);
  const [togglingBroadcast, setTogglingBroadcast] = useState(false);
  const [pushDiag, setPushDiag] = useState(null);
  const [loadingPushDiag, setLoadingPushDiag] = useState(false);

  const fetchPushDiagnostic = async () => {
    setLoadingPushDiag(true);
    try {
      const { data } = await axios.get(`${API}/admin/drivers/push-diagnostic`, auth);
      setPushDiag(data);
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Erreur diagnostic push');
    } finally {
      setLoadingPushDiag(false);
    }
  };

  useEffect(() => {
    let alive = true;
    axios.get(`${API}/admin/broadcast-mode`, auth).then(({ data }) => {
      if (!alive) return;
      setBroadcastMode(!!data.enabled);
      setBroadcastDriversCount(data.validated_drivers_count || 0);
    }).catch(() => alive && setBroadcastMode(false));
    return () => { alive = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const toggleBroadcastMode = async () => {
    const next = !broadcastMode;
    const message = next
      ? `Activer le MODE BROADCAST (pré-lancement) ?\n\n• Tous les ${broadcastDriversCount} chauffeurs validés vont apparaître DISPONIBLES aux usagers, même s'ils n'ont pas ouvert leur app.\n• Le système anti-fantôme (auto-offline après 3 min sans GPS) sera DÉSACTIVÉ.\n• Chaque demande de course déclenchera un push sur les téléphones de tous les chauffeurs.\n\nÀ utiliser uniquement pendant la phase de pré-lancement pour amorcer la pompe. À DÉSACTIVER dès que le bouche-à-oreille naturel décolle.`
      : `Désactiver le MODE BROADCAST ?\n\nLes chauffeurs devront à nouveau ouvrir leur app et activer leur disponibilité eux-mêmes pour apparaître aux usagers. Le système anti-fantôme sera réactivé.`;
    if (!window.confirm(message)) return;
    setTogglingBroadcast(true);
    try {
      const { data } = await axios.post(`${API}/admin/broadcast-mode`, { enabled: next }, auth);
      setBroadcastMode(data.enabled);
      if (data.enabled) {
        toast.success(`📡 Broadcast ON. ${data.drivers_reactivated} chauffeurs réactivés.`);
      } else {
        toast.success('📡 Broadcast OFF. Système anti-fantôme réactivé.');
      }
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Erreur toggle broadcast.');
    } finally {
      setTogglingBroadcast(false);
    }
  };

  const handleGenerateSepa = async () => {
    if (!window.confirm("Générer le batch SEPA XML de la semaine en cours ?\n\nLe fichier sera envoyé à ton adresse admin avec le récap des virements.\nLes earnings concernés seront marqués 'paid' avec un sepa_batch_id.\nAction non réversible : utilise-la uniquement si tu vas effectivement uploader le XML dans ta banque.")) return;
    setGeneratingSepa(true);
    try {
      const { data } = await axios.post(`${API}/admin/sepa/generate-current-week`, {}, auth);
      if (data.transactions_count === 0) {
        toast.info(data.message || 'Aucun virement à générer.');
      } else {
        toast.success(`✅ Batch SEPA : ${data.transactions_count} virements, ${data.total_amount_eur} €. Mail envoyé à ${data.email_recipient}.`);
        if (data.errors && data.errors.length > 0) {
          toast.warning(`${data.errors.length} chauffeur(s) ignoré(s) (IBAN manquant ou invalide).`);
        }
      }
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Erreur génération batch SEPA.');
    } finally {
      setGeneratingSepa(false);
    }
  };

  const handleActivateAll = async () => {
    if (!window.confirm("Activer en bloc :\n• TOUS les chauffeurs inscrits (is_active, is_validated, email_verified)\n• UNIQUEMENT les usagers ayant un abonnement actif (email_verified)\n\nAction tracée dans admin_audit_log. Idempotente.")) return;
    setActivatingAll(true);
    try {
      const { data } = await axios.post(`${API}/admin/accounts/activate-all`, {}, auth);
      toast.success(`✅ ${data.drivers_activated} chauffeurs et ${data.users_activated} usagers abonnés activés.`);
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Erreur activation massive.');
    } finally {
      setActivatingAll(false);
    }
  };

  // Nettoie les extensions BSON de mongoexport : {"$oid":"abc"} -> "abc", {"$date":"..."} -> ISO string, etc.
  const cleanBsonExtensions = (obj) => {
    if (obj === null || obj === undefined) return obj;
    if (Array.isArray(obj)) return obj.map(cleanBsonExtensions);
    if (typeof obj !== 'object') return obj;
    const keys = Object.keys(obj);
    if (keys.length === 1) {
      const k = keys[0];
      if (k === '$oid') return String(obj[k]);
      if (k === '$date') {
        const v = obj[k];
        if (typeof v === 'string') return v;
        if (v && typeof v === 'object' && v.$numberLong) return new Date(parseInt(v.$numberLong, 10)).toISOString();
        return String(v);
      }
      if (k === '$numberLong' || k === '$numberInt') return parseInt(obj[k], 10);
      if (k === '$numberDouble' || k === '$numberDecimal') return parseFloat(obj[k]);
    }
    const out = {};
    for (const k of keys) out[k] = cleanBsonExtensions(obj[k]);
    return out;
  };

  // Parser ultra-tolérant : accepte JSON array, JSONL (1 objet par ligne), espaces, ][
  const tolerantParseArray = (raw) => {
    if (!raw || !raw.trim()) return [];
    let t = raw.trim();
    // Vire les BOM et caractères de contrôle invisibles
    t = t.replace(/^\uFEFF/, '');
    // Essai 1 : JSON array standard
    try {
      const arr = JSON.parse(t);
      if (Array.isArray(arr)) return arr.map(cleanBsonExtensions);
      if (typeof arr === 'object' && arr !== null) return [cleanBsonExtensions(arr)];
    } catch (_e1) { /* fallback */ }
    // Essai 2 : plusieurs arrays concaténés [...][...] -> on les fusionne
    if (t.includes('][')) {
      try {
        const fixed = '[' + t.replace(/\]\s*\[/g, ',') + ']';
        // ça va donner [[...],[...]] -> flatten
        const arr = JSON.parse(fixed);
        if (Array.isArray(arr)) return arr.flat(Infinity).map(cleanBsonExtensions);
      } catch (_e2) { /* fallback */ }
    }
    // Essai 3 : JSONL (un objet JSON par ligne, format mongoexport par défaut)
    const lines = t.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
    const out = [];
    for (const line of lines) {
      if (!line || line === '[' || line === ']' || line === ',') continue;
      const clean = line.replace(/,\s*$/, ''); // virgule de fin éventuelle
      try {
        const obj = JSON.parse(clean);
        out.push(cleanBsonExtensions(obj));
      } catch (_e3) { /* skip ligne foireuse */ }
    }
    if (out.length > 0) return out;
    throw new Error('Aucun format reconnu');
  };

  const handleFileUpload = async (e, target) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    const text = await file.text();
    if (target === 'users') setImportUsersJson(text);
    else setImportDriversJson(text);
    toast.success(`Fichier "${file.name}" chargé (${(text.length / 1024).toFixed(1)} ko). Clique sur Importer.`);
  };

  const handleImportLegacy = async () => {
    if (!importUsersJson && !importDriversJson) {
      toast.error("Colle ou uploade au moins un des deux fichiers (usagers ou chauffeurs).");
      return;
    }
    let users = [];
    let drivers = [];
    try {
      if (importUsersJson) users = tolerantParseArray(importUsersJson);
      if (importDriversJson) drivers = tolerantParseArray(importDriversJson);
    } catch (e) {
      toast.error("Format JSON invalide. Essaie le bouton 'Choisir un fichier' pour uploader directement ton .json.");
      console.error('JSON parse error:', e);
      return;
    }
    if (!window.confirm(`Importer ${users.length} usagers et ${drivers.length} chauffeurs ? Les emails déjà existants seront ignorés.`)) return;
    setImportLoading(true);
    try {
      const { data } = await axios.post(
        `${API}/admin/import/legacy-vps`,
        { users, drivers },
        auth
      );
      setImportResult(data);
      toast.success(`✅ ${data.users_imported} usagers + ${data.drivers_imported} chauffeurs importés`);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Erreur lors de l'import.");
    } finally {
      setImportLoading(false);
    }
  };

  const handleExtendByEmail = async () => {
    if (!extendEmail || !extendEmail.includes('@')) {
      toast.error("Saisis un email valide.");
      return;
    }
    setLoading((l) => ({ ...l, extend: true }));
    try {
      const { data } = await axios.post(
        `${API}/admin/users/extend-subscription-by-email?email=${encodeURIComponent(extendEmail)}&days=${extendDays}`,
        {},
        auth
      );
      setExtendResult(data);
      toast.success(`✅ Abonnement de ${data.user_email} prolongé de ${data.days_added} jours`);
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Erreur lors de la prolongation.');
    } finally {
      setLoading((l) => ({ ...l, extend: false }));
    }
  };

  return (
    <div className="space-y-6">
      {/* Diagnostic push subscriptions — décision Capitaine 30/06/2026 */}
      <Card className="bg-[#18181B] border-indigo-700 border-2 p-6">
        <h2 className="text-xl font-bold text-indigo-400 mb-2 flex items-center gap-2">
          🔔 Diagnostic notifications push chauffeurs
        </h2>
        <p className="text-sm text-zinc-400 mb-4">
          Combien de chauffeurs sont effectivement joignables par push PWA ?
          Un chauffeur sans push subscription en BDD <b>ne recevra pas la sonnerie</b> lors d&apos;un broadcast.
          Il doit avoir ouvert l&apos;app Métro-Taxi sur son tél et autorisé les notifications.
        </p>
        <Button
          onClick={fetchPushDiagnostic}
          disabled={loadingPushDiag}
          className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-6 mb-4"
          data-testid="push-diagnostic-btn"
        >
          {loadingPushDiag ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : '🔍 '}
          Lancer le diagnostic
        </Button>

        {pushDiag && (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-zinc-800 p-3 rounded text-center">
                <p className="text-3xl font-bold text-white">{pushDiag.total_validated}</p>
                <p className="text-xs text-zinc-400 mt-1">Chauffeurs validés</p>
              </div>
              <div className="bg-green-900/30 border border-green-700 p-3 rounded text-center">
                <p className="text-3xl font-bold text-green-400">{pushDiag.with_push_count}</p>
                <p className="text-xs text-zinc-400 mt-1">Avec push actif</p>
              </div>
              <div className="bg-red-900/30 border border-red-700 p-3 rounded text-center">
                <p className="text-3xl font-bold text-red-400">{pushDiag.without_push_count}</p>
                <p className="text-xs text-zinc-400 mt-1">SANS push (= sourds)</p>
              </div>
            </div>

            {pushDiag.without_push_count > 0 && (
              <div className="bg-red-900/10 border border-red-800/50 rounded p-3">
                <p className="text-sm text-red-300 font-bold mb-2">
                  ⚠️ {pushDiag.without_push_count} chauffeurs ne reçoivent AUCUNE notification push :
                </p>
                <div className="max-h-64 overflow-y-auto space-y-1">
                  {pushDiag.without_push.map(d => (
                    <div key={d.id} className="text-xs text-zinc-300 flex items-center justify-between py-1 border-b border-zinc-800">
                      <span><b>{d.name || '(sans nom)'}</b> — {d.phone || 'sans tél'}</span>
                      <span className="text-zinc-500 font-mono text-[10px]">{d.email}</span>
                    </div>
                  ))}
                </div>
                <p className="text-[11px] text-zinc-400 mt-3 italic">
                  Action : appelle ces chauffeurs en visio WhatsApp et fais-les ouvrir https://metro-taxi.com sur Chrome (Android) ou Safari (iPhone),
                  installer la PWA (Menu &gt; Ajouter à l&apos;écran d&apos;accueil), se connecter et autoriser les notifications quand la popup apparaît.
                </p>
                <Button
                  onClick={async () => {
                    if (!window.confirm(`Envoyer un email d'activation aux ${pushDiag.without_push_count} chauffeurs sourds ?\n\nChacun recevra un email Resend avec les instructions précises (Android + iPhone) pour activer ses notifications.`)) return;
                    try {
                      const { data } = await axios.post(`${API}/admin/drivers/send-activation-emails`, {}, auth);
                      toast.success(`✅ ${data.emails_sent} emails envoyés, ${data.emails_failed} échecs.`);
                      fetchPushDiagnostic();
                    } catch (err) {
                      toast.error(err?.response?.data?.detail || 'Erreur envoi emails');
                    }
                  }}
                  className="mt-3 bg-amber-600 hover:bg-amber-700 text-white font-bold py-2 px-4 text-sm"
                  data-testid="send-activation-emails-btn"
                >
                  📧 Envoyer email d&apos;activation aux {pushDiag.without_push_count} chauffeurs sourds
                </Button>
                <Button
                  onClick={async () => {
                    if (!window.confirm(`Envoyer le mail de RECTIFICATION aux ${pushDiag.without_push_count} chauffeurs sourds ?\n\nCe mail annule la mention "Saint-Denis 26 juillet" du précédent envoi et recentre sur "des usagers attendent tes courses dès maintenant". Action tracée dans l'audit log.`)) return;
                    try {
                      const { data } = await axios.post(`${API}/admin/drivers/send-rectification-email`, {}, auth);
                      toast.success(`✅ ${data.emails_sent} rectificatifs envoyés, ${data.emails_failed} échecs.`);
                      fetchPushDiagnostic();
                    } catch (err) {
                      toast.error(err?.response?.data?.detail || 'Erreur envoi rectificatif');
                    }
                  }}
                  className="ml-2 mt-3 bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 text-sm"
                  data-testid="send-rectification-emails-btn"
                >
                  📨 Envoyer le rectificatif
                </Button>
              </div>
            )}

            {pushDiag.with_push_count > 0 && (
              <div className="bg-green-900/10 border border-green-800/50 rounded p-3">
                <p className="text-sm text-green-300 font-bold mb-2">
                  ✅ {pushDiag.with_push_count} chauffeurs joignables par push :
                </p>
                <div className="max-h-48 overflow-y-auto space-y-1">
                  {pushDiag.with_push.map(d => (
                    <div key={d.id} className="text-xs text-zinc-300 flex items-center justify-between py-1 border-b border-zinc-800">
                      <span>
                        <b>{d.name || '(sans nom)'}</b> — {d.phone || 'sans tél'}
                        {d.is_active && <span className="ml-2 text-[10px] px-1 py-0.5 bg-green-700/40 text-green-300 rounded">en ligne</span>}
                      </span>
                      <span className="text-zinc-500 font-mono text-[10px]">{d.email}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </Card>

      {/* Mode Broadcast pré-lancement — décision Capitaine 30/06/2026 */}
      <Card className={`bg-[#18181B] border-2 p-6 ${broadcastMode ? 'border-pink-500' : 'border-zinc-700'}`}>
        <div className="flex items-start justify-between gap-4 mb-3">
          <div className="flex-1">
            <h2 className="text-xl font-bold text-pink-400 mb-1 flex items-center gap-2">
              📡 Mode Broadcast — Pré-lancement
              {broadcastMode && (
                <span className="ml-2 px-2 py-0.5 bg-pink-500 text-black text-xs font-bold rounded">ACTIF</span>
              )}
            </h2>
            <p className="text-xs text-zinc-500">
              {broadcastDriversCount} chauffeurs validés en base.
            </p>
          </div>
          <Button
            onClick={toggleBroadcastMode}
            disabled={togglingBroadcast || broadcastMode === null}
            className={`min-w-[160px] font-bold ${broadcastMode ? 'bg-zinc-700 hover:bg-zinc-600 text-white' : 'bg-pink-600 hover:bg-pink-700 text-white'}`}
            data-testid="toggle-broadcast-mode-btn"
          >
            {togglingBroadcast || broadcastMode === null
              ? <Loader2 className="w-4 h-4 animate-spin" />
              : (broadcastMode ? '🛑 Désactiver' : '📡 Activer')}
          </Button>
        </div>
        <p className="text-sm text-zinc-400">
          Quand <b>ACTIF</b> : tous les chauffeurs validés apparaissent <b>disponibles aux usagers</b> même s&apos;ils n&apos;ont pas
          ouvert leur app. Chaque demande de course déclenchera un push critique sur leurs téléphones (système anti-fantôme désactivé).
          <br/>À utiliser pour <b>amorcer la pompe</b> avant le 26 juillet. À désactiver dès que les chauffeurs prennent l&apos;habitude d&apos;ouvrir l&apos;app eux-mêmes.
        </p>
      </Card>

      {/* Activation massive comptes — décision Capitaine 30/06/2026 */}
      <Card className="bg-[#18181B] border-emerald-700 border-2 p-6">
        <h2 className="text-xl font-bold text-emerald-400 mb-2 flex items-center gap-2">
          ⚡ Activation massive des comptes
        </h2>
        <p className="text-sm text-zinc-400 mb-4">
          Active en 1 clic <b>tous les chauffeurs inscrits</b> + <b>uniquement les usagers ayant un abonnement actif</b>.
          Les nouveaux chauffeurs sont activés automatiquement à l&apos;inscription.
          Les nouveaux usagers sont activés automatiquement au paiement de leur abonnement.
          Action idempotente, tracée dans <code>admin_audit_log</code>.
        </p>
        <Button
          onClick={handleActivateAll}
          disabled={activatingAll}
          className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 px-6 flex items-center gap-2"
          data-testid="activate-all-accounts-btn"
        >
          {activatingAll ? <Loader2 className="w-4 h-4 animate-spin" /> : '⚡'}
          Activer chauffeurs inscrits + usagers abonnés
        </Button>
      </Card>

      {/* Batch SEPA hebdomadaire — décision Capitaine 30/06/2026 */}
      <Card className="bg-[#18181B] border-amber-700 border-2 p-6">
        <h2 className="text-xl font-bold text-amber-400 mb-2 flex items-center gap-2">
          🏦 Batch SEPA — Virements chauffeurs
        </h2>
        <p className="text-sm text-zinc-400 mb-4">
          Génère le <b>fichier SEPA XML</b> de la semaine en cours et l&apos;envoie à ton mail admin (avec récap).
          À uploader ensuite dans <b>Société Générale Pro &gt; Virement multiple &gt; Importer un fichier SEPA</b>.
          Le scheduler automatique tourne déjà chaque lundi — ce bouton sert uniquement pour <b>rattraper</b> un lundi manqué ou tester.
          <br/>Les earnings concernés sont marqués <code>paid</code> avec un <code>sepa_batch_id</code>.
        </p>
        <Button
          onClick={handleGenerateSepa}
          disabled={generatingSepa}
          className="bg-amber-600 hover:bg-amber-700 text-white font-bold py-3 px-6 flex items-center gap-2"
          data-testid="generate-sepa-batch-btn"
        >
          {generatingSepa ? <Loader2 className="w-4 h-4 animate-spin" /> : '🏦'}
          Générer le batch SEPA de cette semaine
        </Button>
      </Card>

      {/* Outil diagnostic revenus chauffeur — NOUVEAU */}
      <Card className="bg-[#18181B] border-orange-700 border-2 p-6">
        <h2 className="text-xl font-bold text-orange-400 mb-2 flex items-center gap-2">
          <Search className="w-5 h-5" />
          🔍 Diagnostic revenus chauffeur
        </h2>
        <p className="text-sm text-zinc-400 mb-4">
          Si un chauffeur signale des revenus qui ont disparu ou un virement manquant, lance ce diagnostic.
          Il détecte : (1) doublons de profils (post-import legacy), (2) écarts entre les courses terminées et les revenus stockés,
          (3) courses orphelines (driver_id qui n&apos;existe plus). Tu peux ensuite recalculer les revenus en 1 clic — les mois déjà PAYÉS ne sont jamais touchés.
        </p>
        <Button
          onClick={() => setShowDiagnostic(true)}
          className="bg-orange-600 hover:bg-orange-700 text-white font-bold py-3 px-6 flex items-center gap-2"
          data-testid="open-driver-diagnostic-btn"
        >
          <Search className="w-4 h-4" />
          Ouvrir le diagnostic revenus
        </Button>
      </Card>

      <DriverEarningsDiagnosticDialog
        open={showDiagnostic}
        onClose={() => setShowDiagnostic(false)}
        token={token}
      />

      <Card className="bg-[#18181B] border-blue-700 border-2 p-6">
        <h2 className="text-xl font-bold text-blue-400 mb-2">📥 Importer mes anciens usagers/chauffeurs depuis le VPS</h2>
        <p className="text-sm text-zinc-400 mb-4">
          Deux façons de procéder :<br/>
          1. <b>Uploade ton fichier .json</b> directement (recommandé) — le bouton &quot;Choisir un fichier&quot; ci-dessous.<br/>
          2. Ou colle le contenu dans la zone de texte.<br/>
          Le parser détecte automatiquement le format mongoexport (JSON array OU JSONL ligne par ligne), nettoie les <code>$oid</code>/<code>$date</code>, et ignore les emails déjà présents. Les mots de passe bcrypt sont préservés — tes utilisateurs se reconnectent avec leurs anciens identifiants.
        </p>
        <div className="space-y-4 mb-4">
          <div>
            <label className="block text-xs text-zinc-400 mb-1">Fichier USAGERS (.json export de mongoexport) :</label>
            <input
              type="file"
              accept=".json,.txt,application/json"
              onChange={(e) => handleFileUpload(e, 'users')}
              className="block w-full text-xs text-zinc-300 file:mr-3 file:py-2 file:px-4 file:rounded file:border-0 file:bg-blue-600 file:text-white file:cursor-pointer hover:file:bg-blue-700 mb-2"
              data-testid="import-users-file"
            />
            <textarea
              value={importUsersJson}
              onChange={(e) => setImportUsersJson(e.target.value)}
              placeholder='Ou colle ici : [{"email":"..."}] ou JSONL (1 objet par ligne)'
              rows={3}
              className="w-full px-3 py-2 rounded bg-zinc-900 border border-zinc-700 text-white font-mono text-xs"
              data-testid="import-users-json"
            />
            {importUsersJson && (
              <p className="text-xs text-green-400 mt-1">{importUsersJson.length.toLocaleString()} caractères chargés</p>
            )}
          </div>
          <div>
            <label className="block text-xs text-zinc-400 mb-1">Fichier CHAUFFEURS (.json export de mongoexport) :</label>
            <input
              type="file"
              accept=".json,.txt,application/json"
              onChange={(e) => handleFileUpload(e, 'drivers')}
              className="block w-full text-xs text-zinc-300 file:mr-3 file:py-2 file:px-4 file:rounded file:border-0 file:bg-blue-600 file:text-white file:cursor-pointer hover:file:bg-blue-700 mb-2"
              data-testid="import-drivers-file"
            />
            <textarea
              value={importDriversJson}
              onChange={(e) => setImportDriversJson(e.target.value)}
              placeholder='Ou colle ici : [{"email":"..."}] ou JSONL (1 objet par ligne)'
              rows={3}
              className="w-full px-3 py-2 rounded bg-zinc-900 border border-zinc-700 text-white font-mono text-xs"
              data-testid="import-drivers-json"
            />
            {importDriversJson && (
              <p className="text-xs text-green-400 mt-1">{importDriversJson.length.toLocaleString()} caractères chargés</p>
            )}
          </div>
        </div>
        <Button
          onClick={handleImportLegacy}
          disabled={importLoading}
          className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-6 px-8 w-full flex items-center justify-center gap-2"
          data-testid="import-legacy-btn"
        >
          {importLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : null}
          Importer depuis l&apos;ancien VPS
        </Button>
        {importResult && (
          <div className="mt-4 p-4 bg-zinc-900 border border-green-700 rounded-lg">
            <h3 className="font-bold text-green-400">✅ Import terminé</h3>
            <p className="text-sm text-zinc-300 mt-2">
              {importResult.users_imported} usagers ajoutés ({importResult.users_skipped_already_exist} déjà présents)<br/>
              {importResult.drivers_imported} chauffeurs ajoutés ({importResult.drivers_skipped_already_exist} déjà présents)
            </p>
            {importResult.errors && importResult.errors.length > 0 && (
              <details className="mt-2 text-xs text-red-400">
                <summary>Erreurs ({importResult.errors.length})</summary>
                <ul className="list-disc list-inside mt-1">
                  {importResult.errors.map((e, i) => <li key={i}>{e}</li>)}
                </ul>
              </details>
            )}
          </div>
        )}
      </Card>

      <Card className="bg-[#18181B] border-zinc-800 p-6">
        <h2 className="text-xl font-bold text-[#FFD60A] mb-2">🧹 Maintenance & Comptes de test</h2>
        <p className="text-sm text-zinc-400 mb-6">
          Supprime les anciens comptes de tests laissés par l&apos;agent qualité (emails contenant @test, @example, demo@, etc.).
          Ton compte et celui de contact@metro-taxi.com sont absolument protégés.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Bouton 1 : Aperçu */}
          <Button
            onClick={handlePreview}
            disabled={loading.preview}
            className="bg-blue-600 hover:bg-blue-700 text-white py-6 flex items-center justify-center gap-2"
            data-testid="maintenance-preview-btn"
          >
            {loading.preview ? <Loader2 className="w-5 h-5 animate-spin" /> : <Eye className="w-5 h-5" />}
            Voir les comptes de test (sans supprimer)
          </Button>

          {/* Bouton 2 : Purge */}
          <Button
            onClick={handlePurge}
            disabled={loading.purge}
            className="bg-red-600 hover:bg-red-700 text-white py-6 flex items-center justify-center gap-2"
            data-testid="maintenance-purge-btn"
          >
            {loading.purge ? <Loader2 className="w-5 h-5 animate-spin" /> : <Trash2 className="w-5 h-5" />}
            Supprimer définitivement les comptes de test
          </Button>
        </div>

        {/* Résultat aperçu */}
        {previewResult && (
          <div className="mt-6 p-4 bg-zinc-900 border border-blue-700 rounded-lg" data-testid="maintenance-preview-result">
            <h3 className="font-bold text-blue-400 mb-2">
              Aperçu : {previewResult.total_users} utilisateurs + {previewResult.total_drivers} chauffeurs seront supprimés
            </h3>
            <details className="text-xs text-zinc-300 cursor-pointer">
              <summary className="text-zinc-400 mb-2">Voir la liste détaillée</summary>
              <div className="max-h-60 overflow-y-auto">
                <p className="text-zinc-500 mt-2 font-bold">Utilisateurs :</p>
                <ul className="list-disc list-inside">
                  {previewResult.users_to_delete.map((u) => (
                    <li key={u.id}>{u.email} {u.first_name && `(${u.first_name})`}</li>
                  ))}
                </ul>
                {previewResult.drivers_to_delete.length > 0 && (
                  <>
                    <p className="text-zinc-500 mt-2 font-bold">Chauffeurs :</p>
                    <ul className="list-disc list-inside">
                      {previewResult.drivers_to_delete.map((d) => (
                        <li key={d.id}>{d.email} {d.name && `(${d.name})`}</li>
                      ))}
                    </ul>
                  </>
                )}
              </div>
            </details>
          </div>
        )}

        {/* Résultat purge */}
        {purgeResult && (
          <div className="mt-6 p-4 bg-zinc-900 border border-green-700 rounded-lg" data-testid="maintenance-purge-result">
            <h3 className="font-bold text-green-400">
              ✅ Purge effectuée : {purgeResult.deleted_users} utilisateurs + {purgeResult.deleted_drivers} chauffeurs supprimés
            </h3>
            <p className="text-xs text-zinc-500 mt-2">Comptes préservés : {purgeResult.preserved_emails.join(', ')}</p>
          </div>
        )}
      </Card>

      <Card className="bg-[#18181B] border-zinc-800 p-6">
        <h2 className="text-xl font-bold text-[#FFD60A] mb-2">📅 Prolonger un abonnement (7 jours par défaut)</h2>
        <p className="text-sm text-zinc-400 mb-6">
          Tape l&apos;email de l&apos;usager dont tu veux prolonger l&apos;abonnement (ex: ton compte usager judeemane@hotmail.com).
          7 jours sont ajoutés par défaut.
        </p>

        <div className="flex flex-col md:flex-row gap-3 mb-4">
          <input
            type="email"
            value={extendEmail}
            onChange={(e) => setExtendEmail(e.target.value)}
            placeholder="email@exemple.com"
            className="flex-1 px-4 py-3 rounded-lg bg-zinc-900 border border-zinc-700 text-white focus:border-[#FFD60A] focus:outline-none"
            data-testid="maintenance-extend-email-input"
          />
          <input
            type="number"
            min="1"
            max="365"
            value={extendDays}
            onChange={(e) => setExtendDays(parseInt(e.target.value, 10) || 7)}
            className="w-24 px-4 py-3 rounded-lg bg-zinc-900 border border-zinc-700 text-white focus:border-[#FFD60A] focus:outline-none"
            data-testid="maintenance-extend-days-input"
          />
          <Button
            onClick={handleExtendByEmail}
            disabled={loading.extend || !extendEmail}
            className="bg-[#FFD60A] hover:bg-yellow-400 text-black font-bold px-8 flex items-center gap-2"
            data-testid="maintenance-extend-email-btn"
          >
            {loading.extend ? <Loader2 className="w-5 h-5 animate-spin" /> : <CalendarPlus className="w-5 h-5" />}
            Prolonger
          </Button>
        </div>

        {extendResult && (
          <div className="mt-4 p-4 bg-zinc-900 border border-yellow-700 rounded-lg" data-testid="maintenance-extend-result">
            <h3 className="font-bold text-[#FFD60A]">
              ✅ Abonnement de {extendResult.user_email} prolongé jusqu&apos;au {new Date(extendResult.new_expiry).toLocaleString('fr-FR')}
            </h3>
            <p className="text-xs text-zinc-500 mt-2">+{extendResult.days_added} jours ajoutés{extendResult.user_name ? ` · ${extendResult.user_name}` : ''}</p>
          </div>
        )}
      </Card>
    </div>
  );
};

export default MaintenanceTab;
