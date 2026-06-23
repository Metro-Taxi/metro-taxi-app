import React, { useState } from 'react';
import axios from 'axios';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { toast } from 'sonner';
import { Trash2, Eye, CalendarPlus, Loader2 } from 'lucide-react';

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
