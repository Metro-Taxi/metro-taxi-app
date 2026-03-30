import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Car, Mail, Lock, User, Phone, Eye, EyeOff, CreditCard, FileText, Users, Building2, MapPin, Globe, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';
import { useTranslation } from 'react-i18next';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

// Country flag mapping
const countryFlags = {
  FR: '🇫🇷',
  GB: '🇬🇧',
  ES: '🇪🇸',
  DE: '🇩🇪',
  IT: '🇮🇹',
  PT: '🇵🇹',
  NL: '🇳🇱',
  BE: '🇧🇪',
  CH: '🇨🇭',
  SE: '🇸🇪',
  NO: '🇳🇴',
  DK: '🇩🇰',
  SA: '🇸🇦',
  RU: '🇷🇺',
  CN: '🇨🇳',
  IN: '🇮🇳',
};

// Tax ID labels by country (in local language)
const taxIdLabels = {
  FR: { label: 'Numéro SIRET', placeholder: 'Ex: 123 456 789 00012', format: 'SIRET (14 chiffres)' },
  ES: { label: 'NIF / NIE', placeholder: 'Ex: 12345678A', format: 'NIF/NIE' },
  PT: { label: 'NIF', placeholder: 'Ex: 123456789', format: 'NIF (9 chiffres)' },
  DE: { label: 'Steuernummer', placeholder: 'Ex: 12/345/67890', format: 'Steuernummer' },
  IT: { label: 'Partita IVA', placeholder: 'Ex: IT12345678901', format: 'Partita IVA' },
  GB: { label: 'VAT Number / UTR', placeholder: 'Ex: GB123456789', format: 'VAT/UTR' },
  NL: { label: 'BTW-nummer', placeholder: 'Ex: NL123456789B01', format: 'BTW-nummer' },
  BE: { label: 'Numéro TVA / BTW', placeholder: 'Ex: BE0123456789', format: 'TVA/BTW' },
  CH: { label: 'UID / MwSt-Nr', placeholder: 'Ex: CHE-123.456.789', format: 'UID' },
  SE: { label: 'Organisationsnummer', placeholder: 'Ex: 5501011234', format: 'Org.nummer' },
  NO: { label: 'Organisasjonsnummer', placeholder: 'Ex: 123456789', format: 'Org.nummer' },
  DK: { label: 'CVR-nummer', placeholder: 'Ex: 12345678', format: 'CVR' },
  SA: { label: 'رقم التسجيل الضريبي', placeholder: 'Ex: 300000000000003', format: 'VAT Number' },
  RU: { label: 'ИНН', placeholder: 'Ex: 1234567890', format: 'ИНН' },
  CN: { label: '统一社会信用代码', placeholder: 'Ex: 91110000...', format: '统一社会信用代码' },
  IN: { label: 'GST Number / PAN', placeholder: 'Ex: ABCDE1234F', format: 'GST/PAN' },
  DEFAULT: { label: 'Tax ID', placeholder: 'Enter your tax ID', format: 'Tax ID' }
};

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
    tax_id: '',
    iban: '',
    bic: '',
    region_id: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [regions, setRegions] = useState([]);
  const [regionsLoading, setRegionsLoading] = useState(true);
  const [detectingLocation, setDetectingLocation] = useState(false);
  const [selectedRegion, setSelectedRegion] = useState(null);
  const { registerDriver } = useAuth();
  const navigate = useNavigate();

  // Get tax ID label based on selected region's country
  const getTaxIdConfig = () => {
    if (selectedRegion && selectedRegion.country) {
      return taxIdLabels[selectedRegion.country] || taxIdLabels.DEFAULT;
    }
    return taxIdLabels.DEFAULT;
  };

  useEffect(() => {
    fetchRegions();
  }, []);

  const fetchRegions = async () => {
    try {
      const response = await axios.get(`${API}/api/regions/active`);
      setRegions(response.data);
      // Auto-select if only one region
      if (response.data.length === 1) {
        setFormData(prev => ({ ...prev, region_id: response.data[0].id }));
        setSelectedRegion(response.data[0]);
      }
    } catch (error) {
      console.error('Error fetching regions:', error);
    } finally {
      setRegionsLoading(false);
    }
  };

  const detectRegion = async () => {
    if (!navigator.geolocation) {
      toast.error(t('regions.geolocationNotSupported', 'Geolocation not supported'));
      return;
    }

    setDetectingLocation(true);
    try {
      const position = await new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0
        });
      });

      const { latitude, longitude } = position.coords;
      const response = await axios.get(`${API}/api/regions/detect`, {
        params: { lat: latitude, lng: longitude }
      });

      if (response.data.detected && response.data.region) {
        setFormData(prev => ({ ...prev, region_id: response.data.region.id }));
        setSelectedRegion(response.data.region);
        toast.success(t('regions.detected', 'Region detected: ') + response.data.region.name);
      } else {
        toast.info(t('regions.notDetected', 'No active region found for your location'));
      }
    } catch (error) {
      console.error('Error detecting region:', error);
      toast.error(t('regions.detectionError', 'Error detecting your location'));
    } finally {
      setDetectingLocation(false);
    }
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSelectChange = (name, value) => {
    setFormData({ ...formData, [name]: value });
    // Update selectedRegion when region changes
    if (name === 'region_id') {
      const region = regions.find(r => r.id === value);
      setSelectedRegion(region || null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.password !== formData.confirmPassword) {
      toast.error(t('driverRegister.passwordMismatch'));
      return;
    }

    if (formData.password.length < 6) {
      toast.error(t('driverRegister.passwordTooShort'));
      return;
    }

    if (!formData.region_id) {
      toast.error(t('regions.regionRequired', 'Please select a region'));
      return;
    }

    setLoading(true);

    try {
      const { confirmPassword, ...submitData } = formData;
      submitData.seats = parseInt(submitData.seats);
      await registerDriver(submitData);
      toast.success(t('driverRegister.successMessage'));
      navigate('/login');
    } catch (error) {
      const message = error.response?.data?.detail || t('driverRegister.errorMessage');
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
          <h1 className="text-2xl font-bold text-white mb-2 text-center">{t('driverRegister.title')}</h1>
          <p className="text-zinc-400 text-center mb-6">{t('driverRegister.subtitle')}</p>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Personal Info */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="first_name" className="text-zinc-300">{t('driverRegister.firstName')}</Label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-zinc-500" />
                  <Input
                    id="first_name"
                    name="first_name"
                    value={formData.first_name}
                    onChange={handleChange}
                    placeholder={t('driverRegister.firstNamePlaceholder')}
                    className="pl-10 bg-zinc-900 border-zinc-700 text-white h-12 focus:border-[#FFD60A]"
                    required
                    data-testid="driver-firstname-input"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="last_name" className="text-zinc-300">{t('driverRegister.lastName')}</Label>
                <Input
                  id="last_name"
                  name="last_name"
                  value={formData.last_name}
                  onChange={handleChange}
                  placeholder={t('driverRegister.lastNamePlaceholder')}
                  className="bg-zinc-900 border-zinc-700 text-white h-12 focus:border-[#FFD60A]"
                  required
                  data-testid="driver-lastname-input"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="email" className="text-zinc-300">{t('driverRegister.email')}</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-zinc-500" />
                <Input
                  id="email"
                  name="email"
                  type="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder={t('driverRegister.emailPlaceholder')}
                  className="pl-10 bg-zinc-900 border-zinc-700 text-white h-12 focus:border-[#FFD60A]"
                  required
                  data-testid="driver-email-input"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="phone" className="text-zinc-300">{t('driverRegister.phone')}</Label>
              <div className="relative">
                <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-zinc-500" />
                <Input
                  id="phone"
                  name="phone"
                  type="tel"
                  value={formData.phone}
                  onChange={handleChange}
                  placeholder={t('driverRegister.phonePlaceholder')}
                  className="pl-10 bg-zinc-900 border-zinc-700 text-white h-12 focus:border-[#FFD60A]"
                  required
                  data-testid="driver-phone-input"
                />
              </div>
            </div>

            {/* Region Selection */}
            <div className="pt-4 border-t border-zinc-800">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                  <Globe className="w-5 h-5 text-[#FFD60A]" />
                  {t('regions.selectRegion', 'Select your region')}
                </h3>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={detectRegion}
                  disabled={detectingLocation}
                  className="text-xs"
                >
                  {detectingLocation ? (
                    <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                  ) : (
                    <MapPin className="w-3 h-3 mr-1" />
                  )}
                  {t('regions.detectLocation', 'Detect')}
                </Button>
              </div>
              
              {regionsLoading ? (
                <div className="flex items-center justify-center py-4">
                  <Loader2 className="w-6 h-6 animate-spin text-[#FFD60A]" />
                </div>
              ) : regions.length === 0 ? (
                <p className="text-zinc-400 text-center py-4">
                  {t('regions.noRegions', 'No regions available')}
                </p>
              ) : (
                <div className="grid grid-cols-1 gap-3">
                  {regions.map((region) => (
                    <button
                      key={region.id}
                      type="button"
                      onClick={() => handleSelectChange('region_id', region.id)}
                      className={`
                        relative p-4 rounded-lg border-2 transition-all text-left
                        ${formData.region_id === region.id
                          ? 'border-[#FFD60A] bg-[#FFD60A]/10'
                          : 'border-zinc-700 hover:border-zinc-500 bg-zinc-900/50'
                        }
                      `}
                      data-testid={`region-option-${region.id}`}
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">{countryFlags[region.country] || '🌍'}</span>
                        <div>
                          <h4 className="font-semibold text-white">{region.name}</h4>
                          <p className="text-sm text-zinc-400">
                            {region.currency} • {region.language.toUpperCase()}
                          </p>
                        </div>
                        {formData.region_id === region.id && (
                          <div className="ml-auto">
                            <div className="w-5 h-5 rounded-full bg-[#FFD60A] flex items-center justify-center">
                              <svg className="w-3 h-3 text-black" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                              </svg>
                            </div>
                          </div>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              )}
              
              <p className="text-xs text-zinc-500 mt-3">
                {t('driverRegister.regionNote', 'As a driver, you can only operate in one region.')}
              </p>
            </div>

            {/* Vehicle Info */}
            <div className="pt-4 border-t border-zinc-800">
              <h3 className="text-lg font-semibold text-white mb-4">{t('driverRegister.vehicleInfo')}</h3>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="vehicle_plate" className="text-zinc-300">{t('driverRegister.vehiclePlate')}</Label>
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
                  <Label htmlFor="vehicle_type" className="text-zinc-300">{t('driverRegister.vehicleType')}</Label>
                  <Select 
                    value={formData.vehicle_type} 
                    onValueChange={(value) => handleSelectChange('vehicle_type', value)}
                  >
                    <SelectTrigger className="bg-zinc-900 border-zinc-700 text-white h-12" data-testid="driver-vehicle-type-select">
                      <SelectValue placeholder={t('driverRegister.selectPlaceholder')} />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-900 border-zinc-700">
                      <SelectItem value="berline">{t('driverRegister.vehicleTypes.sedan')}</SelectItem>
                      <SelectItem value="suv">{t('driverRegister.vehicleTypes.suv')}</SelectItem>
                      <SelectItem value="monospace">{t('driverRegister.vehicleTypes.minivan')}</SelectItem>
                      <SelectItem value="van">{t('driverRegister.vehicleTypes.van')}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mt-4">
                <div className="space-y-2">
                  <Label htmlFor="seats" className="text-zinc-300">{t('driverRegister.seats')}</Label>
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
                  <Label htmlFor="vtc_license" className="text-zinc-300">{t('driverRegister.vtcLicense')}</Label>
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
                
                {/* Tax ID field - changes based on country */}
                <div className="space-y-2">
                  <Label htmlFor="tax_id" className="text-zinc-300">
                    {getTaxIdConfig().label}
                    <span className="text-zinc-500 text-xs ml-2">({getTaxIdConfig().format})</span>
                  </Label>
                  <div className="relative">
                    <FileText className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-zinc-500" />
                    <Input
                      id="tax_id"
                      name="tax_id"
                      value={formData.tax_id}
                      onChange={handleChange}
                      placeholder={getTaxIdConfig().placeholder}
                      className="pl-10 bg-zinc-900 border-zinc-700 text-white h-12 focus:border-[#FFD60A]"
                      required
                      data-testid="driver-tax-id-input"
                    />
                  </div>
                  {!selectedRegion && (
                    <p className="text-amber-400 text-xs">{t('driverRegister.selectRegionForTaxId', 'Sélectionnez une région pour voir le format requis')}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Bank Information */}
            <div className="space-y-4 pt-4 border-t border-zinc-800">
              <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                <Building2 className="w-5 h-5 text-[#FFD60A]" />
                {t('driverRegister.bankInfo')}
              </h3>
              <p className="text-zinc-500 text-sm">{t('driverRegister.bankInfoDesc')}</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="iban" className="text-zinc-300">IBAN</Label>
                  <div className="relative">
                    <CreditCard className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-zinc-500" />
                    <Input
                      id="iban"
                      name="iban"
                      value={formData.iban}
                      onChange={handleChange}
                      placeholder="FR76 XXXX XXXX XXXX XXXX XXXX XXX"
                      className="pl-10 bg-zinc-900 border-zinc-700 text-white h-12 focus:border-[#FFD60A] font-mono"
                      data-testid="driver-iban-input"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="bic" className="text-zinc-300">BIC / SWIFT</Label>
                  <div className="relative">
                    <Building2 className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-zinc-500" />
                    <Input
                      id="bic"
                      name="bic"
                      value={formData.bic}
                      onChange={handleChange}
                      placeholder="BNPAFRPP"
                      className="pl-10 bg-zinc-900 border-zinc-700 text-white h-12 focus:border-[#FFD60A] font-mono"
                      data-testid="driver-bic-input"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Password */}
            <div className="pt-4 border-t border-zinc-800">
              <div className="space-y-2">
                <Label htmlFor="password" className="text-zinc-300">{t('driverRegister.password')}</Label>
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
                <Label htmlFor="confirmPassword" className="text-zinc-300">{t('driverRegister.confirmPassword')}</Label>
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

            <div className="bg-green-900/30 p-4 rounded border border-green-700 mt-4">
              <p className="text-green-400 text-sm">
                ✅ {t('driverRegister.autoValidation')}
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
                t('driverRegister.submitBtn')
              )}
            </Button>
          </form>

          <p className="text-zinc-400 text-center mt-6">
            {t('driverRegister.alreadyRegistered')}{' '}
            <Link to="/login" className="text-[#FFD60A] hover:underline">
              {t('driverRegister.loginLink')}
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
};

export default RegisterDriver;
