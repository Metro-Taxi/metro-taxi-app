import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Car, Mail, Lock, Eye, EyeOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const result = await login(email, password);
      toast.success('Connexion réussie !');
      
      if (result.admin) {
        navigate('/admin');
      } else if (result.driver) {
        navigate('/driver');
      } else {
        navigate('/dashboard');
      }
    } catch (error) {
      const message = error.response?.data?.detail || 'Erreur de connexion';
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
        {/* Logo */}
        <Link to="/" className="flex items-center justify-center gap-2 mb-8">
          <Car className="w-10 h-10 text-[#FFD60A]" />
          <span className="text-3xl font-black text-white">MÉTRO-TAXI</span>
        </Link>

        {/* Login Form */}
        <div className="bg-[#18181B] border border-zinc-800 p-8 rounded-sm">
          <h1 className="text-2xl font-bold text-white mb-6 text-center">Connexion</h1>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-zinc-300">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-zinc-500" />
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="votre@email.com"
                  className="pl-10 bg-zinc-900 border-zinc-700 text-white h-12 focus:border-[#FFD60A] focus:ring-[#FFD60A]"
                  required
                  data-testid="login-email-input"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-zinc-300">Mot de passe</Label>
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
                'SE CONNECTER'
              )}
            </Button>
          </form>

          <div className="mt-8 pt-6 border-t border-zinc-800">
            <p className="text-zinc-400 text-center mb-4">Pas encore de compte ?</p>
            <div className="flex flex-col gap-3">
              <Link to="/register/user">
                <Button 
                  variant="outline" 
                  className="w-full border-zinc-700 text-white hover:bg-zinc-800"
                  data-testid="register-user-link"
                >
                  S'inscrire comme usager
                </Button>
              </Link>
              <Link to="/register/driver">
                <Button 
                  variant="outline" 
                  className="w-full border-zinc-700 text-white hover:bg-zinc-800"
                  data-testid="register-driver-link"
                >
                  S'inscrire comme chauffeur
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {/* Admin Login Info */}
        <div className="mt-4 p-4 bg-zinc-900/50 border border-zinc-800 rounded-sm">
          <p className="text-zinc-500 text-sm text-center mb-2">
            Admin: admin@metrotaxi.fr / admin123
          </p>
          <p className="text-zinc-600 text-xs text-center">
            💡 Si vous êtes déjà connecté, <a href="/admin" className="text-[#FFD60A] hover:underline">cliquez ici pour l'admin</a>
          </p>
        </div>
      </motion.div>
    </div>
  );
};

export default Login;
