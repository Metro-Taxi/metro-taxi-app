#!/usr/bin/env python3
"""
PATCH v6 — Saisie IBAN/BIC chauffeur (écran dans l'app)
======================================================

Ajoute dans /var/www/metro-taxi-app/frontend/src/pages/DriverEarnings.js :
- States: bankInfo, bankEditing, bankSaving, bankErrors
- Helpers de validation IBAN/BIC + masquage
- Chargement initial via GET /api/drivers/bank-info
- Sauvegarde via PUT /api/drivers/bank-info (endpoint backend déjà existant)
- UI complet : affichage masqué + bouton Modifier + formulaire édition

Le backend a déjà l'endpoint /drivers/bank-info (rien à patcher côté Python).

Usage sur le VPS :
    cd /var/www/metro-taxi-app
    curl -fsSL https://metro-taxi-demo.preview.emergentagent.com/patch_v6_driver_bank.py -o /tmp/patch_v6.py
    python3 /tmp/patch_v6.py
    cd frontend && yarn build && cd ..
    pm2 restart all --update-env

Idempotent : si le patch est déjà appliqué, ne fait rien.
"""
import sys
import shutil
from pathlib import Path
from datetime import datetime

ROOT = Path("/var/www/metro-taxi-app")
FRONTEND_FILE = ROOT / "frontend" / "src" / "pages" / "DriverEarnings.js"


def log(msg, status="ok"):
    icons = {"ok": "✅", "skip": "⏭️ ", "warn": "⚠️ ", "err": "❌"}
    print(f"{icons.get(status, '•')} {msg}")


def backup(path: Path):
    if path.exists():
        bk = path.with_suffix(path.suffix + f".bak-{datetime.now():%Y%m%d-%H%M%S}")
        shutil.copy2(path, bk)
        return bk
    return None


# =========================================================
# Bloc 1 : nouveaux states (à ajouter après historyExpanded)
# =========================================================
NEW_STATES_MARKER = "  const [historyExpanded, setHistoryExpanded] = useState(false);"
NEW_STATES_BLOCK = """  const [historyExpanded, setHistoryExpanded] = useState(false);

  // Bank info management (IBAN + BIC) — patch v6
  const [bankInfo, setBankInfo] = useState({ iban: '', bic: '' });
  const [bankEditing, setBankEditing] = useState(false);
  const [bankSaving, setBankSaving] = useState(false);
  const [bankErrors, setBankErrors] = useState({ iban: '', bic: '' });"""


# =========================================================
# Bloc 2 : useEffect + helpers + load/save (remplace l'ancien useEffect)
# =========================================================
OLD_USEEFFECT = """  useEffect(() => {
    fetchData();
  }, []);"""

NEW_USEEFFECT_AND_HELPERS = """  useEffect(() => {
    fetchData();
    loadBankInfo();
  }, []);

  // ===== Bank info helpers (patch v6) =====
  const normalizeIban = (v) => (v || '').toUpperCase().replace(/\\s+/g, '');
  const normalizeBic = (v) => (v || '').toUpperCase().replace(/\\s+/g, '');
  const isIbanValid = (v) => {
    const s = normalizeIban(v);
    return /^[A-Z]{2}\\d{2}[A-Z0-9]{11,30}$/.test(s);
  };
  const isBicValid = (v) => {
    const s = normalizeBic(v);
    return /^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$/.test(s);
  };
  const maskIban = (v) => {
    const s = normalizeIban(v);
    if (!s || s.length < 8) return s;
    return `${s.slice(0, 4)} •••• •••• ${s.slice(-4)}`;
  };

  const loadBankInfo = async () => {
    try {
      const { data } = await axios.get(`${API}/drivers/bank-info`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setBankInfo({ iban: data?.iban || '', bic: data?.bic || '' });
    } catch (err) {
      // non-bloquant
    }
  };

  const saveBankInfo = async () => {
    const iban = normalizeIban(bankInfo.iban);
    const bic = normalizeBic(bankInfo.bic);
    const errors = {
      iban: isIbanValid(iban) ? '' : 'IBAN invalide (ex: FR76 1234 5678 90...)',
      bic: isBicValid(bic) ? '' : 'BIC invalide (8 ou 11 caractères)',
    };
    setBankErrors(errors);
    if (errors.iban || errors.bic) return;
    setBankSaving(true);
    try {
      await axios.put(`${API}/drivers/bank-info`, { iban, bic }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setBankInfo({ iban, bic });
      setBankEditing(false);
      toast.success(t('driverEarnings.bankSaved', 'Coordonnées bancaires enregistrées'));
    } catch (err) {
      const msg = err?.response?.data?.detail || 'Erreur lors de la sauvegarde';
      toast.error(msg);
    } finally {
      setBankSaving(false);
    }
  };"""


