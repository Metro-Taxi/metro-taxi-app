import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Car, Mail, Lock, User, Phone, Eye, EyeOff, AlertTriangle, LogIn, MapPin, Calendar } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import { toast } from 'sonner';

const RegisterUser = () => {
  const { t } = useTranslation();
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    password: '',
    confirmPassword: '',
    // Nouveaux champs obligatoires
    street_address: '',
    postal_code: '',
    city: '',
    date_of_birth: ''
  });
  // Champs séparés pour la date de naissance
  const [birthDay, setBirthDay] = useState('');
  const [birthMonth, setBirthMonth] = useState('');
  const [birthYear, setBirthYear] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const { registerUser } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  // Construire la date de naissance au format YYYY-MM-DD
  const buildDateOfBirth = () => {
    if (birthDay && birthMonth && birthYear) {
      const day = birthDay.padStart(2, '0');
      const month = birthMonth.padStart(2, '0');
      return `${birthYear}-${month}-${day}`;
    }
    return '';
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.password !== formData.confirmPassword) {
      toast.error(t('auth.register.passwordMismatch'));
      return;
    }

    if (formData.password.length < 6) {
      toast.error(t('errors.passwordTooShort'));
      return;
    }

    // Valider la date de naissance
    const dateOfBirth = buildDateOfBirth();
    if (!birthDay || !birthMonth || !birthYear) {
      toast.error(t('auth.register.dateRequired', 'Veuillez entrer votre date de naissance complète'));
      return;
    }
    
    // Valider que c'est une date valide
    const birthDate = new Date(dateOfBirth);
    const today = new Date();
    const age = today.getFullYear() - birthDate.getFullYear();
    if (age < 16 || age > 120) {
      toast.error(t('auth.register.invalidAge', 'Âge invalide (minimum 16 ans)'));
      return;
    }

    setLoading(true);

    try {
      const { confirmPassword, ...submitData } = formData;
      submitData.date_of_birth = dateOfBirth;
      await registerUser(submitData);
      toast.success(t('auth.register.success'));
      navigate('/subscription');
    } catch (error) {
      const message = error.response?.data?.detail || t('auth.register.error');
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#09090B] flex items-center justify-center px-4 py-12">
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

        {/* Register Form */}
        <div className="bg-[#18181B] border border-zinc-800 p-8 rounded-sm">
          <h1 className="text-2xl font-bold text-white mb-2 text-center">{t('auth.register.user.title')}</h1>
          <p className="text-zinc-400 text-center mb-4">{t('auth.register.user.subtitle')}</p>
          
          {/* PROTECTION DOUBLE PAIEMENT (C) - Message d'avertissement */}
          <div className="mb-6 p-3 bg-amber-500/10 border border-amber-500/40 rounded-lg">
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
              <div className="text-sm">
                <span className="text-amber-400 font-medium">{t('auth.register.alreadyHaveAccount', 'Déjà un compte ?')}</span>
                <p className="text-zinc-400 mt-1">
                  {t('auth.register.loginToAccess', 'Connectez-vous pour retrouver votre abonnement.')}
                </p>
                <Link 
                  to="/login" 
                  className="inline-flex items-center gap-1 text-amber-400 hover:text-amber-300 mt-2 font-medium"
                >
                  <LogIn className="w-4 h-4" />
                  {t('common.login', 'Se connecter')}
                </Link>
              </div>
            </div>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="first_name" className="text-zinc-300">{t('auth.register.firstName')}</Label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-zinc-500" />
                  <Input
                    id="first_name"
                    name="first_name"
                    value={formData.first_name}
                    onChange={handleChange}
                    placeholder="Jean"
                    className="pl-10 bg-zinc-900 border-zinc-700 text-white h-12 focus:border-[#FFD60A]"
                    required
                    data-testid="register-firstname-input"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="last_name" className="text-zinc-300">{t('auth.register.lastName')}</Label>
                <Input
                  id="last_name"
                  name="last_name"
                  value={formData.last_name}
                  onChange={handleChange}
                  placeholder="Dupont"
                  className="bg-zinc-900 border-zinc-700 text-white h-12 focus:border-[#FFD60A]"
                  required
                  data-testid="register-lastname-input"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="email" className="text-zinc-300">{t('auth.register.email')}</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-zinc-500" />
                <Input
                  id="email"
                  name="email"
                  type="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="jean@exemple.com"
                  className="pl-10 bg-zinc-900 border-zinc-700 text-white h-12 focus:border-[#FFD60A]"
                  required
                  data-testid="register-email-input"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="phone" className="text-zinc-300">{t('auth.register.phone')}</Label>
              <div className="relative">
                <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-zinc-500" />
                <Input
                  id="phone"
                  name="phone"
                  type="tel"
                  value={formData.phone}
                  onChange={handleChange}
                  placeholder="06 12 34 56 78"
                  className="pl-10 bg-zinc-900 border-zinc-700 text-white h-12 focus:border-[#FFD60A]"
                  required
                  data-testid="register-phone-input"
                />
              </div>
            </div>

            {/* Adresse complète */}
            <div className="space-y-2">
              <Label htmlFor="street_address" className="text-zinc-300">{t('auth.register.streetAddress')}</Label>
              <div className="relative">
                <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-zinc-500" />
                <Input
                  id="street_address"
                  name="street_address"
                  value={formData.street_address}
                  onChange={handleChange}
                  placeholder="12 rue de la Paix"
                  className="pl-10 bg-zinc-900 border-zinc-700 text-white h-12 focus:border-[#FFD60A]"
                  required
                  data-testid="register-street-input"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="postal_code" className="text-zinc-300">{t('auth.register.postalCode')}</Label>
                <Input
                  id="postal_code"
                  name="postal_code"
                  value={formData.postal_code}
                  onChange={handleChange}
                  placeholder="75001"
                  className="bg-zinc-900 border-zinc-700 text-white h-12 focus:border-[#FFD60A]"
                  required
                  data-testid="register-postal-input"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="city" className="text-zinc-300">{t('auth.register.city')}</Label>
                <Input
                  id="city"
                  name="city"
                  value={formData.city}
                  onChange={handleChange}
                  placeholder="Paris"
                  className="bg-zinc-900 border-zinc-700 text-white h-12 focus:border-[#FFD60A]"
                  required
                  data-testid="register-city-input"
                />
              </div>
            </div>

            {/* Date de naissance - 3 champs séparés */}
            <div className="space-y-2">
              <Label className="text-zinc-300">{t('auth.register.dateOfBirth')}</Label>
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <Input
                    type="text"
                    inputMode="numeric"
                    maxLength={2}
                    value={birthDay}
                    onChange={(e) => {
                      const val = e.target.value.replace(/\D/g, '').slice(0, 2);
                      setBirthDay(val);
                    }}
                    placeholder={t('auth.register.day', 'JJ')}
                    className="bg-zinc-900 border-zinc-700 text-white h-12 focus:border-[#FFD60A] text-center"
                    required
                    data-testid="register-dob-day"
                  />
                </div>
                <div>
                  <Input
                    type="text"
                    inputMode="numeric"
                    maxLength={2}
                    value={birthMonth}
                    onChange={(e) => {
                      const val = e.target.value.replace(/\D/g, '').slice(0, 2);
                      setBirthMonth(val);
                    }}
                    placeholder={t('auth.register.month', 'MM')}
                    className="bg-zinc-900 border-zinc-700 text-white h-12 focus:border-[#FFD60A] text-center"
                    required
                    data-testid="register-dob-month"
                  />
                </div>
                <div>
                  <Input
                    type="text"
                    inputMode="numeric"
                    maxLength={4}
                    value={birthYear}
                    onChange={(e) => {
                      const val = e.target.value.replace(/\D/g, '').slice(0, 4);
                      setBirthYear(val);
                    }}
                    placeholder={t('auth.register.year', 'AAAA')}
                    className="bg-zinc-900 border-zinc-700 text-white h-12 focus:border-[#FFD60A] text-center"
                    required
                    data-testid="register-dob-year"
                  />
                </div>
              </div>
              <p className="text-xs text-zinc-500">{t('auth.register.dateFormat', 'Format: JJ / MM / AAAA')}</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-zinc-300">{t('auth.register.password')}</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-zinc-500" />
                <Input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="••••••••"
                  className="pl-10 pr-10 bg-zinc-900 border-zinc-700 text-white h-12 focus:border-[#FFD60A]"
                  required
                  data-testid="register-password-input"
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

            <div className="space-y-2">
              <Label htmlFor="confirmPassword" className="text-zinc-300">{t('auth.register.confirmPassword')}</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-zinc-500" />
                <Input
                  id="confirmPassword"
                  name="confirmPassword"
                  type={showPassword ? 'text' : 'password'}
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  placeholder="••••••••"
                  className="pl-10 bg-zinc-900 border-zinc-700 text-white h-12 focus:border-[#FFD60A]"
                  required
                  data-testid="register-confirm-password-input"
                />
              </div>
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-[#FFD60A] text-black font-bold h-12 hover:bg-[#E6C209] btn-press mt-6"
              data-testid="register-submit-btn"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-black border-t-transparent rounded-full animate-spin" />
              ) : (
                t('auth.register.submit')
              )}
            </Button>
          </form>

          <p className="text-zinc-400 text-center mt-6">
            {t('auth.register.haveAccount')}{' '}
            <Link to="/login" className="text-[#FFD60A] hover:underline">
              {t('auth.register.login')}
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
};

export default RegisterUser;
