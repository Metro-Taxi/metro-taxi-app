import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Car, Mail, Lock, User, Phone, Eye, EyeOff, CreditCard, FileText, Users, Building2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';
import { useTranslation } from 'react-i18next';

const RegisterDriver = () => {
  const { t } = useTranslation();
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    password: '',
    confirmPassword: '',
    vehicle_plate: '',
    vehicle_type: '',
    seats: 4,
    vtc_license: '',
    iban: '',
    bic: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const { registerDriver } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSelectChange = (name, value) => {
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.password !== formData.confirmPassword) {
      toast.error('Les mots de passe ne correspondent pas');
      return;
    }

    if (formData.password.length < 6) {
      toast.error('Le mot de passe doit contenir au moins 6 caractères');
      return;
    }

    setLoading(true);

    try {
      const { confirmPassword, ...submitData } = formData;
      submitData.seats = parseInt(submitData.seats);
      await registerDriver(submitData);
      toast.success('Inscription réussie ! Votre compte est en attente de validation par un administrateur.');
      navigate('/login');
    } catch (error) {
      const message = error.response?.data?.detail || 'Erreur lors de l\'inscription';
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
        className="w-full max-w-lg"
      >
        {/* Logo */}
        <Link to="/" className="flex items-center justify-center gap-2 mb-8">
          <Car className="w-10 h-10 text-[#FFD60A]" />
          <span className="text-3xl font-black text-white">MÉTRO-TAXI</span>
        </Link>

        {/* Register Form */}
        <div className="bg-[#18181B] border border-zinc-800 p-8 rounded-sm">
          <h1 className="text-2xl font-bold text-white mb-2 text-center">Inscription Chauffeur VTC</h1>
          <p className="text-zinc-400 text-center mb-6">Rejoignez notre réseau de chauffeurs partenaires</p>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Personal Info */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="first_name" className="text-zinc-300">Prénom</Label>
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
                    data-testid="driver-firstname-input"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="last_name" className="text-zinc-300">Nom</Label>
                <Input
                  id="last_name"
                  name="last_name"
                  value={formData.last_name}
                  onChange={handleChange}
                  placeholder="Dupont"
                  className="bg-zinc-900 border-zinc-700 text-white h-12 focus:border-[#FFD60A]"
                  required
                  data-testid="driver-lastname-input"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="email" className="text-zinc-300">Email</Label>
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
                  data-testid="driver-email-input"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="phone" className="text-zinc-300">Téléphone</Label>
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
                  data-testid="driver-phone-input"
                />
              </div>
            </div>

            {/* Vehicle Info */}
            <div className="pt-4 border-t border-zinc-800">
              <h3 className="text-lg font-semibold text-white mb-4">Informations véhicule</h3>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="vehicle_plate" className="text-zinc-300">Plaque d'immatriculation</Label>
                  <div className="relative">
                    <CreditCard className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-zinc-500" />
                    <Input
                      id="vehicle_plate"
                      name="vehicle_plate"
                      value={formData.vehicle_plate}
                      onChange={handleChange}
                      placeholder="AB-123-CD"
                      className="pl-10 bg-zinc-900 border-zinc-700 text-white h-12 focus:border-[#FFD60A] uppercase"
                      required
                      data-testid="driver-plate-input"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="vehicle_type" className="text-zinc-300">Type de véhicule</Label>
                  <Select 
                    value={formData.vehicle_type} 
                    onValueChange={(value) => handleSelectChange('vehicle_type', value)}
                  >
                    <SelectTrigger className="bg-zinc-900 border-zinc-700 text-white h-12" data-testid="driver-vehicle-type-select">
                      <SelectValue placeholder="Sélectionner" />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-900 border-zinc-700">
                      <SelectItem value="berline">Berline</SelectItem>
                      <SelectItem value="suv">SUV</SelectItem>
                      <SelectItem value="monospace">Monospace</SelectItem>
                      <SelectItem value="van">Van</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mt-4">
                <div className="space-y-2">
                  <Label htmlFor="seats" className="text-zinc-300">Nombre de places</Label>
                  <div className="relative">
                    <Users className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-zinc-500" />
                    <Input
                      id="seats"
                      name="seats"
                      type="number"
                      min="1"
                      max="8"
                      value={formData.seats}
                      onChange={handleChange}
                      className="pl-10 bg-zinc-900 border-zinc-700 text-white h-12 focus:border-[#FFD60A]"
                      required
                      data-testid="driver-seats-input"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="vtc_license" className="text-zinc-300">Numéro licence VTC</Label>
                  <div className="relative">
                    <FileText className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-zinc-500" />
                    <Input
                      id="vtc_license"
                      name="vtc_license"
                      value={formData.vtc_license}
                      onChange={handleChange}
                      placeholder="VTC-XXXXX"
                      className="pl-10 bg-zinc-900 border-zinc-700 text-white h-12 focus:border-[#FFD60A]"
                      required
                      data-testid="driver-license-input"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Password */}
            <div className="pt-4 border-t border-zinc-800">
              <div className="space-y-2">
                <Label htmlFor="password" className="text-zinc-300">Mot de passe</Label>
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
                    data-testid="driver-password-input"
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

              <div className="space-y-2 mt-4">
                <Label htmlFor="confirmPassword" className="text-zinc-300">Confirmer le mot de passe</Label>
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
                    data-testid="driver-confirm-password-input"
                  />
                </div>
              </div>
            </div>

            <div className="bg-zinc-900/50 p-4 rounded border border-zinc-800 mt-4">
              <p className="text-zinc-400 text-sm">
                ⚠️ Votre compte sera validé par un administrateur avant de pouvoir recevoir des demandes de trajet.
              </p>
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-[#FFD60A] text-black font-bold h-12 hover:bg-[#E6C209] btn-press mt-6"
              data-testid="driver-submit-btn"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-black border-t-transparent rounded-full animate-spin" />
              ) : (
                'SOUMETTRE MA CANDIDATURE'
              )}
            </Button>
          </form>

          <p className="text-zinc-400 text-center mt-6">
            Déjà inscrit ?{' '}
            <Link to="/login" className="text-[#FFD60A] hover:underline">
              Se connecter
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
};

export default RegisterDriver;