# =========================================================
# Bloc 3 : remplace le vieux bloc Bank Info statique par le nouveau UI complet
# =========================================================
OLD_BANK_BLOCK = """                {/* Bank Info */}
                {driver?.iban && (
                  <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
                    <h4 className="text-white font-medium mb-3 flex items-center gap-2">
                      <Building2 className="w-4 h-4 text-zinc-500" />
                      {t('driverEarnings.bankInfo', 'Informations bancaires')}
                    </h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-zinc-500">IBAN</span>
                        <span className="text-white font-mono">
                          {driver.iban?.slice(0, 4)}****{driver.iban?.slice(-4)}
                        </span>
                      </div>
                      {driver?.bic && (
                        <div className="flex justify-between">
                          <span className="text-zinc-500">BIC</span>
                          <span className="text-white font-mono">{driver.bic}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}"""

NEW_BANK_BLOCK = """                {/* Bank Info — patch v6 : saisie & édition par le chauffeur */}
                <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4" data-testid="driver-bank-info-card">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-white font-medium flex items-center gap-2">
                      <Building2 className="w-4 h-4 text-zinc-500" />
                      {t('driverEarnings.bankInfo', 'Informations bancaires')}
                    </h4>
                    {!bankEditing && bankInfo.iban && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setBankEditing(true)}
                        className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
                        data-testid="driver-bank-edit-btn"
                      >
                        Modifier
                      </Button>
                    )}
                  </div>

                  {!bankEditing && bankInfo.iban && (
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-zinc-500">IBAN</span>
                        <span className="text-white font-mono">{maskIban(bankInfo.iban)}</span>
                      </div>
                      {bankInfo.bic && (
                        <div className="flex justify-between">
                          <span className="text-zinc-500">BIC</span>
                          <span className="text-white font-mono">{bankInfo.bic}</span>
                        </div>
                      )}
                      <p className="text-xs text-zinc-500 mt-3">
                        🔒 Vos coordonnées sont chiffrées et utilisées uniquement pour vos virements mensuels.
                      </p>
                    </div>
                  )}

                  {(bankEditing || !bankInfo.iban) && (
                    <div className="space-y-3">
                      {!bankInfo.iban && (
                        <p className="text-xs text-zinc-400 bg-zinc-950 border border-zinc-800 rounded p-3">
                          ℹ️ Saisissez vos coordonnées bancaires pour recevoir vos virements mensuels (le 15 de chaque mois).
                        </p>
                      )}
                      <div>
                        <label className="block text-xs text-zinc-400 mb-1">IBAN *</label>
                        <input
                          type="text"
                          placeholder="FR76 1234 5678 9012 3456 7890 123"
                          value={bankInfo.iban}
                          onChange={(e) => setBankInfo({ ...bankInfo, iban: e.target.value })}
                          onBlur={() => setBankInfo({ ...bankInfo, iban: normalizeIban(bankInfo.iban) })}
                          className="w-full bg-zinc-950 border border-zinc-700 rounded px-3 py-2 text-white font-mono text-sm focus:outline-none focus:border-yellow-500"
                          data-testid="driver-bank-iban-input"
                          autoComplete="off"
                          spellCheck={false}
                        />
                        {bankErrors.iban && (
                          <p className="text-xs text-red-400 mt-1">{bankErrors.iban}</p>
                        )}
                      </div>
                      <div>
                        <label className="block text-xs text-zinc-400 mb-1">BIC *</label>
                        <input
                          type="text"
                          placeholder="BNPAFRPP (8 ou 11 caractères)"
                          value={bankInfo.bic}
                          onChange={(e) => setBankInfo({ ...bankInfo, bic: e.target.value })}
                          onBlur={() => setBankInfo({ ...bankInfo, bic: normalizeBic(bankInfo.bic) })}
                          className="w-full bg-zinc-950 border border-zinc-700 rounded px-3 py-2 text-white font-mono text-sm focus:outline-none focus:border-yellow-500"
                          data-testid="driver-bank-bic-input"
                          autoComplete="off"
                          spellCheck={false}
                        />
                        {bankErrors.bic && (
                          <p className="text-xs text-red-400 mt-1">{bankErrors.bic}</p>
                        )}
                      </div>
                      <div className="flex gap-2 pt-2">
                        <Button
                          onClick={saveBankInfo}
                          disabled={bankSaving}
                          className="flex-1 bg-yellow-500 hover:bg-yellow-600 text-black font-semibold"
                          data-testid="driver-bank-save-btn"
                        >
                          {bankSaving ? 'Enregistrement...' : 'Enregistrer mes coordonnées'}
                        </Button>
                        {bankInfo.iban && (
                          <Button
                            variant="outline"
                            onClick={() => { setBankEditing(false); setBankErrors({ iban: '', bic: '' }); loadBankInfo(); }}
                            disabled={bankSaving}
                            className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
                            data-testid="driver-bank-cancel-btn"
                          >
                            Annuler
                          </Button>
                        )}
                      </div>
                      <p className="text-xs text-zinc-500">
                        🔒 Données chiffrées. Utilisées uniquement pour vos virements mensuels.
                      </p>
                    </div>
                  )}
                </div>"""


