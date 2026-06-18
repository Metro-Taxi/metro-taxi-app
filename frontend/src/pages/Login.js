import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Car, Mail, Lock, Eye, EyeOff, ShieldCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import { toast } from 'sonner';

const Login = () => {
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [otpRequired, setOtpRequired] = useState(false);
  const [otpCode, setOtpCode] = useState('');
  const [otpLoading, setOtpLoading] = useState(false);
  const { login, verifyAdminOtp } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const result = await login(email, password);

      // Admin 2FA: switch to OTP screen
      if (result.otp_required) {
        toast.success(t('auth.login.otpSent', 'Code envoyé par email — vérifiez votre boîte de réception'));
        setOtpRequired(true);
        setLoading(false);
        return;
      }

      toast.success(t('auth.login.success'));
      
      if (result.driver) {
        navigate('/driver');
      } else {
        navigate('/dashboard');
      }
    } catch (error) {
      const message = error.response?.data?.detail || t('auth.login.error');
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const handleOtpSubmit = async (e) => {
    e.preventDefault();
    setOtpLoading(true);
    try {
      await verifyAdminOtp(email, otpCode);
      toast.success(t('auth.login.success'));
      navigate('/admin');
    } catch (error) {
      const message = error.response?.data?.detail || t('auth.login.otpError', 'Code invalide');
      toast.error(message);
    } finally {
      setOtpLoading(false);
    }
  };

  const handleResetToLogin = () => {
    setOtpRequired(false);
    setOtpCode('');
    setPassword('');
  };

  return (
    <div className="min-h-screen bg-[#09090B] flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        {/* Logo */}
        <Link to="/" className="flex items-center justify-center gap-2 mb-8">
          <Car className="w-10 h-10 text-[#FFD60A]" />
          <span className="text-3xl font-black text-white">MÉTRO-TAXI</span>
        </Link>

        {/* Login Form */}
        <div className="bg-[#18181B] border border-zinc-800 p-8 rounded-sm">
          <h1 className="text-2xl font-bold text-white mb-6 text-center">{t('auth.login.title')}</h1>
          
          {otpRequired ? (
            <form onSubmit={handleOtpSubmit} className="space-y-6" data-testid="admin-otp-form">
              <div className="text-center mb-2">
                <ShieldCheck className="w-12 h-12 text-[#FFD60A] mx-auto mb-2" />
                <p className="text-zinc-300 text-sm">
                  {t('auth.login.otpInstruction', 'Un code à 6 chiffres a été envoyé à')}
                </p>
                <p className="text-[#FFD60A] font-semibold mt-1">{email}</p>
                <p className="text-zinc-500 text-xs mt-2">
                  {t('auth.login.otpValidity', 'Le code expire dans 5 minutes.')}
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="otp" className="text-zinc-300">
                  {t('auth.login.otpLabel', 'Code de vérification')}
                </Label>
                <Input
                  id="otp"
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]{6}"
                  maxLength={6}
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  placeholder="000000"
                  className="bg-zinc-900 border-zinc-700 text-white h-14 text-center text-2xl tracking-widest font-mono focus:border-[#FFD60A] focus:ring-[#FFD60A]"
                  required
                  autoFocus
                  data-testid="admin-otp-input"
                />
              </div>
              <Button
                type="submit"
                className="w-full bg-[#FFD60A] text-black hover:bg-[#E6C209] h-12 font-bold"
                disabled={otpLoading || otpCode.length !== 6}
                data-testid="admin-otp-submit-btn"
              >
                {otpLoading ? t('auth.login.verifying', 'Vérification...') : t('auth.login.verify', 'Valider le code')}
              </Button>
              <button
                type="button"
                onClick={handleResetToLogin}
                className="w-full text-zinc-400 text-sm hover:text-white transition-colors"
                data-testid="admin-otp-back-btn"
              >
                {t('auth.login.otpBack', '← Retour à la connexion')}
              </button>
            </form>
          ) : (
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-zinc-300">{t('auth.login.email')}</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-zinc-500" />
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="your@email.com"
                  className="pl-10 bg-zinc-900 border-zinc-700 text-white h-12 focus:border-[#FFD60A] focus:ring-[#FFD60A]"
                  required
                  data-testid="login-email-input"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-zinc-300">{t('auth.login.password')}</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-zinc-500" />
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="pl-10 pr-10 bg-zinc-900 border-zinc-700 text-white h-12 focus:border-[#FFD60A] focus:ring-[#FFD60A]"
                  required
                  data-testid="login-password-input"
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
              disabled={loading}
              className="w-full bg-[#FFD60A] text-black font-bold h-12 hover:bg-[#E6C209] btn-press"
              data-testid="login-submit-btn"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-black border-t-transparent rounded-full animate-spin" />
              ) : (
                t('auth.login.submit')
              )}
            </Button>

            <div className="text-center">
              <Link
                to="/forgot-password"
                className="text-zinc-400 hover:text-[#FFD60A] text-sm transition-colors"
                data-testid="forgot-password-link"
              >
                {t('auth.login.forgotPassword', 'Mot de passe oublié ?')}
              </Link>
            </div>
          </form>
          )}

          {!otpRequired && (
          <div className="mt-8 pt-6 border-t border-zinc-800">
            <p className="text-zinc-400 text-center mb-4">{t('auth.login.noAccount')}</p>
            <div className="flex flex-col gap-3">
              <Link to="/register/user">
                <Button 
                  variant="outline" 
                  className="w-full border-zinc-700 text-white hover:bg-zinc-800"
                  data-testid="register-user-link"
                >
                  {t('auth.login.signUp')} {t('auth.login.asUser')}
                </Button>
              </Link>
              <Link to="/register/driver">
                <Button 
                  variant="outline" 
                  className="w-full border-zinc-700 text-white hover:bg-zinc-800"
                  data-testid="register-driver-link"
                >
                  {t('auth.login.signUp')} {t('auth.login.asDriver')}
                </Button>
              </Link>
            </div>
          </div>
          )}
        </div>

      </motion.div>
    </div>
  );
};

export default Login;
