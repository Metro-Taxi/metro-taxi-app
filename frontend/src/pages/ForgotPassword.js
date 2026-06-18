import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Car, Mail, Lock, Eye, EyeOff, KeyRound, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ForgotPassword = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1); // 1: email, 2: code + new pwd
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleRequestCode = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API}/auth/forgot-password`, { email });
      toast.success('Si un compte existe, un code à 6 chiffres a été envoyé par email.');
      setStep(2);
    } catch (error) {
      const message = error.response?.data?.detail || "Erreur lors de l'envoi du code";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    if (newPassword.length < 8) {
      toast.error('Le mot de passe doit faire au moins 8 caractères.');
      return;
    }
    setLoading(true);
    try {
      await axios.post(`${API}/auth/reset-password`, { email, code, new_password: newPassword });
      toast.success('Mot de passe réinitialisé. Connecte-toi avec ton nouveau mot de passe !');
      navigate('/login');
    } catch (error) {
      const message = error.response?.data?.detail || 'Code invalide ou expiré';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#09090B] flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        <Link to="/" className="flex items-center justify-center gap-2 mb-8">
          <Car className="w-10 h-10 text-[#FFD60A]" />
          <span className="text-3xl font-black text-white">MÉTRO-TAXI</span>
        </Link>

        <div className="bg-[#18181B] border border-zinc-800 p-8 rounded-sm">
          <div className="text-center mb-6">
            <KeyRound className="w-12 h-12 text-[#FFD60A] mx-auto mb-2" />
            <h1 className="text-2xl font-bold text-white mb-2">
              {step === 1 ? 'Mot de passe oublié ?' : 'Nouveau mot de passe'}
            </h1>
            <p className="text-zinc-400 text-sm">
              {step === 1
                ? 'Entre ton email, on t\'envoie un code à 6 chiffres.'
                : `Saisis le code reçu sur ${email} et choisis un nouveau mot de passe.`}
            </p>
          </div>

          {step === 1 ? (
            <form onSubmit={handleRequestCode} className="space-y-5" data-testid="forgot-step1-form">
              <div className="space-y-2">
                <Label htmlFor="email" className="text-zinc-300">Email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-zinc-500" />
                  <Input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="ton@email.com"
                    className="pl-10 bg-zinc-900 border-zinc-700 text-white h-12 focus:border-[#FFD60A]"
                    required
                    data-testid="forgot-email-input"
                  />
                </div>
              </div>
              <Button
                type="submit"
                disabled={loading || !email}
                className="w-full bg-[#FFD60A] text-black font-bold h-12 hover:bg-[#E6C209]"
                data-testid="forgot-send-code-btn"
              >
                {loading ? (
                  <div className="w-5 h-5 border-2 border-black border-t-transparent rounded-full animate-spin" />
                ) : (
                  'Envoyer le code'
                )}
              </Button>
            </form>
          ) : (
            <form onSubmit={handleResetPassword} className="space-y-5" data-testid="forgot-step2-form">
              <div className="space-y-2">
                <Label htmlFor="code" className="text-zinc-300">Code à 6 chiffres</Label>
                <Input
                  id="code"
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]{6}"
                  maxLength={6}
                  value={code}
                  onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  placeholder="000000"
                  className="bg-zinc-900 border-zinc-700 text-white h-14 text-center text-2xl tracking-widest font-mono focus:border-[#FFD60A]"
                  required
                  data-testid="forgot-code-input"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="new-password" className="text-zinc-300">Nouveau mot de passe</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-zinc-500" />
                  <Input
                    id="new-password"
                    type={showPassword ? 'text' : 'password'}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Au moins 8 caractères"
                    className="pl-10 pr-10 bg-zinc-900 border-zinc-700 text-white h-12 focus:border-[#FFD60A]"
                    required
                    minLength={8}
                    data-testid="forgot-new-password-input"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-zinc-500 hover:text-white"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>
              <Button
                type="submit"
                disabled={loading || code.length !== 6 || newPassword.length < 8}
                className="w-full bg-[#FFD60A] text-black font-bold h-12 hover:bg-[#E6C209]"
                data-testid="forgot-reset-btn"
              >
                {loading ? (
                  <div className="w-5 h-5 border-2 border-black border-t-transparent rounded-full animate-spin" />
                ) : (
                  'Valider le nouveau mot de passe'
                )}
              </Button>
              <button
                type="button"
                onClick={() => { setStep(1); setCode(''); setNewPassword(''); }}
                className="w-full text-zinc-400 text-sm hover:text-white transition-colors"
                data-testid="forgot-back-btn"
              >
                ← Renvoyer un code
              </button>
            </form>
          )}

          <div className="mt-6 pt-4 border-t border-zinc-800 text-center">
            <Link
              to="/login"
              className="inline-flex items-center gap-1 text-zinc-400 hover:text-white text-sm transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Retour à la connexion
            </Link>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default ForgotPassword;
