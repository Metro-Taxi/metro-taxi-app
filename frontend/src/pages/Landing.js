import React, { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Car, Users, MapPin, CreditCard, Shield, Clock, Globe, ChevronDown, Volume2, VolumeX, Loader2, HelpCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useTranslation } from 'react-i18next';
import { languages } from '@/i18n';
import HelpCenter from '@/components/HelpCenter';

const API = process.env.REACT_APP_BACKEND_URL;

const Landing = () => {
  const { t, i18n } = useTranslation();
  const [languageMenuOpen, setLanguageMenuOpen] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const [audioPlaying, setAudioPlaying] = useState(false);
  const [audioLoading, setAudioLoading] = useState(false);
  const audioRef = useRef(null);
  const videoRef = useRef(null);
  const videoSectionRef = useRef(null);

  // Get language code - keep full code if it exists in languages list, otherwise get base
  const getLanguageCode = (langCode) => {
    if (!langCode) return 'fr';
    const fullCode = langCode.split('@')[0];
    if (languages.find(l => l.code === fullCode)) {
      return fullCode;
    }
    return fullCode.split('-')[0];
  };
  
  const currentLanguage = languages.find(l => l.code === getLanguageCode(i18n.language)) || languages[0];

  const changeLanguage = (code) => {
    // Stop audio when changing language
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
      setAudioPlaying(false);
    }
    i18n.changeLanguage(code);
    setLanguageMenuOpen(false);
  };

  // SIMPLE audio player - no preloading, just load and play on click
  const playVoiceover = () => {
    // If already playing, stop
    if (audioPlaying && audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
      setAudioPlaying(false);
      return;
    }

    // Show loading state
    setAudioLoading(true);

    // Build audio URL
    const langCode = i18n.language.split('-')[0];
    const audioUrl = `/audio/voiceover/voiceover_${langCode}.mp3`;

    // Create and play audio directly
    const audio = new Audio(audioUrl);
    audioRef.current = audio;

    audio.oncanplaythrough = () => {
      setAudioLoading(false);
      audio.play()
        .then(() => {
          setAudioPlaying(true);
        })
        .catch((err) => {
          console.warn('Play failed:', err);
          setAudioLoading(false);
          setAudioPlaying(false);
        });
    };

    audio.onended = () => {
      setAudioPlaying(false);
      audioRef.current = null;
    };

    audio.onerror = () => {
      console.error('Audio load error');
      setAudioLoading(false);
      setAudioPlaying(false);
      audioRef.current = null;
    };

    // Start loading
    audio.load();
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  return (
    <div className="min-h-screen bg-[#09090B]">
      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
        {/* Background Image */}
        <div 
          className="absolute inset-0 bg-cover bg-center"
          style={{ 
            backgroundImage: 'url(https://images.unsplash.com/photo-1768297941301-1009a05e5514?crop=entropy&cs=srgb&fm=jpg&q=85)',
            filter: 'brightness(0.3)'
          }}
        />
        
        {/* Overlay */}
        <div className="absolute inset-0 bg-gradient-to-b from-[#09090B]/50 via-transparent to-[#09090B]" />
        
        {/* Navigation */}
        <nav className="absolute top-0 left-0 right-0 z-50 px-6 py-4">
          <div className="max-w-7xl mx-auto flex justify-between items-center">
            <div className="flex items-center gap-2">
              <Car className="w-8 h-8 text-[#FFD60A]" />
              <span className="text-2xl font-black text-white tracking-tight">MÉTRO-TAXI</span>
            </div>
            <div className="flex items-center gap-4">
              {/* Language Selector */}
              <div className="relative">
                <Button 
                  variant="ghost" 
                  className="text-white hover:text-[#FFD60A] flex items-center gap-2"
                  onClick={() => setLanguageMenuOpen(!languageMenuOpen)}
                  data-testid="language-selector-btn"
                >
                  <Globe className="w-5 h-5" />
                  <span className="hidden sm:inline">{currentLanguage.flag} {currentLanguage.name}</span>
                  <span className="sm:hidden">{currentLanguage.flag}</span>
                  <ChevronDown className={`w-4 h-4 transition-transform ${languageMenuOpen ? 'rotate-180' : ''}`} />
                </Button>
                
                <AnimatePresence>
                  {languageMenuOpen && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="absolute right-0 mt-2 w-52 bg-[#18181B] border border-zinc-700 rounded-lg shadow-xl overflow-hidden z-50 max-h-80 overflow-y-auto"
                    >
                      {languages.map((lang) => (
                        <button
                          key={lang.code}
                          onClick={() => changeLanguage(lang.code)}
                          className={`w-full px-4 py-2.5 text-left flex items-center gap-3 hover:bg-zinc-800 transition-colors text-sm ${
                            i18n.language === lang.code ? 'bg-[#FFD60A]/10 text-[#FFD60A]' : 'text-white'
                          }`}
                          data-testid={`lang-${lang.code}`}
                        >
                          <span className="text-lg">{lang.flag}</span>
                          <span>{lang.name}</span>
                        </button>
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Help Button */}
              <Button 
                onClick={() => setHelpOpen(true)}
                className="bg-[#FFD60A] text-black font-bold hover:bg-[#E6C209] hidden sm:flex items-center gap-2"
                data-testid="help-nav-btn"
              >
                <HelpCircle className="w-4 h-4" />
                {t('help.button', 'AIDE')}
              </Button>

              <Link to="/login">
                <Button variant="ghost" className="text-white hover:text-[#FFD60A]" data-testid="login-nav-btn">
                  {t('nav.login')}
                </Button>
              </Link>
            </div>
          </div>
        </nav>
        
        {/* Hero Content */}
        <div className="relative z-10 text-center px-6 max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            {/* Eco Badge */}
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.3, duration: 0.5 }}
              className="inline-flex items-center gap-2 bg-green-500/20 border border-green-500/50 px-4 py-2 rounded-full mb-6"
            >
              <span className="text-green-400 text-2xl">🌿</span>
              <span className="text-green-400 font-medium text-sm md:text-base">{t('hero.ecoSlogan')}</span>
            </motion.div>

            <h1 className="text-5xl md:text-7xl font-black text-white mb-6 leading-tight">
              {t('hero.title')}
              <br />
              <span className="text-[#FFD60A]">{t('hero.subtitleHighlight')}</span>
            </h1>
            <p className="text-xl md:text-2xl text-zinc-300 mb-4 max-w-2xl mx-auto">
              {t('hero.description')}
            </p>
            
            {/* Environmental message */}
            <p className="text-sm md:text-base text-green-400 mb-10 max-w-xl mx-auto flex items-center justify-center gap-2">
              <span>🌍</span>
              {t('hero.ecoMessage')}
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/register/user">
                <Button 
                  size="lg" 
                  className="bg-[#FFD60A] text-black font-bold text-lg px-8 py-6 hover:bg-[#E6C209] btn-press"
                  data-testid="signup-user-btn"
                >
                  {t('pricing.cta')}
                </Button>
              </Link>
              <Link to="/register/driver">
                <Button 
                  size="lg" 
                  variant="outline"
                  className="border-2 border-white text-white font-bold text-lg px-8 py-6 hover:bg-white hover:text-black btn-press"
                  data-testid="signup-driver-btn"
                >
                  {t('drivers.cta').split(' ').slice(0, 3).join(' ')}
                </Button>
              </Link>
            </div>
          </motion.div>
        </div>
        
        {/* Scroll Indicator */}
        <motion.div 
          className="absolute bottom-8 left-1/2 transform -translate-x-1/2"
          animate={{ y: [0, 10, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <div className="w-6 h-10 border-2 border-white/50 rounded-full flex justify-center pt-2">
            <div className="w-1 h-3 bg-white/50 rounded-full" />
          </div>
        </motion.div>
      </section>
      
      {/* Video Section */}
      <section ref={videoSectionRef} className="py-20 px-6 bg-[#09090B]">
        <div className="max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-4xl md:text-5xl font-black text-white mb-4">
              {t('video.title').split(' ')[0]} <span className="text-[#FFD60A]">MÉTRO-TAXI</span>
            </h2>
            <p className="text-zinc-400 text-lg">{t('hero.subtitle')}</p>
          </motion.div>
          
          {/* Video Player - AI Generated Promo */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="relative aspect-video bg-zinc-900 rounded-lg overflow-hidden border border-zinc-800"
          >
            <video
              ref={videoRef}
              className="w-full h-full object-cover"
              controls
              autoPlay
              muted
              loop
              playsInline
              poster="https://images.unsplash.com/photo-1768297941301-1009a05e5514?crop=entropy&cs=srgb&fm=jpg&q=85"
            >
              <source src="/videos/metro-taxi-promo.mp4" type="video/mp4" />
              {t('common.error')}
            </video>
            
            {/* Voiceover Button - Simple synchronous click handler for mobile compatibility */}
            <button
              onClick={playVoiceover}
              disabled={audioLoading}
              className={`absolute bottom-4 right-4 flex items-center gap-2 px-4 py-2 rounded-full font-bold transition-all ${
                audioPlaying 
                  ? 'bg-[#FFD60A] text-black' 
                  : audioLoading
                    ? 'bg-zinc-700 text-zinc-400 cursor-wait'
                    : 'bg-green-600 text-white hover:bg-green-700'
              }`}
              data-testid="voiceover-btn"
            >
              {audioLoading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span className="hidden sm:inline">{t('video.loading', 'Chargement...')}</span>
                </>
              ) : audioPlaying ? (
                <>
                  <VolumeX className="w-5 h-5" />
                  <span className="hidden sm:inline">{t('video.stop', 'Stop')}</span>
                </>
              ) : (
                <>
                  <Volume2 className="w-5 h-5" />
                  <span className="hidden sm:inline">{currentLanguage.flag} {t('video.listen', 'Écouter')}</span>
                </>
              )}
            </button>
          </motion.div>
          
          <p className="text-center text-zinc-500 text-sm mt-4">
            🎬 {t('video.title')} - {t('hero.subtitle')}
          </p>
        </div>
      </section>
      
      {/* Features Section */}
      <section className="py-20 px-6 bg-zinc-900/50">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-black text-white mb-4">
              {t('howItWorks.title')}
            </h2>
          </motion.div>
          
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: CreditCard,
                title: t('howItWorks.steps.step1.title'),
                description: t('howItWorks.steps.step1.description')
              },
              {
                icon: MapPin,
                title: t('howItWorks.steps.step2.title'),
                description: t('howItWorks.steps.step2.description')
              },
              {
                icon: Car,
                title: t('howItWorks.steps.step3.title'),
                description: t('howItWorks.steps.step3.description')
              }
            ].map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.2 }}
                viewport={{ once: true }}
                className="bg-[#18181B] border border-zinc-800 p-8 text-center"
              >
                <div className="w-16 h-16 bg-[#FFD60A] rounded-sm flex items-center justify-center mx-auto mb-6">
                  <feature.icon className="w-8 h-8 text-black" />
                </div>
                <h3 className="text-xl font-bold text-white mb-3">{feature.title}</h3>
                <p className="text-zinc-400">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
      
      {/* Pricing Preview */}
      <section className="py-20 px-6 bg-[#09090B]">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-black text-white mb-4">
              {t('pricing.title')}
            </h2>
            <p className="text-zinc-400 text-lg">{t('pricing.subtitle')}</p>
          </motion.div>
          
          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {[
              { name: t('pricing.plans.day.name'), price: t('pricing.plans.day.priceLocal'), period: t('subscription.perDay') },
              { name: t('pricing.plans.week.name'), price: t('pricing.plans.week.priceLocal'), period: t('subscription.perWeek'), popular: true },
              { name: t('pricing.plans.month.name'), price: t('pricing.plans.month.priceLocal'), period: t('subscription.perMonth') }
            ].map((plan, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.2 }}
                viewport={{ once: true }}
                className={`subscription-card ${plan.popular ? 'popular' : ''}`}
              >
                {plan.popular && (
                  <span className="popular-badge">{t('pricing.popularBadge')}</span>
                )}
                <h3 className="text-lg font-bold text-zinc-400 mb-4">{plan.name}</h3>
                <div className="mb-6">
                  <span className="text-5xl font-black text-[#FFD60A]">{plan.price}</span>
                </div>
                <p className="text-zinc-500 mb-6">{plan.period}</p>
                <ul className="space-y-3 text-zinc-300 mb-8">
                  <li className="flex items-center gap-2">
                    <Shield className="w-4 h-4 text-[#FFD60A]" />
                    {t('pricing.features.unlimited')}
                  </li>
                  <li className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-[#FFD60A]" />
                    {t('pricing.features.allVehicles')}
                  </li>
                  <li className="flex items-center gap-2">
                    <Users className="w-4 h-4 text-[#FFD60A]" />
                    {t('pricing.features.eco')}
                  </li>
                </ul>
                <Link to="/register/user">
                  <Button 
                    className={`w-full ${plan.popular ? 'bg-[#FFD60A] text-black hover:bg-[#E6C209]' : 'bg-zinc-800 text-white hover:bg-zinc-700'} font-bold`}
                    data-testid={`plan-${index}-btn`}
                  >
                    {t('pricing.cta')}
                  </Button>
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
      
      {/* Driver Section - Complete */}
      <section className="py-20 px-6 bg-[#09090B]" id="chauffeurs">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-black text-white mb-4">
              {t('drivers.title')}
            </h2>
            <p className="text-zinc-400 text-lg max-w-2xl mx-auto">
              {t('drivers.subtitle')}
            </p>
          </motion.div>

          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Revenue Card */}
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
              className="bg-gradient-to-br from-[#FFD60A] to-[#E6C209] p-8 rounded-lg"
            >
              <h3 className="text-2xl font-black text-black mb-6">{t('drivers.revenue.title')}</h3>
              <div className="bg-black/10 backdrop-blur-sm rounded-lg p-6 mb-6">
                <div className="text-center">
                  <p className="text-black/70 text-sm uppercase tracking-wide mb-2">{t('drivers.revenue.monthly')}</p>
                  <div className="flex items-baseline justify-center gap-2">
                    <span className="text-4xl md:text-5xl font-black text-black">{t('drivers.revenue.rangeMin')}</span>
                    <span className="text-2xl text-black/70">-</span>
                    <span className="text-4xl md:text-5xl font-black text-black">{t('drivers.revenue.rangeMax')}</span>
                  </div>
                  <p className="text-black/60 mt-2">{t('drivers.revenue.monthly')}</p>
                </div>
              </div>
              <div className="bg-black text-white rounded-lg p-4 text-center">
                <p className="text-sm text-zinc-400 mb-1">{t('drivers.revenue.upTo')}</p>
                <p className="text-3xl font-black text-[#FFD60A]">{t('drivers.revenue.maxRevenue')}</p>
                <p className="text-sm text-zinc-400">{t('drivers.revenue.depending')}</p>
              </div>
            </motion.div>

            {/* Benefits List */}
            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
            >
              <h3 className="text-2xl font-bold text-white mb-8">{t('drivers.benefits.title')}</h3>
              <div className="space-y-4">
                {[
                  { icon: "💰", text: t('drivers.benefits.noSubscription'), desc: t('drivers.benefits.noSubscriptionDesc') },
                  { icon: "📊", text: t('drivers.benefits.noCommission'), desc: t('drivers.benefits.noCommissionDesc') },
                  { icon: "👥", text: t('drivers.benefits.subscribedPassengers'), desc: t('drivers.benefits.subscribedPassengersDesc') },
                  { icon: "🗺️", text: t('drivers.benefits.optimizedRoutes'), desc: t('drivers.benefits.optimizedRoutesDesc') },
                  { icon: "🚀", text: t('drivers.benefits.morePassengers'), desc: t('drivers.benefits.morePassengersDesc') }
                ].map((benefit, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4, delay: index * 0.1 }}
                    viewport={{ once: true }}
                    className="flex items-start gap-4 bg-zinc-900 border border-zinc-800 p-4 rounded-lg hover:border-[#FFD60A]/50 transition-colors"
                  >
                    <span className="text-2xl">{benefit.icon}</span>
                    <div>
                      <p className="font-bold text-white">{benefit.text}</p>
                      <p className="text-sm text-zinc-400">{benefit.desc}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          </div>

          {/* Driver App Preview */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="mt-16 bg-zinc-900 border border-zinc-800 rounded-lg p-8"
          >
            <div className="text-center mb-8">
              <h3 className="text-2xl font-bold text-white mb-2">{t('drivers.app.title')}</h3>
              <p className="text-zinc-400">{t('drivers.app.subtitle')}</p>
            </div>
            <div className="grid md:grid-cols-3 gap-6">
              {[
                { icon: "📱", title: t('drivers.app.requests'), desc: t('drivers.app.requestsDesc') },
                { icon: "🛣️", title: t('drivers.app.routes'), desc: t('drivers.app.routesDesc') },
                { icon: "🔄", title: t('drivers.app.transfers'), desc: t('drivers.app.transfersDesc') }
              ].map((feature, index) => (
                <div key={index} className="text-center p-4">
                  <span className="text-4xl mb-4 block">{feature.icon}</span>
                  <h4 className="font-bold text-white mb-2">{feature.title}</h4>
                  <p className="text-sm text-zinc-400">{feature.desc}</p>
                </div>
              ))}
            </div>
          </motion.div>

          {/* CTA */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="mt-12 text-center"
          >
            <Link to="/register/driver">
              <Button 
                size="lg"
                className="bg-[#FFD60A] text-black font-bold text-lg px-10 py-6 hover:bg-[#E6C209] btn-press"
                data-testid="driver-cta-btn"
              >
                {t('drivers.cta')}
              </Button>
            </Link>
            <p className="text-zinc-500 mt-4 text-sm">{t('drivers.ctaSubtext')}</p>
          </motion.div>
        </div>
      </section>
      
      {/* Footer */}
      <footer className="py-12 px-6 bg-[#09090B] border-t border-zinc-800">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center gap-2 mb-4 md:mb-0">
              <Car className="w-6 h-6 text-[#FFD60A]" />
              <span className="text-xl font-black text-white">MÉTRO-TAXI</span>
            </div>
            <div className="flex gap-8 text-zinc-400">
              <Link to="/login" className="hover:text-white transition-colors">{t('nav.login')}</Link>
              <Link to="/register/user" className="hover:text-white transition-colors">{t('nav.register')}</Link>
              <Link to="/register/driver" className="hover:text-white transition-colors">{t('nav.drivers')}</Link>
              <Link to="/cgu" className="hover:text-white transition-colors">{t('footer.cgu', 'CGU')}</Link>
              <Link to="/cgv" className="hover:text-white transition-colors">{t('footer.cgv', 'CGV')}</Link>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t border-zinc-800 text-center text-zinc-500">
            <p>© {new Date().getFullYear()} Métro-Taxi. {t('footer.rights')}.</p>
          </div>
        </div>
      </footer>

      {/* Floating Help Button for Mobile */}
      <button
        onClick={() => setHelpOpen(true)}
        className="fixed bottom-6 right-6 sm:hidden w-14 h-14 bg-[#FFD60A] text-black rounded-full shadow-lg flex items-center justify-center z-40 hover:bg-[#E6C209] transition-colors"
        data-testid="help-floating-btn"
      >
        <HelpCircle className="w-6 h-6" />
      </button>

      {/* Help Center Modal */}
      <HelpCenter 
        isOpen={helpOpen} 
        onClose={() => setHelpOpen(false)} 
        userType="user" 
      />
    </div>
  );
};

export default Landing;
