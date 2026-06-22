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