def main():
    print("\n" + "=" * 70)
    print("  PATCH v6 — Saisie IBAN/BIC chauffeur dans l'app")
    print("=" * 70 + "\n")

    if not FRONTEND_FILE.exists():
        log(f"{FRONTEND_FILE} introuvable — abandon", "err")
        sys.exit(1)

    content = FRONTEND_FILE.read_text()
    original = content
    changes = 0

    # Bloc 1 : states
    if "bankEditing" in content:
        log("States bankInfo déjà présents", "skip")
    else:
        if NEW_STATES_MARKER not in content:
            log(f"Ancre states introuvable", "err")
            sys.exit(1)
        content = content.replace(NEW_STATES_MARKER, NEW_STATES_BLOCK, 1)
        log("States bankInfo + helpers ajoutés", "ok")
        changes += 1

    # Bloc 2 : useEffect + helpers
    if "loadBankInfo" in content:
        log("Helpers loadBankInfo/saveBankInfo déjà présents", "skip")
    else:
        if OLD_USEEFFECT not in content:
            log("useEffect d'origine introuvable", "err")
            sys.exit(1)
        content = content.replace(OLD_USEEFFECT, NEW_USEEFFECT_AND_HELPERS, 1)
        log("useEffect + helpers IBAN/BIC ajoutés", "ok")
        changes += 1

    # Bloc 3 : UI bank info
    if 'data-testid="driver-bank-info-card"' in content:
        log("Bloc UI bank info déjà présent", "skip")
    else:
        if OLD_BANK_BLOCK not in content:
            log("Bloc UI bank info d'origine introuvable", "err")
            sys.exit(1)
        content = content.replace(OLD_BANK_BLOCK, NEW_BANK_BLOCK, 1)
        log("Bloc UI bank info remplacé (saisie + édition)", "ok")
        changes += 1

    if changes == 0:
        log("Aucune modification nécessaire — patch déjà appliqué", "skip")
        print("\n" + "=" * 70)
        print("  ✅ DriverEarnings.js déjà à jour")
        print("=" * 70 + "\n")
        return

    bk = backup(FRONTEND_FILE)
    if bk:
        log(f"Backup créé : {bk.name}", "ok")
    FRONTEND_FILE.write_text(content)
    log(f"DriverEarnings.js patché ({changes} bloc(s) modifié(s))", "ok")

    print("\n" + "=" * 70)
    print("  ✅ PATCH v6 APPLIQUÉ — Prochaines étapes :")
    print("=" * 70)
    print("    1. cd /var/www/metro-taxi-app/frontend && yarn build && cd ..")
    print("    2. pm2 restart all --update-env")
    print("    3. Les chauffeurs verront le formulaire IBAN/BIC dans 'Mes gains' > onglet Virements/Stripe")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
