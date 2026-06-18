import React, { useState } from 'react';
import { Lock, Eye, EyeOff, X, KeyRound } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { useAuth } from '@/contexts/AuthContext';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/**
 * Modal de changement de mot de passe (utilisateur connecté).
 * Réutilisé dans Profile (usager) et DriverDashboard (chauffeur).
 * Patch V9 - 06/2026.
 */
const ChangePasswordModal = ({ open, onClose }) => {
  const { token } = useAuth();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (newPassword.length < 8) {
      toast.error('Le nouveau mot de passe doit faire au moins 8 caractères.');
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error('Les deux mots de passe ne correspondent pas.');
      return;
    }
    setLoading(true);
    try {
      await axios.post(
        `${API}/auth/change-password`,
        { current_password: currentPassword, new_password: newPassword },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Mot de passe modifié avec succès ✅');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      onClose();
    } catch (error) {
      const message = error.response?.data?.detail || 'Erreur lors du changement';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[2500] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={onClose}
          data-testid="change-password-modal"
        >
          <motion.div
            initial={{ scale: 0.95, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.95, y: 20 }}
            onClick={(e) => e.stopPropagation()}
            className="bg-[#18181B] border border-zinc-800 rounded-2xl w-full max-w-md p-6 relative"
          >
            <button
              onClick={onClose}
              className="absolute top-4 right-4 text-zinc-400 hover:text-white"
              data-testid="close-change-password-btn"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="text-center mb-6">
              <KeyRound className="w-12 h-12 text-[#FFD60A] mx-auto mb-2" />
              <h2 className="text-xl font-bold text-white">Changer le mot de passe</h2>
              <p className="text-zinc-400 text-sm mt-1">Pour des raisons de sécurité, choisis-en un fort.</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label className="text-zinc-300 text-sm">Mot de passe actuel</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-zinc-500" />
                  <Input
                    type={showCurrent ? 'text' : 'password'}
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    placeholder="Mot de passe actuel"
                    className="pl-10 pr-10 bg-zinc-900 border-zinc-700 text-white h-11"
                    required
                    data-testid="current-password-input"
                  />
                  <button
                    type="button"
                    onClick={() => setShowCurrent(!showCurrent)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-zinc-500"
                  >
                    {showCurrent ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <Label className="text-zinc-300 text-sm">Nouveau mot de passe</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-zinc-500" />
                  <Input
                    type={showNew ? 'text' : 'password'}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Au moins 8 caractères"
                    className="pl-10 pr-10 bg-zinc-900 border-zinc-700 text-white h-11"
                    required
                    minLength={8}
                    data-testid="new-password-input"
                  />
                  <button
                    type="button"
                    onClick={() => setShowNew(!showNew)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-zinc-500"
                  >
                    {showNew ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <Label className="text-zinc-300 text-sm">Confirmer le nouveau mot de passe</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-zinc-500" />
                  <Input
                    type={showNew ? 'text' : 'password'}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Confirmer"
                    className="pl-10 bg-zinc-900 border-zinc-700 text-white h-11"
                    required
                    minLength={8}
                    data-testid="confirm-password-input"
                  />
                </div>
              </div>

              <Button
                type="submit"
                disabled={loading || !currentPassword || newPassword.length < 8 || newPassword !== confirmPassword}
                className="w-full bg-[#FFD60A] text-black font-bold h-11 hover:bg-[#E6C209]"
                data-testid="submit-change-password-btn"
              >
                {loading ? (
                  <div className="w-5 h-5 border-2 border-black border-t-transparent rounded-full animate-spin" />
                ) : (
                  'Modifier le mot de passe'
                )}
              </Button>
            </form>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default ChangePasswordModal;
